#!/usr/bin/env python3
"""
descargar_todos_reglamentos.py – Descarga los reglamentos internos de los fondos
de TODAS las AGF (Administradoras Generales de Fondos) inscritas en la CMF de Chile.

Flujo de navegación:
  1. Ruta Inicial: https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF
  2. Se procesa SOLO la tabla con columnas "R.U.T." y "Entidad".
     Se usa el link del RUT de cada AGF.
  3. En la página de cada AGF se hace clic en el botón "Fondos Administrados".
  4. Se procesa SOLO la tabla con columnas "R.U.T." y "Entidad".
     Se usa el link del RUT de cada Fondo.
  5. En la página de cada Fondo se hace clic en el botón "reglamento interno".
  6. Aparecen dos tablas con id="Tabla"; se toma la PRIMERA.
  7. En esa tabla hay dos links "Descarga". Se descargan ambos archivos:
       - Primer link  → nombre: <original>_<rut_agf>_<rut_fondo>_Reg_Interno.<ext>
       - Segundo link → nombre: <original>_<rut_agf>_<rut_fondo>_modif.<ext>
  8. Se recorren todos los fondos de la AGF y luego se pasa a la siguiente AGF.

Genera (por cada AGF):
  <CARPETA_AGF>/fondos.csv   Índice CSV con datos de fondos y estado de descarga
  <CARPETA_AGF>/fondos.md    Versión Markdown del mismo índice
  <CARPETA_AGF>/pdfs/        Archivos descargados (reglamento + modificaciones)

Genera (global):
  indice_agf.csv             Resumen de todas las AGF procesadas
  indice_agf.md              Versión Markdown del resumen global

Uso:
  python descargar_todos_reglamentos.py                  # descarga todo
  python descargar_todos_reglamentos.py --solo-indice    # solo genera índices CSV/MD
  python descargar_todos_reglamentos.py --agf "BICE"     # solo AGF cuyo nombre/RUT contenga "BICE"
  python descargar_todos_reglamentos.py --delay 1.5      # pausa entre peticiones (seg)

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
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent

CMF_BASE = "https://www.cmfchile.cl"

# Ruta Inicial – listado de AGF vigentes en el portal institucional CMF
CMF_AGF_LISTA = (
    f"{CMF_BASE}/institucional/mercados/consulta.php"
    "?mercado=V&Estado=VI&entidad=RGAGF"
)

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

# Campos de los índices CSV
CAMPOS_CSV_FONDOS = [
    "rut_fondo",
    "nombre_fondo",
    "link_fondo",
    "link_reglamento",
    "archivo_reg_interno",
    "archivo_modif",
    "estado",
]

CAMPOS_CSV_AGF = [
    "nombre_agf",
    "rut",
    "carpeta",
    "total_fondos",
    "con_reglamento",
    "link_cmf",
]

# Estados de fondo que se consideran fallos de extracción
ESTADOS_FALLO = {
    "sin_link",
    "error_fondo",
    "sin_reglamento",
    "error_reglamento",
    "sin_descarga",
    "descarga_fallida",
    "descarga_parcial",
    "error_fondos_agf",
    "error_general",
}

CAMPOS_CSV_FALLOS = [
    "nombre_agf",
    "rut_agf",
    "nombre_fondo",
    "rut_fondo",
    "estado",
    "link_fondo",
    "link_reglamento",
]

# ---------------------------------------------------------------------------
# Helpers HTTP
# ---------------------------------------------------------------------------


def fetch(url: str, retries: int = 3) -> str:
    """
    Realiza una petición HTTP GET y retorna el cuerpo de la respuesta.

    Args:
        url:     URL destino.
        retries: Número de reintentos ante error de red.

    Returns:
        HTML/texto de la respuesta.

    Raises:
        RuntimeError: Si no se puede obtener la respuesta tras los reintentos.
    """
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers=REQUEST_HEADERS)
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


def download_file(url: str, dest: Path) -> "Path | None":
    """
    Descarga un archivo desde *url* y lo guarda en *dest*.

    Verifica que el contenido descargado sea realmente un documento (PDF,
    Word, etc.) y no una página HTML de error o redirección del servidor.
    Si el Content-Type o los bytes mágicos indican una extensión diferente a
    la de *dest*, el archivo se guarda con la extensión correcta.

    Returns:
        El ``Path`` real donde se guardó el archivo si la descarga fue
        exitosa, o ``None`` en caso contrario.
    """
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  [OMITIDO]  {dest.name} (ya existe)")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  [DESCARGANDO] {dest.name} … ", end="", flush=True)
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read()
        if len(data) < 1000:
            print(f"ERROR (respuesta muy pequeña: {len(data)} bytes)")
            return None
        # Rechazar respuestas HTML (páginas de error o redirección del portal)
        if "text/html" in content_type and not (len(data) >= 4 and data[:4] == b"%PDF"):
            print(
                f"ERROR (el servidor devolvió HTML en lugar de un documento; "
                f"Content-Type: {content_type})"
            )
            return None
        # Ajustar extensión del archivo destino según el contenido real
        dest = _ajustar_extension_por_contenido(dest, content_type, data)
        dest.write_bytes(data)
        print(f"OK ({len(data):,} bytes)")
        return dest
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"ERROR ({exc})")
        return None


def _ajustar_extension_por_contenido(dest: Path, content_type: str, data: bytes) -> Path:
    """
    Devuelve *dest* con la extensión corregida según el Content-Type o los
    bytes mágicos del archivo, cuando la extensión actual no corresponde al
    contenido real.

    Por ejemplo, si el archivo fue nombrado `descarga.php` pero el servidor
    devuelve `application/pdf`, la función retorna el mismo path con extensión
    `.pdf`.
    """
    ext_actual = dest.suffix.lower()

    # Mapeo de Content-Type a extensión esperada
    tipo_a_ext: dict[str, str] = {
        "application/pdf": ".pdf",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        "application/vnd.ms-excel": ".xls",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    }

    ext_correcta: str | None = None
    for mime, ext in tipo_a_ext.items():
        if mime in content_type:
            ext_correcta = ext
            break

    # Fallback: detectar PDF por bytes mágicos (%PDF)
    if ext_correcta is None and len(data) >= 4 and data[:4] == b"%PDF":
        ext_correcta = ".pdf"

    if ext_correcta and ext_actual != ext_correcta:
        nuevo_dest = dest.with_suffix(ext_correcta)
        print(
            f"\n  [AVISO] extensión corregida: {dest.name} → {nuevo_dest.name} "
            f"(Content-Type: {content_type or 'desconocido'})",
            end="",
        )
        return nuevo_dest

    return dest


# ---------------------------------------------------------------------------
# Parseo de HTML del portal CMF
# ---------------------------------------------------------------------------


class _RutTablaParser(HTMLParser):
    """
    Extrae las filas de la tabla con columnas R.U.T. y Entidad del portal CMF.

    Para cada fila de datos retorna el texto del RUT, el href del link en esa
    celda y el texto de la columna Entidad.
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
        self.rows: list[list[tuple[str, str]]] = []
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
            self._cell_href = ""
        elif tag == "a" and self._in_cell and not self._cell_href:
            self._cell_href = (ad.get("href", "") or "").strip()

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._in_cell:
            self._current_row.append(
                (self._cell_text.strip(), self._cell_href.strip())
            )
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if self._current_row:
                texts = [t for t, _ in self._current_row]
                if not self._header_captured:
                    self.headers = texts
                    self._header_captured = True
                else:
                    self.rows.append(list(self._current_row))
            self._in_row = False
        elif tag == "table":
            self._in_table = max(0, self._in_table - 1)

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_text += data


class _LinksParser(HTMLParser):
    """Extrae todos los pares (texto, href) de los links de un HTML."""

    def __init__(self) -> None:
        super().__init__()
        self._in_a = False
        self._current_href = ""
        self._current_text = ""
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self._in_a = True
            ad = dict(attrs)
            self._current_href = (ad.get("href", "") or "").strip()
            self._current_text = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._in_a:
            self.links.append((self._current_text.strip(), self._current_href))
            self._in_a = False

    def handle_data(self, data: str) -> None:
        if self._in_a:
            self._current_text += data


class _TablaIdParser(HTMLParser):
    """
    Extrae los links de la PRIMERA tabla con id="Tabla" (case-insensitive)
    del HTML.

    En la página de reglamento interno del portal CMF aparecen dos tablas con
    ese id; se procesa únicamente la primera.
    """

    def __init__(self) -> None:
        super().__init__()
        self._in_target_table = False
        self._depth = 0
        self._target_found = False
        self._done = False
        self._in_a = False
        self._current_href = ""
        self._current_text = ""
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._done:
            return
        ad = dict(attrs)
        if tag == "table":
            tabla_id = (ad.get("id", "") or "").strip().lower()
            if tabla_id == "tabla" and not self._target_found:
                self._target_found = True
                self._in_target_table = True
                self._depth = 1
            elif self._in_target_table:
                self._depth += 1
        elif self._in_target_table and tag == "a":
            self._in_a = True
            self._current_href = (ad.get("href", "") or "").strip()
            self._current_text = ""

    def handle_endtag(self, tag: str) -> None:
        if self._done:
            return
        if tag == "table" and self._in_target_table:
            self._depth -= 1
            if self._depth == 0:
                self._in_target_table = False
                self._done = True
        elif self._in_target_table and tag == "a" and self._in_a:
            href = self._current_href
            text = self._current_text.strip()
            if href:
                self.links.append((text, href))
            self._in_a = False

    def handle_data(self, data: str) -> None:
        if self._in_a and self._in_target_table and not self._done:
            self._current_text += data


# ---------------------------------------------------------------------------
# Funciones de parseo de la tabla R.U.T. / Entidad
# ---------------------------------------------------------------------------


def _parse_tabla_rut_entidad(html: str) -> list[dict]:
    """
    Extrae las entradas de la tabla con columnas R.U.T. y Entidad del HTML.

    Busca la primera tabla que contenga una columna cuya cabecera incluya
    "R.U.T" o "RUT" y una columna cuya cabecera incluya "ENTIDAD" o similar.
    Para cada fila de datos retorna el texto del RUT, el href del link en esa
    celda y el texto de la columna Entidad.

    Returns:
        Lista de dicts con claves: rut, entidad, link.
    """
    p = _RutTablaParser()
    p.feed(html)

    if not p.headers:
        return []

    # Identificar índice de columna RUT y columna Entidad
    rut_idx: int | None = None
    entidad_idx: int | None = None
    for i, h in enumerate(p.headers):
        h_norm = h.upper().strip().replace(".", "").replace(" ", "")
        if "RUT" in h_norm or "RUN" in h_norm:
            if rut_idx is None:
                rut_idx = i
        elif any(
            kw in h_norm
            for kw in ("ENTIDAD", "NOMBRE", "RAZON", "DENOMINACION", "SOCIEDAD")
        ):
            if entidad_idx is None:
                entidad_idx = i

    if rut_idx is None:
        return []

    result: list[dict] = []
    for row_cells in p.rows:
        if rut_idx >= len(row_cells):
            continue
        rut_text, rut_href = row_cells[rut_idx]
        rut_text = rut_text.strip()
        rut_href = rut_href.strip()

        entidad_text = ""
        if entidad_idx is not None and entidad_idx < len(row_cells):
            entidad_text = row_cells[entidad_idx][0].strip()

        if not rut_text and not rut_href:
            continue

        result.append(
            {
                "rut": rut_text,
                "entidad": entidad_text,
                "link": _absolute(rut_href),
            }
        )

    return result


def _buscar_link_por_texto(html: str, texto_buscado: str) -> str:
    """
    Devuelve el href del primer link cuyo texto contiene *texto_buscado*
    (búsqueda case-insensitive).
    """
    p = _LinksParser()
    p.feed(html)
    texto_upper = texto_buscado.upper()
    for texto, href in p.links:
        if texto_upper in texto.upper():
            return href
    return ""


def _extraer_links_primera_tabla(html: str) -> list[tuple[str, str]]:
    """
    Extrae los links (texto, href) de la primera tabla con id="Tabla" del HTML.
    """
    p = _TablaIdParser()
    p.feed(html)
    return p.links


# ---------------------------------------------------------------------------
# Helpers de URL
# ---------------------------------------------------------------------------


def _absolute(href: str) -> str:
    """Convierte un href relativo en URL absoluta del portal CMF.

    Decodifica entidades HTML (p.ej. ``&amp;`` → ``&``) y
    recodifica en porcentaje cualquier espacio o carácter de control en el
    query string para evitar ``http.client.InvalidURL``.
    """
    if not href:
        return ""
    # Decodificar entidades HTML (p.ej. &amp; → &, &amp;amp; → &amp;)
    href = unescape(href)
    if href.startswith("http"):
        url = href
    elif href.startswith("/"):
        url = f"{CMF_BASE}{href}"
    else:
        url = f"{CMF_BASE}/institucional/mercados/{href}"
    # Validar que la URL pertenece al dominio esperado del portal CMF.
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc and parsed.netloc != urllib.parse.urlparse(CMF_BASE).netloc:
        return ""
    # Re-codificar los valores del query string para que los espacios y otros
    # caracteres de control queden como porcentaje (p.ej. ' ' → '%20').
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    encoded_query = urllib.parse.urlencode(
        {k: v[0] if len(v) == 1 else v for k, v in params.items()}, doseq=True
    )
    return urllib.parse.urlunparse(parsed._replace(query=encoded_query))


def _extraer_rut_de_url(url: str) -> str:
    """Extrae el parámetro 'rut' de una URL del portal CMF."""
    try:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        return params.get("rut", [""])[0].strip()
    except Exception:
        return ""


def _cambiar_pestania(url: str, nueva_pestania: int) -> str:
    """
    Devuelve la URL con el parámetro 'pestania' sustituido por *nueva_pestania*.
    """
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    params["pestania"] = [str(nueva_pestania)]
    new_query = urllib.parse.urlencode(
        {k: v[0] if len(v) == 1 else v for k, v in params.items()}, doseq=True
    )
    return urllib.parse.urlunparse(parsed._replace(query=new_query))


# ---------------------------------------------------------------------------
# Funciones de navegación
# ---------------------------------------------------------------------------


def _url_fondos_administrados(html_agf: str, agf_url: str) -> str:
    """
    Obtiene la URL de la pestaña "Fondos Administrados" de una AGF.

    Primero busca el link en el HTML por su texto.  Si no lo encuentra,
    recurre a cambiar ``pestania=39`` en la URL de la AGF (pestania 39 es la
    pestaña de Fondos Administrados según el portal CMF).
    """
    href = _buscar_link_por_texto(html_agf, "Fondos Administrados")
    if href:
        return _absolute(href)
    if agf_url:
        return _cambiar_pestania(agf_url, 39)
    return ""


def _url_reglamento_interno(html_fondo: str, fondo_url: str) -> str:
    """
    Obtiene la URL de la pestaña "Reglamento Interno" de un fondo.

    Primero busca el link en el HTML por su texto.  Si no lo encuentra,
    recurre a cambiar ``pestania=56`` en la URL del fondo (pestania 56 es la
    pestaña de Reglamento Interno según el portal CMF).
    """
    href = _buscar_link_por_texto(html_fondo, "reglamento interno")
    if href:
        return _absolute(href)
    if fondo_url:
        return _cambiar_pestania(fondo_url, 56)
    return ""


# ---------------------------------------------------------------------------
# Sanitización de nombres para carpetas y archivos
# ---------------------------------------------------------------------------


def _sanitizar_nombre_carpeta(nombre: str) -> str:
    """
    Convierte un nombre de AGF en un nombre de carpeta seguro para el sistema
    de archivos.
    """
    normalizado = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in normalizado if not unicodedata.combining(c))
    limpio = re.sub(r"[^\w\s\-]", "", sin_acentos)
    carpeta = re.sub(r"[\s\-]+", "_", limpio.strip())
    return carpeta[:80].upper()


def _nombre_archivo_descarga(
    url_descarga: str,
    rut_agf: str,
    rut_fondo: str,
    sufijo: str,
) -> str:
    """
    Genera el nombre del archivo de descarga con el formato:
    ``<nombre_original>_<rut_agf>_<rut_fondo>_<sufijo>.<ext>``.

    El nombre original se extrae del parámetro ``archivo`` de la URL o del
    último segmento del path.  Si no es posible determinarlo, o si la URL
    apunta a un script PHP/servidor sin extensión de documento, se usa `.pdf`
    como extensión predeterminada.
    """
    # Extensiones de documento consideradas válidas
    _EXTS_DOC = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods"}

    # Intentar extraer nombre original del parámetro ?archivo=...
    try:
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url_descarga).query)
        archivo_param = params.get("archivo", [""])[0]
        if archivo_param:
            stem = Path(urllib.parse.unquote(archivo_param)).stem
            ext = Path(urllib.parse.unquote(archivo_param)).suffix or ".pdf"
        else:
            path_part = urllib.parse.urlparse(url_descarga).path
            stem = Path(path_part).stem or "descarga"
            ext = Path(path_part).suffix or ".pdf"
    except Exception:
        stem = "descarga"
        ext = ".pdf"

    # Si la extensión no es un tipo de documento conocido (p.ej. ".php"),
    # se asume que el servidor entregará un PDF.
    if ext.lower() not in _EXTS_DOC:
        ext = ".pdf"

    # Limpiar componentes
    rut_agf_clean = re.sub(r"\W", "", rut_agf)
    rut_fondo_clean = re.sub(r"\W", "", rut_fondo)
    stem_clean = re.sub(r"[^\w\-]", "_", stem)[:60]
    sufijo_clean = re.sub(r"\s+", "_", sufijo)

    return f"{stem_clean}_{rut_agf_clean}_{rut_fondo_clean}_{sufijo_clean}{ext}"


# ---------------------------------------------------------------------------
# Obtención de la lista de AGF
# ---------------------------------------------------------------------------


def obtener_lista_agfs(filtro_nombre: str = "") -> list[dict]:
    """
    Consulta la ruta inicial del portal CMF y extrae el listado de AGF
    vigentes de la tabla R.U.T. / Entidad.

    URL: https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF

    Args:
        filtro_nombre: Si se indica, retorna solo las AGF cuyo nombre o RUT
                       contenga este texto (insensible a mayúsculas).

    Returns:
        Lista de dicts con claves: rut, entidad, link.
    """
    print("Obteniendo lista de AGF vigentes desde CMF…")
    print(f"  URL: {CMF_AGF_LISTA}")

    try:
        html = fetch(CMF_AGF_LISTA)
    except RuntimeError as exc:
        print(f"  ❌  No se pudo obtener la lista de AGF: {exc}", file=sys.stderr)
        return []

    agfs = _parse_tabla_rut_entidad(html)

    if not agfs:
        print(
            "  ⚠️  No se encontraron entradas en la tabla R.U.T./Entidad.",
            file=sys.stderr,
        )
        return []

    if filtro_nombre:
        filtro_up = filtro_nombre.upper()
        agfs = [
            a for a in agfs
            if filtro_up in a["entidad"].upper() or filtro_up in a["rut"].upper()
        ]

    for a in agfs:
        print(f"  ✅  AGF: {a['entidad']} (RUT: {a['rut']})")

    print(f"\nTotal AGF encontradas: {len(agfs)}\n")
    return agfs


# ---------------------------------------------------------------------------
# Obtención de la lista de fondos de una AGF
# ---------------------------------------------------------------------------


def obtener_fondos_agf(
    agf: dict,
    delay: float = DELAY_ENTRE_REQUESTS,
) -> list[dict]:
    """
    Navega a la página de la AGF, hace clic en "Fondos Administrados" y
    extrae la lista de fondos de la tabla R.U.T. / Entidad.

    Args:
        agf:   Dict con claves: rut, entidad, link.
        delay: Pausa entre peticiones HTTP (segundos).

    Returns:
        Lista de dicts con claves: rut, entidad, link.
    """
    agf_url = agf["link"]
    if not agf_url:
        print(
            f"    ⚠️  Sin link para AGF {agf['entidad']}; se omite.",
            file=sys.stderr,
        )
        return []

    # 1. Obtener página principal de la AGF
    try:
        time.sleep(delay)
        html_agf = fetch(agf_url)
    except RuntimeError as exc:
        print(
            f"    ⚠️  No se pudo obtener página de AGF ({agf_url}): {exc}",
            file=sys.stderr,
        )
        return []

    # 2. Determinar URL de "Fondos Administrados"
    fondos_url = _url_fondos_administrados(html_agf, agf_url)
    if not fondos_url:
        print(
            f"    ⚠️  No se encontró enlace 'Fondos Administrados' para {agf['entidad']}.",
            file=sys.stderr,
        )
        return []

    # 3. Obtener página de fondos administrados
    try:
        time.sleep(delay)
        html_fondos = fetch(fondos_url)
    except RuntimeError as exc:
        print(
            f"    ⚠️  No se pudo obtener fondos de AGF ({fondos_url}): {exc}",
            file=sys.stderr,
        )
        return []

    # 4. Parsear tabla R.U.T. / Entidad
    fondos = _parse_tabla_rut_entidad(html_fondos)
    return fondos


# ---------------------------------------------------------------------------
# Procesamiento de un Fondo
# ---------------------------------------------------------------------------


def procesar_fondo(
    fondo: dict,
    rut_agf: str,
    pdfs_dir: Path,
    delay: float = DELAY_ENTRE_REQUESTS,
    solo_indice: bool = False,
) -> dict:
    """
    Para un fondo dado:
      1. Navega a la página del fondo.
      2. Hace clic en "reglamento interno".
      3. Descarga los dos archivos de la primera tabla con id="Tabla".

    Los archivos se nombran:
      <original>_<rut_agf>_<rut_fondo>_Reg_Interno.<ext>
      <original>_<rut_agf>_<rut_fondo>_modif.<ext>

    Returns:
        Dict con info del fondo y estado de la descarga.
    """
    fondo_url = fondo["link"]
    rut_fondo = fondo["rut"] or _extraer_rut_de_url(fondo_url)
    nombre_fondo = fondo["entidad"]

    resultado: dict = {
        "rut_fondo": rut_fondo,
        "nombre_fondo": nombre_fondo,
        "link_fondo": fondo_url,
        "link_reglamento": "",
        "archivo_reg_interno": "",
        "archivo_modif": "",
        "estado": "ok",
    }

    if not fondo_url:
        resultado["estado"] = "sin_link"
        return resultado

    # 1. Obtener página del fondo
    try:
        time.sleep(delay)
        html_fondo = fetch(fondo_url)
    except RuntimeError as exc:
        print(
            f"      ⚠️  No se pudo obtener página del fondo ({fondo_url}): {exc}",
            file=sys.stderr,
        )
        resultado["estado"] = "error_fondo"
        return resultado

    # 2. Determinar URL de "reglamento interno"
    reglamento_url = _url_reglamento_interno(html_fondo, fondo_url)
    if not reglamento_url:
        print(
            f"      ⚠️  No se encontró 'reglamento interno' para {nombre_fondo}.",
            file=sys.stderr,
        )
        resultado["estado"] = "sin_reglamento"
        return resultado

    resultado["link_reglamento"] = reglamento_url

    if solo_indice:
        return resultado

    # 3. Obtener página de reglamento interno
    try:
        time.sleep(delay)
        html_reglamento = fetch(reglamento_url)
    except RuntimeError as exc:
        print(
            f"      ⚠️  No se pudo obtener reglamento ({reglamento_url}): {exc}",
            file=sys.stderr,
        )
        resultado["estado"] = "error_reglamento"
        return resultado

    # 4. Extraer links de la PRIMERA tabla con id="Tabla"
    links_descarga = _extraer_links_primera_tabla(html_reglamento)

    if not links_descarga:
        print(
            f"      ⚠️  No se encontraron links en la tabla id=Tabla para {nombre_fondo}.",
            file=sys.stderr,
        )
        resultado["estado"] = "sin_descarga"
        return resultado

    # 5. Descargar archivos
    #    Primer link  → "Reg Interno"
    #    Segundo link → "modif"
    sufijos = ["Reg_Interno", "modif"]
    campos = ["archivo_reg_interno", "archivo_modif"]

    descargas_ok = 0
    for i, (texto_link, href_link) in enumerate(links_descarga[:2]):
        sufijo = sufijos[i]
        url_descarga = _absolute(href_link)
        nombre_pdf = _nombre_archivo_descarga(url_descarga, rut_agf, rut_fondo, sufijo)
        dest = pdfs_dir / nombre_pdf

        saved = download_file(url_descarga, dest)
        if saved is not None:
            resultado[campos[i]] = saved.name
            descargas_ok += 1
        time.sleep(delay)

    n_links = min(len(links_descarga), 2)
    if descargas_ok == 0:
        resultado["estado"] = "descarga_fallida"
    elif descargas_ok < n_links:
        resultado["estado"] = "descarga_parcial"

    return resultado


# ---------------------------------------------------------------------------
# Procesamiento de una AGF
# ---------------------------------------------------------------------------


def procesar_agf(
    agf: dict,
    solo_indice: bool,
    delay: float,
) -> tuple[dict, list[dict]]:
    """
    Procesa una AGF: obtiene su lista de fondos y descarga los reglamentos.

    Args:
        agf:         Dict con claves: rut, entidad, link.
        solo_indice: Si True, no descarga archivos (solo genera índices CSV/MD).
        delay:       Pausa entre peticiones HTTP (segundos).

    Returns:
        Tupla (stats_dict, fallos_list) donde stats_dict es el resumen de la
        AGF con estadísticas y fallos_list es la lista de fondos (y la propia
        AGF cuando corresponde) para los que no se pudo extraer información.
    """
    nombre = agf["entidad"]
    rut_agf = agf["rut"]

    carpeta_nombre = _sanitizar_nombre_carpeta(nombre)
    agf_dir = BASE_DIR / carpeta_nombre

    print(f"\n{'=' * 70}")
    print(f"  AGF: {nombre}  (RUT: {rut_agf})")
    print(f"  Carpeta: {agf_dir}")
    print(f"{'=' * 70}")

    agf_dir.mkdir(parents=True, exist_ok=True)

    fallos: list[dict] = []

    # Obtener lista de fondos navigando AGF → Fondos Administrados
    fondos_lista = obtener_fondos_agf(agf, delay)
    print(f"  → {len(fondos_lista)} fondo(s) encontrado(s)")

    if not fondos_lista:
        fallos.append(
            {
                "nombre_agf": nombre,
                "rut_agf": rut_agf,
                "nombre_fondo": "",
                "rut_fondo": "",
                "estado": "error_fondos_agf",
                "link_fondo": agf.get("link", ""),
                "link_reglamento": "",
            }
        )

    fondos_procesados: list[dict] = []
    pdfs_dir = agf_dir / "pdfs"

    for fondo in fondos_lista:
        print(f"    Fondo: {fondo['entidad']}  (RUT: {fondo['rut']})")
        resultado = procesar_fondo(fondo, rut_agf, pdfs_dir, delay, solo_indice)
        fondos_procesados.append(resultado)
        if resultado.get("estado") in ESTADOS_FALLO:
            fallos.append(
                {
                    "nombre_agf": nombre,
                    "rut_agf": rut_agf,
                    "nombre_fondo": resultado.get("nombre_fondo", ""),
                    "rut_fondo": resultado.get("rut_fondo", ""),
                    "estado": resultado.get("estado", ""),
                    "link_fondo": resultado.get("link_fondo", ""),
                    "link_reglamento": resultado.get("link_reglamento", ""),
                }
            )

    # Generar índices CSV y Markdown por AGF
    csv_ruta = agf_dir / "fondos.csv"
    md_ruta = agf_dir / "fondos.md"

    escribir_csv_fondos(fondos_procesados, csv_ruta)
    escribir_md_fondos(fondos_procesados, nombre, rut_agf, md_ruta)

    print(f"  📄  CSV: {csv_ruta}")
    print(f"  📄  MD:  {md_ruta}")

    con_reg = sum(1 for f in fondos_procesados if f.get("archivo_reg_interno"))

    return (
        {
            "nombre_agf": nombre,
            "rut": rut_agf,
            "carpeta": carpeta_nombre,
            "total_fondos": len(fondos_lista),
            "con_reglamento": con_reg,
            "link_cmf": agf.get("link", ""),
        },
        fallos,
    )


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


def escribir_md_fondos(
    fondos: list[dict],
    nombre_agf: str,
    rut_agf: str,
    ruta: Path,
) -> None:
    """Escribe el índice de fondos de una AGF en formato Markdown."""
    ahora = datetime.now().strftime(TIMESTAMP_FORMAT)
    lineas: list[str] = [
        f"# Reglamentos Internos – {nombre_agf}",
        "",
        f"> RUT AGF: **{rut_agf}**  ",
        f"> Generado el {ahora}  ",
        f"> Fuente: [CMF – Portal Institucional]({CMF_BASE})",
        "",
        f"Total de fondos encontrados: **{len(fondos)}**",
        "",
        "| RUT Fondo | Nombre | Reglamento Interno | Modif en trámite | Estado |",
        "|-----------|--------|--------------------|------------------|--------|",
    ]
    for f in fondos:
        link_reg = (
            f"[Reglamento ↗]({f['link_reglamento']})"
            if f.get("link_reglamento")
            else "–"
        )
        arch_reg = f.get("archivo_reg_interno", "") or "–"
        arch_mod = f.get("archivo_modif", "") or "–"
        lineas.append(
            f"| {f.get('rut_fondo', '')} "
            f"| {f.get('nombre_fondo', '')} "
            f"| {arch_reg} "
            f"| {arch_mod} "
            f"| {f.get('estado', '')} |"
        )
    lineas += [
        "",
        "---",
        "",
        "## Referencias normativas",
        "",
        "- [NCG N° 365](../../normativa/ncg/ncg_365.md) – Reglamentos internos de fondos",
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
        "| AGF | RUT | Fondos | Con Reglamento | Carpeta |",
        "|-----|-----|--------|----------------|---------|",
    ]

    for agf in sorted(resumen, key=lambda x: x.get("nombre_agf", "")):
        carpeta = agf.get("carpeta", "")
        link_carpeta = f"[{carpeta}](./{carpeta}/fondos.md)" if carpeta else "–"
        lineas.append(
            f"| {agf.get('nombre_agf', '')} "
            f"| {agf.get('rut', '')} "
            f"| {agf.get('total_fondos', 0)} "
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
        "# Regenerar todos los índices y descargar los archivos",
        "python descargar_todos_reglamentos.py",
        "",
        "# Solo regenerar los índices (sin descargar archivos)",
        "python descargar_todos_reglamentos.py --solo-indice",
        "",
        "# Solo una AGF específica",
        'python descargar_todos_reglamentos.py --agf "NOMBRE AGF"',
        "```",
        "",
        "## Referencias normativas",
        "",
        "- [NCG N° 365](../normativa/ncg/ncg_365.md) – Reglamentos internos de fondos",
        "- [Ley N° 20.712](../normativa/leyes/ley_20712.md) – Ley Única de Fondos",
        f"- [Portal CMF – Lista de AGF]({CMF_AGF_LISTA})",
        "",
    ]

    ruta.write_text("\n".join(lineas), encoding="utf-8")


def escribir_csv_fallos(fallos: list[dict], ruta: Path) -> None:
    """Escribe el archivo de fallos de extracción en formato CSV.

    Cada fila representa un fondo (o una AGF entera) para el que no fue
    posible extraer la información del portal CMF.
    """
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CAMPOS_CSV_FALLOS,
            extrasaction="ignore",
            restval="",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for fallo in fallos:
            writer.writerow(fallo)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def construir_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga reglamentos internos de fondos de TODAS las AGF "
            "inscritas en la CMF de Chile, navegando el flujo correcto del portal."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--agf",
        metavar="TEXTO",
        default="",
        help=(
            "Filtrar por nombre o RUT de AGF (búsqueda parcial, insensible a "
            'mayúsculas). Ejemplo: --agf "BICE".'
        ),
    )
    parser.add_argument(
        "--solo-indice",
        action="store_true",
        help="Generar los índices CSV/MD sin descargar los archivos.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DELAY_ENTRE_REQUESTS,
        metavar="SEGUNDOS",
        help=(
            f"Pausa en segundos entre peticiones HTTP "
            f"(por defecto: {DELAY_ENTRE_REQUESTS}). "
            "Aumentar si el portal CMF rechaza las peticiones."
        ),
    )
    return parser


def main() -> None:
    args = construir_arg_parser().parse_args()
    delay = max(0.5, args.delay)

    # 1. Obtener lista de AGF desde la ruta inicial
    agfs = obtener_lista_agfs(filtro_nombre=args.agf)

    if not agfs:
        print(
            "\n⚠️  No se encontraron AGF en el portal CMF.\n"
            "   Posibles causas:\n"
            "   • Sin acceso a internet o portal temporalmente no disponible.\n"
            f"   • URL: {CMF_AGF_LISTA}\n"
            "   • El portal CMF puede haber actualizado su estructura HTML.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Procesar cada AGF
    resumen: list[dict] = []
    all_fallos: list[dict] = []

    for agf in agfs:
        try:
            stats, fallos = procesar_agf(agf, args.solo_indice, delay)
            resumen.append(stats)
            all_fallos.extend(fallos)
        except (RuntimeError, OSError, KeyError, ValueError) as exc:
            print(
                f"\n  ❌  Error al procesar AGF '{agf['entidad']}': {exc}",
                file=sys.stderr,
            )
            resumen.append(
                {
                    "nombre_agf": agf["entidad"],
                    "rut": agf.get("rut", ""),
                    "carpeta": _sanitizar_nombre_carpeta(agf["entidad"]),
                    "total_fondos": 0,
                    "con_reglamento": 0,
                    "link_cmf": agf.get("link", ""),
                }
            )
            all_fallos.append(
                {
                    "nombre_agf": agf["entidad"],
                    "rut_agf": agf.get("rut", ""),
                    "nombre_fondo": "",
                    "rut_fondo": "",
                    "estado": "error_general",
                    "link_fondo": agf.get("link", ""),
                    "link_reglamento": "",
                }
            )

    # 3. Escribir índice global
    csv_global = BASE_DIR / "indice_agf.csv"
    md_global = BASE_DIR / "indice_agf.md"

    escribir_csv_agf(resumen, csv_global)
    escribir_md_agf(resumen, md_global)

    print(f"\n📄  Índice global CSV: {csv_global}")
    print(f"📄  Índice global MD:  {md_global}")

    # 4. Escribir archivo de fallos de extracción
    if all_fallos:
        csv_fallos = BASE_DIR / "fallos_extraccion.csv"
        escribir_csv_fallos(all_fallos, csv_fallos)
        print(f"⚠️   Fallos de extracción : {len(all_fallos)}")
        print(f"📄  Fallos CSV           : {csv_fallos}")
    else:
        print("✅  Sin fallos de extracción.")

    total_fondos = sum(r.get("total_fondos", 0) for r in resumen)
    total_con_reg = sum(r.get("con_reglamento", 0) for r in resumen)

    print(f"\n✅  Proceso finalizado.")
    print(f"   AGF procesadas      : {len(resumen)}")
    print(f"   Fondos encontrados  : {total_fondos}")
    print(f"   Con reglamento      : {total_con_reg}")
    if not args.solo_indice:
        print(f"   Archivos en         : {BASE_DIR}/<CARPETA_AGF>/pdfs/")


if __name__ == "__main__":
    main()
