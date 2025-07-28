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

## Estructura esperada de la hoja "maestro"

La hoja de Google Sheets debe tener una hoja llamada `administracion` con las siguientes columnas:

- `nombre_inmueble`
- `dir_inmueble`
- `inquilino`
- `in_dni`
- `propietario`
- `prop_dni`
- `precio_original`
- `actualizacion` (trimestral, semestral, anual)
- `indice` (por ejemplo, "IPC" o "10%")
- `fecha_inicio_contrato` (YYYY-MM-DD)
- `duracion_meses`
- `comision_inmo` (porcentaje, ej: "5%")
- `comision` ("Pagado", "2 cuotas", "3 cuotas")
- `deposito` ("Pagado", "2 cuotas", "3 cuotas")
- `municipalidad` (monto fijo mensual, opcional)
- `luz` (monto fijo mensual de servicio de luz, opcional)
- `gas` (monto fijo mensual de servicio de gas, opcional)
- `expensas` (monto fijo mensual de expensas, opcional)
- `descuento` (porcentaje de descuento aplicado, opcional, ej: "15%", "0%")

### Funcionalidad de Comisión y Depósito en Cuotas

Las columnas `comision` y `deposito` permiten configurar el pago fraccionado de estos conceptos:

- **"Pagado"**: La comisión/depósito ya fue pagado por separado, no se suma al alquiler mensual
- **"2 cuotas"**: Se divide el monto (equivalente a 1 mes de alquiler) en 2 partes iguales y se suma a los primeros 2 meses
- **"3 cuotas"**: Se divide el monto (equivalente a 1 mes de alquiler) en 3 partes iguales y se suma a los primeros 3 meses

**Ejemplo**: Si el alquiler base es $100,000, comisión "2 cuotas" y depósito "3 cuotas":
- Mes 1: $100,000 + $50,000 (comisión) + $33,333 (depósito) = $183,333
- Mes 2: $100,000 + $50,000 (comisión) + $33,333 (depósito) = $183,333  
- Mes 3: $100,000 + $0 (comisión) + $33,334 (depósito) = $133,334
- Mes 4 en adelante: $100,000

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

Este proyecto incluye una suite completa de tests unitarios y de integración para garantizar la calidad y correctness de todos los cálculos.

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
./venv/bin/python tests/run_tests.py

# O activando el entorno
source venv/bin/activate
python tests/run_tests.py
```

3. **Ejecutar tests específicos**:
```sh
python tests/run_tests.py calculations    # Solo cálculos matemáticos
python tests/run_tests.py contract       # Solo lógica de contratos  
python tests/run_tests.py integration    # Solo tests de integración
```

### Cobertura de Tests

- ✅ **36 tests** cubriendo todas las funciones críticas
- ✅ **Cálculos matemáticos**: inflación, comisiones, cuotas adicionales
- ✅ **Lógica de contratos**: ciclos, actualizaciones, vigencia
- ✅ **Casos extremos**: datos faltantes, contratos vencidos, formatos inválidos
- ✅ **Integración**: flujo completo extremo a extremo

Los tests garantizan que:
- Los cálculos financieros sean precisos
- La lógica de actualización funcione correctamente
- El manejo de errores sea robusto
- Los cambios no rompan funcionalidad existente

## Notas

### Archivos Generados
- **Reportes mensuales**: Si la hoja de pagos para ese mes ya existe, será sobrescrita.
- **Historial**: La hoja "historico" se actualiza incrementalmente, preservando registros existentes.

### Autenticación
- El archivo `token.pickle` guarda tu sesión autorizada y puede ser eliminado si necesitas reautenticarte.

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

### Ajustes Manuales en Historial
- Puedes modificar cualquier `precio_original` en la hoja "historico"
- Los cálculos futuros respetarán ese valor ajustado
- Útil para reflejar negociaciones o ajustes contractuales especiales

---

¿Dudas o problemas? Revisa los mensajes de error en la terminal y asegúrate de tener permisos y credenciales correctas. También puedes consultar la documentación de Google Sheets API y Python para más detalles.
