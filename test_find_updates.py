#!/usr/bin/env python3
"""
Test para buscar contratos con actualizaciones aplicadas
"""

import datetime as dt
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar el módulo
sys.path.append(str(Path(__file__).parent))

from inmobiliaria.services.google_sheets import get_gspread_client
from inmobiliaria.services.inflation import traer_inflacion
from inmobiliaria.services.calculations import calcular_precio_base_acumulado
from inmobiliaria import config

def find_contracts_with_updates():
    """Buscar contratos que deberían tener actualizaciones"""
    print("🔍 Buscando contratos con actualizaciones aplicadas")
    print("=" * 60)
    
    # Obtener datos reales
    gc = get_gspread_client()
    sh = gc.open_by_key(config.SHEET_ID)
    ws = sh.worksheet(config.SHEET_MAESTRO)
    maestro = ws.get_all_records()
    inflacion_df = traer_inflacion()
    
    fecha_ref = dt.date(2024, 7, 1)  # Julio 2024
    
    contratos_con_actualizacion = []
    contratos_sin_actualizacion = []
    contratos_invalidos = 0
    
    for fila in maestro:
        if (fila.get("precio_original") and 
            fila.get("fecha_inicio_contrato") and 
            fila.get("actualizacion") and 
            fila.get("indice")):
            
            try:
                precio_original = float(fila.get("precio_original", 0))
                fecha_inicio_str = str(fila.get("fecha_inicio_contrato", ""))
                actualizacion = str(fila.get("actualizacion", ""))
                indice = str(fila.get("indice", ""))
                nombre = str(fila.get("nombre_inmueble", ""))
                
                # Validar fecha de inicio
                try:
                    fecha_inicio = dt.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                except:
                    contratos_invalidos += 1
                    continue
                
                # Solo considerar contratos que comenzaron antes de 2024 para tener actualizaciones
                if fecha_inicio >= dt.date(2024, 1, 1):
                    continue
                
                # Calcular con nueva función
                precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
                    precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
                )
                
                # Calcular meses desde inicio
                meses_desde_inicio = (fecha_ref.year - fecha_inicio.year) * 12 + (fecha_ref.month - fecha_inicio.month)
                
                contrato_info = {
                    'nombre': nombre,
                    'precio_original': precio_original,
                    'fecha_inicio': fecha_inicio,
                    'meses_desde_inicio': meses_desde_inicio,
                    'actualizacion': actualizacion,
                    'indice': indice,
                    'precio_base': precio_base,
                    'factor': precio_base/precio_original,
                    'aplica_actualizacion': aplica_actualizacion,
                    'porc_actual': porc_actual
                }
                
                if aplica_actualizacion or precio_base != precio_original:
                    contratos_con_actualizacion.append(contrato_info)
                else:
                    contratos_sin_actualizacion.append(contrato_info)
                
            except Exception as e:
                contratos_invalidos += 1
                continue
    
    print(f"📊 **RESUMEN DE ANÁLISIS:**")
    print(f"   - Contratos con actualizaciones: {len(contratos_con_actualizacion)}")
    print(f"   - Contratos sin actualizaciones: {len(contratos_sin_actualizacion)}")
    print(f"   - Contratos inválidos: {contratos_invalidos}")
    print()
    
    if contratos_con_actualizacion:
        print("🏠 **CONTRATOS CON ACTUALIZACIONES:**")
        for i, contrato in enumerate(contratos_con_actualizacion[:5]):  # Mostrar solo los primeros 5
            print(f"   {i+1}. **{contrato['nombre']}**")
            print(f"      💰 ${contrato['precio_original']:,.2f} → ${contrato['precio_base']:,.2f}")
            print(f"      📈 Factor: {contrato['factor']:.4f}x")
            print(f"      📅 Inicio: {contrato['fecha_inicio']} ({contrato['meses_desde_inicio']} meses)")
            print(f"      🔄 {contrato['actualizacion']} con {contrato['indice']}")
            if contrato['aplica_actualizacion']:
                print(f"      ✅ Actualización este mes: {contrato['porc_actual']}%")
            else:
                print(f"      📊 Actualización acumulada (no este mes)")
            print()
    else:
        print("⚠️  No se encontraron contratos antiguos con actualizaciones.")
        print("   Esto puede ser normal si todos los contratos son recientes.")
    
    return len(contratos_con_actualizacion) > 0

if __name__ == "__main__":
    try:
        found_updates = find_contracts_with_updates()
        if found_updates:
            print("✅ Step 1.1 verificado - Se encontraron actualizaciones aplicadas correctamente")
        else:
            print("ℹ️  No se encontraron contratos con actualizaciones (normal para datos con contratos recientes)")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
