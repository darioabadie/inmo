# Tests - Aplicación Inmobiliaria

Esta carpeta contiene todos los tests unitarios y de integración para validar el correcto funcionamiento de la aplicación de generación de pagos para propiedades administradas.

## 📁 Estructura de Tests

```
tests/
├── __init__.py                           # Configuración del módulo de tests
├── test_data.py                         # Datos de prueba y casos esperados
├── test_calculations.py                 # Tests para cálculos matemáticos (legacy)
├── test_contract_logic.py              # Tests para lógica de contratos (legacy)
├── test_integration.py                 # Tests de integración completos (legacy)
├── test_fase1_logica_critica.py       # Tests FASE 1: Correcciones críticas
├── test_fase2_logica_icl.py           # Tests FASE 2: Lógica ICL mejorada
├── test_integracion_sistema_completo.py # Tests de integración post-refactor
├── run_tests.py                        # Script para ejecutar tests
└── README.md                           # Esta documentación
```

## 🧪 Tipos de Tests

### Tests Legacy (Pre-refactor)

#### 1. **test_calculations.py**
- ✅ Cálculo de inflación acumulada (IPC)
- ✅ Cálculo de comisiones inmobiliarias
- ✅ Cálculo de cuotas adicionales (comisión inquilino + depósito)
- ✅ Validación de formatos de entrada
- ✅ Manejo de errores en cálculos

#### 2. **test_contract_logic.py**
- ✅ Cálculo de meses desde inicio del contrato
- ✅ Determinación de ciclos cumplidos
- ✅ Lógica de aplicación de actualizaciones

### Tests del Refactor (Post-correcciones)

#### 3. **test_fase1_logica_critica.py** ⭐ NUEVO
- ✅ **Step 1.1**: Cálculo acumulado de `precio_base` con efecto compuesto
- ✅ **Step 1.2**: Estructura de output según `technical_specs.md`
- ✅ **Step 1.3**: Validación de contratos vencidos
- ✅ Tests con porcentaje fijo acumulado
- ✅ Tests sin ciclos cumplidos
- ✅ Tests con múltiples ciclos
- ✅ Tests con diferentes frecuencias

#### 4. **test_fase2_logica_icl.py** ⭐ NUEVO
- ✅ **Step 2.1**: Función `traer_factor_icl` mejorada
- ✅ **Step 2.2**: Cálculo ICL acumulado detallado
- ✅ Tests de integración ICL en sistema principal
- ✅ Tests de manejo de errores de API
- ✅ Tests con mocks para casos controlados
- ✅ Tests de validaciones y warnings

#### 5. **test_integracion_sistema_completo.py** ⭐ NUEVO
- ✅ Tests de integración FASE 1 + FASE 2
- ✅ Verificación de estructura de output
- ✅ Comparación porcentaje fijo vs ICL
- ✅ Tests de consistencia entre campos
- ✅ Tests de precisión en cálculos
- ✅ Tests de regresión con casos reales
- ✅ Verificación exacta con `technical_specs.md`
- ✅ Cálculo de meses hasta próxima actualización
- ✅ Cálculo de meses hasta renovación
- ✅ Validación de vigencia de contratos
- ✅ Validación de campos requeridos

## 🧪 Tests del Sistema de Logging

#### 6. **test_error_logging.py** ⭐ NUEVO
- ✅ **Configuración de logger**: Tests para `setup_error_logger()`
  - Creación automática del directorio `logs/`
  - Configuración correcta del logger `historical_errors`
  - Formato de mensajes con timestamp y contexto
  - Modo append (no sobrescribe logs existentes)
  - Prevención de handlers duplicados
- ✅ **Integración con HistoricalService**: 
  - Aceptación del logger en constructor
  - Funcionamiento sin logger (modo opcional)
  - Logging detallado de errores de propiedades
  - Manejo de campos faltantes en datos
- ✅ **Tests de integración end-to-end**:
  - Flujo completo desde setup hasta archivo
  - Verificación de contenido y formato de logs
  - Validación de timestamps y estructura

## 🚀 Cómo Ejecutar Tests

### Opción 1: Ejecutar todos los tests
```bash
cd tests
python run_tests.py all
```

### Opción 2: Ejecutar tests específicos

#### Tests del Refactor (Recomendado)
```bash
python run_tests.py refactor
```
Este comando ejecuta únicamente los tests de las correcciones implementadas:
- `test_fase1_logica_critica.py`
- `test_fase2_logica_icl.py` 
- `test_integracion_sistema_completo.py`

#### Tests Legacy (Pre-refactor)
```bash
python run_tests.py legacy
```
Ejecuta los tests originales:
- `test_calculations.py`
- `test_contract_logic.py`
- `test_integration.py`

#### Tests por fase específica
```bash
# Solo FASE 1 (lógica crítica)
python run_tests.py fase1

# Solo FASE 2 (lógica ICL)  
python run_tests.py fase2

# Solo integración completa
python run_tests.py integracion
```

#### Tests individuales
```bash
# Ejecutar un archivo específico
python -m unittest test_fase1_logica_critica.py -v

# Ejecutar un test específico
python -m unittest test_fase1_logica_critica.TestStep11PrecioBaseAcumulado.test_calculo_acumulado_porcentaje_fijo -v

# Ejecutar tests de logging de errores
python -m unittest unit.test_error_logging -v
```

## 📊 Interpretación de Resultados

### ✅ Resultado Exitoso
```
test_calculo_acumulado_porcentaje_fijo (test_fase1_logica_critica.TestStep11PrecioBaseAcumulado) ... ok
test_integracion_sistema_completo (test_integracion_sistema_completo.TestSistemaCompleto) ... ok

Ran 15 tests in 2.341s
OK
```

### ❌ Resultado con Errores
```
test_ejemplo_fallido (test_fase1_logica_critica.TestStep11PrecioBaseAcumulado) ... FAIL

FAIL: test_ejemplo_fallido
AssertionError: Expected 115000.0, got 110000.0
```

## 🔍 Cobertura de Tests

### Funcionalidades Críticas Cubiertas ✅
- Cálculo acumulado de `precio_base` con efecto compuesto
- Integración con API ICL del BCRA
- Validación de contratos vencidos
- Estructura de output según especificaciones técnicas
- Manejo de errores y casos límite
- Consistencia entre diferentes tipos de actualización
- Precisión decimal en cálculos financieros

### Archivos del Sistema Testeados ✅
- `inmobiliaria/main.py` (función principal)
- `inmobiliaria/services/calculations.py` (cálculos)
- `inmobiliaria/services/google_sheets.py` (integración)
- `inmobiliaria/services/inflation.py` (inflación)

## ⚠️ Notas Importantes

1. **Tests con API Real**: Algunos tests hacen llamadas reales a la API del BCRA. Si hay problemas de conectividad, estos tests pueden fallar.

2. **Datos de Prueba**: Los tests utilizan datos sintéticos que reflejan casos reales encontrados durante el desarrollo.

3. **Mocking**: Tests críticos usan mocking para APIs externas para garantizar reproducibilidad.

4. **Regresión**: Los tests de integración validan que las correcciones no rompan funcionalidad existente.

## 🛠️ Mantenimiento

- **Agregar nuevos tests**: Crear archivos `test_nueva_funcionalidad.py` siguiendo el patrón unittest
- **Actualizar casos**: Modificar `test_data.py` para nuevos escenarios
- **Debug tests**: Usar `-v` para output detallado y agregar `print()` statements según necesidad

### Ejecutar un test específico:
```bash
python -m unittest tests.test_calculations.TestInflacionCalculations.test_inflacion_acumulada_trimestral
```

## 📊 Casos de Prueba Cubiertos

### **Contratos de Prueba:**
1. **Casa Palermo** - Trimestral, IPC, con cuotas
2. **Depto Belgrano** - Semestral, porcentaje fijo, cuotas parciales
3. **Local Comercial** - Anual, ICL, configuración diferente
4. **Casa Incompleta** - Datos faltantes para probar validación

### **Escenarios de Cálculo:**
- ✅ Primer mes del contrato (sin actualización)
- ✅ Mes de actualización (trimestral, semestral, anual)
- ✅ Meses intermedios (sin actualización)
- ✅ Contratos próximos a vencer
- ✅ Contratos vencidos
- ✅ Cuotas en primeros meses
- ✅ Meses sin cuotas adicionales

### **Validaciones:**
- ✅ Campos requeridos completos
- ✅ Campos requeridos faltantes
- ✅ Formatos de comisión válidos e inválidos
- ✅ Valores de frecuencia válidos e inválidos
- ✅ Manejo de errores en APIs externas

## 🎯 Cobertura de Funciones

| Función | Cobertura | Tests |
|---------|-----------|-------|
| `inflacion_acumulada()` | ✅ 100% | 3 tests |
| `calcular_comision()` | ✅ 100% | 6 tests |
| `calcular_cuotas_adicionales()` | ✅ 100% | 8 tests |
| Lógica de ciclos y actualizaciones | ✅ 100% | 12 tests |
| Validación de campos | ✅ 100% | 4 tests |
| Flujo de integración | ✅ 100% | 8 tests |
| **Sistema de logging de errores** | ✅ 100% | **11 tests** |
| `setup_error_logger()` | ✅ 100% | 5 tests |
| Error logging en HistoricalService | ✅ 100% | 6 tests |

## 📈 Métricas Esperadas

Al ejecutar todos los tests, deberías ver:
- **Total de tests**: ~52 tests (41 previos + 11 nuevos de error logging)
- **Tiempo de ejecución**: < 3 segundos
- **Cobertura**: 100% de las funciones críticas + sistema de logging
- **Status esperado**: ✅ TODOS EXITOSOS

### Tests por Categoría:
- **Tests funcionales (1-110)**: ~39 tests
- **Tests histórico (111-165)**: ~13 tests  
- **Tests de logging**: 11 tests nuevos

## 🐛 Qué hacer si fallan tests

### 1. **Leer el mensaje de error cuidadosamente**
Los tests están diseñados con mensajes descriptivos que explican qué se esperaba vs qué se obtuvo.

### 2. **Verificar cambios recientes**
Si modificaste código en `app.py`, verifica que no hayas alterado la lógica de cálculo.

### 3. **Ejecutar tests individuales**
```bash
python -m unittest tests.test_calculations.TestInflacionCalculations.test_inflacion_acumulada_trimestral -v
```

### 4. **Verificar datos de prueba**
Los datos de prueba están en `test_data.py`. Si cambias la lógica, puede que necesites actualizar los valores esperados.

## 🔧 Agregar Nuevos Tests

### Para agregar un test de cálculo:
```python
def test_nuevo_calculo(self):
    """Test para nuevo cálculo"""
    resultado = nueva_funcion(parametros)
    self.assertEqual(resultado, valor_esperado, "Mensaje descriptivo")
```

### Para agregar datos de prueba:
Edita `test_data.py` y agrega nuevos casos a las estructuras correspondientes.

## 📝 Notas Importantes

- **Tolerancia de decimales**: Los tests usan `assertAlmostEqual()` para comparaciones con decimales
- **Fechas**: Usa formato ISO (YYYY-MM-DD) en datos de prueba
- **Mocks**: Para APIs externas, considera usar `unittest.mock`
- **Independencia**: Cada test debe ser independiente y no depender de otros

## 🎉 Beneficios de estos Tests

1. **Confianza**: Puedes modificar código sin temor a romper funcionalidad
2. **Documentación**: Los tests sirven como documentación de cómo funciona el código
3. **Regresión**: Detectan automáticamente si cambios rompen funcionalidad existente
4. **Calidad**: Garantizan que los cálculos financieros sean precisos
5. **Mantenimiento**: Facilitan el mantenimiento y evolución del código

---

**¡Ejecuta los tests regularmente y mantén la cobertura al 100%!** 🚀
