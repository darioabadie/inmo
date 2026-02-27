# Arquitectura agentica (5 agentes)

## 1) Agente Director (Control + UX)
**Responsabilidad**
- Punto unico de contacto por WhatsApp (operador e inquilinos).
- Mantiene el estado del ciclo: pendiente -> aprobado -> enviado.
- Decide que agente ejecuta cada paso.
- Presenta resumenes y solicita aprobaciones.

**Entradas**
- Mensajes de WhatsApp del operador.
- Resumenes/outputs de otros agentes.

**Salidas**
- Instrucciones a otros agentes.
- Solicitudes de aprobacion.
- Resumenes y notificaciones finales.

## 2) Agente de Operacion Mensual
**Responsabilidad**
- Ejecuta el ciclo completo mensual:
  - Historico -> pagos -> recibos.
- Genera paquete de resultados (montos, PDFs, errores).
- No envia: solo prepara.

**Entradas**
- Mes objetivo.
- Datos normalizados.

**Salidas**
- Lote de recibos PDF y metadatos.
- Resumen de procesados/omitidos/errores.

## 3) Agente de Reglas y Condiciones Especiales
**Responsabilidad**
- Lee reglas globales y por inquilino en .md.
- Interpreta formulas.
- Actualiza JSON derivado de reglas.
- Marca recibos manuales y aplica overrides.

**Entradas**
- `rules/global.md`
- `rules/tenants/<inquilino>.md`

**Salidas**
- JSON derivado de reglas.
- Overrides aplicables por inquilino.

## 4) Agente de Correcciones
**Responsabilidad**
- Atiende cambios monetarios solicitados por el operador.
- Aplica override en JSON derivado local.
- Regenera recibos afectados.
- Devuelve al Director para aprobacion.

**Entradas**
- Instruccion de cambio (recibo, campo, valor).

**Salidas**
- Recibo actualizado.
- Log de correccion.

## 5) Agente de Entrega y Auditoria
**Responsabilidad**
- Envia recibos aprobados por WhatsApp a inquilinos.
- Maneja reintentos y errores.
- Registra auditoria final del ciclo.

**Entradas**
- Lote aprobado de envios.

**Salidas**
- Estado de entrega por inquilino.
- Log final y resumen.

## Flujo principal
1) Director -> Operacion Mensual
2) Director -> Reglas/Condiciones
3) Director -> Aprobacion (operador)
4) Director -> Entrega/Auditoria

## Flujo de correcciones
1) Operador solicita cambio -> Director
2) Director -> Correcciones
3) Correcciones -> Director
4) Director solicita aprobacion
5) Entrega/Auditoria si aprobado

## Documentacion relacionada
- `docs/contratos_agentes.md`
