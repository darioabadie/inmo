# Tests Funcionales - Sistema de Cálculo de Pagos Inmobiliarios

## Introducción

Este documento define todos los tests funcionales que debe pasar el sistema de cálculo de pagos mensuales para propiedades administradas. Cada test está descrito en lenguaje coloquial para facilitar su comprensión y posterior implementación en código.

## Categorías de Tests

### 1. VALIDACIÓN DE DATOS DE ENTRADA

#### 1.1 Campos Obligatorios
1. **Test**: El sistema debe rechazar registros que no tengan nombre_inmueble
2. **Test**: El sistema debe rechazar registros que no tengan precio_original
3. **Test**: El sistema debe rechazar registros que no tengan fecha_inicio_contrato
4. **Test**: El sistema debe rechazar registros que no tengan duracion_meses
5. **Test**: El sistema debe rechazar registros que no tengan actualizacion
6. **Test**: El sistema debe rechazar registros que no tengan indice
7. **Test**: El sistema debe rechazar registros que no tengan comision_inmo
8. **Test**: El sistema debe crear registro con campos calculados en blanco cuando faltan datos obligatorios, pero no debe fallar

#### 1.2 Validación de Fechas
9. **Test**: El sistema debe aceptar fechas en formato YYYY-MM-DD
10. **Test**: El sistema debe aceptar fechas en formato YYYY_MM_DD (con underscore)
11. **Test**: El sistema debe rechazar fechas en formato incorrecto como "32/13/2024"
12. **Test**: El sistema debe rechazar fechas con texto como "inicio ayer"
13. **Test**: El sistema debe manejar fechas vacías o nulas sin fallar

#### 1.3 Validación de Números
14. **Test**: El sistema debe aceptar precio_original como número entero
15. **Test**: El sistema debe aceptar precio_original como número decimal
16. **Test**: El sistema debe rechazar precio_original con texto como "cien mil"
17. **Test**: El sistema debe aceptar duracion_meses como número entero positivo
18. **Test**: El sistema debe rechazar duracion_meses negativo o cero

#### 1.4 Validación de Campos de Configuración
19. **Test**: El sistema debe aceptar actualización "trimestral", "cuatrimestral", "semestral", "anual"
20. **Test**: El sistema debe usar "trimestral" como default si la actualización es inválida
21. **Test**: El sistema debe aceptar índice "IPC", "ICL" y porcentajes como "10%", "7.5%"
22. **Test**: El sistema debe aceptar comisión_inmo en formato porcentaje como "5%", "3.5%"
23. **Test**: El sistema debe aceptar comision como "Pagado", "2 cuotas", "3 cuotas"
24. **Test**: El sistema debe usar "Pagado" como default para comision si no se especifica
25. **Test**: El sistema debe aceptar deposito como "Pagado", "2 cuotas", "3 cuotas"
26. **Test**: El sistema debe usar "Pagado" como default para deposito si no se especifica

### 2. LÓGICA DE CONTRATOS

#### 2.1 Vigencia de Contratos
27. **Test**: El sistema debe incluir contratos que aún están vigentes
28. **Test**: El sistema debe excluir contratos que ya vencieron (fecha_inicio + duracion_meses < fecha_referencia)
29. **Test**: El sistema debe incluir contratos que vencen exactamente en el mes de referencia
30. **Test**: El sistema debe calcular correctamente la vigencia para contratos de 12, 24, 36 meses

#### 2.2 Cálculo de Meses desde Inicio
31. **Test**: Para un contrato iniciado en enero 2024, en marzo 2024 deben ser 2 meses desde inicio
32. **Test**: Para un contrato iniciado en diciembre 2023, en febrero 2024 deben ser 2 meses desde inicio
33. **Test**: Para un contrato iniciado el mismo mes de referencia deben ser 0 meses desde inicio

### 3. CÁLCULOS DE ACTUALIZACIÓN

#### 3.1 Actualización Trimestral
34. **Test**: Un contrato trimestral debe actualizarse en los meses 3, 6, 9, 12, 15, 18... desde inicio
35. **Test**: Un contrato trimestral NO debe actualizarse en los meses 1, 2, 4, 5, 7, 8... desde inicio
36. **Test**: La primera actualización trimestral debe ocurrir en el mes 3, no antes

#### 3.2 Actualización Semestral
37. **Test**: Un contrato semestral debe actualizarse en los meses 6, 12, 18, 24... desde inicio
38. **Test**: Un contrato semestral NO debe actualizarse en los meses 1-5, 7-11, 13-17... desde inicio

#### 3.3 Actualización Anual
39. **Test**: Un contrato anual debe actualizarse en los meses 12, 24, 36... desde inicio
40. **Test**: Un contrato anual NO debe actualizarse en los meses 1-11, 13-23... desde inicio

#### 3.4 Cálculo con Porcentaje Fijo
41. **Test**: Con índice "10%" y 1 ciclo cumplido, el precio debe incrementarse 10%
42. **Test**: Con índice "10%" y 2 ciclos cumplidos, el precio debe incrementarse 21% (1.1²)
43. **Test**: Con índice "7.5%" y 3 ciclos cumplidos, el precio debe calcularse correctamente
44. **Test**: El sistema debe manejar porcentajes con coma como "7,5%"

#### 3.5 Cálculo con IPC
45. **Test**: El sistema debe obtener datos de inflación de la API Argentina Datos
46. **Test**: El sistema debe calcular inflación acumulada para el período correcto
47. **Test**: El sistema debe aplicar inflación compuesta, no simple
48. **Test**: El sistema debe manejar períodos sin datos de inflación

#### 3.6 Cálculo con ICL
49. **Test**: El sistema debe obtener datos ICL de la API del BCRA
50. **Test**: El sistema debe calcular el factor ICL entre las fechas correctas del ciclo
51. **Test**: El sistema debe manejar la respuesta de la API BCRA (orden cronológico inverso)
52. **Test**: El sistema debe aplicar múltiples factores ICL de forma compuesta

### 4. CÁLCULO DE CUOTAS ADICIONALES

#### 4.1 Comisión del Inquilino
53. **Test**: Con comisión "Pagado", no debe sumarse nada al alquiler
54. **Test**: Con comisión "2 cuotas", debe sumarse precio_base/2 en los meses 1 y 2
55. **Test**: Con comisión "2 cuotas", NO debe sumarse nada desde el mes 3 en adelante
56. **Test**: Con comisión "3 cuotas", debe sumarse precio_base/3 en los meses 1, 2 y 3
57. **Test**: Con comisión "3 cuotas", NO debe sumarse nada desde el mes 4 en adelante

#### 4.2 Depósito
58. **Test**: Con depósito "Pagado", no debe sumarse nada al alquiler
59. **Test**: Con depósito "2 cuotas", debe sumarse precio_base/2 en los meses 1 y 2
60. **Test**: Con depósito "3 cuotas", debe sumarse precio_base/3 en los meses 1, 2 y 3

#### 4.3 Combinación Comisión + Depósito
61. **Test**: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 1 debe sumarse precio_base/2 + precio_base/3
62. **Test**: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 3 debe sumarse solo precio_base/3
63. **Test**: Con ambos "Pagado", nunca debe sumarse nada adicional

#### 4.4 Interacción con Actualizaciones
64. **Test**: Las cuotas adicionales deben calcularse sobre el precio_base actualizado, no el original
65. **Test**: Si hay actualización en el mes 3, la tercera cuota de depósito debe usar el precio actualizado

### 5. GASTOS MUNICIPALES

#### 5.1 Manejo de Campo Municipalidad
66. **Test**: Si municipalidad está vacío, debe usarse 0
67. **Test**: Si municipalidad es un número, debe sumarse al precio final
68. **Test**: Si municipalidad tiene texto inválido, debe usarse 0
69. **Test**: Los gastos municipales deben sumarse a precio_base + cuotas_adicionales

### 6. CÁLCULO DEL PRECIO FINAL

#### 6.1 Composición del precio_mes_actual
70. **Test**: precio_mes_actual debe ser la suma de precio_base + cuotas_adicionales + municipalidad
71. **Test**: En el primer mes con cuotas, el precio total debe ser significativamente mayor
72. **Test**: Después de que terminen las cuotas, el precio debe ser solo precio_base + municipalidad
73. **Test**: El precio_mes_actual nunca debe ser negativo

### 7. COMISIONES Y PAGOS AL PROPIETARIO

#### 7.1 Comisión de Administración
74. **Test**: La comisión_inmo debe calcularse sobre precio_base, no sobre precio_mes_actual
75. **Test**: Con comision_inmo "5%" y precio_base $100000, la comisión debe ser $5000
76. **Test**: La comisión debe redondearse a 2 decimales

#### 7.2 Pago al Propietario
77. **Test**: pago_prop debe ser precio_base - comision_inmo
78. **Test**: pago_prop nunca debe incluir las cuotas adicionales (esas las paga el inquilino)
79. **Test**: pago_prop nunca debe incluir gastos municipales

### 8. CAMPOS INFORMATIVOS

#### 8.1 Indicador de Actualización
80. **Test**: actualizacion debe ser "SI" solo en meses donde corresponde ajuste
81. **Test**: actualizacion debe ser "NO" en todos los demás meses
82. **Test**: En el primer mes del contrato, actualizacion siempre debe ser "NO"

#### 8.2 Porcentaje Actual
83. **Test**: porc_actual debe tener valor solo cuando actualizacion = "SI"
84. **Test**: porc_actual debe estar vacío cuando actualizacion = "NO"
85. **Test**: porc_actual debe mostrar el porcentaje del último factor aplicado

#### 8.3 Meses hasta Próxima Actualización
86. **Test**: En un mes de actualización trimestral, meses_prox_actualizacion debe ser 3
87. **Test**: Un mes después de actualización trimestral, meses_prox_actualizacion debe ser 2
88. **Test**: Dos meses después de actualización trimestral, meses_prox_actualizacion debe ser 1

#### 8.4 Meses hasta Renovación
89. **Test**: meses_prox_renovacion debe decrecer mes a mes
90. **Test**: En el último mes del contrato, meses_prox_renovacion debe ser 0
91. **Test**: meses_prox_renovacion nunca debe ser negativo

### 9. CASOS EXTREMOS Y MANEJO DE ERRORES

#### 9.1 APIs Externas
92. **Test**: El sistema debe manejar graciosamente cuando la API de inflación no responde
93. **Test**: El sistema debe manejar graciosamente cuando la API del BCRA no responde
94. **Test**: El sistema debe continuar procesando otros registros si falla una API
95. **Test**: El sistema debe usar valores por defecto si no puede obtener datos externos

#### 9.2 Datos Inconsistentes
96. **Test**: El sistema debe manejar fechas de inicio posteriores a la fecha de referencia
97. **Test**: El sistema debe manejar contratos con duración 0 o negativa
98. **Test**: El sistema debe manejar precios originales de 0 o negativos

#### 9.3 Precisión Numérica
99. **Test**: Todos los cálculos monetarios deben redondearse a 2 decimales
100. **Test**: Los factores de actualización deben mantener precisión durante cálculos intermedios
101. **Test**: Las divisiones para cuotas deben distribuir correctamente los centavos restantes

### 10. INTEGRACIÓN Y FLUJO COMPLETO

#### 10.1 Procesamiento Masivo
102. **Test**: El sistema debe procesar correctamente múltiples contratos en una sola ejecución
103. **Test**: El sistema debe generar un registro de salida por cada contrato válido de entrada
104. **Test**: El sistema debe loggear apropiadamente contratos omitidos y razones

#### 10.2 Escenarios Reales Complejos
105. **Test**: Un contrato de 24 meses, trimestral, IPC, con cuotas debe calcularse correctamente mes a mes
106. **Test**: Un contrato de 36 meses, semestral, ICL, sin cuotas debe calcularse correctamente
107. **Test**: Múltiples contratos con diferentes configuraciones deben procesarse sin interferencia

#### 10.3 Validación de Output
108. **Test**: Todos los registros de salida deben tener el formato de columnas esperado
109. **Test**: No debe haber valores nulos inesperados en campos calculados
110. **Test**: Las fechas en el output deben mantener el formato correcto

---

## Notas para Implementación

- Cada test debe ser independiente y ejecutable por separado
- Los tests deben usar datos de prueba controlados, no APIs reales cuando sea posible
- Los tests de APIs externas deben poder usar mocks o datos simulados
- Cada test debe tener un resultado esperado claro y verificable
- Los tests deben cubrir tanto casos exitosos como casos de error
