#!/usr/bin/env python3
"""
analizar.py – Análisis de cumplimiento normativo para AGF (CMF Chile)

Genera un reporte de análisis sobre el marco regulatorio de las
Administradoras Generales de Fondos (AGF) en Chile, con foco en los
requisitos de presentación de información financiera bajo IFRS
(Circulares N° 1997 y N° 1998 de la CMF).

Uso:
    python analizar.py                    # reporte completo en consola
    python analizar.py --circular 1997    # solo Circular 1997 (Fondos Mutuos)
    python analizar.py --circular 1998    # solo Circular 1998 (Fondos de Inversión)
    python analizar.py --salida reporte.md  # exportar a archivo Markdown
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
NORMATIVA_DIR = BASE_DIR / "normativa"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def leer_archivo(ruta: Path) -> str:
    """Lee un archivo de texto y retorna su contenido, o cadena vacía si no existe."""
    if ruta.exists():
        return ruta.read_text(encoding="utf-8")
    return ""


def extraer_casos_prueba(contenido: str) -> list[dict]:
    """
    Extrae los casos de prueba de un archivo QA Markdown.

    Retorna una lista de dicts con keys: id, descripcion, estado.
    """
    casos = []
    # Cada caso comienza con "### CP-" y contiene una tabla Markdown
    bloques = re.split(r"\n### (CP-[A-Z0-9\-]+)", contenido)

    for i in range(1, len(bloques), 2):
        cp_id = bloques[i].strip()
        cuerpo = bloques[i + 1] if i + 1 < len(bloques) else ""

        # Descripción: primera fila de la tabla con "Descripción"
        descripcion = ""
        m = re.search(r"\|\s*\*\*Descripción\*\*\s*\|\s*(.+?)\s*\|", cuerpo)
        if m:
            descripcion = m.group(1).strip()

        # Estado: ⬜ Pendiente / ✅ Aprobado / ❌ Fallido
        estado = "⬜ Pendiente"
        m_estado = re.search(r"\|\s*\*\*Estado\*\*\s*\|\s*(.+?)\s*\|", cuerpo)
        if m_estado:
            estado = m_estado.group(1).strip()

        casos.append({"id": cp_id, "descripcion": descripcion, "estado": estado})

    return casos


def contar_estados(casos: list[dict]) -> dict:
    """Cuenta cuántos casos hay por estado."""
    conteo = {"pendiente": 0, "aprobado": 0, "fallido": 0, "otro": 0}
    for c in casos:
        s = c["estado"].lower()
        if "pendiente" in s:
            conteo["pendiente"] += 1
        elif "aprobado" in s or "✅" in s:
            conteo["aprobado"] += 1
        elif "fallido" in s or "❌" in s:
            conteo["fallido"] += 1
        else:
            conteo["otro"] += 1
    return conteo


def extraer_archivos_requeridos(contenido: str) -> list[dict]:
    """
    Extrae la tabla de archivos requeridos (F-01, F-02, …) del plan QA.
    Retorna lista de dicts con keys: id, descripcion, formato, periodicidad.
    """
    archivos = []
    # Busca filas de tabla con | F-XX |
    for linea in contenido.splitlines():
        m = re.match(
            r"\|\s*(F-\d+)\s*\|\s*(.+?)\s*\|\s*([A-Za-z/]+)\s*\|"
            r"(?:\s*(.+?)\s*\|)?",
            linea,
        )
        if m:
            archivos.append(
                {
                    "id": m.group(1).strip(),
                    "descripcion": m.group(2).strip(),
                    "formato": m.group(3).strip(),
                    "periodicidad": (m.group(4) or "").strip(),
                }
            )
    return archivos


# ---------------------------------------------------------------------------
# Secciones del reporte
# ---------------------------------------------------------------------------

SEPARADOR = "=" * 72


def seccion_encabezado() -> list[str]:
    """Encabezado del reporte con fecha/hora."""
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return [
        SEPARADOR,
        "  ANÁLISIS NORMATIVO – PRESENTACIÓN DE IF CMF",
        "  Administradoras Generales de Fondos (AGF) – Chile",
        SEPARADOR,
        f"  Generado el: {ahora}",
        SEPARADOR,
        "",
    ]


def seccion_resumen_normativa() -> list[str]:
    """Resumen del marco normativo disponible en el repositorio."""
    lineas = [
        "## 1. MARCO NORMATIVO DISPONIBLE EN EL REPOSITORIO",
        "",
    ]

    documentos = {
        "Leyes": [
            ("Ley N° 20.712", "normativa/leyes/ley_20712.md",
             "Ley Única de Fondos – marco principal de las AGF"),
        ],
        "NCG (Normas de Carácter General)": [
            ("NCG N° 365", "normativa/ncg/ncg_365.md",
             "Reglamentos internos de fondos"),
            ("NCG N° 435", "normativa/ncg/ncg_435.md",
             "Participación y votación a distancia en asambleas"),
            ("NCG N° 507", "normativa/ncg/ncg_507.md",
             "Gobierno corporativo y gestión de riesgos (base)"),
            ("NCG N° 526", "normativa/ncg/ncg_526.md",
             "Patrimonio mínimo y garantías de las AGF (2024)"),
            ("NCG N° 527", "normativa/ncg/ncg_527.md",
             "Gobierno corporativo y gestión integral de riesgos (2024)"),
            ("NCG N° 532", "normativa/ncg/ncg_532.md",
             "Manual del Sistema de Información de Fondos – MSI (2025)"),
        ],
        "Circulares": [
            ("Circular N° 1997", "normativa/circulares/cir_1997.md",
             "IFRS para fondos mutuos"),
            ("Circular N° 1998", "normativa/circulares/cir_1998.md",
             "IFRS para fondos de inversión"),
        ],
        "Planes QA": [
            ("QA – Circular 1997", "normativa/circulares/qa_cir_1997.md",
             "Casos de prueba – Fondos Mutuos"),
            ("QA – Circular 1998", "normativa/circulares/qa_cir_1998.md",
             "Casos de prueba – Fondos de Inversión"),
        ],
    }

    for categoria, items in documentos.items():
        lineas.append(f"  ### {categoria}")
        for nombre, ruta, descripcion in items:
            existe = "✅" if (BASE_DIR / ruta).exists() else "❌"
            lineas.append(f"    {existe}  {nombre:<22}  {descripcion}")
        lineas.append("")

    return lineas


def seccion_circular(numero: int) -> list[str]:
    """
    Genera el análisis completo de una Circular (1997 o 1998).
    Incluye archivos requeridos y estado de los casos de prueba.
    """
    if numero == 1997:
        titulo = "CIRCULAR N° 1997 – FONDOS MUTUOS (IFRS)"
        qa_path = NORMATIVA_DIR / "circulares" / "qa_cir_1997.md"
        tipo_fondo = "Fondo Mutuo"
        notas_obligatorias = [
            "1. Política de Inversión del Fondo",
            "2. Activos Financieros a Valor Razonable con Efecto en Resultados",
            "3. Activos Financieros a Costo Amortizado",
            "4. Distribución de Beneficios a los Partícipes",
            "5. Rentabilidad del Fondo (nominal y real para APV/APVC)",
            "6. Custodia de Valores",
            "7. Excesos de Inversión",
            "8. Garantía constituida por la AGF",
            "9. Garantía Fondos Mutuos Estructurados Garantizados (si aplica)",
            "10. Operaciones de Compra con Retroventa",
            "11. Información Estadística (mensual)",
            "12. Sanciones",
            "13. Hechos Relevantes",
            "14. Hechos Posteriores",
        ]
        plazo = (
            "Anual – hasta el último día del bimestre siguiente al 31/12 "
            "(EEFF auditados)"
        )
        estados_fin = [
            "Estado de Situación Financiera (ESIF)",
            "Estado de Resultados Integrales (ERI)",
            "Estado de Cambios en el Activo Neto atribuible a los Partícipes (ECAN)",
            "Estado de Flujos de Efectivo (EFE)",
        ]
    else:
        titulo = "CIRCULAR N° 1998 – FONDOS DE INVERSIÓN (IFRS)"
        qa_path = NORMATIVA_DIR / "circulares" / "qa_cir_1998.md"
        tipo_fondo = "Fondo de Inversión"
        notas_obligatorias = [
            "1. Política de Inversión del Fondo",
            "2. Activos Financieros a Valor Razonable",
            "3. Inversiones método de participación",
            "4. Activos a Costo Amortizado",
            "5. Distribución de Beneficios",
            "6. Rentabilidad del Fondo",
            "7. Custodia de Valores",
            "8. Excesos de Inversión",
            "9. Garantía AGF",
            "10. Operaciones de Compra con Retroventa",
            "11. Información Estadística",
            "12. Sanciones",
            "13. Hechos Relevantes",
            "14. Hechos Posteriores",
        ]
        plazo = (
            "Trimestral – dentro de los 60 días siguientes al cierre del trimestre; "
            "auditor externo requerido solo en EEFF anuales"
        )
        estados_fin = [
            "Estado de Situación Financiera (ESIF)",
            "Estado de Resultados Integrales (ERI)",
            "Estado de Cambios en el Patrimonio Neto (ECPN)",
            "Estado de Flujos de Efectivo (EFE)",
        ]

    num_seccion = 2 if numero == 1997 else 3
    lineas = [
        f"## {num_seccion}. {titulo}",
        "",
        f"  Tipo de fondo: {tipo_fondo}",
        f"  Plazo de presentación: {plazo}",
        "",
    ]

    # Estados financieros
    lineas.append("  ### Estados financieros a presentar")
    for ef in estados_fin:
        lineas.append(f"    • {ef}")
    lineas.append("")

    # Notas obligatorias
    lineas.append("  ### Notas obligatorias a los EEFF")
    for nota in notas_obligatorias:
        lineas.append(f"    • {nota}")
    lineas.append("")

    # Archivos requeridos
    qa_contenido = leer_archivo(qa_path)
    archivos = extraer_archivos_requeridos(qa_contenido)
    if archivos:
        lineas.append("  ### Archivos electrónicos a generar y enviar a la CMF")
        lineas.append(
            f"    {'ID':<8} {'Descripción':<55} {'Formato':<8} Periodicidad"
        )
        lineas.append("    " + "-" * 90)
        for a in archivos:
            per = f"  {a['periodicidad']}" if a["periodicidad"] else ""
            lineas.append(
                f"    {a['id']:<8} {a['descripcion']:<55} {a['formato']:<8}{per}"
            )
        lineas.append("")

    # Casos de prueba QA
    if qa_contenido:
        casos = extraer_casos_prueba(qa_contenido)
        conteo = contar_estados(casos)
        total = len(casos)

        lineas += [
            "  ### Resumen del plan QA",
            f"    Total de casos de prueba : {total}",
            f"    ✅  Aprobados             : {conteo['aprobado']}",
            f"    ❌  Fallidos              : {conteo['fallido']}",
            f"    ⬜  Pendientes            : {conteo['pendiente']}",
            "",
        ]

        if casos:
            lineas.append("  ### Detalle de casos de prueba")
            lineas.append(
                f"    {'ID':<28} {'Estado':<20} Descripción"
            )
            lineas.append("    " + "-" * 90)
            for c in casos:
                desc = c["descripcion"]
                if len(desc) > 46:
                    desc = desc[:43] + "..."
                lineas.append(
                    f"    {c['id']:<28} {c['estado']:<20} {desc}"
                )
            lineas.append("")
    else:
        lineas.append(
            f"  ⚠️  Archivo QA no encontrado: {qa_path.relative_to(BASE_DIR)}"
        )
        lineas.append("")

    return lineas


def seccion_msi_fondos() -> list[str]:
    """Resumen de los 7 archivos MSI (NCG 532)."""
    lineas = [
        "## 4. MSI DE FONDOS – NCG N° 532 (VIGENCIA JUNIO 2026)",
        "",
        "  Reemplaza progresivamente al SEIL. Canal: plataforma CMF Supervisa.",
        "",
        "  ### Archivos periódicos del MSI",
        f"    {'Archivo':<12} {'Periodicidad':<18} Contenido",
        "    " + "-" * 72,
        "    FONDOS01     Semanal/Mensual    Cartera de inversión (excluye derivados)",
        "    FONDOS02     Mensual            Contratos derivados (sincroniza SIID-TR BCCh)",
        "    FONDOS03     Mensual            Gastos y remuneraciones efectivas (TAC)",
        "    FONDOS04     Mensual            Detalle desagregado de gastos (FM y rescatables)",
        "    FONDOS05     Diario             Estado diario de activos, pasivos y patrimonio",
        "    FONDOS06     Mensual            Caracterización de partícipes",
        "    FONDOS07     Al evento          Disminuciones de capital (FI no rescatables)",
        "",
    ]
    return lineas


def seccion_checklist_cumplimiento() -> list[str]:
    """Lista de verificación de cumplimiento para una AGF."""
    return [
        "## 5. CHECKLIST DE CUMPLIMIENTO – AGF",
        "",
        "  Use esta lista como guía de autoevaluación:",
        "",
        "  GOBIERNO CORPORATIVO (NCG 507/527)",
        "    ⬜  Directorio aprobó el apetito de riesgo formalmente",
        "    ⬜  Comité de Auditoría conformado y operativo",
        "    ⬜  Marco de gestión integral de riesgos documentado",
        "    ⬜  Gestor de riesgos designado con independencia funcional",
        "",
        "  PATRIMONIO MÍNIMO Y GARANTÍAS (NCG 526)",
        "    ⬜  Bloque clasificado (1 o 2) según tamaño y clientes",
        "    ⬜  Patrimonio mínimo cubierto conforme a la tabla NCG 526",
        "    ⬜  Garantías vigentes (monto en UF, fechas de cobertura)",
        "",
        "  INFORMACIÓN FINANCIERA – FONDOS MUTUOS (Circular 1997)",
        "    ⬜  EEFF anuales bajo IFRS preparados en miles de la moneda funcional",
        "    ⬜  XML con ESIF + ERI + ECAN + EFE generado y validado",
        "    ⬜  14 notas obligatorias completas en el PDF de notas",
        "    ⬜  Dictamen de auditores externos adjunto",
        "    ⬜  Declaración de responsabilidad firmada por directores y GG",
        "    ⬜  Envío realizado antes del último día del bimestre siguiente al 31/12",
        "",
        "  INFORMACIÓN FINANCIERA – FONDOS DE INVERSIÓN (Circular 1998)",
        "    ⬜  EEFF trimestrales bajo IFRS preparados",
        "    ⬜  XML con ESIF + ERI + ECPN + EFE generado por trimestre",
        "    ⬜  Estados complementarios y carteras de inversión incluidos",
        "    ⬜  Análisis Razonado en PDF adjunto",
        "    ⬜  Dictamen de auditores externos (solo cierre anual)",
        "    ⬜  Envío dentro de los 60 días del cierre trimestral",
        "",
        "  REPORTE PERIÓDICO – MSI DE FONDOS (NCG 532, desde jun-2026)",
        "    ⬜  Sistema de envío migrado a CMF Supervisa",
        "    ⬜  FONDOS01: cartera semanal/mensual configurada",
        "    ⬜  FONDOS05: proceso diario de activos/pasivos/patrimonio",
        "    ⬜  Demás archivos FONDOS02–07 configurados según periodicidad",
        "",
    ]


def seccion_pie() -> list[str]:
    """Pie del reporte con referencias."""
    return [
        SEPARADOR,
        "  REFERENCIAS",
        SEPARADOR,
        "  • Circular N° 1997 : normativa/circulares/cir_1997.md",
        "  • Circular N° 1998 : normativa/circulares/cir_1998.md",
        "  • QA Circular 1997 : normativa/circulares/qa_cir_1997.md",
        "  • QA Circular 1998 : normativa/circulares/qa_cir_1998.md",
        "  • NCG N° 532 (MSI) : normativa/ncg/ncg_532.md",
        "  • Glosario          : normativa/contexto/glosario.md",
        "  • PDFs oficiales    : bash descargar_normativa.sh",
        "  • CMF Portal        : https://www.cmfchile.cl",
        SEPARADOR,
        "",
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def construir_reporte(circular: int | None) -> list[str]:
    """Construye el reporte completo o parcial según el parámetro circular."""
    lineas: list[str] = []
    lineas += seccion_encabezado()

    if circular is None:
        lineas += seccion_resumen_normativa()
        lineas += seccion_circular(1997)
        lineas += seccion_circular(1998)
        lineas += seccion_msi_fondos()
        lineas += seccion_checklist_cumplimiento()
    elif circular == 1997:
        lineas += seccion_circular(1997)
    elif circular == 1998:
        lineas += seccion_circular(1998)
    else:
        print(f"Error: circular '{circular}' no reconocida. Use 1997 o 1998.",
              file=sys.stderr)
        sys.exit(1)

    lineas += seccion_pie()
    return lineas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un reporte de análisis normativo para AGF (CMF Chile).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--circular",
        type=int,
        choices=[1997, 1998],
        metavar="{1997,1998}",
        help="Limitar el análisis a una Circular específica (1997 o 1998).",
    )
    parser.add_argument(
        "--salida",
        metavar="ARCHIVO",
        help="Exportar el reporte a un archivo (p.ej. reporte.md o reporte.txt).",
    )
    args = parser.parse_args()

    lineas = construir_reporte(args.circular)
    reporte = "\n".join(lineas)

    if args.salida:
        ruta_salida = Path(args.salida)
        ruta_salida.write_text(reporte, encoding="utf-8")
        print(f"Reporte guardado en: {ruta_salida}")
    else:
        print(reporte)


if __name__ == "__main__":
    main()
