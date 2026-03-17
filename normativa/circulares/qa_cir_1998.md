# Plan de Pruebas QA – Circular N° 1998 (Fondos de Inversión IFRS)

> **Rol:** Analista de QA  
> **Alcance:** Validación de los archivos electrónicos generados por el sistema para el cumplimiento de la Circular N° 1998 de la CMF.  
> **Referencia normativa:** [Circular N° 1998](./cir_1998.md)

---

## 1. Alcance de las pruebas

El sistema debe generar los siguientes archivos para cada fondo de inversión por período (trimestral y/o anual):

| ID | Archivo | Formato | Periodicidad |
|----|---------|---------|--------------|
| F-01 | Estados Financieros (ESIF + ERI + ECPN + EFE) | XML | Trimestral |
| F-02 | Notas a los Estados Financieros | PDF | Trimestral |
| F-03 | Estados Complementarios (6.1 Resumen Cartera, 6.2 Rdos. Devengado/Realizado, 6.3 Utilidad p/ Dividendos) | XML | Trimestral |
| F-04 | Cartera de inversión – emisores nacionales (7.1) | XML | Trimestral |
| F-05 | Cartera de inversión – emisores extranjeros (7.2) | XML | Trimestral |
| F-06 | Cartera – método participación (7.3) | XML | Trimestral |
| F-07 | Cartera – bienes raíces (7.4) | XML | Trimestral |
| F-08 | Cartera – contratos de opciones (7.5) | XML | Trimestral |
| F-09 | Cartera – futuros y forward (7.6) | XML | Trimestral |
| F-10 | Opciones lanzador (8.1) | XML | Trimestral |
| F-11 | Operaciones VRC/CRV (8.2) | XML | Trimestral |
| F-12 | Información del fondo y otros antecedentes | XML | Trimestral |
| F-13 | Análisis Razonado | PDF | Trimestral |
| F-14 | Hechos Relevantes | PDF | Trimestral |
| F-15 | Declaración de Responsabilidad | PDF | Trimestral |
| F-16 | Dictamen de los auditores externos | PDF | **Anual** |
| F-17 | EEFF anuales auditados de filiales | PDF | **Anual** (si aplica) |

---

## 2. Casos de prueba – Archivo XML de Estados Financieros (F-01)

### CP-1998-XML-001 – Estructura general del archivo XML

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-XML-001 |
| **Descripción** | Verificar que el archivo XML contiene los cuatro estados financieros requeridos |
| **Pasos** | 1. Generar el XML del fondo para el trimestre. 2. Verificar secciones: ESIF, ERI, ECPN, EFE. |
| **Resultado esperado** | El XML contiene las cuatro secciones correctamente etiquetadas. Ausencia de estados genera error. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-XML-002 – Períodos de referencia trimestrales

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-XML-002 |
| **Descripción** | Verificar que el sistema genera correctamente los cuatro cierres trimestrales |
| **Pasos** | Generar archivos para cada trimestre: 31/03, 30/06, 30/09, 31/12. Verificar la fecha de cierre en cada XML. |
| **Resultado esperado** | Cada XML tiene la fecha de cierre correspondiente. Los comparativos son del mismo trimestre del año anterior. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-XML-003 – Moneda funcional en miles

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-XML-003 |
| **Descripción** | Verificar que todos los valores monetarios están expresados en miles de la moneda funcional |
| **Resultado esperado** | El XML especifica la moneda funcional y la unidad "miles". Los valores numéricos son consistentes con los registros contables. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-XML-004 – Ecuación contable del ESIF

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-XML-004 |
| **Descripción** | Verificar que Total Activos = Total Pasivos + Patrimonio Neto |
| **Resultado esperado** | Total Activos = Total Pasivos + Patrimonio Neto (diferencia ≤ 1 por redondeo en miles) |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-XML-005 – EEFF anual con auditoría

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-XML-005 |
| **Descripción** | Verificar que el sistema requiere el PDF del dictamen de auditoría cuando se generan EEFF anuales (31/12) |
| **Pasos** | 1. Intentar enviar EEFF anuales sin adjuntar F-16. 2. Verificar que el sistema bloquea el envío. |
| **Resultado esperado** | El sistema bloquea el envío de EEFF anuales sin el dictamen de auditores adjunto. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 3. Casos de prueba – Estados Complementarios XML (F-03)

### CP-1998-EC-001 – Resumen de la Cartera de Inversiones (6.1)

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-EC-001 |
| **Descripción** | Verificar que el resumen de cartera incluye todos los tipos de instrumento y las columnas Nacional/Extranjero/Total/% |
| **Pasos** | 1. Generar XML de estados complementarios. 2. Localizar sección 6.1. 3. Verificar la presencia de todos los ítems de inversión. 4. Verificar que los totales cuadran. |
| **Resultado esperado** | Todos los instrumentos están listados. Los porcentajes tienen 4 decimales. El TOTAL de la sección = suma de todos los ítems. El monto total cuadra con el activo de inversiones del ESIF. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-EC-002 – Estado de Resultado Devengado y Realizado (6.2)

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-EC-002 |
| **Descripción** | Verificar la correcta separación entre resultados realizados y no realizados |
| **Pasos** | 1. Localizar sección 6.2 del XML. 2. Verificar las tres secciones: Utilidad/Pérdida Neta Realizada, Pérdida No Realizada, Utilidad No Realizada. 3. Verificar que el "Resultado Neto del Ejercicio" = (Realizado + Devengado No Realizado Positivo – Devengado No Realizado Negativo – Gastos ± Diferencias de Cambio) y coincide con el ERI. |
| **Resultado esperado** | El "Resultado neto del ejercicio" del estado 6.2 coincide con el resultado del ERI (diferencia ≤ 1). |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-EC-003 – Estado de Utilidad para Distribución de Dividendos (6.3)

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-EC-003 |
| **Descripción** | Verificar que el "Monto susceptible de distribuir" se calcula correctamente |
| **Pasos** | 1. Localizar sección 6.3. 2. Verificar cada componente: Beneficio percibido ejercicio, dividendos provisorios, beneficio acumulado ejercicios anteriores, ajustes. 3. Calcular el monto susceptible de distribuir manualmente y comparar. |
| **Resultado esperado** | El monto susceptible de distribuir calculado por el sistema coincide con el cálculo manual (diferencia ≤ 1). |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 4. Casos de prueba – Carteras de Inversión XML (F-04 a F-09)

### CP-1998-CAR-001 – Cartera 7.1: Campos obligatorios por instrumento

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-001 |
| **Descripción** | Verificar que cada instrumento en la cartera 7.1 (emisores nacionales) contiene todos los campos requeridos |
| **Pasos** | 1. Generar XML de cartera 7.1. 2. Por cada instrumento verificar: Clasificación ESIF, Nemotécnico, RUT emisor, Código país, Tipo instrumento, Situación, Clasificación de riesgo, Grupo empresarial, Cantidad unidades, Tipo unidades, Valorización, % capital del emisor (4 decimales), % activo del emisor (4 decimales), % activo del fondo (4 decimales), Valorización al cierre en miles. |
| **Resultado esperado** | No hay campos obligatorios vacíos. Los porcentajes tienen exactamente 4 decimales. La valorización en miles es coherente con el valor unitario y la cantidad. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-CAR-002 – Cartera 7.1: Orden alfabético por nemotécnico

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-002 |
| **Descripción** | Verificar que los instrumentos en la cartera 7.1 están ordenados alfabéticamente por nemotécnico |
| **Resultado esperado** | Los registros de la cartera están en orden alfabético ascendente por el campo nemotécnico. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-CAR-003 – Cartera 7.1: Clasificación ESIF válida

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-003 |
| **Descripción** | Verificar que el código de clasificación en el ESIF es uno de los valores permitidos (1, 2, 3 o 4) |
| **Resultado esperado** | Cada instrumento tiene uno de los cuatro valores de clasificación: 1=VR con efecto resultados, 2=VR con efecto ORI, 3=VR entregados en garantía, 4=Costo amortizado. No hay otros valores. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-CAR-004 – Cartera 7.1: Codificación de instrumentos no registrados

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-004 |
| **Descripción** | Verificar que los instrumentos no registrados usan la codificación correcta de tipo de instrumento |
| **Pasos** | 1. Incluir en el fondo inversiones no registradas: ACN, BN, ECN, MH, CFIP, OTDN, ACIN, ACON, OT. 2. Generar cartera. 3. Verificar que cada instrumento no registrado tiene uno de estos códigos. |
| **Resultado esperado** | Los instrumentos no registrados están correctamente codificados según la tabla de la Circular. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-CAR-005 – Cartera 7.3: Inversiones por método de participación

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-005 |
| **Descripción** | Verificar que las inversiones por método de participación no se incluyen en la cartera 7.1 ni 7.2 |
| **Resultado esperado** | Las inversiones valorizadas por el método de participación aparecen exclusivamente en la cartera 7.3, no en 7.1 o 7.2. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-CAR-006 – Cartera 7.4: Campos de bienes raíces

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-CAR-006 |
| **Descripción** | Verificar que la cartera de bienes raíces incluye el tipo de bien raíz con la codificación correcta |
| **Pasos** | 1. Generar XML de cartera 7.4. 2. Verificar que el campo "Tipo de bien raíz" usa uno de los códigos: T (Terrenos sin edificación), C (Casas), D (Departamentos), L (Locales), G (Galpones), CI (Complejo inmobiliario), PD (Proyecto en desarrollo), N (Otros). |
| **Resultado esperado** | Todos los bienes raíces tienen un tipo válido. Los bienes con prohibiciones o gravámenes están correctamente marcados. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 5. Casos de prueba – Otros Informes XML (F-10 y F-11)

### CP-1998-OTR-001 – Operaciones VRC/CRV (8.2): Campos requeridos

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-OTR-001 |
| **Descripción** | Verificar que cada operación VRC/CRV incluye todos los campos requeridos con el formato correcto |
| **Pasos** | 1. Configurar operaciones VRC y CRV vigentes al cierre. 2. Generar XML del informe 8.2. 3. Verificar por cada operación: fecha, contraparte (RUT + nombre), nemotécnico, tipo de instrumento, clasificación de riesgo, unidades nominales (2 decimales), total transado (miles), precio pactado (2 decimales en pesos/UF/USD), fecha de vencimiento. |
| **Resultado esperado** | Todos los campos obligatorios están presentes y correctamente formateados. Las unidades nominales tienen 2 decimales. El precio pactado tiene 2 decimales. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 6. Casos de prueba – Notas obligatorias en PDF (F-02)

### CP-1998-PDF-001 – Presencia de todas las notas obligatorias

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-001 |
| **Descripción** | Verificar que el PDF de notas incluye las 18 notas obligatorias del Anexo 1 |
| **Resultado esperado** | El PDF incluye las notas 1 a 18. Las notas específicas solo para informes anuales (nota 16) están presentes al cierre del 31/12. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-002 – Nota 2: Activos Financieros a Valor Razonable

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-002 |
| **Descripción** | Verificar la estructura de la tabla de composición de cartera con las columnas correctas |
| **Resultado esperado** | La tabla incluye columnas: Instrumento, Nacional, Extranjero, Total, % del total de activos, con comparativo del período anterior y columna de apertura IFRS al 1/1/2010 (solo en año de adopción). Los subtotales de cada categoría están presentes. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-003 – Nota 4: Inversiones por método de participación

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-003 |
| **Descripción** | Verificar que la nota 4 incluye los tres subtablas requeridas: (a) info financiera resumida, (b) movimiento, (c) plusvalías |
| **Resultado esperado** | Las tres subtablas están presentes. Los saldos iniciales y de cierre cuadran entre los períodos. Las plusvalías están separadas del valor contable. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-004 – Nota 8: Excesos de inversión

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-004 |
| **Descripción** | Verificar que la nota 8 usa la codificación correcta para límite excedido (ATF/CE/GE/O) y causa (FV/DP/AV/O) |
| **Resultado esperado** | Los excesos tienen los códigos correctos. El campo "Imputable a la sociedad administradora" es S o N. Si no hay excesos: declaración explícita de ausencia. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-005 – Nota 12: Rentabilidad del fondo

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-005 |
| **Descripción** | Verificar que la nota 12 incluye rentabilidad nominal y real con 4 decimales para los tres períodos |
| **Pasos** | 1. Localizar nota 12. 2. Verificar columnas: "Período actual", "Últimos 12 meses", "Últimos 24 meses". 3. Verificar que los valores tienen 4 decimales. 4. Verificar que los períodos de 12 y 24 meses son períodos móviles. |
| **Resultado esperado** | Los tres períodos están informados. Los valores tienen exactamente 4 decimales. La rentabilidad del período actual corresponde al acumulado desde el 1/1. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-006 – Nota 15: Información estadística mensual

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-006 |
| **Descripción** | Verificar que la nota 15 contiene los datos al último día de cada mes del período informado |
| **Resultado esperado** | Las columnas incluyen: Valor libro cuota (4 decimales), Valor mercado cuota (4 decimales), Patrimonio (miles), N° aportantes. Los meses están completos para el período (ej.: 3 meses para cierre trimestral). |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1998-PDF-007 – Nota 16: Solo presente en cierres anuales

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-PDF-007 |
| **Descripción** | Verificar que la nota 16 (consolidación de subsidiarias/filiales) solo se incluye en los EEFF anuales (31/12) |
| **Pasos** | 1. Generar PDF de notas para cierre trimestral (ej. 31/03). Verificar que la nota 16 no aparece. 2. Generar PDF de notas para cierre anual (31/12). Verificar que la nota 16 aparece con todas las sub-secciones. |
| **Resultado esperado** | La nota 16 solo está presente en el cierre al 31/12. Para trimestres intermedios no se incluye. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 7. Casos de prueba – Validaciones de negocio transversales

### CP-1998-NEG-001 – Plazos de presentación trimestrales

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-001 |
| **Descripción** | Verificar que el sistema controla los plazos de presentación según el trimestre |
| **Resultado esperado** | El sistema registra las fechas de generación/envío y alerta cuando se supera el plazo permitido (según instrucciones CMF para emisores de valores). |
| **Estado** | ⬜ Pendiente |

### CP-1998-NEG-002 – Consistencia entre carteras y ESIF

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-002 |
| **Descripción** | Verificar que la suma de valorizaciones de las carteras 7.1 a 7.6 coincide con el total de inversiones del ESIF |
| **Pasos** | 1. Generar XML de ESIF. 2. Extraer el total de activos de inversión. 3. Sumar las valorizaciones de todas las carteras. 4. Comparar ambos valores. |
| **Resultado esperado** | La suma de las carteras = total de inversiones en el ESIF (diferencia ≤ 1 por redondeo en miles). |
| **Estado** | ⬜ Pendiente |

### CP-1998-NEG-003 – Consistencia entre resumen de cartera (6.1) y carteras detalladas (7.x)

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-003 |
| **Descripción** | Verificar que los totales por tipo de instrumento del resumen 6.1 coinciden con las carteras detalladas |
| **Resultado esperado** | Los montos del resumen 6.1 por categoría de instrumento son iguales a la suma de las valorizaciones de los instrumentos correspondientes en las carteras 7.1, 7.2 y 7.3. |
| **Estado** | ⬜ Pendiente |

### CP-1998-NEG-004 – Resultado neto cuadra entre 6.2, ERI y 6.3

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-004 |
| **Descripción** | Verificar que el Resultado Neto del Ejercicio es consistente entre el ERI, el estado 6.2 y el estado 6.3 |
| **Resultado esperado** | Resultado Neto (ERI) = Resultado Neto (6.2). La utilidad/pérdida neta realizada del estado 6.3 = ítem 1 del estado 6.2. Los dividendos provisorios del 6.3 coinciden con la cuenta correspondiente del ESIF. |
| **Estado** | ⬜ Pendiente |

### CP-1998-NEG-005 – Fondo sin filiales

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-005 |
| **Descripción** | Verificar que el sistema no requiere F-17 (EEFF de filiales) cuando el fondo no tiene inversiones de control |
| **Resultado esperado** | El campo F-17 es opcional y el sistema no bloquea el envío cuando no hay filiales. La nota 16 indica expresamente que no hay subsidiarias. |
| **Estado** | ⬜ Pendiente |

### CP-1998-NEG-006 – Excepción pro forma: no se envían Anexos 3 y 4

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-NEG-006 |
| **Descripción** | Verificar que para la presentación pro forma del 31/12/2010 el sistema no genera/envía las carteras de inversión (Anexo 3) ni los otros informes (Anexo 4) |
| **Resultado esperado** | El sistema identifica que la presentación es "pro forma" y omite la generación de los archivos F-04 a F-11. |
| **Estado** | ⬜ Pendiente |

---

## 8. Casos de prueba – Manejo de errores

### CP-1998-ERR-001 – XML no válido según Ficha Técnica CMF

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-ERR-001 |
| **Descripción** | Verificar que todos los XML generados cumplen con el schema / ficha técnica de la CMF |
| **Pasos** | 1. Generar todos los archivos XML. 2. Validar cada uno contra el schema XSD/especificaciones de la Ficha Técnica. |
| **Resultado esperado** | Todos los XML pasan la validación sin errores ni advertencias. |
| **Estado** | ⬜ Pendiente |

### CP-1998-ERR-002 – Datos incompletos en cartera de inversiones

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-ERR-002 |
| **Descripción** | Verificar que el sistema reporta error si se intenta generar la cartera 7.1 con instrumentos sin RUT de emisor |
| **Resultado esperado** | El sistema lanza un error descriptivo indicando el instrumento y el campo faltante. No genera archivos parciales. |
| **Estado** | ⬜ Pendiente |

### CP-1998-ERR-003 – Porcentajes fuera de rango

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1998-ERR-003 |
| **Descripción** | Verificar que el sistema valida que los porcentajes del activo total del fondo sumen 100% |
| **Resultado esperado** | El sistema alerta si la suma de porcentajes en el resumen 6.1 difiere de 100% más de 0.01 puntos porcentuales. |
| **Estado** | ⬜ Pendiente |

---

## 9. Matriz de trazabilidad normativa

| Requisito circular | Caso(s) de prueba relacionado(s) |
|--------------------|----------------------------------|
| XML con 4 EEFF | CP-1998-XML-001 |
| Cierre trimestral (4 fechas) | CP-1998-XML-002 |
| Moneda funcional en miles | CP-1998-XML-003 |
| Ecuación contable ESIF | CP-1998-XML-004 |
| Dictamen requerido en cierre anual | CP-1998-XML-005 |
| Resumen cartera 6.1 | CP-1998-EC-001 |
| Estado resultado devengado/realizado 6.2 | CP-1998-EC-002 |
| Estado utilidad para dividendos 6.3 | CP-1998-EC-003 |
| Cartera 7.1: campos obligatorios | CP-1998-CAR-001 |
| Cartera 7.1: orden alfabético | CP-1998-CAR-002 |
| Cartera 7.1: clasificación ESIF | CP-1998-CAR-003 |
| Cartera 7.1: codificación no registrados | CP-1998-CAR-004 |
| Cartera 7.3: separación método participación | CP-1998-CAR-005 |
| Cartera 7.4: tipo de bien raíz | CP-1998-CAR-006 |
| Informe 8.2 VRC/CRV: campos | CP-1998-OTR-001 |
| 18 notas obligatorias | CP-1998-PDF-001 |
| Nota 2: Activos a VR | CP-1998-PDF-002 |
| Nota 4: Inversiones método participación | CP-1998-PDF-003 |
| Nota 8: Excesos de inversión | CP-1998-PDF-004 |
| Nota 12: Rentabilidad | CP-1998-PDF-005 |
| Nota 15: Estadística mensual | CP-1998-PDF-006 |
| Nota 16: Solo en cierre anual | CP-1998-PDF-007 |
| Plazos de presentación | CP-1998-NEG-001 |
| Consistencia carteras ↔ ESIF | CP-1998-NEG-002 |
| Consistencia 6.1 ↔ 7.x | CP-1998-NEG-003 |
| Cuadre ERI / 6.2 / 6.3 | CP-1998-NEG-004 |
| Fondo sin filiales | CP-1998-NEG-005 |
| Excepción pro forma 2010 | CP-1998-NEG-006 |
| Validación schema XML | CP-1998-ERR-001 |
| Datos incompletos en cartera | CP-1998-ERR-002 |
| Porcentajes suman 100% | CP-1998-ERR-003 |
