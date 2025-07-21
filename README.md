# inmo - Generador de Pagos para Propiedades Administradas

Esta aplicación automatiza la generación mensual de reportes de pagos para propiedades administradas, utilizando datos de un archivo maestro en Google Sheets y aplicando reglas de actualización de precios según IPC o porcentajes fijos.

## ¿Qué hace la app?

- Lee la información de contratos de alquiler desde una hoja de Google Sheets.
- Calcula el monto a pagar cada mes para cada propiedad, considerando actualizaciones por inflación (IPC) o porcentajes fijos.
- Calcula la comisión de la inmobiliaria y el pago neto al propietario.
- Genera una hoja nueva en el mismo Google Sheets con el detalle de pagos del mes seleccionado.
- Permite elegir el mes de cálculo (por defecto, el mes actual).

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

Ejecuta el script con:

```sh
python app.py --mes AAAA-MM
```

- El parámetro `--mes` es opcional. Si no lo indicas, se usará el mes actual.
- El script generará una nueva hoja en el Google Sheets con el nombre `pagos_AAAA_MM` (por ejemplo, `pagos_2025_06`).

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

## Salida

Se crea una hoja nueva en el mismo Google Sheets con las siguientes columnas:

- `nombre_inmueble`
- `dir_inmueble`
- `inquilino`
- `propietario`
- `mes_actual`
- `precio_mes_actual` (precio total que paga el inquilino, incluyendo cuotas)
- `precio_base` (precio base del alquiler sin cuotas)
- `cuotas_adicionales` (monto de cuotas de comisión/depósito este mes)
- `comision_inmo` (comisión de administración al propietario)
- `pago_prop` (pago neto al propietario)
- `actualizacion` ("SI" si corresponde actualización ese mes)
- `porc_actual` (porcentaje aplicado en la actualización, vacío si no hubo)
- `meses_prox_renovacion` (meses restantes del contrato)

## Notas

- Si la hoja de pagos para ese mes ya existe, será sobrescrita.
- El archivo `token.pickle` guarda tu sesión autorizada y puede ser eliminado si necesitas reautenticarte.
- **Diferencia entre comisiones**:
  - `comision`: Comisión que paga el **inquilino** (equivale a 1 mes de alquiler)
  - `comision_inmo`: Porcentaje de comisión de administración que se descuenta del pago al **propietario**

---

¿Dudas o problemas? Revisa los mensajes de error en la terminal y asegúrate de tener permisos y credenciales correctas. También puedes consultar la documentación de Google Sheets API y Python para más detalles.
