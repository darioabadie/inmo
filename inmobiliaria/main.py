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
from .services.calculations import precio_ajustado, calcular_comision, calcular_cuotas_adicionales, traer_factor_icl

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

            # Calcular meses desde inicio
            meses_desde_inicio = (fecha_ref.year - fecha_inicio_dt.year) * 12 + (fecha_ref.month - fecha_inicio_dt.month) if fecha_inicio_dt else 0

            # Frecuencia de actualización en meses
            freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
            freq_meses = freq_map.get(contrato.actualizacion.lower(), 3)

            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = resto == 0 and ciclos_cumplidos > 0

            # Calcular meses hasta próxima actualización
            if aplica_actualizacion:
                meses_prox_actualizacion = freq_meses
            else:
                meses_prox_actualizacion = freq_meses - resto

            # Calcular meses hasta renovación
            meses_prox_renovacion = max(0, contrato.duracion_meses - meses_desde_inicio)

            # Calcular precio_base (solo se ajusta en mes de actualización)
            if aplica_actualizacion:
                if contrato.indice.upper() == "ICL":
                    if fecha_inicio_dt:
                        factor = traer_factor_icl(fecha_inicio_dt, fecha_ref)
                        precio_actual = round(contrato.precio_original * factor, 2)
                        porc_actual = round((factor - 1) * 100, 2)
                    else:
                        precio_actual = contrato.precio_original
                        porc_actual = 0
                elif contrato.indice.upper() == "IPC":
                    precio_actual = precio_ajustado(
                        contrato.precio_original,
                        contrato.actualizacion,
                        contrato.indice,
                        inflacion_df,
                        fecha_ref,
                        fecha_inicio_dt
                    )
                    porc_actual = 0
                else:
                    precio_actual = precio_ajustado(
                        contrato.precio_original,
                        contrato.actualizacion,
                        contrato.indice,
                        inflacion_df,
                        fecha_ref,
                        fecha_inicio_dt
                    )
                    try:
                        pct = float(contrato.indice.strip().replace("%", "").replace(",", "."))
                        porc_actual = pct
                    except Exception:
                        porc_actual = 0
            else:
                precio_actual = contrato.precio_original
                porc_actual = 0

            comision = calcular_comision(contrato.comision_inmo, precio_actual)
            cuotas_adicionales = calcular_cuotas_adicionales(
                precio_actual,
                contrato.comision or "Pagado",
                contrato.deposito or "Pagado",
                meses_desde_inicio + 1  # mes_actual 1-based
            )
            municipalidad = float(fila.get("municipalidad", 0)) if fila.get("municipalidad") else 0
            pago_prop = round(precio_actual - comision, 2)
            precio_mes_actual = precio_actual + cuotas_adicionales + municipalidad
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

        # Calcular fecha y precio de última actualización (fuera del try)
    # ...existing code...
        # Calcular valor decimal para actualizacion
        if aplica_actualizacion:
            if contrato.indice:
                try:
                    valor_decimal = float(str(porc_actual).replace("%", "").replace(",", ".")) / 100 if isinstance(porc_actual, (int, float)) else 0
                except Exception:
                    valor_decimal = 0
            else:
                valor_decimal = 0
        else:
            valor_decimal = 0

        # Calcular fecha y precio de última actualización
        if fecha_inicio_dt:
            if freq_meses > 0 and meses_desde_inicio >= freq_meses:
                ciclos_anteriores = (meses_desde_inicio // freq_meses)
                meses_ult = freq_meses * (ciclos_anteriores - (0 if aplica_actualizacion else 1))
                fecha_ultima_actual = fecha_inicio_dt + dt.timedelta(days=30 * meses_ult)
                # Calcular precio de la última actualización
                if contrato.indice.upper() == "ICL":
                    fecha_ult = fecha_ultima_actual
                    factor_ult = traer_factor_icl(fecha_inicio_dt, fecha_ult)
                    precio_ultima_actual = round(contrato.precio_original * factor_ult, 2)
                elif contrato.indice.upper() == "IPC":
                    precio_ultima_actual = precio_ajustado(
                        contrato.precio_original,
                        contrato.actualizacion,
                        contrato.indice,
                        inflacion_df,
                        fecha_ultima_actual,
                        fecha_inicio_dt
                    )
                else:
                    precio_ultima_actual = precio_ajustado(
                        contrato.precio_original,
                        contrato.actualizacion,
                        contrato.indice,
                        inflacion_df,
                        fecha_ultima_actual,
                        fecha_inicio_dt
                    )
            else:
                fecha_ultima_actual = fecha_inicio_dt
                precio_ultima_actual = contrato.precio_original
        else:
            fecha_ultima_actual = None
            precio_ultima_actual = contrato.precio_original

        registros.append({
            "nombre_inmueble": propiedad.nombre,
            "dir_inmueble": propiedad.direccion,
            "inquilino": propiedad.inquilino,
            "propietario": propiedad.propietario,
            "mes_actual": pago.mes,
            "precio_mes_actual": precio_mes_actual,  # total que paga el inquilino (incluye municipalidad)
            "precio_base": precio_actual,  # base sin cuotas ni municipalidad
            "cuotas_adicionales": cuotas_adicionales,  # monto de cuotas este mes
            "municipalidad": municipalidad,  # gastos municipales
            "comision_inmo": pago.comision_inmo,
            "pago_prop": pago.pago_prop,
            "actualizacion": valor_decimal,
            "meses_prox_actualizacion": meses_prox_actualizacion,
            "meses_prox_renovacion": meses_prox_renovacion,
            "fecha_ultima_actual": fecha_ultima_actual.strftime("%Y-%m-%d") if fecha_ultima_actual else "",
            "precio_ultima_actual": precio_ultima_actual
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
