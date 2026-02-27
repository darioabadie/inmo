# Requerimientos funcionales

## Proposito
Automatizar la operacion inmobiliaria mensual usando WhatsApp como canal principal, con calculos de pagos y recibos, aprobacion previa al envio, y manejo de condiciones especiales por inquilino.

## Usuarios
- Agente inmobiliario (operador): controla, aprueba y ajusta.
- Inquilino (destinatario): recibe recibos por WhatsApp.

## Objetivos del usuario (agente inmobiliario)
- Generar pagos mensuales y recibos sin tareas manuales repetitivas.
- Aprobar el envio de recibos antes de que salgan por WhatsApp.
- Solicitar correcciones puntuales en campos monetarios de un recibo.
- Gestionar condiciones especiales por inquilino mediante reglas en archivos.
- Recibir alertas de errores o contratos relevantes.

## Alcance funcional
- Generacion de pagos mensuales.
- Actualizacion de historial.
- Generacion de recibos PDF.
- Envio de recibos por WhatsApp con aprobacion previa.
- Correccion de campos monetarios con persistencia local (sin editar Google Sheets).
- Condiciones especiales por inquilino en archivos de reglas.
- Logs y auditoria de acciones.

## Canal principal
- WhatsApp es el medio principal de comunicacion con el operador y los inquilinos.

## Flujo general (journey del agente inmobiliario)

### 1) Onboarding
1. El operador inicia el asistente por WhatsApp.
2. El asistente verifica acceso a datos y configuracion base.
3. El operador confirma el mes de trabajo y activa el modo automatico.

### 2) Ciclo mensual automatico
1. El asistente actualiza el historial hasta el mes actual.
2. Genera pagos del mes.
3. Genera recibos PDF del mes.
4. Prepara el lote de envio.
5. Solicita aprobacion por WhatsApp.
6. Envia recibos a inquilinos aprobados.
7. Registra envios y errores.

### 3) Operacion manual (a demanda)
1. El operador solicita una accion puntual por WhatsApp.
2. El asistente ejecuta la accion.
3. Reporta el resultado y solicita aprobacion si corresponde.

### 4) Correcciones puntuales
1. El operador indica el recibo y el campo monetario a cambiar.
2. El asistente actualiza el valor (persistencia local).
3. Regenera el recibo.
4. Solicita aprobacion.
5. Envia el recibo si es aprobado.

## Reglas y condiciones especiales

### Reglas generales y por inquilino
- Reglas en archivos .md.
- Hay reglas globales por defecto y reglas especificas por inquilino.
- El asistente interpreta el .md y actualiza un JSON derivado.

### Principios
- Las reglas especiales modifican el calculo de un recibo.
- Si existe regla por inquilino, prevalece sobre la global.
- Los cambios se registran en logs.
- El asistente NO edita Google Sheets.

## Aprobaciones
- Todo envio por WhatsApp requiere aprobacion previa.
- Recibos con condiciones especiales siempre requieren aprobacion.
- El operador puede aprobar un lote completo o parcial.

## Campos editables
- Solo campos monetarios (por ejemplo: precio_descuento, expensas, municipalidad, luz, gas, cuotas_deposito, cuotas_comision).

## Restricciones
- Google Sheets (planilla administracion e historico) es solo lectura para el asistente.
- Las reglas especiales se gestionan fuera de la planilla.

## Mensajes esperados por WhatsApp (ejemplos)
- "Pagos 2026-02 generados. 120 procesados, 3 omitidos."
- "Recibos 2026-02 listos. Pendientes de aprobacion."
- "Aprobacion requerida: 120 recibos. Responde APROBAR o lista parcial."
- "Recibos enviados: 118. Errores: 2."

## Criterios de exito
- El operador recibe resumen claro de resultados y errores.
- Los recibos se envian solo con aprobacion.
- Las condiciones especiales se aplican correctamente.
- Las correcciones se reflejan en los recibos generados.
