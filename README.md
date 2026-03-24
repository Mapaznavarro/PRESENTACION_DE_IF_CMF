# PRESENTACION_DE_IF_CMF

Repositorio de normativa base en Chile para las **Administradoras Generales de Fondos (AGF)**, orientado a ser utilizado como contexto de referencia regulatoria.

## ¿Qué es una AGF?

Una **Administradora General de Fondos (AGF)** es una sociedad anónima autorizada por la Comisión para el Mercado Financiero (CMF) para administrar fondos de terceros (fondos mutuos, fondos de inversión, fondos de inversión privados, fondos para la vivienda, etc.) y/o carteras individuales. Opera bajo la fiscalización permanente de la CMF.

## Marco regulatorio

El marco normativo que regula a las AGF en Chile se estructura en torno a:

1. **Ley N° 20.712** – *Ley Única de Fondos (LUF)*: ley principal que define la operación, constitución y fiscalización de las AGF y sus fondos.
2. **Normas de Carácter General (NCG)** emitidas por la CMF que desarrollan los requisitos específicos.
3. **Circulares** con instrucciones operativas particulares.

## Análisis normativo

El repositorio incluye el script `analizar.py` que genera un reporte de análisis sobre el marco regulatorio: documentos disponibles, archivos requeridos por cada Circular, estado de los planes QA y un checklist de cumplimiento para AGF.

```bash
# Reporte completo (todas las secciones)
python analizar.py

# Solo Circular N° 1997 (Fondos Mutuos)
python analizar.py --circular 1997

# Solo Circular N° 1998 (Fondos de Inversión)
python analizar.py --circular 1998

# Exportar el reporte a un archivo
python analizar.py --salida reporte.md
```

Requisitos: Python 3.10 o superior (sin dependencias externas).

## Cómo descargar los PDFs oficiales

Cada documento normativo tiene su PDF oficial publicado por la CMF. Para descargarlos todos localmente:

```bash
bash descargar_normativa.sh
```

Los PDFs quedarán en la carpeta `normativa/pdfs/`. También puedes descargarlos individualmente desde los enlaces en cada documento o desde el [índice de PDFs](normativa/pdfs/README.md).

## Reglamentos internos de fondos – Todas las AGF

La carpeta [`reglamentos_todas_agf/`](reglamentos_todas_agf/) contiene un script Python
que descarga automáticamente los **reglamentos internos** de los fondos de
**todas las AGF** registradas en la CMF, creando una subcarpeta por cada administradora.

```bash
# Descargar reglamentos de TODAS las AGF (índices + PDFs)
cd reglamentos_todas_agf
python descargar_todos_reglamentos.py

# Solo generar los índices sin descargar PDFs
python descargar_todos_reglamentos.py --solo-indice

# Solo una AGF específica
python descargar_todos_reglamentos.py --agf "LARRAIN VIAL"
```

Los resultados quedan organizados en subcarpetas por AGF:
`reglamentos_todas_agf/<NOMBRE_AGF>/fondos.csv`, `fondos.md` y `pdfs/`.  
Consulta la documentación completa en [`reglamentos_todas_agf/README.md`](reglamentos_todas_agf/README.md).

## Reglamentos internos de fondos BCI Asset Management

La carpeta [`reglamentos_bci/`](reglamentos_bci/) contiene un script Python y un
índice de los **reglamentos internos** de los fondos de
BCI Asset Management Administradora General de Fondos S.A. registrados en la CMF.

```bash
# Generar el índice y descargar los PDFs de reglamentos
cd reglamentos_bci
python descargar_reglamentos_bci.py

# Solo generar el índice sin descargar PDFs
python descargar_reglamentos_bci.py --solo-indice
```

Los resultados quedan en `reglamentos_bci/fondos_bci.csv`, `reglamentos_bci/fondos_bci.md`
y `reglamentos_bci/pdfs/`.
Consulta la documentación completa en [`reglamentos_bci/README.md`](reglamentos_bci/README.md).

---

## Índice de documentos

### Leyes

| Documento | Descripción | PDF oficial |
|-----------|-------------|-------------|
| [Ley N° 20.712](normativa/leyes/ley_20712.md) | Ley Única de Fondos – marco principal de las AGF | [CMF ↗](https://www.cmfchile.cl/portal/principal/613/articles-15739_doc_pdf.pdf) |

### Normas de Carácter General (NCG)

| Documento | Descripción | PDF oficial |
|-----------|-------------|-------------|
| [NCG N° 365](normativa/ncg/ncg_365.md) | Información sobre reglamentos internos de fondos | [CMF ↗](https://www.cmfchile.cl/institucional/mercados/ver_archivo.php?archivo=/web/compendio/ncg/ncg_365_2014.pdf) |
| [NCG N° 435](normativa/ncg/ncg_435.md) | Participación y votación a distancia en asambleas de aportantes | [CMF ↗](https://www.cmfchile.cl/normativa/ncg_435_2020.pdf) |
| [NCG N° 507](normativa/ncg/ncg_507.md) | Gobierno corporativo y gestión de riesgos (base) | [CMF ↗](https://www.cmfchile.cl/institucional/mercados/ver_archivo.php?archivo=/web/compendio/ncg/ncg_507_2024.pdf) |
| [NCG N° 526](normativa/ncg/ncg_526.md) | Patrimonio mínimo y garantías de las AGF (2024) | [CMF ↗](https://www.cmfchile.cl/normativa/ncg_526_2024.pdf) |
| [NCG N° 527](normativa/ncg/ncg_527.md) | Gobierno corporativo y gestión integral de riesgos (2024) | [CMF ↗](https://www.cmfchile.cl/normativa/ncg_527_2024.pdf) |
| [NCG N° 532](normativa/ncg/ncg_532.md) | Manual de Sistema de Información de Fondos – MSI (2025) | [CMF ↗](https://www.cmfchile.cl/normativa/ncg_532_2025.pdf) |

### Circulares

| Documento | Descripción | PDF oficial |
|-----------|-------------|-------------|
| [Circular N° 1997](normativa/circulares/cir_1997.md) | Presentación de información financiera bajo IFRS para fondos mutuos | [CMF ↗](https://www.cmfchile.cl/normativa/cir_1997_2010.pdf) |
| [Circular N° 1998](normativa/circulares/cir_1998.md) | Presentación de información financiera bajo IFRS para fondos de inversión | [CMF ↗](https://www.cmfchile.cl/normativa/cir_1998_2010.pdf) |

### Planes de prueba QA – Circulares

| Documento | Descripción |
|-----------|-------------|
| [QA – Circular N° 1997](normativa/circulares/qa_cir_1997.md) | Casos de prueba para validar los archivos generados según Circular 1997 (Fondos Mutuos) |
| [QA – Circular N° 1998](normativa/circulares/qa_cir_1998.md) | Casos de prueba para validar los archivos generados según Circular 1998 (Fondos de Inversión) |

### Contexto y glosario

| Documento | Descripción |
|-----------|-------------|
| [Glosario](normativa/contexto/glosario.md) | Definiciones clave del sector AGF en Chile |
| [Índice de PDFs](normativa/pdfs/README.md) | Lista completa de PDFs y cómo descargarlos |

## Sobre el agente de Copilot

Si ves la pantalla **"Setting up environment"** con líneas como
`Start 'playwright' MCP server` o `Start 'github-mcp-server' MCP server` al
asignarle una tarea al agente de GitHub Copilot, consulta la explicación detallada
en:

📄 [docs/agente-copilot.md](docs/agente-copilot.md)

---

## Fuentes oficiales

- [CMF – Normativa para AGF](https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php?hidden_mercado=V&entidad_web=RGAGF)
- [CMF – Normativa para FFMM](https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php?hidden_mercado=V&entidad_web=RGFMU)
- [CMF – Normativa para FFII](https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php?hidden_mercado=V&entidad_web=RGFIN)

- [Biblioteca del Congreso Nacional – Ley 20.712](https://www.leychile.cl/leychile/Navegar?idNorma=1057895)
- [CMF – Portal institucional](https://www.cmfchile.cl)
