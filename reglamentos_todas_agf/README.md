# Reglamentos Internos – Todas las AGF

Carpeta dedicada a los **reglamentos internos** de los fondos de
**todas las Administradoras Generales de Fondos (AGF)** inscritas ante la
Comisión para el Mercado Financiero (CMF) de Chile.

## Contenido

| Archivo / Carpeta | Descripción |
|-------------------|-------------|
| `descargar_todos_reglamentos.py` | Script Python que consulta el portal CMF, genera los índices y descarga los PDFs para todas las AGF |
| `indice_agf.csv` | Resumen global de todas las AGF procesadas (generado por el script) |
| `indice_agf.md` | Versión Markdown del resumen global (generado por el script) |
| `<NOMBRE_AGF>/` | Subcarpeta por cada AGF (generada por el script) |
| `<NOMBRE_AGF>/fondos.csv` | Índice CSV de los fondos de esa AGF con links a los reglamentos |
| `<NOMBRE_AGF>/fondos.md` | Versión Markdown del índice de fondos |
| `<NOMBRE_AGF>/pdfs/` | PDFs de los reglamentos internos descargados |

> `indice_agf.csv`, `indice_agf.md` y todas las subcarpetas de AGF son
> generados automáticamente por el script.
> Ejecuta el script para obtener los datos actualizados desde el portal CMF.

---

## Cómo obtener los reglamentos

### 1. Instalar requisitos

El script solo requiere **Python 3.10 o superior** y no tiene dependencias externas.

### 2. Ejecutar el script

```bash
# Desde la raíz del repositorio:
cd reglamentos_todas_agf

# Descargar reglamentos de TODAS las AGF (índices + PDFs):
python descargar_todos_reglamentos.py

# Solo generar los índices (sin descargar PDFs):
python descargar_todos_reglamentos.py --solo-indice

# Solo una AGF específica (búsqueda parcial, insensible a mayúsculas):
python descargar_todos_reglamentos.py --agf "LARRAIN VIAL"
python descargar_todos_reglamentos.py --agf "BICE"

# Solo Fondos Mutuos de todas las AGF:
python descargar_todos_reglamentos.py --tipo FM

# Solo Fondos de Inversión de todas las AGF:
python descargar_todos_reglamentos.py --tipo FI

# Aumentar la pausa entre peticiones (útil si el portal rechaza peticiones):
python descargar_todos_reglamentos.py --delay 2.0
```

El script:
1. Consulta `https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF` para obtener el listado de AGF vigentes.
2. Por cada AGF, crea una subcarpeta con su nombre sanitizado.
3. Busca todos los fondos de esa AGF en los registros de Fondos Mutuos y Fondos de Inversión de la CMF.
4. Accede a la página de detalle de cada fondo para extraer el link al reglamento interno.
5. Descarga los PDFs en la subcarpeta `pdfs/` de cada AGF.
6. Genera `fondos.csv` y `fondos.md` con el índice de fondos de cada AGF.
7. Genera `indice_agf.csv` y `indice_agf.md` con el resumen global de todas las AGF.

### 3. Estructura generada tras ejecutar el script

```
reglamentos_todas_agf/
├── descargar_todos_reglamentos.py
├── README.md
├── indice_agf.csv                  ← resumen global de AGF
├── indice_agf.md
├── BCI_ASSET_MANAGEMENT_AGF_SA/
│   ├── fondos.csv
│   ├── fondos.md
│   └── pdfs/
│       ├── ri_fm_FMXXX_bci_liquidez_pesos.pdf
│       └── ri_fi_FIXXX_bci_renta_mixta.pdf
├── LARRAINVIAL_AGF_SA/
│   ├── fondos.csv
│   ├── fondos.md
│   └── pdfs/
│       └── ...
└── ...  (una carpeta por cada AGF vigente en CMF)
```

---

## Índice generado (`indice_agf.md`)

Una vez ejecutado el script, el archivo `indice_agf.md` contiene una tabla con:

| Campo | Descripción |
|-------|-------------|
| AGF | Nombre de la administradora |
| RUT | RUT de la sociedad administradora |
| Estado | Estado de registro en CMF |
| Fondos | Total de fondos encontrados |
| FM | Cantidad de Fondos Mutuos |
| FI | Cantidad de Fondos de Inversión |
| Con Reglamento | Fondos con PDF de reglamento disponible |
| Carpeta | Link a la subcarpeta con los índices de esa AGF |

---

## Índice por AGF (`fondos.md`)

Cada subcarpeta de AGF contiene un `fondos.md` con:

| Campo | Descripción |
|-------|-------------|
| Código | Identificador del fondo en la CMF |
| Nombre | Denominación del fondo |
| Estado | Estado de vigencia (vigente / en liquidación / etc.) |
| Moneda | Moneda de denominación del fondo |
| Fecha Reglamento | Fecha de depósito o última modificación |
| Reglamento Interno | Link directo al PDF en el portal CMF |
| Detalle CMF | Link a la ficha del fondo en el portal CMF |

---

## Acceso directo al portal CMF

| Recurso | URL |
|---------|-----|
| Listado de AGF vigentes | <https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF> |
| Listado de Fondos Mutuos | <https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&entidad=RGFMU> |
| Listado de Fondos de Inversión | <https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&entidad=RGFI> |
| Reglamentos Internos – FM | <https://www.cmfchile.cl/institucional/inc/deposito_fondos_mutuos.php> |
| Reglamentos Internos – FI | <https://www.cmfchile.cl/institucional/inc/deposito_fondos_inversion.php> |

---

## Marco normativo

Los reglamentos internos de fondos son documentos de cumplimiento obligatorio
regulados principalmente por:

| Norma | Descripción |
|-------|-------------|
| [Ley N° 20.712](../normativa/leyes/ley_20712.md) | Ley Única de Fondos – obliga a contar con reglamento interno |
| [NCG N° 365](../normativa/ncg/ncg_365.md) | Instrucciones para el depósito y modificación de reglamentos internos |
| [NCG N° 532](../normativa/ncg/ncg_532.md) | MSI de Fondos – incorpora envío estructurado de variables del reglamento |

Según la **NCG N° 365**, todo fondo administrado por una AGF debe contar con un
reglamento interno depositado en la CMF antes de comenzar a operar. El reglamento
debe incluir, al menos:

- Denominación y objeto del fondo.
- Política de inversiones y diversificación.
- Comisiones, remuneraciones y gastos de cargo del fondo.
- Procedimiento de rescate y plazos de pago (fondos rescatables).
- Procedimiento de valorización de cuotas.
- Mecanismos de información a los partícipes.
