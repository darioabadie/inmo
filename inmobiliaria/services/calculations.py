import requests

import datetime as dt
import requests

def traer_factor_icl(fecha_inicio: dt.date, fecha_hasta: dt.date) -> float:
    """Obtiene el factor de actualización ICL desde la API del BCRA."""
    url = (
        f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/40?desde={fecha_inicio.strftime('%Y-%m-%d')}&hasta={fecha_hasta.strftime('%Y-%m-%d')}"
    )
    res = requests.get(url, timeout=10, verify=False)
    res.raise_for_status()
    data = res.json()["results"]
    if not data:
        raise ValueError("No se encontraron datos de ICL para el rango dado.")
    valor_inicio = data[-1]["valor"]
    valor_final = data[0]["valor"]
    return float(valor_final) / float(valor_inicio)
"""
Funciones de cálculo de precios, comisiones y cuotas adicionales.
"""
import datetime as dt
import pandas as pd
import requests
from .inflation import inflacion_acumulada

def precio_ajustado(precio_anterior: float,
                    frecuencia: str,
                    indice: str,
                    df_infl: pd.DataFrame,
                    fecha_ref: dt.date,
                    fecha_inicio: dt.date | None = None) -> float:
    """Devuelve el precio ajustado según la política de la fila."""
    if frecuencia not in {"trimestral", "cuatrimestral", "semestral", "anual"}:
        return precio_anterior
    meses = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}[frecuencia]
    if indice.upper() == "IPC":
        factor = inflacion_acumulada(df_infl, fecha_ref, meses)
    else:  # Porcentaje fijo: "10 %", "7.5%", etc.
        pct = float(indice.strip().replace("%", "").replace(",", "."))
        factor = 1 + pct / 100
    return round(precio_anterior * factor, 2)

def calcular_comision(comision_str: str, precio_mes: float) -> float:
    try:
        pct = float(comision_str.strip().replace("%", "").replace(",", "."))
        return round(precio_mes * pct / 100, 2)
    except (ValueError, AttributeError):
        raise ValueError(f"Formato de comisión inválido: '{comision_str}'")

def calcular_cuotas_adicionales(precio_base: float, 
                               comision_inquilino: str, 
                               deposito: str, 
                               mes_actual: int) -> float:
    monto_adicional = 0.0
    if comision_inquilino == "2 cuotas" and mes_actual <= 2:
        monto_adicional += precio_base / 2
    elif comision_inquilino == "3 cuotas" and mes_actual <= 3:
        monto_adicional += precio_base / 3
    if deposito == "2 cuotas" and mes_actual <= 2:
        monto_adicional += precio_base / 2
    elif deposito == "3 cuotas" and mes_actual <= 3:
        monto_adicional += precio_base / 3
    return round(monto_adicional, 2)
