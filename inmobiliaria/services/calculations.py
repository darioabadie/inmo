import requests

import datetime as dt
import requests
from dateutil.relativedelta import relativedelta

def traer_factor_icl(fecha_inicio: dt.date, fecha_hasta: dt.date) -> float:
    """
    Obtiene el factor de actualización ICL desde la API del BCRA para un período específico.
    
    Args:
        fecha_inicio: Fecha de inicio del período (inclusive)
        fecha_hasta: Fecha de fin del período (inclusive)
        
    Returns:
        float: Factor multiplicativo de actualización ICL (ej: 1.125 para 12.5% de incremento)
        
    Raises:
        ValueError: Si no se encuentran datos para el rango dado
        requests.RequestException: Si falla la consulta a la API
        
    Note:
        La API del BCRA retorna los datos en orden cronológico inverso (más reciente primero).
        Serie 40 = Índice del Costo Laboral (ICL)
    """
    # Formatear fechas para la API
    fecha_desde_str = fecha_inicio.strftime('%Y-%m-%d')
    fecha_hasta_str = fecha_hasta.strftime('%Y-%m-%d')
    
    url = (
        f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/40"
        f"?desde={fecha_desde_str}&hasta={fecha_hasta_str}"
    )
    
    try:
        res = requests.get(url, timeout=15, verify=False)
        res.raise_for_status()
        data = res.json()
        
        if "results" not in data or not data["results"]:
            raise ValueError(
                f"No se encontraron datos de ICL para el período {fecha_desde_str} a {fecha_hasta_str}"
            )
        
        results = data["results"]
        
        # Los datos vienen ordenados cronológicamente inverso (más reciente primero)
        # Necesitamos el valor más antiguo (último en la lista) y el más reciente (primero)
        valor_final = float(results[0]["valor"])    # Valor más reciente (fecha_hasta)
        valor_inicio = float(results[-1]["valor"])  # Valor más antiguo (fecha_inicio)
        
        if valor_inicio <= 0:
            raise ValueError(f"Valor ICL inicial inválido: {valor_inicio}")
        
        factor = valor_final / valor_inicio
        
        # Validación de sanidad del factor (debe estar entre 0.5 y 3.0 para ser realista)
        if factor < 0.5 or factor > 3.0:
            import warnings
            warnings.warn(
                f"Factor ICL fuera de rango esperado: {factor:.4f} "
                f"para período {fecha_desde_str} a {fecha_hasta_str}"
            )
        
        return factor
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Error al consultar API BCRA para ICL: {e}")
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"Error procesando respuesta API BCRA para ICL: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado al obtener ICL: {e}")

def calcular_factor_icl_acumulado_detallado(precio_original: float,
                                           fecha_inicio: dt.date,
                                           fecha_ref: dt.date,
                                           freq_meses: int,
                                           debug: bool = False) -> tuple[float, list, float]:
    """
    Calcula el factor ICL acumulado con detalle de cada ciclo para debugging.
    
    Args:
        precio_original: Precio inicial del contrato
        fecha_inicio: Fecha de inicio del contrato  
        fecha_ref: Fecha de referencia para el cálculo
        freq_meses: Frecuencia de actualización en meses
        debug: Si mostrar información de debug
        
    Returns:
        tuple: (precio_final, lista_factores_por_ciclo, factor_ultimo_ciclo)
    """
    meses_desde_inicio = (fecha_ref.year - fecha_inicio.year) * 12 + (fecha_ref.month - fecha_inicio.month)
    ciclos_cumplidos = meses_desde_inicio // freq_meses
    
    if ciclos_cumplidos == 0:
        return precio_original, [], 0.0
    
    factor_total = 1.0
    factores_por_ciclo = []
    factor_ultimo_ciclo = 0.0
    
    if debug:
        print(f"🔍 Debug ICL Acumulado:")
        print(f"   Precio original: ${precio_original:,.2f}")
        print(f"   Período: {fecha_inicio} a {fecha_ref}")
        print(f"   Meses transcurridos: {meses_desde_inicio}")
        print(f"   Frecuencia: cada {freq_meses} meses")
        print(f"   Ciclos cumplidos: {ciclos_cumplidos}")
        print()
    
    for ciclo in range(ciclos_cumplidos):
        fecha_inicio_ciclo = fecha_inicio + relativedelta(months=ciclo * freq_meses)
        fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=freq_meses)
        
        try:
            factor_ciclo = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
            factor_total *= factor_ciclo
            
            ciclo_info = {
                'ciclo': ciclo + 1,
                'fecha_inicio': fecha_inicio_ciclo,
                'fecha_fin': fecha_fin_ciclo,
                'factor': factor_ciclo,
                'incremento_pct': (factor_ciclo - 1) * 100,
                'precio_acumulado': precio_original * factor_total
            }
            factores_por_ciclo.append(ciclo_info)
            
            if debug:
                print(f"   Ciclo {ciclo + 1}: {fecha_inicio_ciclo} → {fecha_fin_ciclo}")
                print(f"      Factor: {factor_ciclo:.4f} ({ciclo_info['incremento_pct']:+.1f}%)")
                print(f"      Precio acumulado: ${ciclo_info['precio_acumulado']:,.2f}")
            
            # Guardar el factor del último ciclo
            if ciclo == ciclos_cumplidos - 1:
                factor_ultimo_ciclo = factor_ciclo
                
        except Exception as e:
            if debug:
                print(f"   ❌ Error en ciclo {ciclo + 1}: {e}")
            # En caso de error, usar factor neutro
            factor_ciclo = 1.0
            factor_total *= factor_ciclo
            factor_ultimo_ciclo = 1.0
    
    precio_final = precio_original * factor_total
    
    if debug:
        print(f"\n📊 Resultado final:")
        print(f"   Factor total acumulado: {factor_total:.4f}")
        print(f"   Precio final: ${precio_final:,.2f}")
        print(f"   Incremento total: {(factor_total - 1) * 100:+.1f}%")
        print()
    
    return precio_final, factores_por_ciclo, factor_ultimo_ciclo
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
