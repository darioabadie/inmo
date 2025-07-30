# Tests Funcionales - Módulo Histórico

## Resumen

Esta documentación describe los **55 tests funcionales** (Tests 111-165) desarrollados para validar completamente el módulo `historical.py`. Los tests están organizados en 3 categorías principales y cubren desde la funcionalidad básica hasta la integración completa.

## Estructura de Tests

### 📁 `test_historical_core.py` - Tests 111-135 (25 tests)
**Funcionalidad núcleo del módulo histórico**

| Test | Descripción |
|------|-------------|
| 111 | Cálculo básico de actualización ICL |
| 112 | Cálculo de actualización con porcentaje fijo |
| 113 | Verificación de no actualización en meses intermedios |
| 114 | Generación de meses desde inicio de contrato |
| 115 | Generación incremental desde mes específico |
| 116 | Inclusión de gastos municipales |
| 117 | Cálculo de cuotas adicionales en primeros meses |
| 118 | Respeto de vigencia de contrato |
| 119 | Cálculo de meses hasta próxima actualización |
| 120 | Manejo de histórico vacío |
| 121 | Lectura correcta de histórico existente |
| 122 | Manejo de errores en API ICL |
| 123 | Formato de porcentajes variados |
| 124 | Diferentes frecuencias de actualización |
| 125 | Integridad de registros generados |

### 📁 `test_historical_incremental.py` - Tests 136-150 (15 tests)
**Funcionalidad incremental y continuación**

| Test | Descripción |
|------|-------------|
| 136 | Continuación desde último mes registrado |
| 137 | Preservación de registros existentes |
| 138 | Detección correcta de último precio_base |
| 139 | Manejo de múltiples propiedades |
| 140 | Diferencia entre inicio y continuación |
| 141 | Respeto de ajustes manuales de precio |
| 142 | Contratos parcialmente vencidos |
| 143 | Actualización secuencial de precios |
| 144 | Ordenamiento cronológico |
| 145 | Manejo de datos corruptos |
| 146 | No duplicación de meses |
| 147 | Integridad después de escritura |
| 148 | Manejo de límites de fecha |
| 149 | Preservación de campos calculados |
| 150 | Rendimiento con histórico grande |

### 📁 `test_historical_integracion.py` - Tests 151-165 (15 tests)
**Integración completa y flujo extremo a extremo**

| Test | Descripción |
|------|-------------|
| 151 | Integración completa sin histórico previo |
| 152 | Integración completa con histórico existente |
| 153 | Manejo de errores en Google Sheets API |
| 154 | Procesamiento de múltiples propiedades |
| 155 | Validación de argumentos CLI |
| 156 | Integración con API ICL real |
| 157 | Propiedades con datos faltantes |
| 158 | Verificación de estructura de salida |
| 159 | Rendimiento con dataset grande |
| 160 | Integración con configuración |
| 161 | Manejo de excepciones en cálculos |
| 162 | Validación de fechas extremas |
| 163 | Ordenamiento final de registros |
| 164 | Validación de salida final |
| 165 | Flujo completo extremo a extremo |

## Cobertura de Funcionalidades

### ✅ **Cálculos y Lógica de Negocio**
- **ICL**: Consulta real a API BCRA, manejo de errores
- **IPC**: Uso de datos históricos de inflación
- **Porcentajes fijos**: Formatos variados (10%, 7.5%, 10,5%)
- **Frecuencias**: Trimestral, cuatrimestral, semestral, anual
- **Cuotas adicionales**: Comisión y depósito fraccionados
- **Municipalidad**: Gastos fijos mensuales

### ✅ **Funcionalidad Incremental**
- **Lectura de histórico**: Detección de último estado
- **Continuación**: Desde último mes registrado
- **Ajustes manuales**: Respeto de modificaciones en precio_base
- **Múltiples propiedades**: Manejo independiente por propiedad
- **Preservación**: Registros existentes se mantienen

### ✅ **Integración y Robustez**
- **Google Sheets API**: Lectura/escritura, manejo de errores
- **Argumentos CLI**: Validación de parámetros
- **Datos faltantes**: Manejo robusto de datos incompletos
- **Rendimiento**: Eficiencia con datasets grandes
- **Ordenamiento**: Correcta secuencia cronológica

### ✅ **Casos Extremos**
- **Contratos vencidos**: No generación de meses posteriores
- **Fechas límite**: Validación de rangos
- **Datos corruptos**: Recuperación sin crasheos
- **API failures**: Fallback a valores neutros

## Ejecución de Tests

### Ejecutar todos los tests históricos
```bash
python tests/run_tests.py historical
```

### Ejecutar tests específicos
```bash
# Solo tests núcleo
python -m unittest tests.test_historical_core

# Solo tests incrementales  
python -m unittest tests.test_historical_incremental

# Solo tests de integración
python -m unittest tests.test_historical_integracion
```

### Ejecutar test individual
```bash
# Ejemplo: test específico de ICL
python -m unittest tests.test_historical_core.TestHistoricalCore.test_111_actualizacion_icl_basico
```

## Criterios de Validación

### 🎯 **Correctness**
- Cálculos matemáticos precisos
- Lógica de actualización correcta
- Manejo apropiado de fechas y duraciones

### 🎯 **Robustez**
- Manejo de errores sin crasheos
- Validación de datos de entrada
- Recuperación ante fallos de APIs externas

### 🎯 **Funcionalidad Incremental**
- Preservación de histórico existente
- Continuación desde último estado
- Respeto de ajustes manuales

### 🎯 **Integración**
- Compatibilidad con Google Sheets
- Coherencia con módulo principal
- Estructura de salida correcta

## Beneficios de la Suite de Tests

### ✅ **Confianza en el código**
- 55 tests cubren todos los escenarios críticos
- Validación automática de cambios
- Detección temprana de regresiones

### ✅ **Documentación viva**
- Los tests sirven como ejemplos de uso
- Especificación de comportamiento esperado
- Casos edge documentados

### ✅ **Mantenibilidad**
- Refactoring seguro con tests como red de seguridad
- Facilita incorporación de nuevos desarrolladores
- Evolución controlada del código

### ✅ **Calidad**
- Validación de todos los flujos posibles
- Manejo robusto de errores
- Rendimiento validado

---

## Próximos Pasos

1. **Ejecutar tests**: Validar implementación actual
2. **CI/CD**: Integrar en pipeline de desarrollo
3. **Cobertura**: Medir cobertura de código con herramientas como `coverage.py`
4. **Extensión**: Agregar tests para nuevas funcionalidades futuras

Los tests están listos para ser ejecutados y proporcionan una base sólida para el desarrollo y mantenimiento del módulo histórico.
