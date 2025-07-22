"""
Funciones para obtención y cálculo de inflación.
"""
import pandas as pd
import numpy as np
import requests
from ..config import API_INFLACION
import datetime as dt

def traer_inflacion() -> pd.DataFrame:
    """Devuelve DataFrame con columnas fecha (datetime) y valor (% mensual)."""
    res = requests.get(API_INFLACION, timeout=10)
    res.raise_for_status()
    df = pd.DataFrame(res.json())
    df["fecha"] = pd.to_datetime(df["fecha"])
    df.sort_values("fecha", inplace=True)
    return df

def inflacion_acumulada(df_infl: pd.DataFrame, hasta: dt.date, meses: int) -> float:
    """
    Cálculo compuesto de inflación en los `meses` previos al último dato <= hasta.
    Retorna un factor multiplicativo (ej.: 1.083 para 8,3 %).
    """
    limite = pd.Timestamp(hasta.replace(day=1))  # inicio del mes de referencia
    ultimo = df_infl[df_infl["fecha"] <= limite].tail(meses)
    factores = (1 + ultimo["valor"].astype(float) / 100)
    producto = factores.prod()
    return float(np.asarray(producto).item())
