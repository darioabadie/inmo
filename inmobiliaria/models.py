"""
Modelos y entidades principales del dominio inmobiliario.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Propiedad:
    nombre: str
    direccion: str
    propietario: str
    inquilino: str
    nis: Optional[str] = ""
    gas_nro: Optional[str] = ""
    padron: Optional[str] = ""
    # Agregar más campos según necesidad

@dataclass
class Contrato:
    fecha_inicio: str
    duracion_meses: int
    precio_original: float
    actualizacion: str
    indice: str
    comision_inmo: str
    comision: Optional[str] = None
    deposito: Optional[str] = None
    # Agregar más campos según necesidad

@dataclass
class Pago:
    mes: str
    precio_mes_actual: float
    comision_inmo: float
    pago_prop: float
    # Agregar más campos según necesidad
