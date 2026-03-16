#!/usr/bin/env bash
# =============================================================================
# descargar_normativa.sh
# Script para descargar los PDFs oficiales de la normativa base AGF en Chile
# Fuente: Comisión para el Mercado Financiero (CMF) y Biblioteca del Congreso
# =============================================================================

set -euo pipefail

DEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/normativa/pdfs"
mkdir -p "$DEST_DIR"

echo "Directorio de destino: $DEST_DIR"
echo ""

download_pdf() {
  local filename="$1"
  local url="$2"
  local dest="$DEST_DIR/$filename"

  if [ -f "$dest" ] && [ -s "$dest" ]; then
    echo "[OMITIDO]  $filename (ya existe)"
    return
  fi

  echo -n "[DESCARGANDO] $filename ... "
  if curl -s -L --max-time 60 \
      -H "User-Agent: Mozilla/5.0 (compatible; normativa-agf-downloader)" \
      -o "$dest" \
      "$url"; then
    local size
    size=$(wc -c < "$dest")
    if [ "$size" -gt 1000 ]; then
      echo "OK (${size} bytes)"
    else
      echo "ERROR (respuesta muy pequeña, posiblemente no es un PDF válido)"
      rm -f "$dest"
    fi
  else
    echo "ERROR (curl falló)"
    rm -f "$dest"
  fi
}

echo "=== Ley ==="
download_pdf "ley_20712.pdf" \
  "https://www.cmfchile.cl/portal/principal/613/articles-15739_doc_pdf.pdf"

echo ""
echo "=== Normas de Carácter General (NCG) ==="
download_pdf "ncg_365.pdf" \
  "https://www.cmfchile.cl/institucional/mercados/ver_archivo.php?archivo=/web/compendio/ncg/ncg_365_2014.pdf"

download_pdf "ncg_435.pdf" \
  "https://www.cmfchile.cl/normativa/ncg_435_2020.pdf"

download_pdf "ncg_507.pdf" \
  "https://www.cmfchile.cl/institucional/mercados/ver_archivo.php?archivo=/web/compendio/ncg/ncg_507_2024.pdf"

download_pdf "ncg_526.pdf" \
  "https://www.cmfchile.cl/normativa/ncg_526_2024.pdf"

download_pdf "ncg_527.pdf" \
  "https://www.cmfchile.cl/normativa/ncg_527_2024.pdf"

download_pdf "ncg_532.pdf" \
  "https://www.cmfchile.cl/normativa/ncg_532_2025.pdf"

echo ""
echo "=== Resultado ==="
echo "Archivos en $DEST_DIR:"
ls -lh "$DEST_DIR"/*.pdf 2>/dev/null || echo "  (ningún PDF descargado)"
echo ""
echo "Listo. Si algún PDF no se descargó, revisa los enlaces en normativa/pdfs/README.md"
