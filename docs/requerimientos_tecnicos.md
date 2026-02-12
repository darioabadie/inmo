# Requerimientos tecnicos

## Objetivo
Definir los requisitos tecnicos para un agente inmobiliario que opera por WhatsApp, automatiza calculos y recibos, y aplica reglas especiales sin editar Google Sheets.

## Arquitectura general
- Canal principal: WhatsApp.
- Motor de calculo: scripts Python existentes del repo.
- Fuente de datos: Google Sheets (solo lectura).
- Reglas especiales: archivos .md + JSON derivado local.
- Salidas: PDFs de recibos, logs, y reportes de estado.

## Integracion con el repo
- Usar los modulos existentes:
  - `python -m inmobiliaria.main --mes AAAA-MM`
  - `python -m inmobiliaria.historical --hasta AAAA-MM`
  - `python -m inmobiliaria.recibos --mes AAAA-MM`
- No modificar la planilla `administracion` ni `historico`.

## Reglas especiales (md -> json)
- Archivos fuente:
  - `rules/global.md`
  - `rules/tenants/<inquilino>.md`
- Cache derivado:
  - `rules/cache/global.json`
  - `rules/cache/tenants/<inquilino>.json`
- Secciones soportadas en .md:
  - `[formula]` una linea con formula
  - `[override]` pares clave = valor
- Variables permitidas en formulas: solo campos monetarios y valores del dominio.
- Prioridad: reglas por inquilino sobrescriben globales.
- Validacion estricta (sin ejecucion arbitraria).

## Campos monetarios editables
- `precio_descuento`
- `expensas`
- `municipalidad`
- `luz`
- `gas`
- `cuotas_deposito`
- `cuotas_comision`

## Persistencia y restricciones
- Las correcciones manuales se guardan en JSON derivado y logs.
- Google Sheets permanece solo lectura.

## Aprobaciones y envio
- Todo envio por WhatsApp requiere aprobacion previa.
- Recibos con reglas especiales siempre requieren aprobacion.
- Se soporta aprobacion parcial (lista de inquilinos).

## Auditoria
- Log por recibo:
  - generado
  - modificado
  - aprobado
  - enviado
- Log de reglas aplicadas (global y por inquilino).

## Seguridad
- Restringir comandos del agente a una lista permitida.
- No exponer credenciales ni tokens por WhatsApp.

## Observabilidad
- Reporte de resumen por ejecucion:
  - procesados
  - omitidos
  - errores
  - recibos enviados
