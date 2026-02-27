# Contratos entre agentes

## Objetivo
Establecer los contratos de datos y eventos que intercambian los 5 agentes para coordinar la operacion sin ambiguedades.

## Principios
- Datos inmutables por paso: cada agente produce un payload y no edita el de otro.
- Trazabilidad: todo payload incluye `cycle_id` y `timestamp`.
- Solo lectura de Google Sheets (ningun agente escribe en Sheets).

## Identificadores comunes
- `cycle_id`: string (ej: "2026-02")
- `timestamp`: ISO-8601 (ej: "2026-02-12T10:15:00Z")
- `tenant_id`: string normalizado (ej: "juan_perez")
- `receipt_id`: string estable (ej: "2026-02_juan_perez_av_corrientes_1234")

## Contratos de datos

### 1) CycleContext (Director -> Operacion Mensual)
```json
{
  "cycle_id": "2026-02",
  "mes": "2026-02",
  "modo": "automatico",
  "timestamp": "2026-02-12T10:15:00Z"
}
```

### 2) MonthlyPackage (Operacion Mensual -> Director)
```json
{
  "cycle_id": "2026-02",
  "procesados": 120,
  "omitidos": 3,
  "errores": 2,
  "recibos": [
    {
      "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
      "tenant_id": "juan_perez",
      "nombre_inquilino": "Juan Perez",
      "monto_final": 150000,
      "pdf_path": "recibos/2026-02/sin_firmar/Juan_Perez.pdf",
      "requiere_aprobacion": true
    }
  ],
  "logs": {
    "errores_path": "logs/errors.log"
  },
  "timestamp": "2026-02-12T10:40:00Z"
}
```

### 3) RulesDerivation (Reglas -> Director)
```json
{
  "cycle_id": "2026-02",
  "tenant_id": "juan_perez",
  "source_md": "rules/tenants/juan_perez.md",
  "derived_json": "rules/cache/tenants/juan_perez.json",
  "overrides": {
    "expensas": 35000
  },
  "formula": "precio_original * 0.85 + expensas",
  "timestamp": "2026-02-12T10:25:00Z"
}
```

### 4) ApprovalRequest (Director -> Operador)
```json
{
  "cycle_id": "2026-02",
  "total": 120,
  "pendientes": 120,
  "lote": ["2026-02_juan_perez_av_corrientes_1234"],
  "mensaje": "Aprobacion requerida para envio",
  "timestamp": "2026-02-12T11:00:00Z"
}
```

### 5) ApprovalDecision (Operador -> Director)
```json
{
  "cycle_id": "2026-02",
  "decision": "aprobar",
  "aprobados": ["2026-02_juan_perez_av_corrientes_1234"],
  "timestamp": "2026-02-12T11:05:00Z"
}
```

### 6) CorrectionRequest (Director -> Correcciones)
```json
{
  "cycle_id": "2026-02",
  "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
  "campo": "expensas",
  "valor": 42000,
  "motivo": "ajuste informado por el propietario",
  "timestamp": "2026-02-12T11:20:00Z"
}
```

### 7) CorrectionResult (Correcciones -> Director)
```json
{
  "cycle_id": "2026-02",
  "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
  "cambios": {
    "expensas": 42000
  },
  "pdf_path": "recibos/2026-02/sin_firmar/Juan_Perez.pdf",
  "requiere_aprobacion": true,
  "timestamp": "2026-02-12T11:30:00Z"
}
```

### 8) DeliveryBatch (Director -> Entrega y Auditoria)
```json
{
  "cycle_id": "2026-02",
  "lote": [
    {
      "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
      "tenant_id": "juan_perez",
      "telefono": "+54911XXXXXXX",
      "pdf_path": "recibos/2026-02/sin_firmar/Juan_Perez.pdf"
    }
  ],
  "timestamp": "2026-02-12T11:40:00Z"
}
```

### 9) DeliveryResult (Entrega y Auditoria -> Director)
```json
{
  "cycle_id": "2026-02",
  "enviados": 118,
  "fallidos": 2,
  "detalle": [
    {
      "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
      "estado": "enviado"
    }
  ],
  "timestamp": "2026-02-12T12:10:00Z"
}
```

## Eventos clave
- `cycle_started`
- `rules_derived`
- `monthly_package_ready`
- `approval_requested`
- `approval_granted`
- `approval_rejected`
- `correction_applied`
- `delivery_started`
- `delivery_completed`
- `delivery_failed`

## Estados del recibo
- `pendiente`
- `aprobado`
- `enviado`
- `fallido`
- `manual`

## Ubicaciones recomendadas
- Reglas fuente: `rules/global.md`, `rules/tenants/<inquilino>.md`
- Cache derivado: `rules/cache/global.json`, `rules/cache/tenants/<inquilino>.json`
- Recibos: `recibos/<AAAA-MM>/sin_firmar/` y `recibos/<AAAA-MM>/firmados/`
- Logs: `logs/`
