#!/usr/bin/env python3
"""
Genera el historial completo de pagos desde el inicio de cada contrato hasta un mes límite.
Cada actualización se basa en el último precio_base registrado, permitiendo ajustes manuales.

REFACTORIZADO: Ahora usa arquitectura modular con servicios especializados.
"""

import argparse
import datetime as dt
import logging
import urllib3

from .services.historical_service import HistoricalService

# Configuración de logging
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _parse_args() -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    today = dt.date.today()
    parser = argparse.ArgumentParser(description="Genera el historial completo de pagos")
    parser.add_argument("--hasta", help="Mes límite en formato AAAA-MM",
                        default=f"{today.year}-{today.month:02}")
    return parser.parse_args()


def _parse_fecha_limite(fecha_str: str) -> dt.date:
    """Convierte string de fecha en objeto date."""
    y, m = map(int, fecha_str.split("-"))
    return dt.date(y, m, 1)


def main():
    """
    Función principal simplificada.
    
    La lógica compleja se ha movido a servicios especializados:
    - HistoricalService: Orquesta todo el proceso
    - HistoricalDataManager: Maneja datos de Google Sheets
    - MonthlyRecordGenerator: Genera registros mensuales
    - HistoricalCalculations: Realiza cálculos especializados
    """
    # Parsear argumentos
    args = _parse_args()
    fecha_limite = _parse_fecha_limite(args.hasta)
    
    # Crear el servicio principal
    service = HistoricalService()
    
    # Generar el historial completo
    logging.warning(f"[INICIO] Generando historial hasta {args.hasta}")
    summary = service.generate_historical_until(fecha_limite)
    
    # Mostrar resumen
    print(f"Historial generado hasta {args.hasta} en hoja 'historico' con {summary.total_registros} registros")
    print(f"Propiedades procesadas: {summary.propiedades_procesadas}, omitidas: {summary.propiedades_omitidas}")
    
    if summary.errores:
        print(f"Errores encontrados: {len(summary.errores)}")
        for error in summary.errores[:5]:  # Mostrar solo los primeros 5 errores
            print(f"  - {error}")
        if len(summary.errores) > 5:
            print(f"  ... y {len(summary.errores) - 5} errores más")


if __name__ == "__main__":
    main()
