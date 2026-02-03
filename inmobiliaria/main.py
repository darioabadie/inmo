#!/usr/bin/env python3
"""
Genera el archivo de pagos mensuales para cada propiedad administrada.
"""

import argparse
import datetime as dt
from pathlib import Path

import logging
import warnings
import urllib3

from . import config
from .models import Propiedad, Contrato, Pago
from . import utils
from .services.google_sheets import get_gspread_client
from .services.inflation import traer_inflacion
from .services.calculations import precio_ajustado, calcular_comision, calcular_cuotas_detalladas, traer_factor_icl, calcular_precio_base_acumulado

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _parse_args() -> argparse.Namespace:
    today = dt.date.today()
    parser = argparse.ArgumentParser(description="Genera el archivo mensual de pagos")
    parser.add_argument("--mes", help="Mes de referencia en formato AAAA-MM",
                        default=f"{today.year}-{today.month:02}")
    parser.add_argument("--outdir", type=Path, default=Path("."), help="Directorio de salida")
    return parser.parse_args()


def _calcular_comision_inmo(precio_descuento: float, comision_inmo_str: str) -> float:
    """Calcula la comisión de la inmobiliaria."""
    try:
        # Manejar el caso especial donde no hay comisión
        if comision_inmo_str.strip() == "0":
            return 0.0
            
        # Limpiar y convertir el porcentaje
        porcentaje_str = comision_inmo_str.replace('%', '').replace(',', '.').strip()
        porcentaje = float(porcentaje_str)
        return precio_descuento * (porcentaje / 100)
    except (ValueError, AttributeError):
        return 0.0


def main():
    args = _parse_args()
    y, m = map(int, args.mes.split("-"))
    fecha_ref = dt.date(y, m, 1)

    # Leer maestro desde Google Sheets
    gc = get_gspread_client()
    sh = gc.open_by_key(config.SHEET_ID)
    ws = sh.worksheet(config.SHEET_MAESTRO)
    maestro = ws.get_all_records()
    inflacion_df = traer_inflacion()

    registros = []
    total_omitidos = 0
    total_procesados = 0
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

        # Cálculos principales
        try:
            # Validar y convertir fecha_inicio
            fecha_inicio_dt = None
            if contrato.fecha_inicio:
                try:
                    fecha_inicio_dt = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
                except Exception:
                    fecha_inicio_dt = None

            # Si no hay fecha de inicio válida, omitir registro
            if not fecha_inicio_dt:
                total_omitidos += 1
                logging.warning(f"[FECHA INVÁLIDA] Fecha inicio inválida para {propiedad.nombre}")
                continue

            # Calcular meses desde inicio
            meses_desde_inicio = (fecha_ref.year - fecha_inicio_dt.year) * 12 + (fecha_ref.month - fecha_inicio_dt.month)

            # Validar si el contrato está vencido (Step 1.3)
            if meses_desde_inicio >= contrato.duracion_meses:
                total_omitidos += 1
                logging.warning(f"[CONTRATO FINALIZADO] Contrato vencido para {propiedad.nombre}")
                continue

            # Usar la nueva función para calcular precio base acumulado
            precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
                contrato.precio_original,
                contrato.actualizacion,
                contrato.indice,
                inflacion_df,
                fecha_inicio_dt,
                fecha_ref
            )

            # Calcular meses hasta próxima actualización y renovación
            freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
            freq_meses = freq_map.get(contrato.actualizacion.lower(), 3)
            resto = meses_desde_inicio % freq_meses
            
            if aplica_actualizacion:
                meses_prox_actualizacion = freq_meses
            else:
                meses_prox_actualizacion = freq_meses - resto

            meses_prox_renovacion = max(0, contrato.duracion_meses - meses_desde_inicio)

            # Calcular otros valores
            comision_alquiler = calcular_comision(contrato.comision_inmo, precio_base)
            
            cuotas_detalle = calcular_cuotas_detalladas(
                precio_base,
                contrato.comision or "Pagado",
                contrato.deposito or "Pagado",
                meses_desde_inicio + 1  # mes_actual 1-based
            )
            cuotas_adicionales = float(cuotas_detalle['total_cuotas'])
            cuotas_deposito = float(cuotas_detalle['cuotas_deposito'])
            comision_deposito = calcular_comision(contrato.comision_inmo, cuotas_deposito) if cuotas_deposito > 0 else 0.0
            comision = round(comision_alquiler + comision_deposito, 2)
            municipalidad = float(fila.get("municipalidad", 0)) if fila.get("municipalidad") else 0
            pago_prop = round(precio_base + cuotas_deposito - comision, 2)
            precio_mes_actual = precio_base + cuotas_adicionales + municipalidad
            pago = Pago(
                mes=args.mes,
                precio_mes_actual=precio_mes_actual,
                comision_inmo=comision,
                pago_prop=pago_prop
            )
            total_procesados += 1
        except Exception as e:
            total_omitidos += 1
            logging.warning(f"[ERROR CÁLCULO] {e}")
            continue

        # Campos corregidos según especificaciones técnicas (Step 1.2)
        actualizacion_str = "SI" if aplica_actualizacion else "NO"
        porc_actual_output = porc_actual if aplica_actualizacion else ""

        registros.append({
            # Columnas de Identificación (según technical_specs.md)
            "nombre_inmueble": propiedad.nombre,
            "dir_inmueble": propiedad.direccion,
            "inquilino": propiedad.inquilino,
            "propietario": propiedad.propietario,
            "mes_actual": pago.mes,
            
            # Columnas Calculadas (orden según technical_specs.md)
            "precio_mes_actual": precio_mes_actual,  # PRECIO TOTAL QUE PAGA EL INQUILINO
            "precio_base": precio_base,  # Precio Base Actualizado
            "cuotas_adicionales": cuotas_adicionales,  # Comisión y Depósito Fraccionados  
            "municipalidad": municipalidad,  # Gastos Municipales
            "comision_inmo": pago.comision_inmo,  # Comisión de Administración
            "pago_prop": pago.pago_prop,  # Pago Neto al Propietario
            "actualizacion": actualizacion_str,  # Indicador de Actualización (SI/NO)
            "porc_actual": porc_actual_output,  # Porcentaje Aplicado Este Mes
            "meses_prox_actualizacion": meses_prox_actualizacion,  # Meses Hasta Próxima Actualización
            "meses_prox_renovacion": meses_prox_renovacion  # Meses Restantes del Contrato
        })

    # Escribir pagos en una nueva hoja de Google Sheets
    sheet_name = f"pagos_{args.mes.replace('-', '_')}"
    try:
        sh.add_worksheet(title=sheet_name, rows=len(registros)+10, cols=len(registros[0])+2)
    except Exception:
        pass  # Si ya existe, continuar
    ws_pagos = sh.worksheet(sheet_name)
    ws_pagos.clear()
    if registros:
        ws_pagos.update([list(registros[0].keys())] + [list(r.values()) for r in registros])
    logging.warning(f"[RESUMEN] Registros procesados: {total_procesados}, omitidos: {total_omitidos}")
    print(f"Hoja generada: {sheet_name} en Google Sheets")

if __name__ == "__main__":
    main()
