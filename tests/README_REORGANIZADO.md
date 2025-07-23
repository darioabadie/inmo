# Tests del Sistema de Cálculo de Pagos Inmobiliarios

## Resumen

Esta carpeta contiene todos los tests del sistema, reorganizados según las especificaciones funcionales definidas en `tests_funcionales.md`. Los tests están organizados en **8 categorías principales** que cubren los **110 tests funcionales** especificados.

## Estructura de Tests Reorganizada

### 🔍 **Tests Principales (Basados en tests_funcionales.md)**

| Archivo | Tests | Descripción |
|---------|--------|-------------|
| `test_validacion_datos.py` | 1-26 | Validación de datos de entrada |
| `test_logica_contratos.py` | 27-40 | Lógica de contratos y vigencia |
| `test_actualizaciones.py` | 41-52 | Cálculos de actualización (IPC, ICL, %) |
| `test_cuotas_adicionales.py` | 53-65 | Cálculo de cuotas adicionales |
| `test_precios_finales.py` | 66-79 | Precios finales, municipalidad y comisiones |
| `test_campos_informativos.py` | 80-91 | Campos informativos del output |
| `test_casos_extremos.py` | 92-101 | Casos extremos y manejo de errores |
| `test_integracion_completa.py` | 102-110 | Integración y flujo completo |

### 📁 **Tests Legacy (Mantenidos para compatibilidad)**

| Archivo | Descripción |
|---------|-------------|
| `test_calculations.py` | Tests originales de cálculos |
| `test_contract_logic.py` | Tests originales de lógica de contratos |
| `test_fase1_logica_critica.py` | Tests específicos de la Fase 1 |
| `test_fase2_logica_icl.py` | Tests específicos de la Fase 2 |
| `test_integration.py` | Tests originales de integración |
| `test_integracion_sistema_completo.py` | Tests legacy del sistema completo |

### 🛠 **Archivos de Soporte**

| Archivo | Descripción |
|---------|-------------|
| `test_data.py` | Datos de prueba y configuración |
| `run_tests.py` | Script para ejecutar todos los tests |
| `tests_funcionales.md` | Especificación completa de los 110 tests |

## Ejecución de Tests

### Ejecutar Todos los Tests
```bash
cd tests/
python run_tests.py
```

### Ejecutar Tests por Categoría
```bash
# Tests de validación de datos (Tests 1-26)
python -m unittest test_validacion_datos -v

# Tests de lógica de contratos (Tests 27-40)
python -m unittest test_logica_contratos -v

# Tests de actualizaciones (Tests 41-52)
python -m unittest test_actualizaciones -v

# Tests de cuotas adicionales (Tests 53-65)
python -m unittest test_cuotas_adicionales -v

# Tests de precios finales (Tests 66-79)
python -m unittest test_precios_finales -v

# Tests de campos informativos (Tests 80-91)
python -m unittest test_campos_informativos -v

# Tests de casos extremos (Tests 92-101)
python -m unittest test_casos_extremos -v

# Tests de integración completa (Tests 102-110)
python -m unittest test_integracion_completa -v
```

### Ejecutar Test Específico
```bash
# Ejecutar un test específico
python -m unittest test_validacion_datos.TestValidacionCamposObligatorios.test_registro_sin_nombre_inmueble -v
```

## Categorías Detalladas

### 1. **Validación de Datos de Entrada (Tests 1-26)**
- ✅ Campos obligatorios (Tests 1-8)
- ✅ Validación de fechas (Tests 9-13)
- ✅ Validación de números (Tests 14-18)
- ✅ Validación de campos de configuración (Tests 19-26)

### 2. **Lógica de Contratos (Tests 27-40)**
- ✅ Vigencia de contratos (Tests 27-30)
- ✅ Cálculo de meses desde inicio (Tests 31-33)
- ✅ Actualización trimestral (Tests 34-36)
- ✅ Actualización semestral (Tests 37-38)
- ✅ Actualización anual (Tests 39-40)

### 3. **Cálculos de Actualización (Tests 41-52)**
- ✅ Cálculo con porcentaje fijo (Tests 41-44)
- ✅ Cálculo con IPC (Tests 45-48)
- ✅ Cálculo con ICL (Tests 49-52)

### 4. **Cálculo de Cuotas Adicionales (Tests 53-65)**
- ✅ Comisión del inquilino (Tests 53-57)
- ✅ Depósito (Tests 58-60)
- ✅ Combinación comisión + depósito (Tests 61-63)
- ✅ Interacción con actualizaciones (Tests 64-65)

### 5. **Precios Finales (Tests 66-79)**
- ✅ Gastos municipales (Tests 66-69)
- ✅ Composición del precio_mes_actual (Tests 70-73)
- ✅ Comisión de administración (Tests 74-76)
- ✅ Pago al propietario (Tests 77-79)

### 6. **Campos Informativos (Tests 80-91)**
- ✅ Indicador de actualización (Tests 80-82)
- ✅ Porcentaje actual (Tests 83-85)
- ✅ Meses hasta próxima actualización (Tests 86-88)
- ✅ Meses hasta renovación (Tests 89-91)

### 7. **Casos Extremos (Tests 92-101)**
- ✅ APIs externas (Tests 92-95)
- ✅ Datos inconsistentes (Tests 96-98)
- ✅ Precisión numérica (Tests 99-101)

### 8. **Integración Completa (Tests 102-110)**
- ✅ Procesamiento masivo (Tests 102-104)
- ✅ Escenarios reales complejos (Tests 105-107)
- ✅ Validación de output (Tests 108-110)

## Estado de Implementación

### ✅ **Completamente Implementados**
- Estructura organizacional de todos los 110 tests
- Tests básicos de validación y lógica
- Tests de cálculos principales
- Tests de integración conceptual

### 🚧 **En Desarrollo**
- Algunos tests requieren implementación del código principal
- Tests de APIs externas requieren mocks más sofisticados
- Tests de precisión numérica necesitan casos más específicos

### 📋 **Pendientes**
- Integración completa con el sistema principal
- Tests end-to-end con datos reales
- Benchmarks de performance

## Notas Importantes

1. **Orden de Ejecución**: Los tests están diseñados para ejecutarse en orden lógico, desde validaciones básicas hasta integración completa.

2. **Mocks y Simulaciones**: Los tests utilizan mocks para APIs externas y simulaciones para casos complejos.

3. **Compatibilidad**: Se mantienen los tests legacy para asegurar compatibilidad durante la transición.

4. **Cobertura**: Los tests cubren todos los aspectos críticos especificados en `technical_specs.md`.

## Contribuciones

Al agregar nuevos tests:
1. Identificar la categoría apropiada (Tests 1-110)
2. Seguir la nomenclatura establecida
3. Incluir documentación clara del propósito del test
4. Actualizar este README si es necesario
