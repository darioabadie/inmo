# inmo - Generador de Pagos para Propiedades Administradas

Esta aplicación automatiza la generación mensual de reportes de pagos para propiedades administradas, utilizando datos de un archivo maestro en Google Sheets y aplicando reglas de actualización de precios según IPC o porcentajes fijos.

## ¿Qué hace la app?

### Módulo Principal (`main.py`)
- Lee la información de contratos de alquiler desde una hoja de Google Sheets.
- Calcula el monto a pagar cada mes para cada propiedad, considerando actualizaciones por inflación (IPC), ICL o porcentajes fijos.
- Calcula la comisión de la inmobiliaria y el pago neto al propietario.
- Genera una hoja nueva en el mismo Google Sheets con el detalle de pagos del mes seleccionado.
- Permite elegir el mes de cálculo (por defecto, el mes actual).

### Módulo Historial (`historical.py`)
- Genera el historial completo de pagos desde el inicio de cada contrato hasta una fecha límite.
- **Arquitectura refactorizada**: Utiliza servicios especializados para mejor mantenibilidad:
  - `HistoricalService`: Orquesta todo el proceso
  - `HistoricalDataManager`: Maneja la comunicación con Google Sheets
  - `MonthlyRecordGenerator`: Genera registros mensuales individuales
  - `HistoricalCalculations`: Realiza cálculos especializados
- Cada actualización se basa en el último `precio_original` registrado, permitiendo ajustes manuales.
- Funciona de manera incremental: solo agrega meses nuevos al historial existente.
- Respeta modificaciones manuales en el historial para cálculos futuros.
- Aplica actualizaciones reales de ICL, IPC o porcentajes según corresponda en cada período.

## Requisitos

- Python 3.8 o superior
- Acceso a Google Cloud Platform para obtener credenciales OAuth2
- Paquetes Python listados en `requirements.txt`

Instala las dependencias con:

```sh
pip install -r requirements.txt
```

**Nota**: La aplicación creará automáticamente un directorio `logs/` para almacenar archivos de registro de errores cuando sea necesario.

## Autenticación con Google Sheets

Para que la app pueda acceder y modificar tu Google Sheets, debes autenticarte con Google. Sigue estos pasos:

1. **Obtén las credenciales OAuth2:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/).
   - Crea un proyecto (si no tienes uno).
   - Habilita la API de Google Sheets y Google Drive.
   - Crea una credencial de tipo "ID de cliente de OAuth" para aplicación de escritorio.
   - Descarga el archivo JSON y guárdalo como `client_secret_XXXX.json` en el directorio del proyecto (ya incluido como ejemplo).

2. **Primer uso:**
   - Al ejecutar el script por primera vez, se abrirá una ventana del navegador para que inicies sesión con tu cuenta de Google y autorices el acceso.
   - Tras autorizar, se guardará un archivo `token.pickle` con tus credenciales para futuros usos.

3. **Permisos necesarios:**
   - El usuario debe tener permisos de edición sobre la hoja de Google Sheets indicada en el script.

## Uso

### Generación de Pagos Mensuales

Ejecuta el script principal con:

```sh
python -m inmobiliaria.main --mes AAAA-MM
```

- El parámetro `--mes` es opcional. Si no lo indicas, se usará el mes actual.
- El script generará una nueva hoja en el Google Sheets con el nombre `pagos_AAAA_MM` (por ejemplo, `pagos_2025_06`).

### Generación de Historial Completo

Para generar el historial completo de todos los pagos desde el inicio de cada contrato:

```sh
python -m inmobiliaria.historical --hasta AAAA-MM
```

- El parámetro `--hasta` es opcional. Si no lo indicas, se usará el mes actual como límite.
- El script generará/actualizará una hoja llamada `historico` con todos los registros mensuales.
- **Funcionalidad incremental**: Si ya existe un historial, solo agregará los meses faltantes.
- **Respeta ajustes manuales**: Si modificas un `precio_original` en el historial, los cálculos futuros respetarán ese valor.
- **Logging de errores**: Los errores que impiden procesar propiedades se guardan automáticamente en `logs/errors.log` con información detallada.

### Logging de Errores

El módulo de historial registra automáticamente todos los errores que ocurren durante el procesamiento en un archivo de log dedicado:

- **Ubicación**: `logs/errors.log`
- **Formato**: Incluye timestamp, nivel, contexto y detalles del error
- **Información registrada**: Nombre de la propiedad, inquilino, fecha de inicio del contrato, precio original y descripción del error
- **Rotación**: El archivo se extiende con cada ejecución (no se sobrescribe)

**Ejemplo de entrada en el log:**
```
2025-08-10 17:00:58 - ERROR - [HISTORICAL] - Propiedad: Av Corrientes 1234 | Inquilino: Juan Pérez | Fecha inicio: 2024-01-15 | Precio original: 100000 | Error: Campo obligatorio faltante: actualizacion
```

**Beneficios:**
- Facilita la identificación de propiedades con datos inconsistentes
- Permite auditoría y seguimiento de problemas recurrentes
- No interrumpe el procesamiento de otras propiedades
- Información persistente para análisis posterior

## Estructura esperada de la hoja "maestro"

La hoja de Google Sheets debe tener una hoja llamada `administracion` con las siguientes columnas:

**Campos Obligatorios:**
- `nombre_inmueble` (identificador único de la propiedad)
- `dir_inmueble` (dirección de la propiedad)
- `inquilino` (nombre del inquilino)
- `propietario` (nombre del propietario)
- `precio_original` (precio base del alquiler)
- `fecha_inicio_contrato` (formato YYYY-MM-DD)
- `duracion_meses` (duración total del contrato en meses)
- `actualizacion` (trimestral, cuatrimestral, semestral, anual)
- `indice` (por ejemplo, "IPC", "ICL" o "10%")
- `comision_inmo` (porcentaje, ej: "5%")

**Campos Opcionales:**
- `in_dni` (DNI del inquilino)
- `prop_dni` (DNI del propietario)
- `comision` ("Pagado", "2 cuotas", "3 cuotas") - default: "Pagado"
- `deposito` ("Pagado", "2 cuotas", "3 cuotas") - default: "Pagado"
- `municipalidad` (monto fijo mensual) - default: 0
- `luz` (monto fijo mensual de servicio de luz) - default: 0
- `gas` (monto fijo mensual de servicio de gas) - default: 0
- `expensas` (monto fijo mensual de expensas) - default: 0
- `descuento` (porcentaje de descuento aplicado, ej: "15%") - default: "0%"

### Funcionalidad de Comisión y Depósito en Cuotas

Las columnas `comision` y `deposito` permiten configurar el pago fraccionado de estos conceptos:

- **"Pagado"**: La comisión/depósito ya fue pagado por separado, no se suma al alquiler mensual
- **"2 cuotas"**: Se divide el monto en 2 partes iguales y se suma a los primeros 2 meses
- **"3 cuotas"**: Se divide el monto en 3 partes iguales y se suma a los primeros 3 meses

**NUEVO - Interés en Comisión Fraccionada**:
- **Comisión en 2 cuotas**: Se aplica 10% de interés → Total: precio_base × 1.10
- **Comisión en 3 cuotas**: Se aplica 20% de interés → Total: precio_base × 1.20
- **Depósito**: Se mantiene sin interés

**Ejemplo**: Si el alquiler base es $300,000, comisión "3 cuotas" y depósito "2 cuotas":
- Mes 1: $300,000 + $120,000 (comisión c/interés) + $150,000 (depósito) = $570,000
- Mes 2: $300,000 + $120,000 (comisión c/interés) + $150,000 (depósito) = $570,000  
- Mes 3: $300,000 + $120,000 (comisión c/interés) + $0 (depósito) = $420,000
- Mes 4 en adelante: $300,000

### Servicios Fijos (Municipalidad, Luz, Gas, Expensas)

Los campos `municipalidad`, `luz`, `gas` y `expensas` representan montos fijos mensuales que se suman al precio total:

- **Características**: Son montos fijos que NO se actualizan con inflación/ICL
- **Aplicación**: Se suman directamente al precio final cada mes
- **Comisión**: NO se aplica comisión inmobiliaria sobre estos conceptos
- **Ejemplo**: Con precio_original $100,000, descuento 15%, municipalidad $5,000, luz $3,000, gas $2,000, expensas $1,500:
  - Precio con descuento: $85,000
  - Precio total: $85,000 + $5,000 + $3,000 + $2,000 + $1,500 = $96,500
  - Si hay actualización del 10%: precio_original pasa a $110,000, precio con descuento $93,500, pero servicios siguen siendo $11,500

### Funcionalidad de Descuentos

La columna `descuento` permite aplicar un porcentaje de descuento sobre el precio base actualizado:

- **Formato**: Porcentaje con símbolo % (ej: "15%", "5%", "0%")
- **Aplicación**: Se aplica después de las actualizaciones por inflación/ICL
- **Impacto**: 
  - La comisión inmobiliaria se calcula sobre el precio con descuento
  - Las cuotas adicionales también se calculan sobre el precio con descuento
  - El descuento se mantiene fijo durante toda la vigencia del contrato

**Ejemplo con descuento**: 
- Precio original actualizado: $100,000
- Descuento: 15%
- Precio con descuento: $85,000
- Comisión 5%: $4,250 (sobre $85,000, no sobre $100,000)
- Cuotas adicionales: Se calculan sobre $85,000

## Salida

### Reportes Mensuales

Se crea una hoja nueva en el mismo Google Sheets con las siguientes columnas:

- `nombre_inmueble`
- `dir_inmueble`
- `inquilino`
- `propietario`
- `mes_actual`
- `precio_final` (precio total que paga el inquilino, incluyendo cuotas y servicios)
- `precio_original` (precio base del alquiler sin descuentos ni cuotas)
- `precio_descuento` (precio con descuento aplicado)
- `cuotas_adicionales` (monto de cuotas de comisión/depósito este mes)
- `municipalidad` (gastos municipales mensuales)
- `luz` (servicio de luz mensual)
- `gas` (servicio de gas mensual)
- `expensas` (expensas mensuales)
- `comision_inmo` (comisión de administración al propietario)
- `pago_prop` (pago neto al propietario)
- `actualizacion` ("SI" si corresponde actualización ese mes)
- `porc_actual` (porcentaje aplicado en la actualización, vacío si no hubo)
- `meses_prox_actualizacion` (meses hasta la próxima actualización de precio)
- `meses_prox_renovacion` (meses restantes del contrato)

### Historial Completo

El módulo `historical.py` genera una hoja llamada `historico` con la misma estructura que los reportes mensuales, pero conteniendo **todos los meses** desde el inicio de cada contrato hasta la fecha límite especificada.

#### Características del Historial:

- **Incremental**: Solo calcula meses nuevos, preservando el historial existente
- **Ajustes manuales**: Si modificas un `precio_original` en el historial, respeta ese valor para cálculos futuros
- **Actualizaciones reales**: Aplica ICL, IPC o porcentajes fijos según corresponda en cada período
- **Trazabilidad completa**: Permite auditar todos los cambios de precio mes a mes

#### Casos de Uso del Historial:

1. **Setup inicial**: Generar todo el historial desde cero para contratos existentes
2. **Actualización mensual**: Agregar solo los meses nuevos al historial
3. **Corrección de precios**: Ajustar manualmente un precio_original y recalcular desde ese punto
4. **Auditoría y reportes**: Tener visibilidad completa de la evolución de precios
5. **Análisis de tendencias**: Estudiar el impacto de la inflación/ICL en el tiempo

## Tests

Este proyecto incluye una suite completa de **137 tests** organizados en una arquitectura profesional de tres niveles para garantizar la calidad y correctness de todos los cálculos.

### Estructura de Tests

```
tests/
├── functional/     # Tests de funcionalidad del sistema (110 tests)
├── integration/    # Tests de integración de servicios (10 tests)  
├── unit/          # Tests unitarios de componentes (17 tests)
├── support/       # Datos y utilidades de apoyo
└── run_tests.py   # Runner principal de todos los tests
```

### Ejecutar Tests

1. **Configura el entorno virtual** (primera vez):
```sh
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate     # En Windows
pip install -r requirements.txt
```

2. **Ejecutar todos los tests**:
```sh
# Usando el entorno virtual
source venv/bin/activate
python tests/run_tests.py

# O directamente
python3 tests/run_tests.py
```

### Cobertura de Tests

#### 🧪 **Tests Funcionales (1-110)** - 8 categorías principales:
- ✅ **Validación de datos**: Campos obligatorios, formatos de fecha, números válidos
- ✅ **Lógica de contratos**: Vigencia, ciclos de actualización, cálculo de meses
- ✅ **Actualizaciones de precio**: IPC, ICL, porcentajes fijos con cálculo compuesto
- ✅ **Cuotas adicionales**: Comisión del inquilino, depósito, interacción con actualizaciones
- ✅ **Precios finales**: Composición, gastos municipales, comisiones de administración
- ✅ **Campos informativos**: Indicadores de actualización, próximas fechas importantes
- ✅ **Casos extremos**: APIs no disponibles, datos inconsistentes, precisión numérica
- ✅ **Integración completa**: Escenarios complejos, procesamiento masivo, validación de output

#### 🔧 **Tests de Integración (111-120)**:
- ✅ **Servicios del historial**: Inicialización, flujo completo, validación de contexto
- ✅ **Generación de registros**: Cálculos mensuales, manejo de errores

#### ⚙️ **Tests Unitarios (121-137)**:
- ✅ **HistoricalService**: Inicialización, carga de datos, manejo de errores
- ✅ **HistoricalDataManager**: Google Sheets I/O, validación de datos
- ✅ **MonthlyRecordGenerator**: Generación de registros individuales

### Estadísticas de Calidad

- 📊 **137 tests totales** con **100% tasa de éxito**
- 🎯 **10 categorías** cubriendo todas las funciones críticas
- 🔍 **Casos extremos**: Datos faltantes, contratos vencidos, formatos inválidos
- 🏗️ **Arquitectura profesional**: Separación clara entre functional/integration/unit
- 📖 **Documentación completa**: Cada test explicado en `tests/tests_funcionales.md`

Los tests garantizan que:
- Los cálculos financieros sean precisos al centavo
- La lógica de actualización funcione correctamente en todos los ciclos
- El manejo de errores sea robusto y gracioso
- Los cambios no rompan funcionalidad existente
- La integración con APIs externas sea resiliente

## Notas

### Archivos Generados
- **Reportes mensuales**: Si la hoja de pagos para ese mes ya existe, será sobrescrita.
- **Historial**: La hoja "historico" se actualiza incrementalmente, preservando registros existentes.

### Autenticación
- El archivo `token.pickle` guarda tu sesión autorizada y puede ser eliminado si necesitas reautenticarte.

### Arquitectura del Sistema
- **Módulo principal**: Generación de reportes mensuales simples
- **Módulo historial**: Generación incremental con servicios especializados:
  - `HistoricalService`: Orquestación del proceso completo
  - `HistoricalDataManager`: Comunicación con Google Sheets
  - `MonthlyRecordGenerator`: Generación de registros mensuales
  - `HistoricalCalculations`: Cálculos especializados de actualización

### Tipos de Comisiones
- **`comision`**: Comisión que paga el **inquilino** (equivale a 1 mes de alquiler)
- **`comision_inmo`**: Porcentaje de comisión de administración que se descuenta del pago al **propietario**

### Actualización de Precios
- **ICL**: Consulta automáticamente la API del BCRA para obtener factores reales
- **IPC**: Usa datos de inflación histórica
- **Porcentaje fijo**: Aplica el porcentaje especificado (ej: "10%", "7.5%")

#### Secuencia de Actualizaciones

Las actualizaciones de precio siguen esta secuencia según la frecuencia configurada:

- **Trimestral**: Actualizaciones en los meses 3, 6, 9, 12, 15, 18... del contrato
- **Cuatrimestral**: Actualizaciones en los meses 4, 8, 12, 16, 20, 24... del contrato  
- **Semestral**: Actualizaciones en los meses 6, 12, 18, 24, 30, 36... del contrato
- **Anual**: Actualizaciones en los meses 12, 24, 36, 48... del contrato

**Ejemplo trimestral**: Un contrato que inicia en enero tendrá actualizaciones en marzo (mes 3), junio (mes 6), septiembre (mes 9), etc.

### Validación de Datos

El sistema incluye validación robusta de datos de entrada:

**Campos Obligatorios**: El sistema requiere todos los campos obligatorios y utilizará valores por defecto para campos opcionales faltantes:
- `comision`: "Pagado" (default)
- `deposito`: "Pagado" (default)  
- `municipalidad`: 0 (default)
- `luz`: 0 (default)
- `gas`: 0 (default)
- `expensas`: 0 (default)
- `descuento`: "0%" (default)

**Formatos Soportados**:
- Fechas: YYYY-MM-DD o YYYY_MM_DD
- Porcentajes: "10%", "7.5%", "7,5%" (con coma o punto decimal)
- Actualizaciones: "trimestral", "cuatrimestral", "semestral", "anual"

### Ajustes Manuales en Historial
- Puedes modificar cualquier `precio_original` en la hoja "historico"
- Los cálculos futuros respetarán ese valor ajustado
- Útil para reflejar negociaciones o ajustes contractuales especiales

---

¿Dudas o problemas? Revisa los mensajes de error en la terminal y asegúrate de tener permisos y credenciales correctas. También puedes consultar la documentación de Google Sheets API y Python para más detalles.
