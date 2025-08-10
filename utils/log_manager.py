#!/usr/bin/env python3
"""
Utilidad para gestionar los archivos de log del sistema.
"""

import os
import argparse
from datetime import datetime

def clear_logs():
    """Limpia todos los archivos de log."""
    log_dir = "logs"
    if os.path.exists(log_dir):
        for file in os.listdir(log_dir):
            if file.endswith('.log'):
                file_path = os.path.join(log_dir, file)
                os.remove(file_path)
                print(f"✅ Eliminado: {file_path}")
    print("🧹 Logs limpiados")

def show_log_stats():
    """Muestra estadísticas de los logs."""
    log_dir = "logs"
    error_log = os.path.join(log_dir, "errors.log")
    
    if not os.path.exists(error_log):
        print("📄 No hay archivos de log")
        return
    
    with open(error_log, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    size = os.path.getsize(error_log)
    
    print(f"📊 Estadísticas del log de errores:")
    print(f"   • Archivo: {error_log}")
    print(f"   • Líneas: {len(lines)}")
    print(f"   • Tamaño: {size} bytes")
    
    if lines:
        first_line = lines[0].strip()
        last_line = lines[-1].strip()
        print(f"   • Primera entrada: {first_line.split(' - ')[0] if ' - ' in first_line else 'N/A'}")
        print(f"   • Última entrada: {last_line.split(' - ')[0] if ' - ' in last_line else 'N/A'}")

def main():
    parser = argparse.ArgumentParser(description="Gestionar logs del sistema inmobiliaria")
    parser.add_argument("--clear", action="store_true", help="Limpiar todos los logs")
    parser.add_argument("--stats", action="store_true", help="Mostrar estadísticas de logs")
    
    args = parser.parse_args()
    
    if args.clear:
        clear_logs()
    elif args.stats:
        show_log_stats()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
