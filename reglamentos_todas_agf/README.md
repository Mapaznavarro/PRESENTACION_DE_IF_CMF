# Reglamentos Internos – Todas las AGF

Carpeta dedicada a los **reglamentos internos** de los fondos de
**todas las Administradoras Generales de Fondos (AGF)** inscritas ante la
Comisión para el Mercado Financiero (CMF) de Chile.

## Contenido

| Archivo / Carpeta | Descripción |
|-------------------|-------------|
| `descargar_todos_reglamentos.py` | Script Python que navega el portal CMF, genera los índices y descarga los archivos para todas las AGF |
| `indice_agf.csv` | Resumen global de todas las AGF procesadas (generado por el script) |
| `indice_agf.md` | Versión Markdown del resumen global (generado por el script) |
| `fallos_extraccion.csv` | AGF y fondos para los que no se pudo extraer información (generado por el script, solo si hubo fallos) |
| `<NOMBRE_AGF>/` | Subcarpeta por cada AGF (generada por el script) |
| `<NOMBRE_AGF>/fondos.csv` | Índice CSV de los fondos de esa AGF con estado de descarga |
| `<NOMBRE_AGF>/fondos.md` | Versión Markdown del índice de fondos |
| `<NOMBRE_AGF>/pdfs/` | Archivos descargados (reglamento interno + modificaciones en trámite) |

> `indice_agf.csv`, `indice_agf.md` y todas las subcarpetas de AGF son
> generados automáticamente por el script.
> Ejecuta el script para obtener los datos actualizados desde el portal CMF.

---

## Flujo de navegación

El script sigue el flujo exacto del portal CMF:

```
Ruta Inicial
  └─ https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF
       │  Tabla R.U.T. / Entidad → link del RUT de cada AGF
       ▼
  Página de la AGF  (pestania=1)
       │  Clic en botón "Fondos Administrados"  (pestania=39)
       ▼
  Lista de Fondos Administrados
       │  Tabla R.U.T. / Entidad → link del RUT de cada Fondo
       ▼
  Página del Fondo  (pestania=1)
       │  Clic en botón "reglamento interno"  (pestania=56)
       ▼
  Página de Reglamento Interno
       │  Primera tabla con id="Tabla"
       │    Primer link  "Descarga" → <original>_<rut_agf>_<rut_fondo>_Reg_Interno.<ext>
       └─   Segundo link "Descarga" → <original>_<rut_agf>_<rut_fondo>_modif.<ext>
```

---

## Cómo obtener los reglamentos

### 1. Instalar requisitos

El script solo requiere **Python 3.10 o superior** y no tiene dependencias externas.

### 2. Ejecutar el script

```bash
# Desde la raíz del repositorio:
cd reglamentos_todas_agf

# Descargar reglamentos de TODAS las AGF (índices + archivos):
python descargar_todos_reglamentos.py

# Solo generar los índices (sin descargar archivos):
python descargar_todos_reglamentos.py --solo-indice

# Solo una AGF específica (búsqueda parcial, insensible a mayúsculas):
python descargar_todos_reglamentos.py --agf "LARRAIN VIAL"
python descargar_todos_reglamentos.py --agf "BICE"

# Aumentar la pausa entre peticiones (útil si el portal rechaza peticiones):
python descargar_todos_reglamentos.py --delay 2.0
```

### 3. Estructura generada tras ejecutar el script

```
reglamentos_todas_agf/
├── descargar_todos_reglamentos.py
├── README.md
├── indice_agf.csv                  ← resumen global de AGF
├── indice_agf.md
├── fallos_extraccion.csv           ← AGF/fondos con fallo de extracción (si los hay)
├── BCI_ASSET_MANAGEMENT_AGF_SA/
│   ├── fondos.csv
│   ├── fondos.md
│   └── pdfs/
│       ├── 20240101_96639280_10000_Reg_Interno.pdf   ← reglamento vigente
│       └── 20240101_96639280_10000_modif.pdf          ← modificaciones en trámite
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
| Fondos | Total de fondos encontrados |
| Con Reglamento | Fondos con archivo de reglamento descargado |
| Carpeta | Link a la subcarpeta con los índices de esa AGF |

---

## Índice por AGF (`fondos.md`)

Cada subcarpeta de AGF contiene un `fondos.md` con:

| Campo | Descripción |
|-------|-------------|
| RUT Fondo | RUT del fondo |
| Nombre | Denominación del fondo |
| Reglamento Interno | Nombre del archivo descargado (reglamento vigente) |
| Modif en trámite | Nombre del archivo descargado (modificaciones en trámite) |
| Estado | Estado del proceso (`ok`, `sin_reglamento`, `sin_descarga`, etc.) |

---

## Acceso directo al portal CMF

| Recurso | URL |
|---------|-----|
| **Listado de AGF vigentes (ruta inicial)** | <https://www.cmfchile.cl/institucional/mercados/consulta.php?mercado=V&Estado=VI&entidad=RGAGF> |

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
