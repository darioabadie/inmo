#!/usr/bin/env python3
"""
Genera el historial completo de pagos desde el inicio de cada contrato hasta un mes límite.
Cada actualización se basa en el último precio_base registrado, permitiendo ajustes manuales.

REFACTORIZADO: Ahora usa arquitectura modular con servicios especializados.
"""

import argparse
import datetime as dt
import logging
import os
import urllib3

from .services.historical_service import HistoricalService

# Configuración de logging principal
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s"
)

# Configuración del logger específico para errores del historial
def setup_error_logger():
    """Configura un logger específico para errores del historial."""
    error_logger = logging.getLogger('historical_errors')
    error_logger.setLevel(logging.ERROR)
    
    # Crear el directorio si no existe
    os.makedirs('logs', exist_ok=True)
    
    # Handler para archivo
    file_handler = logging.FileHandler('logs/errors.log', encoding='utf-8')
    file_handler.setLevel(logging.ERROR)
    
    # Formato detallado para el archivo
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [HISTORICAL] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # Evitar duplicar logs si ya está configurado
    if not error_logger.handlers:
        error_logger.addHandler(file_handler)
    
    return error_logger

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
    # Configurar el logger de errores
    error_logger = setup_error_logger()
    
    # Parsear argumentos
    args = _parse_args()
    fecha_limite = _parse_fecha_limite(args.hasta)
    
    # Crear el servicio principal
    service = HistoricalService(error_logger=error_logger)
    
    # Generar el historial completo
    logging.warning(f"[INICIO] Generando historial hasta {args.hasta}")
    summary = service.generate_historical_until(fecha_limite)
    
    # Mostrar resumen
    print(f"Historial generado hasta {args.hasta} en hoja 'historico' con {summary.total_registros} registros")
    print(f"Propiedades procesadas: {summary.propiedades_procesadas}, omitidas: {summary.propiedades_omitidas}")
    
    if summary.errores:
        print(f"Errores encontrados: {len(summary.errores)}")
        print(f"Los errores han sido guardados en 'logs/errors.log'")
        for error in summary.errores[:5]:  # Mostrar solo los primeros 5 errores
            print(f"  - {error}")
        if len(summary.errores) > 5:
            print(f"  ... y {len(summary.errores) - 5} errores más")
        
        # Log de resumen de errores
        error_logger.error(f"RESUMEN: {len(summary.errores)} errores encontrados durante generación de historial hasta {args.hasta}")
    else:
        print("✓ Historial generado sin errores")
    
    # Mostrar resumen de contratos si aplica
    if hasattr(summary, 'contratos_vencidos') and (summary.contratos_vencidos > 0 or summary.contratos_proximos_vencer > 0):
        print(f"\n📋 Resumen de contratos guardado en: resumen_contratos_{dt.date.today():%Y-%m-%d}.txt")
        print(f"   - Contratos vencidos: {summary.contratos_vencidos}")
        print(f"   - Contratos por vencer: {summary.contratos_proximos_vencer}")
    else:
        print("\n📋 No se encontraron contratos vencidos ni próximos a vencer")


if __name__ == "__main__":
    main()
