# Technical Specifications - Sistema de Cálculo de Pagos Inmobiliarios

## Resumen Ejecutivo

Este documento define las especificaciones técnicas del sistema de cálculo de pagos mensuales para propiedades administradas. El sistema procesa contratos de alquiler, aplica actualizaciones por inflación, calcula comisiones y genera reportes mensuales detallados.

## Arquitectura de Datos

### Input: Hoja "administracion" (Google Sheets)
```
Campos obligatorios:
- nombre_inmueble, dir_inmueble, inquilino, propietario
- precio_original, fecha_inicio_contrato, duracion_meses
- actualizacion, indice, comision_inmo
- comision, deposito (opcional: default "Pagado")
- municipalidad, luz, gas, expensas (opcional: default 0)
- descuento (opcional: default "0%")
```

### Output: Hoja "historico" 
```
Columnas calculadas:
- precio_final, precio_original, precio_descuento, descuento
- cuotas_adicionales, municipalidad, luz, gas, expensas
- comision_inmo, pago_prop
- actualizacion, porc_actual
- meses_prox_actualizacion, meses_prox_renovacion
```

## Especificaciones Técnicas por Columna

### 1. Columnas de Identificación (Copia Directa)
- **nombre_inmueble**: Copiado directamente del maestro
- **dir_inmueble**: Copiado directamente del maestro  
- **inquilino**: Copiado directamente del maestro
- **propietario**: Copiado directamente del maestro
- **mes_actual**: Parámetro de entrada (formato: YYYY-MM)

### 2. **precio_base** - Precio Base Actualizado
**Método**: `precio_ajustado()` + cálculo de factor acumulado

**Lógica**:
1. **Cálculo de ciclos**: `meses_desde_inicio = (año_ref - año_inicio) * 12 + (mes_ref - mes_inicio)`
2. **Frecuencia de actualización**: `freq_meses = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}`
3. **Ciclos cumplidos**: `ciclos_cumplidos = meses_desde_inicio // freq_meses`
4. **Factor acumulado**: Se aplica compuestamente según el índice

**Cálculo por Índice**:

**IPC (Inflación)**:
```python
factor_total = 1.0
for ciclo in range(ciclos_cumplidos):
    fecha_corte = inicio + relativedelta(months=(ciclo + 1) * freq_meses)
    factor_ciclo = inflacion_acumulada(inflacion_df, fecha_corte, freq_meses)
    factor_total *= factor_ciclo
precio_base = precio_original * factor_total
```

**ICL (Índice Costo Laboral)**:
```python
factor_total = 1.0
for ciclo in range(ciclos_cumplidos):
    fecha_inicio_ciclo = inicio + relativedelta(months=ciclo * freq_meses)
    fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=freq_meses)
    factor_ciclo = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
    factor_total *= factor_ciclo
precio_base = precio_original * factor_total
```

**Porcentaje Fijo**:
```python
pct = float(indice.replace("%", "").replace(",", "."))
factor_total = (1 + pct / 100) ** ciclos_cumplidos
precio_base = precio_original * factor_total
```

**Ejemplo**:
- Precio original: $100,000
- Inicio: 2024-01-01, Referencia: 2024-07-01
- Actualización: trimestral, Índice: "10%"
- Meses desde inicio: 6, Ciclos cumplidos: 2
- Factor total: (1.10)² = 1.21
- **precio_base = $121,000**

### 3. **cuotas_adicionales** - Comisión y Depósito Fraccionados
**Método**: `calcular_cuotas_adicionales()`

**Lógica**:
- Tanto comisión como depósito equivalen a **1 mes de alquiler base**
- Se fraccionan según configuración: "2 cuotas", "3 cuotas" o "Pagado"
- Solo se suman en los primeros meses del contrato
- **NUEVO**: La comisión aplica interés según el número de cuotas:
  - **2 cuotas**: 10% de interés
  - **3 cuotas**: 20% de interés
- El depósito se mantiene sin interés

```python
def calcular_cuotas_adicionales(precio_base, comision_inquilino, deposito, mes_actual):
    monto_adicional = 0.0
    
    # Comisión fraccionada con interés
    if comision_inquilino == "2 cuotas" and mes_actual <= 2:
        monto_adicional += (precio_base * 1.10) / 2  # 10% interés
    elif comision_inquilino == "3 cuotas" and mes_actual <= 3:
        monto_adicional += (precio_base * 1.20) / 3  # 20% interés
    
    # Depósito fraccionado sin interés
    if deposito == "2 cuotas" and mes_actual <= 2:
        monto_adicional += precio_base / 2
    elif deposito == "3 cuotas" and mes_actual <= 3:
        monto_adicional += precio_base / 3
    
    return round(monto_adicional, 2)
```

**Ejemplo**:
- precio_base: $300,000
- comision: "3 cuotas", deposito: "2 cuotas"
- Mes 1: $300,000 × 1.20 ÷ 3 + $300,000 ÷ 2 = $120,000 + $150,000 = **$270,000**
- Mes 2: $300,000 × 1.20 ÷ 3 + $300,000 ÷ 2 = $120,000 + $150,000 = **$270,000**  
- Mes 3: $300,000 × 1.20 ÷ 3 + $0 = $120,000 + $0 = **$120,000**
- Mes 4+: **$0**

### 4. **municipalidad** - Gastos Municipales
**Método**: Copia directa con validación

**Lógica**:
```python
municipalidad = float(fila.get("municipalidad", 0)) if fila.get("municipalidad") and str(fila.get("municipalidad")).strip() != "" else 0
```

### 5. **precio_mes_actual** - PRECIO TOTAL QUE PAGA EL INQUILINO
**Método**: Suma de componentes

**Lógica** (CRÍTICA):
```python
precio_mes_actual = precio_base + cuotas_adicionales + municipalidad
```

**Componentes**:
1. **precio_base**: Alquiler actualizado por inflación/índice
2. **cuotas_adicionales**: Fracción de comisión + depósito (solo primeros meses)
3. **municipalidad**: Gastos municipales fijos

**Ejemplo Completo**:
```
Contrato: $100,000 inicial, trimestral 10%, inicio 2024-01-01
Configuración: comision "2 cuotas", deposito "3 cuotas", municipalidad $5,000
Cálculo para mes 2024-07-01 (mes 7 del contrato):

1. precio_base = $100,000 * (1.10)² = $121,000
2. cuotas_adicionales = $0 (ya pasaron los primeros meses)
3. municipalidad = $5,000
4. precio_mes_actual = $121,000 + $0 + $5,000 = $126,000
```

**Ejemplo Mes Inicial**:
```
Mismo contrato, mes 2024-01-01 (mes 1):

1. precio_base = $100,000 (sin actualizaciones aún)
2. cuotas_adicionales = $50,000 + $33,333 = $83,333
3. municipalidad = $5,000
4. precio_mes_actual = $100,000 + $83,333 + $5,000 = $188,333
```

### 6. **comision_inmo** - Comisión de Administración
**Método**: `calcular_comision()`

**Lógica**:
- Se calcula sobre el **precio_base** (sin cuotas ni municipalidad)
- Expresada como porcentaje: "5%", "7.5%"

```python
def calcular_comision(comision_str, precio_mes):
    pct = float(comision_str.strip().replace("%", "").replace(",", "."))
    return round(precio_mes * pct / 100, 2)
```

**Ejemplo**: precio_base $121,000, comision_inmo "5%" → **$6,050**

### 7. **pago_prop** - Pago Neto al Propietario
**Método**: Resta simple

**Lógica**:
```python
pago_prop = precio_base - comision_inmo
```

**Ejemplo**: $121,000 - $6,050 = **$114,950**

### 8. **actualizacion** - Indicador de Actualización
**Método**: Cálculo de módulo

**Lógica**:
```python
resto = meses_desde_inicio % freq_meses
aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
```

**Ejemplo**: 
- Trimestral (freq_meses=3), mes 6: resto = 6%3 = 0, ciclos = 6//3 = 2 → **"SI"**
- Trimestral, mes 7: resto = 7%3 = 1 → **"NO"**

### 9. **porc_actual** - Porcentaje Aplicado Este Mes
**Método**: Cálculo del último factor aplicado en el mes de actualización

**Lógica General**:
- Solo se calcula si `actualizacion == "SI"` (es decir, este mes corresponde actualización)
- Representa el porcentaje de incremento aplicado **exclusivamente en este ciclo**
- Se expresa como porcentaje (ej: 15.3 para un incremento del 15.3%)

**Implementación por Índice**:

**IPC (Inflación)**:
```python
if aplica_actualizacion == "SI" and ciclos_cumplidos > 0:
    fecha_corte = inicio + relativedelta(months=ciclos_cumplidos * freq_meses)
    porc_actual = (inflacion_acumulada(inflacion_df, fecha_corte, freq_meses) - 1) * 100
```

**ICL (Índice Costo Laboral) - CASO MÁS COMÚN**:
```python
if aplica_actualizacion == "SI" and ciclos_cumplidos > 0:
    fecha_inicio_ult = inicio + relativedelta(months=(ciclos_cumplidos - 1) * freq_meses)
    fecha_fin_ult = fecha_inicio_ult + relativedelta(months=freq_meses)
    factor_icl = traer_factor_icl(fecha_inicio_ult, fecha_fin_ult)
    porc_actual = (factor_icl - 1) * 100
```

**Porcentaje Fijo**:
```python
if aplica_actualizacion == "SI" and ciclos_cumplidos > 0:
    porc_actual = float(fila["indice"].replace("%", ""))
```

**Explicación Detallada ICL**:

El ICL (Índice Costo Laboral) es el índice más utilizado para actualizaciones de alquileres en Argentina. Se obtiene del BCRA y representa la variación del costo laboral entre dos fechas.

**API Call ICL**:
```python
def traer_factor_icl(fecha_inicio: dt.date, fecha_hasta: dt.date) -> float:
    url = f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/40?desde={fecha_inicio.strftime('%Y-%m-%d')}&hasta={fecha_hasta.strftime('%Y-%m-%d')}"
    res = requests.get(url, timeout=10, verify=False)
    data = res.json()["results"]
    
    # Los datos vienen ordenados cronológicamente inverso
    valor_inicio = data[-1]["valor"]  # Valor más antiguo
    valor_final = data[0]["valor"]    # Valor más reciente
    
    return float(valor_final) / float(valor_inicio)
```

**Ejemplo Completo - Contrato con Actualizaciones ICL Trimestrales**:

**Configuración del Contrato**:
- Precio inicial: $100,000
- Fecha inicio: 2024-01-01  
- Actualización: trimestral
- Índice: ICL
- Duración: 24 meses

**Evolución del Contrato**:

**Trimestre 1 (Enero-Marzo 2024)**:
- `meses_desde_inicio`: 0, 1, 2
- `ciclos_cumplidos`: 0
- `actualizacion`: "NO" 
- `porc_actual`: "" (vacío)
- `precio_base`: $100,000

**Trimestre 2 (Abril 2024 - Primera Actualización)**:
- Fecha referencia: 2024-04-01
- `meses_desde_inicio`: 3
- `ciclos_cumplidos`: 3 // 3 = 1
- `resto`: 3 % 3 = 0 → `actualizacion`: "SI"

**Cálculo ICL Abril 2024**:
```python
fecha_inicio_ciclo = 2024-01-01  # Inicio del primer trimestre
fecha_fin_ciclo = 2024-04-01     # Fin del primer trimestre
factor_icl = traer_factor_icl(2024-01-01, 2024-04-01)
# Supongamos que ICL subió de 100.0 a 112.5
factor_icl = 112.5 / 100.0 = 1.125
porc_actual = (1.125 - 1) * 100 = 12.5%
precio_base = $100,000 * 1.125 = $112,500
```

**Trimestre 3 (Mayo-Junio 2024)**:
- `actualizacion`: "NO"
- `porc_actual`: "" (vacío)
- `precio_base`: $112,500 (mantiene precio del trimestre anterior)

**Julio 2024 (Segunda Actualización)**:
- Fecha referencia: 2024-07-01
- `meses_desde_inicio`: 6
- `ciclos_cumplidos`: 6 // 3 = 2  
- `resto`: 6 % 3 = 0 → `actualizacion`: "SI"

**Cálculo ICL Julio 2024**:
```python
# Para el segundo ciclo (abril-julio)
fecha_inicio_ult = 2024-04-01    # Inicio del segundo trimestre
fecha_fin_ult = 2024-07-01       # Fin del segundo trimestre
factor_icl = traer_factor_icl(2024-04-01, 2024-07-01)
# Supongamos ICL subió de 112.5 a 125.0
factor_icl = 125.0 / 112.5 = 1.111
porc_actual = (1.111 - 1) * 100 = 11.1%

# Precio acumulado
factor_total = 1.125 * 1.111 = 1.250
precio_base = $100,000 * 1.250 = $125,000
```

**Detalle Mes a Mes - Primer Año del Contrato**:

| Mes | Fecha Ref. | Meses desde inicio | Ciclos | Resto | Actualización | ICL Factor | % Actual | Precio Base |
|-----|------------|-------------------|---------|-------|---------------|------------|----------|-------------|
| 1 | 2024-01-01 | 0 | 0 | 0 | NO | - | - | $100,000 |
| 2 | 2024-02-01 | 1 | 0 | 1 | NO | - | - | $100,000 |
| 3 | 2024-03-01 | 2 | 0 | 2 | NO | - | - | $100,000 |
| 4 | 2024-04-01 | 3 | 1 | 0 | **SI** | 1.125 | **12.5%** | **$112,500** |
| 5 | 2024-05-01 | 4 | 1 | 1 | NO | - | - | $112,500 |
| 6 | 2024-06-01 | 5 | 1 | 2 | NO | - | - | $112,500 |
| 7 | 2024-07-01 | 6 | 2 | 0 | **SI** | 1.111 | **11.1%** | **$125,000** |
| 8 | 2024-08-01 | 7 | 2 | 1 | NO | - | - | $125,000 |
| 9 | 2024-09-01 | 8 | 2 | 2 | NO | - | - | $125,000 |
| 10 | 2024-10-01 | 9 | 3 | 0 | **SI** | 1.089 | **8.9%** | **$136,125** |
| 11 | 2024-11-01 | 10 | 3 | 1 | NO | - | - | $136,125 |
| 12 | 2024-12-01 | 11 | 3 | 2 | NO | - | - | $136,125 |

**Observaciones del Patrón**:
- **Actualizaciones ocurren**: cuando `resto = 0` y `ciclos > 0` (meses 4, 7, 10...)
- **Meses sin actualización**: mantienen el precio del último ajuste
- **Patrón trimestral**: Ajuste cada 3 meses (3, 6, 9, 12... meses desde inicio)
- **Factor acumulado**: Se va multiplicando secuencialmente

**Resumen de Actualizaciones**:
```
Mes         | Actualización | ICL Factor | % Actual | Precio Base
------------|---------------|------------|----------|-------------
2024-01     | NO           | -          | -        | $100,000
2024-04     | SI           | 1.125      | 12.5%    | $112,500  
2024-07     | SI           | 1.111      | 11.1%    | $125,000
2024-10     | SI           | 1.089      | 8.9%     | $136,125
2025-01     | SI           | 1.156      | 15.6%    | $157,440
```

**Aspectos Críticos del Cálculo ICL**:

1. **Fechas de Corte**: Se calculan desde el inicio de cada ciclo, no desde el inicio del contrato
2. **Acumulación**: Los factores se multiplican secuencialmente (efecto compuesto)
3. **API BCRA**: Los valores vienen en orden cronológico inverso
4. **Verificación SSL**: Deshabilitada (`verify=False`) por problemas con certificados BCRA

**Diferencias con IPC**:
- **IPC**: Se basa en inflación mensual acumulada de los últimos N meses
- **ICL**: Se basa en la variación del índice entre fechas específicas del BCRA
- **Timing**: ICL puede tener desfases en la publicación de datos oficiales

### 10. **meses_prox_actualizacion** - Meses Hasta Próxima Actualización
**Método**: Cálculo de ciclo restante

**Lógica**:
```python
if resto == 0 and ciclos_cumplidos > 0:
    # Estamos en mes de actualización, próxima en un ciclo completo
    meses_prox_actualizacion = freq_meses
else:
    # Faltan (freq_meses - resto) meses
    meses_prox_actualizacion = freq_meses - resto
```

### 11. **meses_prox_renovacion** - Meses Restantes del Contrato
**Método**: Resta simple

**Lógica**:
```python
meses_prox_renovacion = duracion_meses - meses_desde_inicio
```

## Validaciones y Manejo de Errores

### Campos Obligatorios
```python
campos_requeridos = [
    "precio_original", "fecha_inicio_contrato", "duracion_meses", 
    "actualizacion", "indice", "comision_inmo"
]
```

### Contratos Vencidos
```python
if (fecha_ref - inicio).days // 30 >= fila["duracion_meses"]:
    # Omitir registro - contrato finalizado
    continue
```

### Fechas Inválidas
```python
try:
    inicio = pd.to_datetime(fecha_inicio).date()
except Exception as e:
    # Log warning y omitir registro
    continue
```

### Valores por Defecto
- **comision/deposito**: "Pagado" si no se especifica
- **municipalidad**: 0 si está vacío
- **actualizacion**: "trimestral" si es inválida

## APIs Externas

### API de Inflación Argentina
- **URL**: `https://api.argentinadatos.com/v1/finanzas/indices/inflacion`
- **Método**: `traer_inflacion()` → DataFrame con fecha y valor mensual
- **Uso**: `inflacion_acumulada()` calcula factor compuesto

### API BCRA - Índice Costo Laboral (ICL)
- **URL**: `https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/40`
- **Método**: `traer_factor_icl()` → factor entre dos fechas
- **Configuración**: `verify=False` para SSL

## Consideraciones de Implementación

### Precisión Numérica
- Todos los montos se redondean a 2 decimales con `round()`
- Los factores de inflación se mantienen con precisión completa hasta el cálculo final

### Manejo de Estados
- Registros incompletos se procesan con campos calculados en blanco
- Contratos vencidos se omiten completamente
- Errores de cálculo mantienen el registro con valores por defecto

### Logging
- WARNING level para errores no críticos
- Categorización: `[REGISTRO INCOMPLETO]`, `[CONTRATO FINALIZADO]`, `[FECHA INVÁLIDA]`, etc.

---

## Puntos Críticos para Refactoring

1. **Separación de Responsabilidades**: La función `main()` hace demasiado - debería separarse en clases especializadas
2. **Cálculo de precio_mes_actual**: Lógica compleja distribuida en múltiples funciones
3. **Manejo de APIs**: Sin patrón de retry ni cache
4. **Validación**: Dispersa por todo el código, debería centralizarse
5. **Configuración**: Hardcoded, debería externalizarse

Este documento servirá como base para el refactoring arquitectural manteniendo la compatibilidad funcional.
