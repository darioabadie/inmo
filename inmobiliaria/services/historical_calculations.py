"""
Servicio de cálculos especializados para el historial.
Contiene toda la lógica de cálculo de actualizaciones, proximidades y validaciones.
"""
import datetime as dt
import logging
from typing import Tuple
from dateutil.relativedelta import relativedelta

from ..constants import FREQUENCY_MONTHS_MAP, DEFAULT_FREQUENCY
from ..domain.historical_models import CalculationContext
from ..services.inflation import inflacion_acumulada
from ..services.calculations import traer_factor_icl


class HistoricalCalculations:
    """
    Servicio que encapsula todos los cálculos relacionados con el historial.
    
    Responsabilidades:
    - Cálculo de actualizaciones de precios por índice (IPC, ICL, porcentaje fijo)
    - Cálculo de meses de proximidad (actualización, renovación)
    - Validación de frecuencias y configuraciones
    """
    
    def get_frequency_months(self, actualizacion: str) -> int:
        """
        Obtiene el número de meses para una frecuencia de actualización.
        
        Args:
            actualizacion: Frecuencia de actualización ("trimestral", "semestral", etc.)
            
        Returns:
            Número de meses correspondiente a la frecuencia
        """
        return FREQUENCY_MONTHS_MAP.get(actualizacion.lower(), 
                                       FREQUENCY_MONTHS_MAP[DEFAULT_FREQUENCY])
    
    def should_apply_update(self, context: CalculationContext) -> bool:
        """
        Determina si corresponde aplicar actualización en este mes.
        
        Args:
            context: Contexto de cálculo mensual
            
        Returns:
            True si corresponde actualización este mes
        """
        freq_meses = self.get_frequency_months(context.contrato.actualizacion)
        return (context.meses_desde_inicio > 0 and 
                context.meses_desde_inicio % freq_meses == 0)
    
    def calculate_price_update(self, context: CalculationContext) -> Tuple[float, str, bool]:
        """
        Calcula si corresponde actualización en este mes específico y el nuevo precio_base.
        
        Args:
            context: Contexto de cálculo mensual
            
        Returns:
            Tuple[nuevo_precio_base, porcentaje_aplicado, aplica_actualizacion]
        """
        if not self.should_apply_update(context):
            return context.precio_base_actual, "", False
        
        freq_meses = self.get_frequency_months(context.contrato.actualizacion)
        
        # Calcular el factor de actualización según el índice
        try:
            if context.contrato.indice.upper() == "IPC":
                factor, porcentaje = self._calculate_ipc_update(context, freq_meses)
            elif context.contrato.indice.upper() == "ICL":
                factor, porcentaje = self._calculate_icl_update(context, freq_meses)
            else:
                factor, porcentaje = self._calculate_fixed_percentage_update(context)
                
            nuevo_precio = context.precio_base_actual * factor
            return round(nuevo_precio, 2), f"{porcentaje:.2f}%", True
            
        except Exception as e:
            logging.warning(f"[ACTUALIZACIÓN] Error calculando actualización {context.contrato.indice}: {e}")
            return context.precio_base_actual, "", False
    
    def _calculate_ipc_update(self, context: CalculationContext, freq_meses: int) -> Tuple[float, float]:
        """Calcula actualización por IPC."""
        factor = inflacion_acumulada(context.inflacion_df, context.fecha_actual, freq_meses)
        porcentaje = (factor - 1) * 100
        return factor, porcentaje
    
    def _calculate_icl_update(self, context: CalculationContext, freq_meses: int) -> Tuple[float, float]:
        """Calcula actualización por ICL."""
        fecha_inicio_ciclo = context.fecha_actual - relativedelta(months=freq_meses)
        fecha_fin_ciclo = context.fecha_actual
        
        factor = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
        porcentaje = (factor - 1) * 100
        return factor, porcentaje
    
    def _calculate_fixed_percentage_update(self, context: CalculationContext) -> Tuple[float, float]:
        """Calcula actualización por porcentaje fijo."""
        porcentaje = float(context.contrato.indice.replace('%', '').replace(',', '.').strip())
        factor = 1 + (porcentaje / 100)
        return factor, porcentaje
    
    def calculate_proximity_months(self, context: CalculationContext) -> Tuple[int, int]:
        """
        Calcula meses hasta próxima actualización y renovación.
        
        Args:
            context: Contexto de cálculo mensual
            
        Returns:
            Tuple[meses_prox_actualizacion, meses_prox_renovacion]
        """
        freq_meses = self.get_frequency_months(context.contrato.actualizacion)
        
        # Meses hasta próxima actualización
        if self.should_apply_update(context):
            # Estamos en mes de actualización, próxima en un ciclo completo
            meses_prox_actualizacion = freq_meses
        else:
            # Calcular cuántos meses faltan para la próxima actualización
            resto = context.meses_desde_inicio % freq_meses
            meses_prox_actualizacion = freq_meses - resto
        
        # Meses hasta renovación/vencimiento
        meses_prox_renovacion = max(0, context.contrato.duracion_meses - context.meses_desde_inicio)
        
        return meses_prox_actualizacion, meses_prox_renovacion
    
    def validate_contract_active(self, context: CalculationContext) -> bool:
        """
        Valida si el contrato sigue vigente en la fecha actual.
        
        Args:
            context: Contexto de cálculo mensual
            
        Returns:
            True si el contrato sigue vigente
        """
        return context.meses_desde_inicio < context.contrato.duracion_meses
    
    def calculate_months_since_start(self, fecha_actual: dt.date, fecha_inicio: dt.date) -> int:
        """
        Calcula los meses transcurridos desde el inicio del contrato.
        
        Args:
            fecha_actual: Fecha del mes que se está calculando
            fecha_inicio: Fecha de inicio del contrato
            
        Returns:
            Número de meses transcurridos
        """
        return (fecha_actual.year - fecha_inicio.year) * 12 + (fecha_actual.month - fecha_inicio.month)
    
    def get_next_month_date(self, fecha_actual: dt.date) -> dt.date:
        """
        Obtiene la fecha del mes siguiente.
        
        Args:
            fecha_actual: Fecha actual
            
        Returns:
            Fecha del mes siguiente (siempre día 1)
        """
        if fecha_actual.month == 12:
            return dt.date(fecha_actual.year + 1, 1, 1)
        else:
            return dt.date(fecha_actual.year, fecha_actual.month + 1, 1)
