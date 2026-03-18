#!/usr/bin/env python3
"""
descargar_reglamentos_bci.py – Obtiene y descarga los reglamentos internos
de los fondos de BCI Asset Management Administradora General de Fondos S.A.
registrados en la CMF (Comisión para el Mercado Financiero de Chile).

El script consulta el portal institucional de la CMF para obtener el listado
completo de fondos administrados por BCI Asset Management y los links a sus
reglamentos internos depositados ante la CMF según la NCG N° 365.

Genera:
  fondos_bci.csv   Índice CSV con datos de cada fondo y enlace al reglamento
  fondos_bci.md    Versión Markdown del mismo índice
  pdfs/            Carpeta con los PDFs de reglamentos descargados

Uso:
  python descargar_reglamentos_bci.py                 # descarga todo
  python descargar_reglamentos_bci.py --solo-indice   # solo genera el índice
  python descargar_reglamentos_bci.py --tipo FM        # solo Fondos Mutuos
  python descargar_reglamentos_bci.py --tipo FI        # solo Fondos de Inversión
  python descargar_reglamentos_bci.py --salida mi_indice.csv

Requisitos: Python 3.10+ (sin dependencias externas).
"""

import argparse
import csv
import re
import sys
import time
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
PDFS_DIR = BASE_DIR / "pdfs"

CMF_BASE = "https://www.cmfchile.cl"

# Página de listado de Fondos Mutuos en el portal CMF (nuevo portal post-2024)
CMF_FM_BUSQUEDA = f"{CMF_BASE}/institucional/mercados/consulta.php?mercado=V&entidad=RGFMU"
# Página de listado de Fondos de Inversión en el portal CMF (nuevo portal post-2024)
CMF_FI_BUSQUEDA = f"{CMF_BASE}/institucional/mercados/consulta.php?mercado=V&entidad=RGFI"
# Registro Público de Depósito de Reglamentos Internos – Fondos Mutuos
CMF_FM_REGLAMENTOS = f"{CMF_BASE}/institucional/inc/deposito_fondos_mutuos.php"
# Registro Público de Depósito de Reglamentos Internos – Fondos de Inversión
CMF_FI_REGLAMENTOS = f"{CMF_BASE}/institucional/inc/deposito_fondos_inversion.php"
# Buscador global de entidades fiscalizadas
CMF_BUSQUEDA_GLOBAL = f"{CMF_BASE}/institucional/mercados/consulta_busqueda.php"

# Nombre oficial de BCI Asset Management en el registro CMF.
# Si la búsqueda no retorna resultados, verifica el nombre exacto en:
# https://www.cmfchile.cl/institucional/mercados/agf.php
BCI_AM_NOMBRE = "BCI ASSET MANAGEMENT"

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

CAMPOS_CSV = [
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
    except Exception as exc:  # noqa: BLE001
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
        self._current_row: list[tuple[str, str]] = []   # (texto, href)
        self.headers: list[str] = []
        self.rows: list[dict] = []
        self._header_captured = False

    # -- tag handlers --------------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        ad = dict(attrs)
        if tag == "table":
            self._in_table += 1
        elif tag in ("tr",) and self._in_table:
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
# Búsqueda de fondos en CMF
# ---------------------------------------------------------------------------


def _es_bci(row: dict) -> bool:
    """Retorna True si algún campo de la fila contiene el identificador BCI."""
    texto = " ".join(str(v) for v in row.values()).upper()
    return BCI_AM_NOMBRE in texto


def _safe_get_detalle(href: str) -> str:
    """Obtiene el HTML de una página de detalle de fondo; retorna '' en error."""
    if not href:
        return ""
    url = _absolute(href)
    try:
        time.sleep(DELAY_ENTRE_REQUESTS)
        return fetch(url)
    except RuntimeError as exc:
        print(f"    ⚠️  No se pudo obtener detalle ({url}): {exc}", file=sys.stderr)
        return ""


def buscar_fondos_mutuos() -> list[dict]:
    """
    Consulta el portal CMF para obtener los Fondos Mutuos de BCI AM.

    Intenta primero el Registro Público de Depósito de Reglamentos Internos
    (deposito_fondos_mutuos.php) filtrando por administradora.  Si no retorna
    resultados, recurre al listado general (consulta.php) y filtra localmente.

    Returns:
        Lista de dicts con los campos definidos en CAMPOS_CSV.
    """
    print("Buscando Fondos Mutuos de BCI Asset Management en CMF…")
    fondos: list[dict] = []

    # Estrategia 1: Registro de reglamentos filtrado por administradora
    html_reg = ""
    try:
        html_reg = fetch(
            CMF_FM_REGLAMENTOS,
            post_data={"administradora": BCI_AM_NOMBRE, "boton_buscar": "Buscar"},
        )
    except RuntimeError as exc:
        print(f"  ⚠️  No se pudo usar registro de reglamentos FM: {exc}", file=sys.stderr)

    # Estrategia 2: Listado general (GET sin filtro, se filtra localmente)
    html_lista = ""
    try:
        html_lista = fetch(CMF_FM_BUSQUEDA)
    except RuntimeError as exc:
        print(f"  ❌  Error al buscar fondos mutuos: {exc}", file=sys.stderr)

    # Usar el HTML con más contenido relacionado con BCI
    html = html_reg if html_reg and BCI_AM_NOMBRE.upper() in html_reg.upper() else html_lista
    if not html:
        return fondos

    try:
        _, rows = _parse_tabla(html)

        for row in rows:
            if not _es_bci(row):
                continue

            nombre = _primer_valor(row, ("nombre", "fondo", "denominacion"))
            codigo = _primer_valor(row, ("codigo", "run", "rut", "cod"))
            estado = _primer_valor(row, ("estado", "vigencia"))
            moneda = _primer_valor(row, ("moneda", "currency"))
            series = _primer_valor(row, ("series", "serie", "n_series"))
            agf = _primer_valor(row, ("administradora", "agf", "admin"))
            detalle_href = _primer_href(row)

            detalle_html = _safe_get_detalle(detalle_href)
            link_reg = extraer_link_reglamento(detalle_html) if detalle_html else ""
            fecha_reg = _extraer_fecha_reglamento(detalle_html)

            fondos.append({
                "tipo": "FM",
                "codigo": codigo,
                "nombre": nombre,
                "administrador": agf or "BCI Asset Management AGF S.A.",
                "series": series,
                "moneda": moneda,
                "estado": estado,
                "fecha_reglamento": fecha_reg,
                "link_reglamento": link_reg,
                "archivo_pdf": "",
                "link_detalle_cmf": _absolute(detalle_href) if detalle_href else "",
            })
            print(f"  ✅  FM: {nombre}")
            time.sleep(DELAY_ENTRE_REQUESTS)

    except Exception as exc:  # noqa: BLE001
        print(f"  ❌  Error al procesar fondos mutuos: {exc}", file=sys.stderr)

    return fondos


def buscar_fondos_inversion() -> list[dict]:
    """
    Consulta el portal CMF para obtener los Fondos de Inversión de BCI AM.

    Intenta primero el Registro Público de Depósito de Reglamentos Internos
    (deposito_fondos_inversion.php) filtrando por administradora.  Si no
    retorna resultados, recurre al listado general (consulta.php) y filtra
    localmente.

    Returns:
        Lista de dicts con los campos definidos en CAMPOS_CSV.
    """
    print("Buscando Fondos de Inversión de BCI Asset Management en CMF…")
    fondos: list[dict] = []

    # Estrategia 1: Registro de reglamentos filtrado por administradora
    html_reg = ""
    try:
        html_reg = fetch(
            CMF_FI_REGLAMENTOS,
            post_data={"administradora": BCI_AM_NOMBRE, "boton_buscar": "Buscar"},
        )
    except RuntimeError as exc:
        print(f"  ⚠️  No se pudo usar registro de reglamentos FI: {exc}", file=sys.stderr)

    # Estrategia 2: Listado general (GET sin filtro, se filtra localmente)
    html_lista = ""
    try:
        html_lista = fetch(CMF_FI_BUSQUEDA)
    except RuntimeError as exc:
        print(f"  ❌  Error al buscar fondos de inversión: {exc}", file=sys.stderr)

    # Usar el HTML con más contenido relacionado con BCI
    html = html_reg if html_reg and BCI_AM_NOMBRE.upper() in html_reg.upper() else html_lista
    if not html:
        return fondos

    try:
        _, rows = _parse_tabla(html)

        for row in rows:
            if not _es_bci(row):
                continue

            nombre = _primer_valor(row, ("nombre", "fondo", "denominacion"))
            codigo = _primer_valor(row, ("codigo", "run", "rut", "cod"))
            estado = _primer_valor(row, ("estado", "vigencia"))
            moneda = _primer_valor(row, ("moneda", "currency"))
            series = _primer_valor(row, ("cuotas", "series", "serie"))
            agf = _primer_valor(row, ("administradora", "agf", "admin"))
            detalle_href = _primer_href(row)

            detalle_html = _safe_get_detalle(detalle_href)
            link_reg = extraer_link_reglamento(detalle_html) if detalle_html else ""
            fecha_reg = _extraer_fecha_reglamento(detalle_html)

            fondos.append({
                "tipo": "FI",
                "codigo": codigo,
                "nombre": nombre,
                "administrador": agf or "BCI Asset Management AGF S.A.",
                "series": series,
                "moneda": moneda,
                "estado": estado,
                "fecha_reglamento": fecha_reg,
                "link_reglamento": link_reg,
                "archivo_pdf": "",
                "link_detalle_cmf": _absolute(detalle_href) if detalle_href else "",
            })
            print(f"  ✅  FI: {nombre}")
            time.sleep(DELAY_ENTRE_REQUESTS)

    except Exception as exc:  # noqa: BLE001
        print(f"  ❌  Error al procesar fondos de inversión: {exc}", file=sys.stderr)

    return fondos


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
    # Busca patrones de fecha como "dd/mm/yyyy" o "yyyy-mm-dd" cerca de la palabra "reglamento"
    bloque = html[max(0, html.lower().find("reglamento")):][:500]
    m = re.search(r"(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", bloque)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Descarga de PDFs
# ---------------------------------------------------------------------------


def nombre_archivo_pdf(fondo: dict) -> str:
    """Genera un nombre de archivo seguro para el PDF del reglamento del fondo."""
    nombre = re.sub(r"[^\w\s\-]", "", fondo["nombre"], flags=re.UNICODE)
    nombre = re.sub(r"\s+", "_", nombre.strip().lower())
    tipo = fondo["tipo"].lower()
    codigo = re.sub(r"\W", "", fondo.get("codigo", ""))
    if codigo:
        return f"ri_{tipo}_{codigo}_{nombre[:60]}.pdf"
    return f"ri_{tipo}_{nombre[:80]}.pdf"


def descargar_pdfs(fondos: list[dict]) -> list[dict]:
    """
    Descarga los PDFs de reglamentos internos para todos los fondos con link.

    Actualiza el campo ``archivo_pdf`` de cada fondo con el nombre del archivo
    descargado.

    Returns:
        La misma lista de fondos con el campo ``archivo_pdf`` actualizado.
    """
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
    con_link = [f for f in fondos if f.get("link_reglamento")]
    sin_link = len(fondos) - len(con_link)

    print(f"\nDescargando PDFs ({len(con_link)} con link, {sin_link} sin link)…")

    for fondo in fondos:
        url = fondo.get("link_reglamento", "")
        if not url:
            continue
        nombre_pdf = nombre_archivo_pdf(fondo)
        dest = PDFS_DIR / nombre_pdf
        ok = download_pdf(url, dest)
        if ok:
            fondo["archivo_pdf"] = nombre_pdf
        time.sleep(DELAY_ENTRE_REQUESTS)

    return fondos


# ---------------------------------------------------------------------------
# Generación de índice CSV
# ---------------------------------------------------------------------------


def escribir_csv(fondos: list[dict], ruta: Path) -> None:
    """
    Escribe el índice de fondos en formato CSV.

    Args:
        fondos: Lista de dicts con los campos de CAMPOS_CSV.
        ruta:   Ruta del archivo CSV de salida.
    """
    with ruta.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CAMPOS_CSV,
            extrasaction="ignore",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for fondo in fondos:
            writer.writerow({k: fondo.get(k, "") for k in CAMPOS_CSV})
    print(f"  📄  CSV generado: {ruta}")


# ---------------------------------------------------------------------------
# Generación de índice Markdown
# ---------------------------------------------------------------------------


def escribir_md(fondos: list[dict], ruta: Path) -> None:
    """
    Escribe el índice de fondos en formato Markdown.

    Args:
        fondos: Lista de dicts con los campos de CAMPOS_CSV.
        ruta:   Ruta del archivo Markdown de salida.
    """
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    fm = [f for f in fondos if f["tipo"] == "FM"]
    fi = [f for f in fondos if f["tipo"] == "FI"]

    lineas: list[str] = [
        "# Reglamentos Internos – BCI Asset Management AGF",
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
        "## Cómo actualizar este índice",
        "",
        "```bash",
        "# Regenerar el índice y volver a descargar los PDFs",
        "python descargar_reglamentos_bci.py",
        "",
        "# Solo regenerar el índice (sin descargar PDFs)",
        "python descargar_reglamentos_bci.py --solo-indice",
        "```",
        "",
        "## Referencias normativas",
        "",
        "- [NCG N° 365](../normativa/ncg/ncg_365.md) – Información sobre reglamentos internos de fondos",
        "- [Ley N° 20.712](../normativa/leyes/ley_20712.md) – Ley Única de Fondos",
        f"- [Portal CMF – Buscador de entidades]({CMF_BUSQUEDA_GLOBAL})",
        "",
    ]

    ruta.write_text("\n".join(lineas), encoding="utf-8")
    print(f"  📄  Markdown generado: {ruta}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def construir_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Descarga reglamentos internos de fondos de BCI Asset Management desde CMF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--tipo",
        choices=["FM", "FI"],
        metavar="{FM,FI}",
        help="Limitar la búsqueda a un tipo de fondo: FM (Fondos Mutuos) o FI (Fondos de Inversión).",
    )
    parser.add_argument(
        "--solo-indice",
        action="store_true",
        help="Generar el índice CSV/MD sin descargar los PDFs.",
    )
    parser.add_argument(
        "--salida",
        metavar="ARCHIVO",
        default=str(BASE_DIR / "fondos_bci.csv"),
        help="Ruta del archivo CSV de salida (por defecto: fondos_bci.csv).",
    )
    return parser


def main() -> None:
    args = construir_arg_parser().parse_args()

    fondos: list[dict] = []

    if args.tipo in (None, "FM"):
        fondos += buscar_fondos_mutuos()
    if args.tipo in (None, "FI"):
        fondos += buscar_fondos_inversion()

    if not fondos:
        print(
            "\n⚠️  No se encontraron fondos de BCI Asset Management en el portal CMF.\n"
            "   Posibles causas:\n"
            "   • Sin acceso a internet o portal CMF temporalmente no disponible.\n"
            "   • El nombre de búsqueda no coincide exactamente con el registro CMF.\n"
            f"     Verifica en: {CMF_BUSQUEDA_GLOBAL}\n"
            "   • El portal CMF puede haber actualizado su estructura de URLs.\n"
            f"     Listado FM: {CMF_FM_BUSQUEDA}\n"
            f"     Listado FI: {CMF_FI_BUSQUEDA}\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\nTotal: {len(fondos)} fondos encontrados.\n")

    if not args.solo_indice:
        fondos = descargar_pdfs(fondos)

    ruta_csv = Path(args.salida)
    ruta_md = ruta_csv.with_suffix(".md")

    escribir_csv(fondos, ruta_csv)
    escribir_md(fondos, ruta_md)

    print("\n✅  Proceso finalizado.")
    print(f"   CSV  : {ruta_csv}")
    print(f"   MD   : {ruta_md}")
    if not args.solo_indice:
        descargados = sum(1 for f in fondos if f.get("archivo_pdf"))
        print(f"   PDFs : {descargados} archivo(s) en {PDFS_DIR}/")


if __name__ == "__main__":
    main()
