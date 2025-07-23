import requests

import datetime as dt
import requests
from dateutil.relativedelta import relativedelta

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

def calcular_precio_base_acumulado(precio_original: float,
                                  actualizacion: str,
                                  indice: str,
                                  df_infl: pd.DataFrame,
                                  fecha_inicio: dt.date,
                                  fecha_ref: dt.date) -> tuple[float, float, bool]:
    """
    Calcula el precio base aplicando TODOS los ciclos acumulados con efecto compuesto.
    
    Returns:
        tuple: (precio_base_final, porcentaje_ultimo_ciclo, aplica_actualizacion_este_mes)
    """
    # Validar frecuencia
    freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
    freq_meses = freq_map.get(actualizacion.lower(), 3)
    
    # Calcular meses desde inicio y ciclos
    meses_desde_inicio = (fecha_ref.year - fecha_inicio.year) * 12 + (fecha_ref.month - fecha_inicio.month)
    ciclos_cumplidos = meses_desde_inicio // freq_meses
    resto = meses_desde_inicio % freq_meses
    aplica_actualizacion = resto == 0 and ciclos_cumplidos > 0
    
    # Si no hay ciclos cumplidos, retornar precio original
    if ciclos_cumplidos == 0:
        return precio_original, 0.0, False
    
    # Calcular factor acumulado según el tipo de índice
    factor_total = 1.0
    porcentaje_ultimo_ciclo = 0.0
    
    if indice.upper() == "IPC":
        # Para IPC: aplicar inflación acumulada por cada ciclo
        for ciclo in range(ciclos_cumplidos):
            fecha_corte = fecha_inicio + relativedelta(months=(ciclo + 1) * freq_meses)
            factor_ciclo = inflacion_acumulada(df_infl, fecha_corte, freq_meses)
            factor_total *= factor_ciclo
            
            # Si es el último ciclo y aplica actualización este mes, guardar el porcentaje
            if ciclo == ciclos_cumplidos - 1 and aplica_actualizacion:
                porcentaje_ultimo_ciclo = (factor_ciclo - 1) * 100
    
    elif indice.upper() == "ICL":
        # Para ICL: aplicar factor por cada período
        for ciclo in range(ciclos_cumplidos):
            fecha_inicio_ciclo = fecha_inicio + relativedelta(months=ciclo * freq_meses)
            fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=freq_meses)
            
            try:
                factor_ciclo = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
                factor_total *= factor_ciclo
                
                # Si es el último ciclo y aplica actualización este mes, guardar el porcentaje
                if ciclo == ciclos_cumplidos - 1 and aplica_actualizacion:
                    porcentaje_ultimo_ciclo = (factor_ciclo - 1) * 100
            except Exception:
                # Si falla la API, usar factor 1.0 para este ciclo
                factor_ciclo = 1.0
                factor_total *= factor_ciclo
    
    else:
        # Para porcentaje fijo: aplicar compuestamente
        try:
            pct = float(indice.replace("%", "").replace(",", "."))
            factor_ciclo = 1 + pct / 100
            factor_total = factor_ciclo ** ciclos_cumplidos
            
            # Si aplica actualización este mes, el porcentaje es el fijo
            if aplica_actualizacion:
                porcentaje_ultimo_ciclo = pct
        except ValueError:
            # Si el porcentaje es inválido, no aplicar ajuste
            factor_total = 1.0
    
    precio_base_final = round(precio_original * factor_total, 2)
    
    return precio_base_final, porcentaje_ultimo_ciclo, aplica_actualizacion

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
