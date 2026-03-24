#!/usr/bin/env python3
"""
descargar_todos_reglamentos.py – Descarga los reglamentos internos de los fondos
de TODAS las AGF (Administradoras Generales de Fondos) inscritas en la CMF de Chile.

El script:
  1. Consulta el portal institucional de la CMF para obtener el listado completo
     de AGF vigentes registradas.
  2. Por cada AGF, crea una subcarpeta con su nombre sanitizado.
  3. Busca todos los Fondos Mutuos (FM) y Fondos de Inversión (FI) asociados.
  4. Accede a la página de detalle de cada fondo para obtener el link al reglamento
     interno depositado ante la CMF según la NCG N° 365.
  5. Descarga los PDFs en la subcarpeta `pdfs/` de cada AGF.
  6. Genera `fondos.csv` y `fondos.md` con el índice de fondos por AGF.
  7. Genera un índice global `indice_agf.csv` y `indice_agf.md`.

Genera (por cada AGF):
  <carpeta_agf>/fondos.csv   Índice CSV con datos de fondos y links a reglamentos
  <carpeta_agf>/fondos.md    Versión Markdown del mismo índice
  <carpeta_agf>/pdfs/        PDFs de los reglamentos internos descargados

Genera (global):
  indice_agf.csv             Resumen de todas las AGF procesadas
  indice_agf.md              Versión Markdown del resumen global

Uso:
  python descargar_todos_reglamentos.py                  # descarga todo
  python descargar_todos_reglamentos.py --solo-indice    # solo genera índices
  python descargar_todos_reglamentos.py --agf "BICE"     # solo la AGF que contenga "BICE"
  python descargar_todos_reglamentos.py --tipo FM        # solo Fondos Mutuos
  python descargar_todos_reglamentos.py --tipo FI        # solo Fondos de Inversión
  python descargar_todos_reglamentos.py --delay 1.5      # pausa entre peticiones

Requisitos: Python 3.10+ (sin dependencias externas).
"""

import argparse
import csv
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent

CMF_BASE = "https://www.cmfchile.cl"

# Listado de AGF vigentes
CMF_AGF_LISTA = (
    f"{CMF_BASE}/institucional/mercados/consulta.php"
    "?mercado=V&Estado=VI&entidad=RGAGF"
)
# Registro Público de Depósito de Reglamentos Internos – Fondos Mutuos
CMF_FM_REGLAMENTOS = f"{CMF_BASE}/institucional/inc/deposito_fondos_mutuos.php"
# Registro Público de Depósito de Reglamentos Internos – Fondos de Inversión
CMF_FI_REGLAMENTOS = f"{CMF_BASE}/institucional/inc/deposito_fondos_inversion.php"
# Listado general de Fondos Mutuos
CMF_FM_BUSQUEDA = (
    f"{CMF_BASE}/institucional/mercados/consulta.php?mercado=V&entidad=RGFMU"
)
# Listado general de Fondos de Inversión
CMF_FI_BUSQUEDA = (
    f"{CMF_BASE}/institucional/mercados/consulta.php?mercado=V&entidad=RGFI"
)
# Buscador global de entidades fiscalizadas
CMF_BUSQUEDA_GLOBAL = f"{CMF_BASE}/institucional/mercados/consulta_busqueda.php"

TIMESTAMP_FORMAT = "%d/%m/%Y %H:%M:%S"

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
}

DELAY_ENTRE_REQUESTS = 1.0   # segundos entre peticiones sucesivas
TIMEOUT_S = 30               # tiempo máximo por petición (segundos)

CAMPOS_CSV_FONDOS = [
    "tipo",
    "codigo",
    "nombre",
    "administrador",
    "series",
    "moneda",
    "estado",
    "fecha_reglamento",
    "link_reglamento",
    "archivo_pdf",
    "link_detalle_cmf",
]

CAMPOS_CSV_AGF = [
    "nombre_agf",
    "rut",
    "estado",
    "carpeta",
    "total_fondos",
    "fondos_mutuos",
    "fondos_inversion",
    "con_reglamento",
    "link_cmf",
]

# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------


def fetch(url: str, post_data: dict | None = None, retries: int = 3) -> str:
    """
    Realiza una petición HTTP GET o POST y retorna el cuerpo de la respuesta.

    Args:
        url:       URL destino.
        post_data: Si se provee, realiza POST con estos parámetros form-encoded.
        retries:   Número de reintentos ante error de red.

    Returns:
        HTML/texto de la respuesta.

    Raises:
        RuntimeError: Si no se puede obtener la respuesta tras los reintentos.
    """
    encoded = urllib.parse.urlencode(post_data).encode("utf-8") if post_data else None
    headers = dict(REQUEST_HEADERS)
    if encoded:
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, data=encoded, headers=headers)
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError as exc:
            if attempt == retries:
                raise RuntimeError(
                    f"No se pudo acceder a {url} (intento {attempt}/{retries}): {exc}"
                ) from exc
            wait = 2 ** attempt
            print(
                f"  ⚠️  Reintentando {url} en {wait}s (error: {exc})…",
                file=sys.stderr,
            )
            time.sleep(wait)
    return ""  # inalcanzable


def download_pdf(url: str, dest: Path) -> bool:
    """
    Descarga un PDF desde *url* y lo guarda en *dest*.

    Returns:
        True si la descarga fue exitosa, False en caso contrario.
    """
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  [OMITIDO]  {dest.name} (ya existe)")
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  [DESCARGANDO] {dest.name} … ", end="", flush=True)
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            data = resp.read()
        if len(data) < 1000:
            print(f"ERROR (respuesta muy pequeña: {len(data)} bytes)")
            return False
        dest.write_bytes(data)
        print(f"OK ({len(data):,} bytes)")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"ERROR ({exc})")
        return False


# ---------------------------------------------------------------------------
# Parseo de HTML del portal CMF
# ---------------------------------------------------------------------------


class _TablaParser(HTMLParser):
    """
    Extrae filas de tablas HTML del portal CMF.

    Registra las cabeceras de la primera fila ``<th>`` o ``<tr>`` y los
    datos de las filas siguientes.  También captura el primer ``href`` de
    cada celda para extraer links a páginas de detalle.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_table = 0
        self._in_row = False
        self._in_cell = False
        self._cell_text = ""
        self._cell_href = ""
        self._current_row: list[tuple[str, str]] = []  # (texto, href)
        self.headers: list[str] = []
        self.rows: list[dict] = []
        self._header_captured = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if tag == "table":
            self._in_table += 1
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
        elif tag in ("td", "th") and self._in_row:
            self._in_cell = True
            self._cell_text = ""
            self._cell_href = ad.get("href", "") or ""
        elif tag == "a" and self._in_cell and not self._cell_href:
            self._cell_href = ad.get("href", "") or ""

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            self._current_row.append((self._cell_text.strip(), self._cell_href.strip()))
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._current_row:
                texts = [t for t, _ in self._current_row]
                if not self._header_captured:
                    self.headers = texts
                    self._header_captured = True
                else:
                    row: dict = {}
                    for i, (text, href) in enumerate(self._current_row):
                        key = self.headers[i] if i < len(self.headers) else f"col_{i}"
                        row[key] = text
                        if href:
                            row[f"__href_{key}"] = href
                    self.rows.append(row)
            self._in_row = False
        elif tag == "table":
            self._in_table = max(0, self._in_table - 1)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_text += data


def _parse_tabla(html: str) -> tuple[list[str], list[dict]]:
    """Devuelve (headers, rows) extraídos de la primera tabla del HTML."""
    p = _TablaParser()
    p.feed(html)
    return p.headers, p.rows


# ---------------------------------------------------------------------------
# Extracción de links de reglamento interno
# ---------------------------------------------------------------------------

_RE_REGLAMENTO_HREF = re.compile(
    r'href=["\']([^"\']*(?:reglamento|REGLAMENTO|Reglamento)[^"\']*)["\']',
    re.IGNORECASE,
)
_RE_PDF_HREF = re.compile(
    r'href=["\']([^"\']+\.pdf)["\']',
    re.IGNORECASE,
)


def extraer_link_reglamento(html: str) -> str:
    """
    Extrae el primer link a un PDF de reglamento interno desde un HTML.

    Primero busca links cuyo href contenga la palabra «reglamento»; si no
    encuentra ninguno, devuelve el primer PDF listado en la página.

    Returns:
        URL absoluta del PDF, o cadena vacía si no se encuentra.
    """
    for m in _RE_REGLAMENTO_HREF.finditer(html):
        href = m.group(1).strip()
        if href.endswith(".pdf") or "pdf" in href.lower():
            return _absolute(href)

    # Segundo intento: cualquier PDF en la página
    for m in _RE_PDF_HREF.finditer(html):
        href = m.group(1).strip()
        return _absolute(href)

    return ""


def _absolute(href: str) -> str:
    """Convierte un href relativo en URL absoluta del portal CMF."""
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return f"{CMF_BASE}{href}"
    return f"{CMF_BASE}/{href}"


# ---------------------------------------------------------------------------
# Helpers de extracción de campos
# ---------------------------------------------------------------------------


def _primer_valor(row: dict, claves: tuple[str, ...]) -> str:
    """Retorna el primer valor del dict cuya clave (en minúsculas) contenga alguna de las claves dadas."""
    for k, v in row.items():
        k_lower = k.lower()
        if any(c in k_lower for c in claves) and not k.startswith("__href_"):
            return str(v).strip()
    return ""


def _primer_href(row: dict) -> str:
    """Retorna el primer valor de href almacenado en el dict."""
    for k, v in row.items():
        if k.startswith("__href_") and v:
            return str(v).strip()
    return ""


def _extraer_fecha_reglamento(html: str) -> str:
    """Extrae la fecha del reglamento interno desde el HTML de detalle del fondo."""
    if not html:
        return ""
    bloque = html[max(0, html.lower().find("reglamento")):][:500]
    m = re.search(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", bloque)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Sanitización de nombres para carpetas y archivos
# ---------------------------------------------------------------------------


def _sanitizar_nombre_carpeta(nombre: str) -> str:
    """
    Convierte un nombre de AGF en un nombre de carpeta seguro para el sistema
    de archivos.

    Elimina tildes y caracteres especiales, reemplaza espacios con guiones
    bajos y trunca a 80 caracteres.
    """
    # Normalizar unicode y eliminar diacríticos
    normalizado = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    # Conservar solo letras, dígitos, espacios y guiones
    limpio = re.sub(r"[^\w\s\-]", "", sin_acentos)
    # Reemplazar espacios y guiones múltiples con un único guion bajo
    carpeta = re.sub(r"[\s\-]+", "_", limpio.strip())
    return carpeta[:80].upper()


def _sanitizar_nombre_pdf(nombre: str) -> str:
    """Convierte un nombre de fondo en un prefijo seguro para nombre de archivo PDF."""
    normalizado = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    limpio = re.sub(r"[^\w\s\-]", "", sin_acentos)
    return re.sub(r"[\s\-]+", "_", limpio.strip().lower())[:60]


# ---------------------------------------------------------------------------
# Obtención de lista de AGF
# ---------------------------------------------------------------------------


def obtener_lista_agfs(filtro_nombre: str = "") -> list[dict]:
    """
    Consulta el portal CMF para obtener la lista de todas las AGF vigentes.

    Args:
        filtro_nombre: Si se indica, retorna solo las AGF cuyo nombre contenga
                       este texto (insensible a mayúsculas).

    Returns:
        Lista de dicts con claves: nombre, rut, estado, link_detalle.
    """
    print("Obteniendo lista de AGF vigentes desde CMF…")
    agfs: list[dict] = []

    try:
        html = fetch(CMF_AGF_LISTA)
    except RuntimeError as exc:
        print(f"  ❌  No se pudo obtener la lista de AGF: {exc}", file=sys.stderr)
        return agfs

    _, rows = _parse_tabla(html)

    for row in rows:
        nombre = _primer_valor(row, ("nombre", "razon", "denominacion", "sociedad"))
        rut = _primer_valor(row, ("rut", "run", "rut_sociedad"))
        estado = _primer_valor(row, ("estado", "vigencia"))
        href = _primer_href(row)

        if not nombre:
            continue

        if filtro_nombre and filtro_nombre.upper() not in nombre.upper():
            continue

        agfs.append({
            "nombre": nombre,
            "rut": rut,
            "estado": estado,
            "link_detalle": _absolute(href) if href else "",
        })
        print(f"  ✅  AGF: {nombre}")

    if not agfs and not filtro_nombre:
        # Segundo intento: si la tabla está vacía, puede que haya un listado
        # en un formato diferente; intentar con la búsqueda POST
        print("  ⚠️  Tabla vacía; intentando búsqueda alternativa…", file=sys.stderr)
        try:
            html2 = fetch(
                CMF_BUSQUEDA_GLOBAL,
                post_data={"entidad": "RGAGF", "mercado": "V"},
            )
            _, rows2 = _parse_tabla(html2)
            for row in rows2:
                nombre = _primer_valor(row, ("nombre", "razon", "denominacion"))
                rut = _primer_valor(row, ("rut", "run"))
                estado = _primer_valor(row, ("estado", "vigencia"))
                href = _primer_href(row)
                if nombre:
                    agfs.append({
                        "nombre": nombre,
                        "rut": rut,
                        "estado": estado,
                        "link_detalle": _absolute(href) if href else "",
                    })
        except RuntimeError:
            pass

    print(f"\nTotal AGF encontradas: {len(agfs)}\n")
    return agfs


# ---------------------------------------------------------------------------
# Búsqueda de fondos por AGF
# ---------------------------------------------------------------------------


def _safe_get_detalle(href: str, delay: float = DELAY_ENTRE_REQUESTS) -> str:
    """Obtiene el HTML de una página de detalle de fondo; retorna '' en error."""
    if not href:
        return ""
    url = _absolute(href)
    try:
        time.sleep(delay)
        return fetch(url)
    except RuntimeError as exc:
        print(f"    ⚠️  No se pudo obtener detalle ({url}): {exc}", file=sys.stderr)
        return ""


def buscar_fondos_mutuos_agf(
    agf_nombre: str,
    delay: float = DELAY_ENTRE_REQUESTS,
) -> list[dict]:
    """
    Busca los Fondos Mutuos de la AGF indicada en el portal CMF.

    Intenta primero el Registro de Reglamentos filtrado por administradora.
    Si no retorna resultados, recurre al listado general y filtra localmente.

    Args:
        agf_nombre: Nombre de la AGF tal como aparece en el registro CMF.
        delay:      Pausa entre peticiones HTTP (segundos).

    Returns:
        Lista de dicts con los campos CAMPOS_CSV_FONDOS.
    """
    fondos: list[dict] = []
    agf_upper = agf_nombre.upper()

    # Estrategia 1: Registro de reglamentos filtrado por administradora
    html_reg = ""
    try:
        html_reg = fetch(
            CMF_FM_REGLAMENTOS,
            post_data={"administradora": agf_nombre, "boton_buscar": "Buscar"},
        )
        time.sleep(delay)
    except RuntimeError as exc:
        print(
            f"    ⚠️  No se pudo usar registro de reglamentos FM para {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    # Estrategia 2: Listado general
    html_lista = ""
    try:
        html_lista = fetch(CMF_FM_BUSQUEDA)
        time.sleep(delay)
    except RuntimeError as exc:
        print(
            f"    ❌  Error al buscar fondos mutuos para {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    html = (
        html_reg
        if html_reg and agf_upper in html_reg.upper()
        else html_lista
    )
    if not html:
        return fondos

    try:
        _, rows = _parse_tabla(html)

        for row in rows:
            texto_fila = " ".join(str(v) for v in row.values()).upper()
            if agf_upper not in texto_fila:
                continue

            nombre = _primer_valor(row, ("nombre", "fondo", "denominacion"))
            codigo = _primer_valor(row, ("codigo", "run", "rut", "cod"))
            estado = _primer_valor(row, ("estado", "vigencia"))
            moneda = _primer_valor(row, ("moneda", "currency"))
            series = _primer_valor(row, ("series", "serie", "n_series"))
            agf = _primer_valor(row, ("administradora", "agf", "admin"))
            detalle_href = _primer_href(row)

            detalle_html = _safe_get_detalle(detalle_href, delay)
            link_reg = extraer_link_reglamento(detalle_html) if detalle_html else ""
            fecha_reg = _extraer_fecha_reglamento(detalle_html)

            fondos.append({
                "tipo": "FM",
                "codigo": codigo,
                "nombre": nombre,
                "administrador": agf or agf_nombre,
                "series": series,
                "moneda": moneda,
                "estado": estado,
                "fecha_reglamento": fecha_reg,
                "link_reglamento": link_reg,
                "archivo_pdf": "",
                "link_detalle_cmf": _absolute(detalle_href) if detalle_href else "",
            })
            print(f"    FM: {nombre}")
            time.sleep(delay)

    except (RuntimeError, KeyError, IndexError, ValueError) as exc:
        print(
            f"    ❌  Error al procesar fondos mutuos de {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    return fondos


def buscar_fondos_inversion_agf(
    agf_nombre: str,
    delay: float = DELAY_ENTRE_REQUESTS,
) -> list[dict]:
    """
    Busca los Fondos de Inversión de la AGF indicada en el portal CMF.

    Args:
        agf_nombre: Nombre de la AGF tal como aparece en el registro CMF.
        delay:      Pausa entre peticiones HTTP (segundos).

    Returns:
        Lista de dicts con los campos CAMPOS_CSV_FONDOS.
    """
    fondos: list[dict] = []
    agf_upper = agf_nombre.upper()

    # Estrategia 1: Registro de reglamentos filtrado por administradora
    html_reg = ""
    try:
        html_reg = fetch(
            CMF_FI_REGLAMENTOS,
            post_data={"administradora": agf_nombre, "boton_buscar": "Buscar"},
        )
        time.sleep(delay)
    except RuntimeError as exc:
        print(
            f"    ⚠️  No se pudo usar registro de reglamentos FI para {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    # Estrategia 2: Listado general
    html_lista = ""
    try:
        html_lista = fetch(CMF_FI_BUSQUEDA)
        time.sleep(delay)
    except RuntimeError as exc:
        print(
            f"    ❌  Error al buscar fondos de inversión para {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    html = (
        html_reg
        if html_reg and agf_upper in html_reg.upper()
        else html_lista
    )
    if not html:
        return fondos

    try:
        _, rows = _parse_tabla(html)

        for row in rows:
            texto_fila = " ".join(str(v) for v in row.values()).upper()
            if agf_upper not in texto_fila:
                continue

            nombre = _primer_valor(row, ("nombre", "fondo", "denominacion"))
            codigo = _primer_valor(row, ("codigo", "run", "rut", "cod"))
            estado = _primer_valor(row, ("estado", "vigencia"))
            moneda = _primer_valor(row, ("moneda", "currency"))
            series = _primer_valor(row, ("cuotas", "series", "serie"))
            agf = _primer_valor(row, ("administradora", "agf", "admin"))
            detalle_href = _primer_href(row)

            detalle_html = _safe_get_detalle(detalle_href, delay)
            link_reg = extraer_link_reglamento(detalle_html) if detalle_html else ""
            fecha_reg = _extraer_fecha_reglamento(detalle_html)

            fondos.append({
                "tipo": "FI",
                "codigo": codigo,
                "nombre": nombre,
                "administrador": agf or agf_nombre,
                "series": series,
                "moneda": moneda,
                "estado": estado,
                "fecha_reglamento": fecha_reg,
                "link_reglamento": link_reg,
                "archivo_pdf": "",
                "link_detalle_cmf": _absolute(detalle_href) if detalle_href else "",
            })
            print(f"    FI: {nombre}")
            time.sleep(delay)

    except (RuntimeError, KeyError, IndexError, ValueError) as exc:
        print(
            f"    ❌  Error al procesar fondos de inversión de {agf_nombre}: {exc}",
            file=sys.stderr,
        )

    return fondos


# ---------------------------------------------------------------------------
# Descarga de PDFs
# ---------------------------------------------------------------------------


def nombre_archivo_pdf(fondo: dict) -> str:
    """Genera un nombre de archivo seguro para el PDF del reglamento del fondo."""
    nombre = _sanitizar_nombre_pdf(fondo.get("nombre", "sin_nombre"))
    tipo = fondo["tipo"].lower()
    codigo = re.sub(r"\W", "", fondo.get("codigo", ""))
    if codigo:
        return f"ri_{tipo}_{codigo}_{nombre}.pdf"
    return f"ri_{tipo}_{nombre}.pdf"


def descargar_pdfs_agf(fondos: list[dict], pdfs_dir: Path) -> list[dict]:
    """
    Descarga los PDFs de reglamentos internos en la carpeta indicada.

    Actualiza el campo ``archivo_pdf`` de cada fondo con el nombre del archivo
    descargado.

    Returns:
        La misma lista de fondos con el campo ``archivo_pdf`` actualizado.
    """
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    con_link = [f for f in fondos if f.get("link_reglamento")]
    sin_link = len(fondos) - len(con_link)

    if not con_link:
        return fondos

    print(f"  Descargando PDFs ({len(con_link)} con link, {sin_link} sin link)…")

    for fondo in fondos:
        url = fondo.get("link_reglamento", "")
        if not url:
            continue
        nombre_pdf = nombre_archivo_pdf(fondo)
        dest = pdfs_dir / nombre_pdf
        ok = download_pdf(url, dest)
        if ok:
            fondo["archivo_pdf"] = nombre_pdf
        time.sleep(DELAY_ENTRE_REQUESTS)

    return fondos


# ---------------------------------------------------------------------------
# Generación de índices CSV y Markdown por AGF
# ---------------------------------------------------------------------------


def escribir_csv_fondos(fondos: list[dict], ruta: Path) -> None:
    """Escribe el índice de fondos de una AGF en formato CSV."""
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CAMPOS_CSV_FONDOS,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for fondo in fondos:
            writer.writerow({k: fondo.get(k, "") for k in CAMPOS_CSV_FONDOS})


def escribir_md_fondos(fondos: list[dict], agf_nombre: str, ruta: Path) -> None:
    """Escribe el índice de fondos de una AGF en formato Markdown."""
    ahora = datetime.now().strftime(TIMESTAMP_FORMAT)
    fm = [f for f in fondos if f["tipo"] == "FM"]
    fi = [f for f in fondos if f["tipo"] == "FI"]

    lineas: list[str] = [
        f"# Reglamentos Internos – {agf_nombre}",
        "",
        f"> Generado el {ahora}  ",
        f"> Fuente: [CMF – Portal Institucional]({CMF_BASE})",
        "",
        f"Total de fondos encontrados: **{len(fondos)}**"
        f" ({len(fm)} Fondos Mutuos · {len(fi)} Fondos de Inversión)",
        "",
    ]

    for titulo, lista in (
        ("Fondos Mutuos (FM)", fm),
        ("Fondos de Inversión (FI)", fi),
    ):
        if not lista:
            continue
        lineas += [
            f"## {titulo}",
            "",
            "| Código | Nombre | Estado | Moneda | Fecha Reglamento | Reglamento Interno | Detalle CMF |",
            "|--------|--------|--------|--------|------------------|--------------------|-------------|",
        ]
        for f in lista:
            link_reg = (
                f"[PDF ↗]({f['link_reglamento']})" if f.get("link_reglamento") else "–"
            )
            link_det = (
                f"[CMF ↗]({f['link_detalle_cmf']})" if f.get("link_detalle_cmf") else "–"
            )
            lineas.append(
                f"| {f.get('codigo', '')} "
                f"| {f.get('nombre', '')} "
                f"| {f.get('estado', '')} "
                f"| {f.get('moneda', '')} "
                f"| {f.get('fecha_reglamento', '')} "
                f"| {link_reg} "
                f"| {link_det} |"
            )
        lineas.append("")

    lineas += [
        "---",
        "",
        "## Referencias normativas",
        "",
        "- [NCG N° 365](../../normativa/ncg/ncg_365.md) – Información sobre reglamentos internos de fondos",
        "- [Ley N° 20.712](../../normativa/leyes/ley_20712.md) – Ley Única de Fondos",
        f"- [Portal CMF]({CMF_BASE})",
        "",
    ]

    ruta.write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# Generación del índice global de AGF
# ---------------------------------------------------------------------------


def escribir_csv_agf(resumen: list[dict], ruta: Path) -> None:
    """Escribe el índice global de AGF en formato CSV."""
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CAMPOS_CSV_AGF,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for agf in resumen:
            writer.writerow({k: agf.get(k, "") for k in CAMPOS_CSV_AGF})


def escribir_md_agf(resumen: list[dict], ruta: Path) -> None:
    """Escribe el índice global de AGF en formato Markdown."""
    ahora = datetime.now().strftime(TIMESTAMP_FORMAT)
    total_fondos = sum(r.get("total_fondos", 0) for r in resumen)
    total_con_reg = sum(r.get("con_reglamento", 0) for r in resumen)

    lineas: list[str] = [
        "# Índice de Reglamentos Internos – Todas las AGF",
        "",
        f"> Generado el {ahora}  ",
        f"> Fuente: [CMF – Portal Institucional]({CMF_BASE})",
        "",
        f"Total de AGF procesadas: **{len(resumen)}**  ",
        f"Total de fondos encontrados: **{total_fondos}**  ",
        f"Fondos con reglamento disponible: **{total_con_reg}**",
        "",
        "## Listado de AGF",
        "",
        "| AGF | RUT | Estado | Fondos | FM | FI | Con Reglamento | Carpeta |",
        "|-----|-----|--------|--------|----|----|----------------|---------|",
    ]

    for agf in sorted(resumen, key=lambda x: x.get("nombre_agf", "")):
        carpeta = agf.get("carpeta", "")
        link_carpeta = f"[{carpeta}](./{carpeta}/fondos.md)" if carpeta else "–"
        link_cmf = (
            f"[CMF ↗]({agf['link_cmf']})" if agf.get("link_cmf") else "–"
        )
        lineas.append(
            f"| {agf.get('nombre_agf', '')} "
            f"| {agf.get('rut', '')} "
            f"| {agf.get('estado', '')} "
            f"| {agf.get('total_fondos', 0)} "
            f"| {agf.get('fondos_mutuos', 0)} "
            f"| {agf.get('fondos_inversion', 0)} "
            f"| {agf.get('con_reglamento', 0)} "
            f"| {link_carpeta} |"
        )

    lineas += [
        "",
        "---",
        "",
        "## Cómo actualizar este índice",
        "",
        "```bash",
        "# Regenerar todos los índices y volver a descargar los PDFs",
        "python descargar_todos_reglamentos.py",
        "",
        "# Solo regenerar los índices (sin descargar PDFs)",
        "python descargar_todos_reglamentos.py --solo-indice",
        "",
        "# Solo una AGF específica",
        'python descargar_todos_reglamentos.py --agf "NOMBRE AGF"',
        "```",
        "",
        "## Referencias normativas",
        "",
        "- [NCG N° 365](../normativa/ncg/ncg_365.md) – Información sobre reglamentos internos de fondos",
        "- [Ley N° 20.712](../normativa/leyes/ley_20712.md) – Ley Única de Fondos",
        f"- [Portal CMF – Lista de AGF]({CMF_AGF_LISTA})",
        "",
    ]

    ruta.write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# Procesamiento de una AGF
# ---------------------------------------------------------------------------


def procesar_agf(
    agf: dict,
    tipos: list[str],
    solo_indice: bool,
    delay: float,
) -> dict:
    """
    Procesa una AGF: busca sus fondos, descarga PDFs y genera índices.

    Args:
        agf:         Dict con keys: nombre, rut, estado, link_detalle.
        tipos:       Lista de tipos a procesar, e.g. ["FM", "FI"].
        solo_indice: Si True, no descarga PDFs.
        delay:       Pausa entre peticiones HTTP.

    Returns:
        Dict resumen de la AGF con estadísticas.
    """
    nombre = agf["nombre"]
    carpeta_nombre = _sanitizar_nombre_carpeta(nombre)
    agf_dir = BASE_DIR / carpeta_nombre

    print(f"\n{'='*70}")
    print(f"  AGF: {nombre}")
    print(f"  Carpeta: {agf_dir}")
    print(f"{'='*70}")

    agf_dir.mkdir(parents=True, exist_ok=True)

    fondos: list[dict] = []

    if "FM" in tipos:
        fm = buscar_fondos_mutuos_agf(nombre, delay)
        fondos.extend(fm)
        print(f"  → {len(fm)} Fondos Mutuos encontrados para {nombre}")

    if "FI" in tipos:
        fi = buscar_fondos_inversion_agf(nombre, delay)
        fondos.extend(fi)
        print(f"  → {len(fi)} Fondos de Inversión encontrados para {nombre}")

    if fondos and not solo_indice:
        pdfs_dir = agf_dir / "pdfs"
        fondos = descargar_pdfs_agf(fondos, pdfs_dir)

    # Escribir índice por AGF
    csv_ruta = agf_dir / "fondos.csv"
    md_ruta = agf_dir / "fondos.md"

    escribir_csv_fondos(fondos, csv_ruta)
    escribir_md_fondos(fondos, nombre, md_ruta)

    print(f"  📄  CSV generado: {csv_ruta}")
    print(f"  📄  MD generado:  {md_ruta}")

    fm_count = sum(1 for f in fondos if f["tipo"] == "FM")
    fi_count = sum(1 for f in fondos if f["tipo"] == "FI")
    con_reg = sum(1 for f in fondos if f.get("link_reglamento"))

    return {
        "nombre_agf": nombre,
        "rut": agf.get("rut", ""),
        "estado": agf.get("estado", ""),
        "carpeta": carpeta_nombre,
        "total_fondos": len(fondos),
        "fondos_mutuos": fm_count,
        "fondos_inversion": fi_count,
        "con_reglamento": con_reg,
        "link_cmf": agf.get("link_detalle", ""),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def construir_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga reglamentos internos de fondos de TODAS las AGF inscritas en la CMF."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--agf",
        metavar="NOMBRE",
        default="",
        help=(
            "Filtrar por nombre de AGF (búsqueda parcial, insensible a mayúsculas). "
            'Ejemplo: --agf "BICE" procesará solo las AGF cuyo nombre contenga "BICE".'
        ),
    )
    parser.add_argument(
        "--tipo",
        choices=["FM", "FI"],
        metavar="{FM,FI}",
        help=(
            "Limitar la búsqueda a un tipo de fondo: "
            "FM (Fondos Mutuos) o FI (Fondos de Inversión)."
        ),
    )
    parser.add_argument(
        "--solo-indice",
        action="store_true",
        help="Generar los índices CSV/MD sin descargar los PDFs.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DELAY_ENTRE_REQUESTS,
        metavar="SEGUNDOS",
        help=(
            f"Pausa en segundos entre peticiones HTTP "
            f"(por defecto: {DELAY_ENTRE_REQUESTS}). "
            "Aumentar este valor si el portal CMF rechaza las peticiones."
        ),
    )
    return parser


def main() -> None:
    args = construir_arg_parser().parse_args()

    tipos = ["FM", "FI"] if args.tipo is None else [args.tipo]
    delay = max(0.5, args.delay)

    # 1. Obtener lista de AGF
    agfs = obtener_lista_agfs(filtro_nombre=args.agf)

    if not agfs:
        print(
            "\n⚠️  No se encontraron AGF en el portal CMF.\n"
            "   Posibles causas:\n"
            "   • Sin acceso a internet o portal CMF temporalmente no disponible.\n"
            f"     URL esperada: {CMF_AGF_LISTA}\n"
            "   • El portal CMF puede haber actualizado su estructura de URLs.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Procesar cada AGF
    resumen: list[dict] = []

    for agf in agfs:
        try:
            stats = procesar_agf(agf, tipos, args.solo_indice, delay)
            resumen.append(stats)
        except (RuntimeError, OSError, KeyError, ValueError) as exc:
            print(
                f"\n  ❌  Error al procesar AGF '{agf['nombre']}': {exc}",
                file=sys.stderr,
            )
            resumen.append({
                "nombre_agf": agf["nombre"],
                "rut": agf.get("rut", ""),
                "estado": agf.get("estado", ""),
                "carpeta": _sanitizar_nombre_carpeta(agf["nombre"]),
                "total_fondos": 0,
                "fondos_mutuos": 0,
                "fondos_inversion": 0,
                "con_reglamento": 0,
                "link_cmf": agf.get("link_detalle", ""),
            })

    # 3. Escribir índice global
    csv_global = BASE_DIR / "indice_agf.csv"
    md_global = BASE_DIR / "indice_agf.md"

    escribir_csv_agf(resumen, csv_global)
    escribir_md_agf(resumen, md_global)

    print(f"\n📄  Índice global CSV: {csv_global}")
    print(f"📄  Índice global MD:  {md_global}")

    total_fondos = sum(r.get("total_fondos", 0) for r in resumen)
    total_pdfs = sum(r.get("con_reglamento", 0) for r in resumen)

    print(f"\n✅  Proceso finalizado.")
    print(f"   AGF procesadas: {len(resumen)}")
    print(f"   Fondos encontrados: {total_fondos}")
    print(f"   Con reglamento disponible: {total_pdfs}")
    if not args.solo_indice:
        print(f"   PDFs descargados en subcarpetas de: {BASE_DIR}/")


if __name__ == "__main__":
    main()
