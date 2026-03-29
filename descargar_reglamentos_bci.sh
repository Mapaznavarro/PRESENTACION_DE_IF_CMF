#!/usr/bin/env bash
# =============================================================================
# descargar_reglamentos_bci.sh
# Script para descargar los PDFs de reglamentos internos de los fondos de
# BCI Asset Management Administradora General de Fondos S.A. registrados
# en la Comisión para el Mercado Financiero (CMF).
#
# Este script es el equivalente a descargar_normativa.sh pero para los
# reglamentos internos de fondos gestionados por BCI Asset Management.
#
# Los PDFs quedarán en la carpeta reglamentos_bci/pdfs/
# El índice se generará en reglamentos_bci/fondos_bci.csv y fondos_bci.md
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGLAMENTOS_DIR="$SCRIPT_DIR/reglamentos_bci"
PYTHON_SCRIPT="$REGLAMENTOS_DIR/descargar_reglamentos_bci.py"

# ---------------------------------------------------------------------------
# Verificar Python 3
# ---------------------------------------------------------------------------

if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
  echo "ERROR: No se encontró Python 3. Instálalo antes de continuar."
  exit 1
fi

# Usa python3 si está disponible, sino python (que puede ser Python 3)
if command -v python3 &>/dev/null; then
  PYTHON_CMD="python3"
else
  PYTHON_CMD="python"
fi

# Verificar que la versión de Python sea 3.10+
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
  echo "ERROR: Se requiere Python 3.10 o superior (versión actual: $PYTHON_VERSION)."
  exit 1
fi

echo "Python detectado: $PYTHON_CMD ($PYTHON_VERSION)"
echo ""

# ---------------------------------------------------------------------------
# Ejecutar el script Python
# ---------------------------------------------------------------------------

echo "Directorio de salida: $REGLAMENTOS_DIR/pdfs/"
echo ""

# Pasar todos los argumentos al script Python (--tipo FM, --solo-indice, etc.)
$PYTHON_CMD "$PYTHON_SCRIPT" "$@"
