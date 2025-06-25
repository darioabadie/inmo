# inmo

Este script genera el archivo de pagos mensuales para cada propiedad administrada a partir de la planilla `maestro.xlsx`.

## Entradas
- `maestro.xlsx` (hoja 'maestro') con las columnas:
  - nombre_inmueble, dir_inmueble, inquilino, in_dni, propietario, prop_dni, precio_original, actualizacion, indice, fecha_inicio_contrato, duracion_meses, comision_inmo
- Parámetro opcional `--mes AAAA-MM` (por defecto, el mes actual)

## Salida
- Archivo `pagos_AAAA_MM.xlsx` con las siguientes columnas:
  - `nombre_inmueble`, `dir_inmueble`, `inquilino`, `propietario`, `mes_actual`, `precio_mes_actual`, `comision_inmo`, `pago_prop`
  - `actualizacion`: "SI" si ese mes corresponde actualización, "NO" si no.
  - `porc_actual`: porcentaje aplicado en la actualización de ese mes (acumulado IPC o fijo), vacío si no hubo actualización.
  - `meses_prox_renovacion`: cantidad de meses que le quedan vigentes al contrato.

## Ejemplo de columnas agregadas
| mes_actual | actualizacion | porc_actual | meses_prox_renovacion |
|------------|---------------|-------------|----------------------|
| 2025-06    | SI            | 8.3         | 6                    |
| 2025-07    | NO            |             | 5                    |

## Ejecución

```bash
python app.py --mes 2025-06
```

El archivo generado se guarda en el mismo directorio o el que indiques con `--outdir`.
