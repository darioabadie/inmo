# Tests - Aplicación Inmobiliaria

Esta carpeta contiene todos los tests unitarios y de integración para validar el correcto funcionamiento de la aplicación de generación de pagos para propiedades administradas.

## 📁 Estructura de Tests

```
tests/
├── __init__.py                 # Configuración del módulo de tests
├── test_data.py               # Datos de prueba y casos esperados
├── test_calculations.py       # Tests para cálculos matemáticos
├── test_contract_logic.py     # Tests para lógica de contratos
├── test_integration.py        # Tests de integración completos
├── run_tests.py              # Script para ejecutar tests
└── README.md                 # Esta documentación
```

## 🧪 Tipos de Tests

### 1. **test_calculations.py**
- ✅ Cálculo de inflación acumulada (IPC)
- ✅ Cálculo de comisiones inmobiliarias
- ✅ Cálculo de cuotas adicionales (comisión inquilino + depósito)
- ✅ Validación de formatos de entrada
- ✅ Manejo de errores en cálculos

### 2. **test_contract_logic.py**
- ✅ Cálculo de meses desde inicio del contrato
- ✅ Determinación de ciclos cumplidos
- ✅ Lógica de aplicación de actualizaciones
- ✅ Cálculo de meses hasta próxima actualización
- ✅ Cálculo de meses hasta renovación
- ✅ Validación de vigencia de contratos
- ✅ Validación de campos requeridos

### 3. **test_integration.py**
- ✅ Procesamiento completo de contratos
- ✅ Integración entre todos los módulos
- ✅ Casos extremos y edge cases
- ✅ Manejo de datos faltantes
- ✅ Flujo completo de cálculo de precios

## 🚀 Ejecutar Tests

### Ejecutar todos los tests:
```bash
cd /Users/darioabadie/deployr/inmobiliaria
python tests/run_tests.py
```

### Ejecutar tests específicos:
```bash
# Solo tests de cálculos
python tests/run_tests.py calculations

# Solo tests de lógica de contratos
python tests/run_tests.py contract

# Solo tests de integración
python tests/run_tests.py integration
```

### Ejecutar un archivo específico:
```bash
python -m unittest tests.test_calculations
python -m unittest tests.test_contract_logic
python -m unittest tests.test_integration
```

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

## 📈 Métricas Esperadas

Al ejecutar todos los tests, deberías ver:
- **Total de tests**: ~41 tests
- **Tiempo de ejecución**: < 2 segundos
- **Cobertura**: 100% de las funciones críticas
- **Status esperado**: ✅ TODOS EXITOSOS

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
