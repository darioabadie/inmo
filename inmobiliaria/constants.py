"""
Constantes y configuraciones para el módulo historical.
"""
from typing import Dict

# Mapeo de frecuencias de actualización a meses
FREQUENCY_MONTHS_MAP: Dict[str, int] = {
    "trimestral": 3,
    "cuatrimestral": 4, 
    "semestral": 6,
    "anual": 12
}

# Frecuencia por defecto si no se especifica o es inválida
DEFAULT_FREQUENCY = "trimestral"

# Valores por defecto para campos opcionales
DEFAULT_VALUES = {
    "comision": "Pagado",
    "deposito": "Pagado",
    "municipalidad": 0.0,
    "luz": 0.0,
    "gas": 0.0,
    "expensas": 0.0,
    "descuento": "0%"
}

# Campos obligatorios en el maestro
REQUIRED_FIELDS = [
    "nombre_inmueble",
    "dir_inmueble", 
    "inquilino",
    "propietario",
    "precio_original",
    "fecha_inicio_contrato",
    "duracion_meses",
    "actualizacion",
    "indice",
    "comision_inmo"
]

# Configuración de logging
LOGGING_CONFIG = {
    "level": "WARNING",
    "format": "%(levelname)s: %(message)s"
}

# Configuración de Google Sheets
SHEET_CONFIG = {
    "historico_sheet_name": "historico",
    "maestro_sheet_name": "administracion",  # Nombre por defecto, puede ser sobrescrito por config.SHEET_MAESTRO
    "expected_columns": 22  # Número de columnas esperadas en la hoja historico
}

# Índices de actualización válidos
VALID_INDICES = ["IPC", "ICL"]  # Los porcentajes fijos se validan dinámicamente

# Configuraciones de interés para cuotas fraccionadas
INTEREST_RATES = {
    "2 cuotas": 0.10,  # 10% de interés
    "3 cuotas": 0.20   # 20% de interés
}

# Límites y validaciones
VALIDATION_LIMITS = {
    "max_duracion_meses": 60,      # Máximo 5 años
    "min_precio_original": 1000,   # Mínimo $1000
    "max_descuento_porcentaje": 50 # Máximo 50% de descuento
}
