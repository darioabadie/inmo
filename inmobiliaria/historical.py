#!/usr/bin/env python3
"""
Genera el historial completo de pagos desde el inicio de cada contrato hasta un mes límite.
Cada actualización se basa en el último precio_base registrado, permitiendo ajustes manuales.
"""

import argparse
import datetime as dt
from pathlib import Path
import logging
import warnings
import urllib3
from typing import Dict, List, Optional, Tuple
from dateutil.relativedelta import relativedelta

from . import config
from .models import Propiedad, Contrato, Pago
from . import utils
from .services.google_sheets import get_gspread_client
from .services.inflation import traer_inflacion
from .services.calculations import precio_ajustado, calcular_comision, calcular_cuotas_adicionales, traer_factor_icl

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _parse_args() -> argparse.Namespace:
    today = dt.date.today()
    parser = argparse.ArgumentParser(description="Genera el historial completo de pagos")
    parser.add_argument("--hasta", help="Mes límite en formato AAAA-MM",
                        default=f"{today.year}-{today.month:02}")
    return parser.parse_args()


def leer_historico_existente(sh) -> Dict[str, Dict]:
    """
    Lee el sheet 'historico' existente y retorna el último precio_original por propiedad.
    
    Returns:
        Dict con estructura: {nombre_inmueble: {
            'ultimo_mes': 'YYYY-MM',
            'ultimo_precio_base': float,  # Mantiene nombre por compatibilidad
            'registros_existentes': List[Dict]
        }}
    """
    try:
        ws_historico = sh.worksheet("historico")
        registros_existentes = ws_historico.get_all_records()
        
        historico_por_propiedad = {}
        
        for registro in registros_existentes:
            nombre = registro.get("nombre_inmueble", "")
            mes = registro.get("mes_actual", "")
            # Intentar leer precio_original primero, si no existe usar precio_base (compatibilidad)
            precio_base = float(registro.get("precio_original", 0)) or float(registro.get("precio_base", 0))
            
            if nombre not in historico_por_propiedad:
                historico_por_propiedad[nombre] = {
                    'ultimo_mes': mes,
                    'ultimo_precio_base': precio_base,
                    'registros_existentes': []
                }
            
            # Mantener el último mes cronológicamente
            if mes > historico_por_propiedad[nombre]['ultimo_mes']:
                historico_por_propiedad[nombre]['ultimo_mes'] = mes
                historico_por_propiedad[nombre]['ultimo_precio_base'] = precio_base
            
            historico_por_propiedad[nombre]['registros_existentes'].append(registro)
        
        logging.warning(f"[HISTORICO] Se encontraron {len(registros_existentes)} registros históricos")
        return historico_por_propiedad
        
    except Exception as e:
        logging.warning(f"[HISTORICO] No se pudo leer historico existente: {e}")
        return {}


def calcular_actualizacion_mes(precio_base_anterior: float, 
                              contrato: Contrato,
                              inflacion_df,
                              fecha_mes: dt.date,
                              meses_desde_inicio: int,
                              fecha_inicio_contrato: dt.date) -> Tuple[float, str, bool]:
    """
    Calcula si corresponde actualización en este mes específico y el nuevo precio_base.
    
    Returns:
        Tuple[nuevo_precio_base, porcentaje_aplicado, aplica_actualizacion]
    """
    freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
    freq_meses = freq_map.get(contrato.actualizacion.lower(), 3)
    
    # Verificar si corresponde actualización este mes
    # Para trimestral: actualizar cuando meses_desde_inicio sea 3, 6, 9, 12...
    # (que corresponde a los meses 4, 7, 10, 13... del contrato)
    # meses_desde_inicio = 0 (mes 1), 1 (mes 2), 2 (mes 3), 3 (mes 4 - primera actualización), etc.
    aplica_actualizacion = (meses_desde_inicio > 0 and meses_desde_inicio % freq_meses == 0)
    
    if not aplica_actualizacion:
        return precio_base_anterior, "", False
    
    # Calcular el factor de actualización para este período específico
    if contrato.indice.upper() == "IPC":
        # Para IPC, calcular inflación del último período usando la función existente
        from .services.inflation import inflacion_acumulada
        try:
            factor = inflacion_acumulada(inflacion_df, fecha_mes, freq_meses)
            nuevo_precio = precio_base_anterior * factor
            porcentaje = round((factor - 1) * 100, 2)
        except Exception as e:
            logging.warning(f"[IPC] Error calculando IPC: {e}")
            return precio_base_anterior, "", False
            
    elif contrato.indice.upper() == "ICL":
        # Para ICL, usar la función existente para obtener el factor del período
        try:
            fecha_inicio_ciclo = fecha_mes - relativedelta(months=freq_meses)
            fecha_fin_ciclo = fecha_mes
            
            factor = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
            nuevo_precio = precio_base_anterior * factor
            porcentaje = round((factor - 1) * 100, 2)
        except Exception as e:
            logging.warning(f"[ICL] Error calculando ICL: {e}")
            return precio_base_anterior, "", False
            
    else:
        # Porcentaje fijo
        try:
            porcentaje = float(contrato.indice.replace('%', '').replace(',', '.').strip())
            factor = 1 + (porcentaje / 100)
            nuevo_precio = precio_base_anterior * factor
        except Exception as e:
            logging.warning(f"[PORCENTAJE] Error parseando porcentaje {contrato.indice}: {e}")
            return precio_base_anterior, "", False
    
    return round(nuevo_precio, 2), f"{porcentaje:.2f}%", True


def generar_meses_faltantes(propiedad: Propiedad, 
                           contrato: Contrato,
                           fecha_limite: dt.date,
                           precio_base_inicial: float,
                           mes_inicial: str,
                           inflacion_df,
                           municipalidad: float = 0.0,
                           luz: float = 0.0,
                           gas: float = 0.0,
                           expensas: float = 0.0,
                           descuento_porcentaje: float = 0.0) -> List[Dict]:
    """
    Genera todos los registros mensuales faltantes desde mes_inicial hasta fecha_limite.
    """
    registros = []
    
    # Convertir mes_inicial a fecha
    if mes_inicial:
        y_inicial, m_inicial = map(int, mes_inicial.split("-"))
        fecha_actual = dt.date(y_inicial, m_inicial, 1)
        # Empezar desde el mes siguiente al último registrado
        if fecha_actual.month == 12:
            fecha_actual = dt.date(fecha_actual.year + 1, 1, 1)
        else:
            fecha_actual = dt.date(fecha_actual.year, fecha_actual.month + 1, 1)
    else:
        # Si no hay historico, empezar desde fecha_inicio del contrato
        fecha_actual = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
    
    precio_base_actual = precio_base_inicial
    fecha_inicio_contrato = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
    
    while fecha_actual <= fecha_limite:
        # Calcular meses desde inicio del contrato
        meses_desde_inicio = (fecha_actual.year - fecha_inicio_contrato.year) * 12 + (fecha_actual.month - fecha_inicio_contrato.month)
        
        # Verificar si el contrato sigue vigente
        if meses_desde_inicio >= contrato.duracion_meses:
            break
        
        # Calcular actualización si corresponde
        precio_base_actual, porc_actual, aplica_actualizacion = calcular_actualizacion_mes(
            precio_base_actual, contrato, inflacion_df, fecha_actual, meses_desde_inicio, fecha_inicio_contrato
        )
        
        # Calcular resto de valores
        freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
        freq_meses = freq_map.get(contrato.actualizacion.lower(), 3)
        
        if aplica_actualizacion:
            meses_prox_actualizacion = freq_meses
        else:
            # Calcular cuántos meses faltan para la próxima actualización
            # Para un contrato trimestral: actualizaciones cuando meses_desde_inicio = 3, 6, 9, etc.
            # (meses 4, 7, 10... del contrato)
            proximo_mes_actualizacion = ((meses_desde_inicio // freq_meses) + 1) * freq_meses
            meses_prox_actualizacion = proximo_mes_actualizacion - meses_desde_inicio
        
        meses_prox_renovacion = max(0, contrato.duracion_meses - meses_desde_inicio)
        
        # Calcular otros valores
        # precio_base_actual es el precio original (sin descuento)
        # precio_descuento es el precio con descuento aplicado
        factor_descuento = 1 - (descuento_porcentaje / 100)
        precio_descuento = round(precio_base_actual * factor_descuento, 2)
        
        comision = calcular_comision(contrato.comision_inmo, precio_descuento)
        cuotas_adicionales = calcular_cuotas_adicionales(
            precio_descuento,
            contrato.comision or "Pagado",
            contrato.deposito or "Pagado",
            meses_desde_inicio + 1  # mes_actual 1-based
        )
        
        pago_prop = round(precio_descuento - comision, 2)
        precio_final = precio_descuento + cuotas_adicionales + municipalidad + luz + gas + expensas
        
        # Crear registro
        mes_str = f"{fecha_actual.year}-{fecha_actual.month:02d}"
        actualizacion_str = "SI" if aplica_actualizacion else "NO"
        porc_actual_output = porc_actual if aplica_actualizacion else ""
        
        registro = {
            # Columnas de Identificación
            "nombre_inmueble": propiedad.nombre,
            "dir_inmueble": propiedad.direccion,
            "inquilino": propiedad.inquilino,
            "propietario": propiedad.propietario,
            "mes_actual": mes_str,
            
            # Columnas Calculadas
            "precio_final": precio_final,
            "precio_original": precio_base_actual,
            "precio_descuento": precio_descuento,
            "descuento": f"{descuento_porcentaje:.1f}%",
            "cuotas_adicionales": cuotas_adicionales,
            "municipalidad": municipalidad,
            "luz": luz,
            "gas": gas,
            "expensas": expensas,
            "comision_inmo": comision,
            "pago_prop": pago_prop,
            "actualizacion": actualizacion_str,
            "porc_actual": porc_actual_output,
            "meses_prox_actualizacion": meses_prox_actualizacion,
            "meses_prox_renovacion": meses_prox_renovacion
        }
        
        registros.append(registro)
        
        # Avanzar al siguiente mes
        if fecha_actual.month == 12:
            fecha_actual = dt.date(fecha_actual.year + 1, 1, 1)
        else:
            fecha_actual = dt.date(fecha_actual.year, fecha_actual.month + 1, 1)
    
    return registros


def main():
    args = _parse_args()
    y, m = map(int, args.hasta.split("-"))
    fecha_limite = dt.date(y, m, 1)
    
    # Leer maestro desde Google Sheets
    gc = get_gspread_client()
    sh = gc.open_by_key(config.SHEET_ID)
    ws = sh.worksheet(config.SHEET_MAESTRO)
    maestro = ws.get_all_records()
    inflacion_df = traer_inflacion()
    
    # Leer historico existente
    historico_existente = leer_historico_existente(sh)
    
    todos_los_registros = []
    total_procesados = 0
    total_omitidos = 0
    
    for fila in maestro:
        # Validación y creación de entidades
        try:
            propiedad = Propiedad(
                nombre=str(fila.get("nombre_inmueble", "")),
                direccion=str(fila.get("dir_inmueble", "")),
                propietario=str(fila.get("propietario", "")),
                inquilino=str(fila.get("inquilino", ""))
            )
            contrato = Contrato(
                fecha_inicio=str(fila.get("fecha_inicio_contrato", "")),
                duracion_meses=int(fila.get("duracion_meses", 0)),
                precio_original=float(fila.get("precio_original", 0)),
                actualizacion=str(fila.get("actualizacion", "")),
                indice=str(fila.get("indice", "")),
                comision_inmo=str(fila.get("comision_inmo", "")),
                comision=str(fila.get("comision", "")) if fila.get("comision", None) is not None else None,
                deposito=str(fila.get("deposito", "")) if fila.get("deposito", None) is not None else None
            )
        except Exception as e:
            total_omitidos += 1
            logging.warning(f"[ERROR ENTIDAD] {e}")
            continue
        
        # Validar fecha de inicio
        try:
            fecha_inicio_dt = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
        except Exception:
            total_omitidos += 1
            logging.warning(f"[FECHA INVÁLIDA] Fecha inicio inválida para {propiedad.nombre}")
            continue
        
        # Verificar si el contrato ya estaba vencido antes de la fecha límite
        if fecha_inicio_dt > fecha_limite:
            total_omitidos += 1
            logging.warning(f"[CONTRATO FUTURO] Contrato inicia después de fecha límite para {propiedad.nombre}")
            continue
        
        try:
            # Leer municipalidad, luz, gas, expensas y descuento de la fila del maestro
            municipalidad = float(fila.get("municipalidad", 0)) if fila.get("municipalidad") else 0
            luz = float(fila.get("luz", 0)) if fila.get("luz") else 0
            gas = float(fila.get("gas", 0)) if fila.get("gas") else 0
            expensas = float(fila.get("expensas", 0)) if fila.get("expensas") else 0
            
            # Leer descuento (viene como "15%", "0%", etc.)
            descuento_str = str(fila.get("descuento", "0%"))
            try:
                descuento_porcentaje = float(descuento_str.replace('%', '').replace(',', '.').strip())
            except:
                descuento_porcentaje = 0.0
            
            # Determinar punto de partida
            if propiedad.nombre in historico_existente:
                # Continuar desde donde se quedó
                info_historico = historico_existente[propiedad.nombre]
                precio_base_inicial = info_historico['ultimo_precio_base']
                mes_inicial = info_historico['ultimo_mes']
                
                # Agregar registros existentes
                todos_los_registros.extend(info_historico['registros_existentes'])
                
                logging.warning(f"[CONTINUACIÓN] {propiedad.nombre}: desde {mes_inicial} con precio_base {precio_base_inicial}")
            else:
                # Empezar desde el principio
                precio_base_inicial = contrato.precio_original
                mes_inicial = ""
                
                logging.warning(f"[NUEVO] {propiedad.nombre}: desde inicio con precio_base {precio_base_inicial}")
            
            # Generar meses faltantes
            nuevos_registros = generar_meses_faltantes(
                propiedad, contrato, fecha_limite, precio_base_inicial, mes_inicial, inflacion_df, 
                municipalidad, luz, gas, expensas, descuento_porcentaje
            )
            
            todos_los_registros.extend(nuevos_registros)
            total_procesados += 1
            
            logging.warning(f"[PROCESADO] {propiedad.nombre}: {len(nuevos_registros)} nuevos registros")
            
        except Exception as e:
            total_omitidos += 1
            logging.warning(f"[ERROR CÁLCULO] {propiedad.nombre}: {e}")
            continue
    
    # Ordenar registros por propiedad y fecha
    todos_los_registros.sort(key=lambda x: (x['nombre_inmueble'], x['mes_actual']))
    
    # Escribir en hoja "historico"
    sheet_name = "historico"
    try:
        # Intentar crear la hoja si no existe (ahora necesitamos 19 columnas)
        sh.add_worksheet(title=sheet_name, rows=len(todos_los_registros)+10, cols=19)
        logging.warning(f"[SHEET] Creada nueva hoja '{sheet_name}'")
    except Exception:
        logging.warning(f"[SHEET] Hoja '{sheet_name}' ya existe, se sobrescribirá")
    
    ws_historico = sh.worksheet(sheet_name)
    ws_historico.clear()
    
    if todos_los_registros:
        # Escribir headers y datos
        headers = list(todos_los_registros[0].keys())
        datos = [list(r.values()) for r in todos_los_registros]
        ws_historico.update([headers] + datos)
    
    logging.warning(f"[RESUMEN] Propiedades procesadas: {total_procesados}, omitidas: {total_omitidos}")
    logging.warning(f"[RESUMEN] Total registros en historico: {len(todos_los_registros)}")
    print(f"Historial generado hasta {args.hasta} en hoja '{sheet_name}' con {len(todos_los_registros)} registros")


if __name__ == "__main__":
    main()
