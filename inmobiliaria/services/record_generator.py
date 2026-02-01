"""
Generador de registros mensuales individuales.
Responsable de crear un HistoricalRecord completo para un mes específico.
"""
import logging
from typing import Dict, Optional

from ..domain.historical_models import HistoricalRecord, CalculationContext
from ..services.calculations import calcular_comision, calcular_cuotas_detalladas
from .historical_calculations import HistoricalCalculations
from dateutil.relativedelta import relativedelta


class MonthlyRecordGenerator:
    """
    Genera registros mensuales individuales del historial.
    
    Responsabilidades:
    - Crear un HistoricalRecord completo para un mes específico
    - Aplicar todas las reglas de negocio y cálculos
    - Formatear correctamente todos los campos
    """
    
    def __init__(self):
        self.calculations = HistoricalCalculations()
    
    def generate_monthly_record(self, context: CalculationContext) -> HistoricalRecord:
        """
        Genera un registro mensual completo.
        
        Args:
            context: Contexto con toda la información necesaria para el cálculo
            
        Returns:
            HistoricalRecord completo para el mes especificado
        """
        # 1. Calcular actualización de precio si corresponde
        precio_base_actualizado, porc_actual, aplica_actualizacion = self.calculations.calculate_price_update(context)
        
        # 2. Calcular descuento
        factor_descuento = 1 - (context.descuento_porcentaje / 100)
        precio_descuento = round(precio_base_actualizado * factor_descuento, 2)
        
        # 3. Calcular comisión inmobiliaria sobre alquiler
        comision_inmo_alquiler = calcular_comision(context.contrato.comision_inmo, precio_descuento)
        
        # 4. Calcular cuotas adicionales con detalle
        cuotas_detalle = calcular_cuotas_detalladas(
            precio_descuento,
            context.contrato.comision or "Pagado",
            context.contrato.deposito or "Pagado",
            context.meses_desde_inicio + 1,  # mes_actual 1-based
            context.monto_comision  # Monto fijo de comisión (opcional)
        )
        
        cuotas_adicionales = float(cuotas_detalle['total_cuotas'])
        cuotas_comision = float(cuotas_detalle['cuotas_comision'])
        cuotas_deposito = float(cuotas_detalle['cuotas_deposito'])
        detalle_cuotas = str(cuotas_detalle['detalle_descripcion'])

        # 4.1 Calcular comisión inmobiliaria sobre depósito (si aplica)
        comision_inmo_deposito = 0.0
        if cuotas_deposito > 0:
            comision_inmo_deposito = calcular_comision(context.contrato.comision_inmo, cuotas_deposito)

        comision_inmo = round(comision_inmo_alquiler + comision_inmo_deposito, 2)
        
        # 5. Calcular pagos finales
        pago_prop = round(
            precio_descuento
            + cuotas_deposito
            + context.municipalidad
            + context.luz
            + context.gas
            + context.expensas
            - comision_inmo,
            2
        )
        precio_final = precio_descuento + cuotas_adicionales + context.municipalidad + context.luz + context.gas + context.expensas
        
        # 6. Calcular proximidades
        meses_prox_actualizacion, meses_prox_renovacion = self.calculations.calculate_proximity_months(context)
        
        # 7. Formatear campos de salida
        actualizacion_str = "SI" if aplica_actualizacion else "NO"
        porc_actual_output = porc_actual if aplica_actualizacion else ""
        descuento_str = f"{context.descuento_porcentaje:.1f}%"
        
        # 8. Calcular vencimiento contrato
        fecha_vencimiento = context.fecha_inicio_contrato + relativedelta(months=context.contrato.duracion_meses) - relativedelta(days=1)
        vencimiento_str = fecha_vencimiento.strftime("%Y-%m-%d")

        # 9. Crear el registro completo
        return HistoricalRecord(
            # Campos de identificación
            nombre_inmueble=context.propiedad.nombre,
            dir_inmueble=context.propiedad.direccion,
            inquilino=context.propiedad.inquilino,
            propietario=context.propiedad.propietario,
            mes_actual=context.mes_actual_str,
            
            # Nuevos campos
            nis=context.propiedad.nis,
            gas_nro=context.propiedad.gas_nro,
            padron=context.propiedad.padron,
            vencimiento_contrato=vencimiento_str,
            
            # Campos de precios principales
            precio_final=precio_final,
            precio_original=precio_base_actualizado,
            precio_descuento=precio_descuento,
            descuento=descuento_str,
            
            # Campos de cuotas adicionales
            cuotas_adicionales=cuotas_adicionales,
            cuotas_comision=cuotas_comision,
            cuotas_deposito=cuotas_deposito,
            detalle_cuotas=detalle_cuotas,
            
            # Servicios adicionales
            municipalidad=context.municipalidad,
            luz=context.luz,
            gas=context.gas,
            expensas=context.expensas,
            
            # Comisiones y pagos
            comision_inmo=comision_inmo,
            pago_prop=pago_prop,
            
            # Información de actualización
            actualizacion=actualizacion_str,
            porc_actual=porc_actual_output,
            
            # Contadores de proximidad
            meses_prox_actualizacion=meses_prox_actualizacion,
            meses_prox_renovacion=meses_prox_renovacion
        )
    
    def create_context_for_month(self, 
                                propiedad,
                                contrato,
                                fecha_actual,
                                precio_base_actual: float,
                                inflacion_df,
                                municipalidad: float = 0.0,
                                luz: float = 0.0,
                                gas: float = 0.0,
                                expensas: float = 0.0,
                                descuento_porcentaje: float = 0.0,
                                monto_comision: Optional[float] = None) -> CalculationContext:
        """
        Crea un contexto de cálculo para un mes específico.
        
        Args:
            propiedad: Entidad Propiedad
            contrato: Entidad Contrato
            fecha_actual: Fecha del mes a calcular
            precio_base_actual: Precio base antes de este mes
            inflacion_df: DataFrame con datos de inflación
            municipalidad: Gastos municipales
            luz: Gastos de luz
            gas: Gastos de gas
            expensas: Expensas
            descuento_porcentaje: Porcentaje de descuento
            monto_comision: Monto fijo de comisión del inquilino (opcional)
            
        Returns:
            CalculationContext configurado para el mes
        """
        import datetime as dt
        
        # Parsear fecha de inicio del contrato
        fecha_inicio_contrato = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
        
        # Calcular meses desde inicio
        meses_desde_inicio = self.calculations.calculate_months_since_start(fecha_actual, fecha_inicio_contrato)
        
        return CalculationContext(
            propiedad=propiedad,
            contrato=contrato,
            fecha_actual=fecha_actual,
            fecha_inicio_contrato=fecha_inicio_contrato,
            meses_desde_inicio=meses_desde_inicio,
            precio_base_actual=precio_base_actual,
            municipalidad=municipalidad,
            luz=luz,
            gas=gas,
            expensas=expensas,
            descuento_porcentaje=descuento_porcentaje,
            monto_comision=monto_comision,
            inflacion_df=inflacion_df
        )
    
    def validate_context(self, context: CalculationContext) -> bool:
        """
        Valida que el contexto sea válido para generar un registro.
        
        Args:
            context: Contexto a validar
            
        Returns:
            True si el contexto es válido
        """
        # Verificar que el contrato sigue vigente
        if not self.calculations.validate_contract_active(context):
            logging.warning(f"[VALIDACIÓN] Contrato vencido para {context.propiedad.nombre}")
            return False
        
        # Verificar que el precio base sea válido
        if context.precio_base_actual <= 0:
            logging.warning(f"[VALIDACIÓN] Precio base inválido para {context.propiedad.nombre}: {context.precio_base_actual}")
            return False
        
        # Verificar que la fecha sea válida (debe ser posterior al inicio del contrato)
        if context.fecha_actual < context.fecha_inicio_contrato:
            logging.warning(f"[VALIDACIÓN] Fecha inválida para {context.propiedad.nombre}: {context.fecha_actual}")
            return False
        
        return True
