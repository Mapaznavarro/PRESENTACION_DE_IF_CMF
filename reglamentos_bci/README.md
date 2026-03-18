# Reglamentos Internos – BCI Asset Management AGF

Carpeta dedicada a los **reglamentos internos** de los fondos administrados por
**BCI Asset Management Administradora General de Fondos S.A.** inscritos ante la
Comisión para el Mercado Financiero (CMF).

## Contenido

| Archivo / Carpeta | Descripción |
|-------------------|-------------|
| `descargar_reglamentos_bci.py` | Script Python que consulta el portal CMF, genera el índice y descarga los PDFs |
| `fondos_bci.csv` | Índice CSV generado automáticamente con datos de cada fondo y link al reglamento interno |
| `fondos_bci.md` | Versión Markdown del mismo índice |
| `pdfs/` | PDFs de los reglamentos internos descargados desde CMF |

> `fondos_bci.csv` y `fondos_bci.md` son generados por el script.
> Ejecuta el script para obtener los datos actualizados.

---

## Cómo obtener los reglamentos

### 1. Instalar requisitos

El script solo requiere **Python 3.10 o superior** y no tiene dependencias externas.

### 2. Ejecutar el script

```bash
# Desde la raíz del repositorio:
cd reglamentos_bci

# Buscar todos los fondos de BCI AM, generar el índice y descargar los PDFs:
python descargar_reglamentos_bci.py

# Solo generar el índice CSV/MD (sin descargar los PDFs):
python descargar_reglamentos_bci.py --solo-indice

# Solo Fondos Mutuos:
python descargar_reglamentos_bci.py --tipo FM

# Solo Fondos de Inversión:
python descargar_reglamentos_bci.py --tipo FI

# Exportar el CSV con un nombre personalizado:
python descargar_reglamentos_bci.py --salida mi_indice.csv
```

El script:
1. Consulta el portal institucional de la CMF para cada tipo de fondo.
2. Filtra los fondos administrados por BCI Asset Management.
3. Accede a la página de detalle de cada fondo para obtener el link al reglamento interno.
4. Descarga los PDFs en la carpeta `pdfs/`.
5. Genera `fondos_bci.csv` y `fondos_bci.md` con el índice completo.

### 3. Consultar el índice generado

Una vez ejecutado el script, el archivo `fondos_bci.md` contiene una tabla con:

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

Si prefieres consultar directamente sin ejecutar el script:

| Recurso | URL |
|---------|-----|
| Buscador de Fondos Mutuos | <https://www.cmfchile.cl/institucional/mercados/fondos_mutuos.php> |
| Buscador de Fondos de Inversión | <https://www.cmfchile.cl/institucional/mercados/fondos_inversion.php> |
| Listado de AGF registradas | <https://www.cmfchile.cl/institucional/mercados/agf.php> |
| Normativa para AGF | <https://www.cmfchile.cl/institucional/legislacion_normativa/normativa2.php?hidden_mercado=V&entidad_web=RGAGF> |

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

---

## Estructura de los archivos generados

### `fondos_bci.csv`

```
tipo,codigo,nombre,administrador,series,moneda,estado,fecha_reglamento,link_reglamento,archivo_pdf,link_detalle_cmf
FM,FMXXX,BCI Liquidez,...,BCI Asset Management AGF S.A.,...,...,...,dd/mm/yyyy,https://...,ri_fm_FMXXX_bci_liquidez.pdf,https://...
FI,FIXXX,BCI Renta Mixta,...,BCI Asset Management AGF S.A.,...,...,...,dd/mm/yyyy,https://...,ri_fi_FIXXX_bci_renta_mixta.pdf,https://...
```

### `pdfs/`

Los PDFs se guardan con el formato de nombre:

```
ri_<tipo>_<codigo>_<nombre_fondo>.pdf
```

Ejemplo: `ri_fm_FM0001_bci_liquidez_pesos.pdf`
