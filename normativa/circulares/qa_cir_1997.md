# Plan de Pruebas QA – Circular N° 1997 (Fondos Mutuos IFRS)

> **Rol:** Analista de QA  
> **Alcance:** Validación de los archivos electrónicos generados por el sistema para el cumplimiento de la Circular N° 1997 de la CMF.  
> **Referencia normativa:** [Circular N° 1997](./cir_1997.md)

---

## 1. Alcance de las pruebas

El sistema debe generar los siguientes archivos para cada fondo mutuo:

| ID | Archivo | Formato |
|----|---------|---------|
| F-01 | Estados Financieros (ESIF + ERI + ECAN + EFE) | XML |
| F-02 | Notas a los Estados Financieros | PDF |
| F-03 | Dictamen de los auditores externos | PDF |
| F-04 | Declaración de responsabilidad | PDF |

---

## 2. Casos de prueba – Archivo XML de Estados Financieros (F-01)

### CP-1997-XML-001 – Estructura general del archivo XML

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-001 |
| **Descripción** | Verificar que el archivo XML contiene los cuatro estados financieros requeridos |
| **Precondición** | El sistema tiene datos de un fondo mutuo con cierre al 31 de diciembre |
| **Pasos** | 1. Generar el XML del fondo. 2. Abrir el archivo y verificar la estructura. |
| **Resultado esperado** | El XML contiene secciones diferenciadas para: Estado de Situación Financiera (ESIF), Estado de Resultados Integrales (ERI), Estado de Cambios en el Activo Neto atribuible a los Partícipes (ECAN) y Estado de Flujos de Efectivo (EFE). |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-XML-002 – Moneda funcional y unidad de medida

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-002 |
| **Descripción** | Verificar que todos los valores monetarios están expresados en miles de la moneda funcional del fondo |
| **Precondición** | El fondo tiene definida una moneda funcional (ej.: CLP, USD) |
| **Pasos** | 1. Generar XML. 2. Revisar metadatos de moneda y unidad de medida en el XML. 3. Comparar los valores contra los registros contables. |
| **Resultado esperado** | Los valores numéricos corresponden a miles de la moneda funcional declarada. El XML especifica la moneda funcional y la unidad "miles". |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-XML-003 – Período de referencia

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-003 |
| **Descripción** | Verificar que el período de referencia del XML es el 31 de diciembre del año que corresponde |
| **Pasos** | 1. Generar XML para el ejercicio anual. 2. Verificar la fecha de cierre declarada en el XML. |
| **Resultado esperado** | La fecha de cierre es "31/12/AAAA". Los EEFF comparativos corresponden al ejercicio anterior. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-XML-004 – Cuadre del Estado de Situación Financiera

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-004 |
| **Descripción** | Verificar que Total Activos = Total Pasivos + Activo Neto en el ESIF |
| **Pasos** | 1. Extraer los valores de Total Activos, Total Pasivos y Activo Neto del XML. 2. Verificar la ecuación contable. |
| **Resultado esperado** | Total Activos = Total Pasivos + Activo Neto (diferencia ≤ 1 por redondeo en miles) |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-XML-005 – Comparativos del ejercicio anterior

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-005 |
| **Descripción** | Verificar que el XML incluye columnas comparativas del ejercicio anterior (excepto primer año) |
| **Pasos** | 1. Generar XML para ejercicio N. 2. Verificar que los saldos del período N-1 están presentes. |
| **Resultado esperado** | Para ejercicios a partir del año 2 (≥ 2011), el XML incluye una columna comparativa con los valores del ejercicio anterior. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-XML-006 – Estados financieros "pro forma" (primer año)

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-XML-006 |
| **Descripción** | Verificar que los EEFF "pro forma" al 31/12/2010 no incluyen comparativos del ejercicio anterior pero sí los saldos de apertura al 1/1/2010 en el ESIF |
| **Pasos** | 1. Generar XML pro forma para el ejercicio 2010. 2. Verificar que no hay columna comparativa para 2009. 3. Verificar que el ESIF incluye saldos al 1/1/2010. |
| **Resultado esperado** | El XML del ESIF tiene dos columnas: "Al 1/1/2010" y "Al 31/12/2010". No existen columnas para el ejercicio 2009. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 3. Casos de prueba – Notas a los EEFF en PDF (F-02)

### CP-1997-PDF-001 – Presencia de todas las notas obligatorias

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-001 |
| **Descripción** | Verificar que el PDF de notas incluye las 14 notas obligatorias definidas en el Anexo de la Circular |
| **Pasos** | 1. Generar PDF de notas. 2. Revisar el índice o el cuerpo del PDF. 3. Confirmar presencia de cada nota numerada. |
| **Resultado esperado** | El PDF incluye las notas 1 a 14: Política de Inversión, Activos a VR, Activos a Costo Amortizado, Distribución de Beneficios, Rentabilidad, Custodia, Excesos de Inversión, Garantías AGF, Garantías Estructurados Garantizados, Retroventa, Información Estadística, Sanciones, Hechos Relevantes, Hechos Posteriores. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-002 – Nota 2: Activos Financieros a Valor Razonable

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-002 |
| **Descripción** | Verificar que la nota 2 incluye la tabla de composición de cartera con las columnas requeridas |
| **Pasos** | 1. Abrir el PDF. 2. Localizar la nota 2. 3. Verificar columnas: Instrumento / Nacional / Extranjero / Total / % del total de activos. 4. Verificar presencia de comparativo y columna de apertura IFRS (1/1/2010 solo en año de adopción). |
| **Resultado esperado** | La tabla tiene estructura columnar correcta. Los subtotales de "Títulos de Renta Variable" y "Títulos de Deuda" están presentes. El total general cuadra con el saldo del ESIF. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-003 – Nota 5: Rentabilidad Nominal

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-003 |
| **Descripción** | Verificar que la nota 5 incluye rentabilidad mensual con 4 decimales y rentabilidades acumuladas para 1, 2 y 3 años |
| **Pasos** | 1. Localizar nota 5 en el PDF. 2. Verificar que los 12 meses del año tienen rentabilidad informada con 4 decimales. 3. Verificar columnas de rentabilidad acumulada: "Último año", "Últimos dos años", "Últimos tres años". |
| **Resultado esperado** | Todos los valores de rentabilidad tienen exactamente 4 decimales. Las columnas acumuladas están presentes. Para fondos con series APV/APVC se incluye rentabilidad real. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-004 – Nota 7: Excesos de inversión

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-004 |
| **Descripción** | Verificar que la nota 7 informa correctamente los excesos de inversión con la codificación establecida |
| **Pasos** | 1. Localizar nota 7. 2. Verificar que la columna "Límite excedido" usa las claves ATF / GE / O. 3. Verificar que "Causa del exceso" usa las claves FV / DP / AV / O. 4. Verificar que los porcentajes tienen 2 decimales. |
| **Resultado esperado** | Si hay excesos: están correctamente codificados y documentados. Si no hay excesos: se declara expresamente su ausencia. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-005 – Nota 8: Garantía de la AGF

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-005 |
| **Descripción** | Verificar que la nota 8 incluye todos los campos requeridos para la garantía de la AGF |
| **Pasos** | 1. Localizar nota 8. 2. Verificar presencia de columnas: Naturaleza, Emisor, Representante de beneficiarios, Monto UF, Vigencia (Desde–Hasta). |
| **Resultado esperado** | Todos los campos están presentes y completos. El monto está expresado en UF. Las fechas de vigencia son válidas (Desde ≤ Hasta). |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-006 – Nota 11: Información estadística

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-006 |
| **Descripción** | Verificar que la nota 11 contiene información mensual completa del ejercicio |
| **Pasos** | 1. Localizar nota 11. 2. Verificar que hay 12 filas (una por mes). 3. Verificar columnas: Valor cuota (4 decimales), Total activos (miles), Remuneración devengada acumulada (miles), N° partícipes. |
| **Resultado esperado** | Los 12 meses del ejercicio están informados. El valor cuota tiene 4 decimales. Los montos están en miles de la moneda funcional. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

### CP-1997-PDF-007 – Nota 12: Sanciones

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-PDF-007 |
| **Descripción** | Verificar que la nota 12 cubre el período correcto y declara explícitamente la ausencia de sanciones si no las hay |
| **Pasos** | 1. Localizar nota 12. 2. Verificar que cubre el período del 1/1 al 31/12 del año anterior y del año actual. 3. Si no hay sanciones: verificar que el texto declara expresamente la ausencia. |
| **Resultado esperado** | El texto cubre ambos ejercicios. Si hay sanciones: todos los campos del cuadro están completos. Si no hay sanciones: la declaración de ausencia es explícita. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 4. Casos de prueba – Declaración de responsabilidad en PDF (F-04)

### CP-1997-DEC-001 – Contenido mínimo de la declaración

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-DEC-001 |
| **Descripción** | Verificar que la Declaración de Responsabilidad incluye todos los campos requeridos |
| **Pasos** | 1. Abrir el PDF de declaración. 2. Verificar presencia de: (a) nombres de todos los directores que aprobaron la información; (b) nombre del gerente general; (c) RUT de cada declarante; (d) cargo de cada declarante. |
| **Resultado esperado** | Todos los campos están presentes. No hay campos vacíos. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 5. Casos de prueba – Dictamen de auditores externos en PDF (F-03)

### CP-1997-AUD-001 – Contenido mínimo del dictamen

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-AUD-001 |
| **Descripción** | Verificar que el dictamen de auditores incluye los campos requeridos por el Anexo III de la Circular |
| **Pasos** | 1. Abrir el PDF del dictamen. 2. Verificar presencia de: referencia al período auditado, razón social de la empresa auditora, RUT de la empresa auditora, nombre de la persona autorizada, RUT de la persona autorizada. |
| **Resultado esperado** | Todos los campos están presentes. La empresa auditora debe estar inscrita en el Registro de Empresas de Auditoría Externa de la CMF. |
| **Resultado obtenido** | |
| **Estado** | ⬜ Pendiente |

---

## 6. Casos de prueba – Validaciones de negocio transversales

### CP-1997-NEG-001 – Plazo de presentación anual

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-NEG-001 |
| **Descripción** | Verificar que el sistema controla que los archivos se generen y/o envíen dentro del plazo (último día del bimestre siguiente al 31/12) |
| **Resultado esperado** | El sistema registra la fecha de generación y alerta si está fuera del plazo. |
| **Estado** | ⬜ Pendiente |

### CP-1997-NEG-002 – Consistencia entre XML y PDF de notas

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-NEG-002 |
| **Descripción** | Verificar que los saldos del ESIF en el XML coinciden con los valores informados en las notas del PDF (ej.: nota 2 cuadra con activos a VR en el ESIF) |
| **Pasos** | 1. Extraer el saldo de "Activos financieros a VR" del XML. 2. Extraer el total de la nota 2 del PDF. 3. Comparar ambos valores. |
| **Resultado esperado** | Los valores son iguales (diferencia ≤ 1 por redondeo en miles). |
| **Estado** | ⬜ Pendiente |

### CP-1997-NEG-003 – Fondo con múltiples series de cuotas

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-NEG-003 |
| **Descripción** | Verificar que la nota 5 (Rentabilidad) informa la rentabilidad para cada serie de cuotas del fondo |
| **Pasos** | 1. Configurar un fondo con 3 series. 2. Generar PDF de notas. 3. Verificar que la nota 5 tiene sección por cada serie. |
| **Resultado esperado** | La nota 5 desglosa la rentabilidad por serie cuando el fondo tiene más de una. |
| **Estado** | ⬜ Pendiente |

### CP-1997-NEG-004 – Fondo sin excesos de inversión

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-NEG-004 |
| **Descripción** | Verificar que cuando no hay excesos, la nota 7 incluye declaración explícita de ausencia |
| **Resultado esperado** | El texto de la nota 7 declara expresamente que no hay excesos de inversión en el período. |
| **Estado** | ⬜ Pendiente |

### CP-1997-NEG-005 – Fondo mutuo estructurado garantizado

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-NEG-005 |
| **Descripción** | Verificar que la nota 9 solo aparece cuando el fondo está definido como Fondo Mutuo Estructurado Garantizado |
| **Pasos** | 1. Generar PDF para fondo ordinario → nota 9 no debe aparecer (o indicar "No aplica"). 2. Generar PDF para fondo estructurado garantizado → nota 9 debe contener las características de la garantía. |
| **Resultado esperado** | La nota 9 se incluye solo para fondos estructurados garantizados, con todos los campos requeridos por la Circular N° 1.790 de 2006. |
| **Estado** | ⬜ Pendiente |

---

## 7. Casos de prueba – Manejo de errores

### CP-1997-ERR-001 – Datos incompletos del fondo

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-ERR-001 |
| **Descripción** | Verificar que el sistema reporta un error descriptivo cuando faltan datos obligatorios (ej.: moneda funcional no definida) |
| **Resultado esperado** | El sistema lanza un error con mensaje claro indicando el campo faltante. No genera archivos parciales o corruptos. |
| **Estado** | ⬜ Pendiente |

### CP-1997-ERR-002 – XML no válido según Ficha Técnica CMF

| Atributo | Detalle |
|----------|---------|
| **ID** | CP-1997-ERR-002 |
| **Descripción** | Verificar que el XML generado cumple con el schema / ficha técnica publicada por la CMF |
| **Pasos** | 1. Generar XML. 2. Validar contra el schema XSD/especificaciones de la Ficha Técnica. |
| **Resultado esperado** | El XML pasa la validación sin errores ni advertencias. |
| **Estado** | ⬜ Pendiente |

---

## 8. Matriz de trazabilidad normativa

| Requisito circular | Caso(s) de prueba relacionado(s) |
|--------------------|----------------------------------|
| XML con 4 estados financieros | CP-1997-XML-001 |
| Moneda funcional en miles | CP-1997-XML-002 |
| Referencia al 31/12 | CP-1997-XML-003 |
| Ecuación contable ESIF | CP-1997-XML-004 |
| Comparativos ejercicio anterior | CP-1997-XML-005 |
| EEFF pro forma primer año | CP-1997-XML-006 |
| 14 notas obligatorias | CP-1997-PDF-001 |
| Nota 2: Activos a VR | CP-1997-PDF-002 |
| Nota 5: Rentabilidad | CP-1997-PDF-003 |
| Nota 7: Excesos | CP-1997-PDF-004 |
| Nota 8: Garantía AGF | CP-1997-PDF-005 |
| Nota 11: Estadística mensual | CP-1997-PDF-006 |
| Nota 12: Sanciones | CP-1997-PDF-007 |
| Declaración de responsabilidad | CP-1997-DEC-001 |
| Dictamen auditores | CP-1997-AUD-001 |
| Plazo de presentación | CP-1997-NEG-001 |
| Consistencia XML ↔ PDF | CP-1997-NEG-002 |
| Fondos con múltiples series | CP-1997-NEG-003 |
| Ausencia de excesos | CP-1997-NEG-004 |
| Fondo Estructurado Garantizado | CP-1997-NEG-005 |
| Manejo de datos incompletos | CP-1997-ERR-001 |
| Validación schema XML | CP-1997-ERR-002 |
