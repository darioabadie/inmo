# Skills OpenClaw (inputs/outputs)

## Objetivo
Mapear los contratos de datos a skills de OpenClaw para ejecutar el flujo end-to-end con 5 agentes.

## Convenciones
- Todos los skills aceptan/retornan JSON.
- `cycle_id` es obligatorio en todos los requests y responses.
- Los paths son relativos al repo.

## Skills del Agente Director

### skill: director.start_cycle
**Input**
```json
{
  "cycle_id": "2026-02",
  "mes": "2026-02",
  "modo": "automatico"
}
```
**Output**
```json
{
  "cycle_id": "2026-02",
  "estado": "pendiente",
  "timestamp": "2026-02-12T10:15:00Z"
}
```

### skill: director.request_approval
**Input**
```json
{
  "cycle_id": "2026-02",
  "total": 120,
  "pendientes": 120,
  "lote": ["2026-02_juan_perez_av_corrientes_1234"],
  "mensaje": "Aprobacion requerida para envio"
}
```
**Output**
```json
{
  "cycle_id": "2026-02",
  "estado": "aprobacion_pendiente",
  "timestamp": "2026-02-12T11:00:00Z"
}
```

### skill: director.receive_approval
**Input**
```json
{
  "cycle_id": "2026-02",
  "decision": "aprobar",
  "aprobados": ["2026-02_juan_perez_av_corrientes_1234"]
}
```
**Output**
```json
{
  "cycle_id": "2026-02",
  "estado": "aprobado",
  "timestamp": "2026-02-12T11:05:00Z"
}
```

## Skills del Agente de Operacion Mensual

### skill: operacion.run_cycle
**Input**
```json
{
  "cycle_id": "2026-02",
  "mes": "2026-02"
}
```
**Output**
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

## Skills del Agente de Reglas y Condiciones Especiales

### skill: reglas.derive
**Input**
```json
{
  "cycle_id": "2026-02",
  "tenant_id": "juan_perez",
  "source_md": "rules/tenants/juan_perez.md"
}
```
**Output**
```json
{
  "cycle_id": "2026-02",
  "tenant_id": "juan_perez",
  "derived_json": "rules/cache/tenants/juan_perez.json",
  "overrides": {
    "expensas": 35000
  },
  "formula": "precio_original * 0.85 + expensas",
  "timestamp": "2026-02-12T10:25:00Z"
}
```

## Skills del Agente de Correcciones

### skill: correcciones.apply
**Input**
```json
{
  "cycle_id": "2026-02",
  "receipt_id": "2026-02_juan_perez_av_corrientes_1234",
  "campo": "expensas",
  "valor": 42000,
  "motivo": "ajuste informado por el propietario"
}
```
**Output**
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

## Skills del Agente de Entrega y Auditoria

### skill: entrega.send_batch
**Input**
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
  ]
}
```
**Output**
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
