"""
Modelos especializados para el historial de pagos inmobiliarios.
"""
import datetime as dt
from dataclasses import dataclass
from typing import Optional, List, Any


@dataclass
class HistoricalRecord:
    """
    Registro mensual completo del historial de pagos.
    
    Representa una fila completa en la hoja 'historico' con todos los campos
    calculados para un mes específico de una propiedad.
    """
    # Campos de identificación (copiados directamente)
    nombre_inmueble: str
    dir_inmueble: str
    inquilino: str
    propietario: str
    mes_actual: str  # Formato: YYYY-MM
    
    # Nuevos campos de identificación de servicios
    nis: str
    gas_nro: str
    padron: str
    
    # Nuevo campo de fecha
    vencimiento_contrato: str  # Formato: YYYY-MM-DD
    
    # Campos de precios principales
    precio_final: float          # Total que paga el inquilino
    precio_original: float       # Precio base actualizado por inflación
    precio_descuento: float      # Precio con descuento aplicado
    descuento: str              # Porcentaje de descuento (ej: "15.0%")
    
    # Campos de cuotas adicionales
    cuotas_adicionales: float   # Total de cuotas de comisión + depósito
    cuotas_comision: float      # Solo cuotas de comisión inmobiliaria
    cuotas_deposito: float      # Solo cuotas de depósito
    detalle_cuotas: str         # Descripción detallada de las cuotas
    
    # Servicios adicionales
    municipalidad: float
    luz: float
    gas: float
    expensas: float
    
    # Comisiones y pagos
    comision_inmo: float        # Comisión de administración
    pago_prop: float           # Pago neto al propietario
    
    # Información de actualización
    actualizacion: str          # "SI" o "NO"
    porc_actual: str           # Porcentaje aplicado este mes (ej: "12.5%")
    
    # Contadores de proximidad
    meses_prox_actualizacion: int  # Meses hasta próxima actualización
    meses_prox_renovacion: int     # Meses hasta vencimiento del contrato
    
    def to_dict(self) -> dict:
        """Convierte el registro a diccionario para escribir en hoja de cálculo."""
        return {
            "nombre_inmueble": self.nombre_inmueble,
            "dir_inmueble": self.dir_inmueble,
            "inquilino": self.inquilino,
            "propietario": self.propietario,
            "mes_actual": self.mes_actual,
            "nis": self.nis,
            "gas_nro": self.gas_nro,
            "padron": self.padron,
            "vencimiento_contrato": self.vencimiento_contrato,
            "precio_final": self.precio_final,
            "precio_original": self.precio_original,
            "precio_descuento": self.precio_descuento,
            "descuento": self.descuento,
            "cuotas_adicionales": self.cuotas_adicionales,
            "cuotas_comision": self.cuotas_comision,
            "cuotas_deposito": self.cuotas_deposito,
            "detalle_cuotas": self.detalle_cuotas,
            "municipalidad": self.municipalidad,
            "luz": self.luz,
            "gas": self.gas,
            "expensas": self.expensas,
            "comision_inmo": self.comision_inmo,
            "pago_prop": self.pago_prop,
            "actualizacion": self.actualizacion,
            "porc_actual": self.porc_actual,
            "meses_prox_actualizacion": self.meses_prox_actualizacion,
            "meses_prox_renovacion": self.meses_prox_renovacion,
        }


@dataclass
class CalculationContext:
    """
    Contexto completo para realizar cálculos mensuales.
    
    Encapsula toda la información necesaria para generar un HistoricalRecord
    de un mes específico, evitando pasar múltiples parámetros individuales.
    """
    # Entidades principales (usar Any para evitar importaciones circulares)
    propiedad: Any              # Tipo: Propiedad
    contrato: Any               # Tipo: Contrato
    
    # Contexto temporal
    fecha_actual: dt.date       # Fecha del mes que se está calculando
    fecha_inicio_contrato: dt.date
    meses_desde_inicio: int     # Meses transcurridos desde inicio del contrato
    
    # Estado de precios
    precio_base_actual: float   # Precio base antes de este mes (para calcular actualizaciones)
    
    # Servicios adicionales
    municipalidad: float = 0.0
    luz: float = 0.0
    gas: float = 0.0
    expensas: float = 0.0
    descuento_porcentaje: float = 0.0
    monto_comision: float = None  # Monto fijo de comisión del inquilino (opcional)
    
    # Datos externos
    inflacion_df: Any = None         # DataFrame con datos de inflación
    
    @property
    def mes_actual_str(self) -> str:
        """Retorna el mes actual en formato YYYY-MM."""
        return f"{self.fecha_actual.year}-{self.fecha_actual.month:02d}"
    
    @property
    def meses_restantes_contrato(self) -> int:
        """Retorna los meses restantes hasta el vencimiento del contrato."""
        return max(0, self.contrato.duracion_meses - self.meses_desde_inicio)
    
    @property
    def contrato_vigente(self) -> bool:
        """Indica si el contrato sigue vigente en esta fecha."""
        return self.meses_desde_inicio < self.contrato.duracion_meses


@dataclass
class HistoricalSummary:
    """
    Resumen del procesamiento del historial.
    
    Contiene estadísticas y metadatos del proceso de generación del historial.
    """
    total_registros: int = 0
    propiedades_procesadas: int = 0
    propiedades_omitidas: int = 0
    fecha_limite: Optional[dt.date] = None
    errores: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errores is None:
            self.errores = []
    
    def add_error(self, propiedad: str, error: str):
        """Agrega un error al resumen."""
        self.errores.append(f"{propiedad}: {error}")
    
    def incrementar_procesada(self):
        """Incrementa el contador de propiedades procesadas."""
        self.propiedades_procesadas += 1
    
    def incrementar_omitida(self):
        """Incrementa el contador de propiedades omitidas."""
        self.propiedades_omitidas += 1
    
    def add_registros(self, cantidad: int):
        """Agrega registros al total."""
        self.total_registros += cantidad
    
    def __str__(self) -> str:
        """Representación en string del resumen."""
        return (
            f"Historial generado hasta {self.fecha_limite.strftime('%Y-%m') if self.fecha_limite else 'N/A'}\n"
            f"Total registros: {self.total_registros}\n"
            f"Propiedades procesadas: {self.propiedades_procesadas}\n"
            f"Propiedades omitidas: {self.propiedades_omitidas}\n"
            f"Errores: {len(self.errores)}"
        )


@dataclass 
class PropertyHistoricalData:
    """
    Datos históricos de una propiedad específica.
    
    Contiene el estado del último registro histórico existente para
    permitir continuación incremental del historial.
    """
    nombre_propiedad: str
    ultimo_mes: str                    # Último mes procesado (YYYY-MM)
    ultimo_precio_base: float          # Último precio_original registrado
    registros_existentes: List[dict]   # Lista de registros históricos existentes
    
    @property
    def tiene_historico(self) -> bool:
        """Indica si la propiedad tiene registros históricos previos."""
        return bool(self.ultimo_mes and self.ultimo_precio_base > 0)
    
    @property
    def ultima_fecha(self) -> Optional[dt.date]:
        """Retorna la fecha del último mes procesado."""
        if not self.ultimo_mes:
            return None
        try:
            y, m = map(int, self.ultimo_mes.split("-"))
            return dt.date(y, m, 1)
        except ValueError:
            return None
