#!/usr/bin/env python3
"""
Genera el archivo de pagos mensuales para cada propiedad administrada.

Entradas
--------
1. maestro.xlsx  – hoja 'maestro' con las columnas:
   nombre_inmueble, dir_inmueble, inquilino, in_dni,
   propietario, prop_dni, precio_original, actualizacion,
   indice, fecha_inicio_contrato, duracion_meses, comision_inmo
2. Parámetro --mes AAAA-MM (opcional).  
   • Si se omite ⇒ se usa el mes calendario actual.

Salidas
-------http://localhost:8080/  
http://localhost:8080/Callback
• pagos_YYYY_MM.xlsx en la misma carpeta (o la que indiques con --outdir)
  con las columnas:
  nombre_inmueble, dir_inmueble, inquilino, propietario,
  mes_actual, precio_mes_anterior, precio_mes_actual,
  comision_inmo, pago_prop
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
import gspread
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning


# ---------- Parámetros de configuración ----------
MAESTRO_PATH = Path("maestro.xlsx")      # <-- cámbialo si hace falta
HOJA_MAESTRO = "maestro"

API_INFLACION = "https://api.argentinadatos.com/v1/finanzas/indices/inflacion"  #:contentReference[oaicite:0]{index=0}
# --------------------------------------------------

# ---------- Google Sheets Config ----------
SHEET_ID = "1MD5J352RQQaC93t_TicG8Spzqy08_2n5ft3KbQy0TRs"
SHEET_MAESTRO = "administracion"  # Nombre de la hoja con el maestro
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CLIENT_SECRET_FILE = "client_secret_126046018868-po1ak4e296153vhr6rfn16lh20hdvbg2.apps.googleusercontent.com.json"
TOKEN_PICKLE = "token.pickle"
# -----------------------------------------

# Ignorar solo los warnings de requests por verify=False
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)


def _parse_args() -> argparse.Namespace:
    today = dt.date.today()
    parser = argparse.ArgumentParser(description="Genera el archivo mensual de pagos")
    parser.add_argument("--mes", help="Mes de referencia en formato AAAA-MM",
                        default=f"{today.year}-{today.month:02}")
    parser.add_argument("--outdir", type=Path, default=Path("."), help="Directorio de salida")
    return parser.parse_args()


# ---------- Inflación ----------
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
    # Composición: (1+r1)*(1+r2)*... - 1
    factores = (1 + ultimo["valor"].astype(float) / 100)
    return factores.prod()


# ---------- ICL ----------
def traer_factor_icl(fecha_inicio: dt.date, fecha_hasta: dt.date) -> float:
    """Obtiene el factor de actualización ICL desde la API del BCRA."""
    url = (
        f"https://api.bcra.gob.ar/estadisticas/v3.0/monetarias/40?desde={fecha_inicio.strftime('%Y-%m-%d')}&hasta={fecha_hasta.strftime('%Y-%m-%d')}"
    )
    res = requests.get(url, timeout=10, verify=False)  # <--- Ignora la verificación SSL
    res.raise_for_status()
    data = res.json()["results"]
    if not data:
        raise ValueError("No se encontraron datos de ICL para el rango dado.")
    valor_inicio = data[-1]["valor"]  # El primer valor cronológico es el último del array
    valor_final = data[0]["valor"]    # El último valor cronológico es el primero del array
    return float(valor_final) / float(valor_inicio)


# ---------- Actualización de precio ----------
def precio_ajustado(precio_anterior: float,
                    frecuencia: str,
                    indice: str,
                    df_infl: pd.DataFrame,
                    fecha_ref: dt.date,
                    fecha_inicio: dt.date = None) -> float:
    """Devuelve el precio ajustado según la política de la fila."""
    if frecuencia not in {"trimestral", "semestral", "anual"}:
        return precio_anterior  # no debería ocurrir

    meses = {"trimestral": 3, "semestral": 6, "anual": 12}[frecuencia]

    if indice.upper() == "IPC":
        factor = inflacion_acumulada(df_infl, fecha_ref, meses)
    elif indice.upper() == "ICL":
        if fecha_inicio is None:
            raise ValueError("Se requiere fecha_inicio para calcular ICL")
        factor = traer_factor_icl(fecha_inicio, fecha_ref)
    else:  # Porcentaje fijo: “10 %”, “7.5%”, etc.
        pct = float(indice.strip().replace("%", "").replace(",", "."))
        factor = 1 + pct / 100

    return round(precio_anterior * factor, 2)


def calcular_comision(comision_str: str, precio_mes: float) -> float:
    """Comisión siempre en porcentaje—ej.: “5 %”."""
    pct = float(comision_str.strip().replace("%", "").replace(",", "."))
    return round(precio_mes * pct / 100, 2)


def get_gspread_client():
    creds = None
    if os.path.exists(TOKEN_PICKLE):
        with open(TOKEN_PICKLE, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PICKLE, "wb") as token:
            pickle.dump(creds, token)
    return gspread.authorize(creds)


# ---------- Flujo principal ----------
def main() -> None:
    args = _parse_args()
    y, m = map(int, args.mes.split("-"))
    fecha_ref = dt.date(y, m, 1)

    # Leer maestro desde Google Sheets
    gc = get_gspread_client()
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.worksheet(SHEET_MAESTRO)
    maestro = pd.DataFrame(ws.get_all_records())
    inflacion_df = traer_inflacion()

    registros = []
    for _, fila in maestro.iterrows():
        # ¿Sigue vigente el contrato?
        inicio = pd.to_datetime(fila["fecha_inicio_contrato"]).date()
        if (fecha_ref - inicio).days // 30 >= fila["duracion_meses"]:
            continue  # contrato finalizado ⇒ omitir

        # Calcular meses desde inicio y ciclos completos
        freq_meses = {"trimestral": 3, "semestral": 6, "anual": 12}[fila["actualizacion"]]
        meses_desde_inicio = (y - inicio.year) * 12 + (m - inicio.month)
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        aplica_actualizacion = "SI" if resto == 0 else "NO"

        # Calcular el factor acumulado
        if fila["indice"].upper() == "IPC":
            factor_total = 1.0
            for ciclo in range(ciclos_cumplidos):
                fecha_corte = inicio + relativedelta(months=(ciclo + 1) * freq_meses)
                factor_ciclo = inflacion_acumulada(inflacion_df, fecha_corte, freq_meses)
                factor_total *= factor_ciclo
            # Porcentaje aplicado este mes (solo si hay actualización)
            if aplica_actualizacion == "SI" and ciclos_cumplidos > 0:
                fecha_corte = inicio + relativedelta(months=ciclos_cumplidos * freq_meses)
                porc_actual = (inflacion_acumulada(inflacion_df, fecha_corte, freq_meses) - 1) * 100
            else:
                porc_actual = 0
        elif fila["indice"].upper() == "ICL":
            factor_total = 1.0
            for ciclo in range(ciclos_cumplidos):
                fecha_inicio_ciclo = inicio + relativedelta(months=ciclo * freq_meses)
                fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=freq_meses)
                factor_ciclo = traer_factor_icl(fecha_inicio_ciclo, fecha_fin_ciclo)
                factor_total *= factor_ciclo
            if aplica_actualizacion == "SI" and ciclos_cumplidos > 0:
                fecha_inicio_ult = inicio + relativedelta(months=(ciclos_cumplidos - 1) * freq_meses)
                fecha_fin_ult = fecha_inicio_ult + relativedelta(months=freq_meses)
                porc_actual = (traer_factor_icl(fecha_inicio_ult, fecha_fin_ult) - 1) * 100
            else:
                porc_actual = 0
        else:
            pct = float(fila["indice"].strip().replace("%", "").replace(",", "."))
            factor_total = (1 + pct / 100) ** ciclos_cumplidos
            porc_actual = pct if aplica_actualizacion == "SI" and ciclos_cumplidos > 0 else 0

        precio_actual = round(fila["precio_original"] * factor_total, 2)
        comision = calcular_comision(fila["comision_inmo"], precio_actual)
        pago_prop = round(precio_actual - comision, 2)

        meses_prox_renovacion = fila["duracion_meses"] - meses_desde_inicio

        registros.append({
            "nombre_inmueble": fila["nombre_inmueble"],
            "dir_inmueble": fila["dir_inmueble"],
            "inquilino": fila["inquilino"],
            "propietario": fila["propietario"],
            "mes_actual": args.mes,
            "precio_mes_actual": precio_actual,
            "comision_inmo": comision,
            "pago_prop": pago_prop,
            "actualizacion": aplica_actualizacion,
            "porc_actual": round(porc_actual, 2) if aplica_actualizacion == "SI" else "",
            "meses_prox_renovacion": meses_prox_renovacion
        })

    pagos = pd.DataFrame(registros)
    # Escribir pagos en una nueva hoja de Google Sheets
    sheet_name = f"pagos_{args.mes.replace('-', '_')}"
    try:
        sh.add_worksheet(title=sheet_name, rows=str(len(pagos)+10), cols=str(len(pagos.columns)+2))
    except Exception:
        pass  # Si ya existe, continuar
    ws_pagos = sh.worksheet(sheet_name)
    ws_pagos.clear()
    ws_pagos.update([pagos.columns.values.tolist()] + pagos.values.tolist())
    print(f"Hoja generada: {sheet_name} en Google Sheets")


if __name__ == "__main__":
    main()
