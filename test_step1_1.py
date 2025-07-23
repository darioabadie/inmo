#!/usr/bin/env python3
"""
Test manual para verificar la corrección del Step 1.1: Cálculo de precio_base acumulado
"""

import datetime as dt
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar el módulo
sys.path.append(str(Path(__file__).parent))

from inmobiliaria.services.calculations import calcular_precio_base_acumulado

def test_porcentaje_fijo_acumulado():
    """Test del cálculo acumulado con porcentaje fijo"""
    print("=== TEST: Porcentaje Fijo Acumulado ===")
    
    # Caso del technical_specs.md:
    # Precio original: $100,000
    # Inicio: 2024-01-01, Referencia: 2024-07-01 (6 meses después)
    # Actualización: trimestral, Índice: "10%"
    # Esperado: 2 ciclos cumplidos, factor = (1.10)² = 1.21, precio = $121,000
    
    precio_original = 100000.0
    actualizacion = "trimestral"
    indice = "10%"
    fecha_inicio = dt.date(2024, 1, 1)
    fecha_ref = dt.date(2024, 7, 1)  # 6 meses después
    df_infl = pd.DataFrame()  # No se usa para porcentaje fijo
    
    precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
        precio_original, actualizacion, indice, df_infl, fecha_inicio, fecha_ref
    )
    
    print(f"Precio original: ${precio_original:,.2f}")
    print(f"Período: {fecha_inicio} a {fecha_ref}")
    print(f"Actualización: {actualizacion} con {indice}")
    print(f"Resultado:")
    print(f"  - Precio base: ${precio_base:,.2f}")
    print(f"  - Porcentaje actual: {porc_actual}%")
    print(f"  - Aplica actualización: {aplica_actualizacion}")
    
    # Verificaciones
    expected_precio = 121000.0  # 100,000 * (1.10)²
    expected_porc = 10.0  # Porcentaje del último ciclo
    expected_aplica = True  # Mes 7 es mes de actualización (6 % 3 = 0)
    
    assert abs(precio_base - expected_precio) < 0.01, f"Esperado ${expected_precio}, obtenido ${precio_base}"
    assert abs(porc_actual - expected_porc) < 0.01, f"Esperado {expected_porc}%, obtenido {porc_actual}%"
    assert aplica_actualizacion == expected_aplica, f"Esperado {expected_aplica}, obtenido {aplica_actualizacion}"
    
    print("✅ Test PASADO - Porcentaje fijo acumulado funciona correctamente")
    print()

def test_sin_ciclos_cumplidos():
    """Test cuando no hay ciclos cumplidos aún"""
    print("=== TEST: Sin Ciclos Cumplidos ===")
    
    precio_original = 100000.0
    actualizacion = "trimestral" 
    indice = "10%"
    fecha_inicio = dt.date(2024, 1, 1)
    fecha_ref = dt.date(2024, 2, 1)  # Solo 1 mes después
    df_infl = pd.DataFrame()
    
    precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
        precio_original, actualizacion, indice, df_infl, fecha_inicio, fecha_ref
    )
    
    print(f"Precio original: ${precio_original:,.2f}")
    print(f"Período: {fecha_inicio} a {fecha_ref} (1 mes)")
    print(f"Resultado:")
    print(f"  - Precio base: ${precio_base:,.2f}")
    print(f"  - Porcentaje actual: {porc_actual}%")
    print(f"  - Aplica actualización: {aplica_actualizacion}")
    
    # Verificaciones
    assert precio_base == precio_original, f"Sin ciclos, precio debe mantenerse igual"
    assert porc_actual == 0.0, f"Sin ciclos, porcentaje debe ser 0"
    assert aplica_actualizacion == False, f"Sin ciclos, no debe aplicar actualización"
    
    print("✅ Test PASADO - Sin ciclos funciona correctamente")
    print()

def test_mes_sin_actualizacion():
    """Test mes que no es de actualización"""
    print("=== TEST: Mes Sin Actualización ===")
    
    precio_original = 100000.0
    actualizacion = "trimestral"
    indice = "10%"
    fecha_inicio = dt.date(2024, 1, 1)
    fecha_ref = dt.date(2024, 5, 1)  # 4 meses después (no es múltiplo de 3)
    df_infl = pd.DataFrame()
    
    precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
        precio_original, actualizacion, indice, df_infl, fecha_inicio, fecha_ref
    )
    
    print(f"Precio original: ${precio_original:,.2f}")
    print(f"Período: {fecha_inicio} a {fecha_ref} (4 meses - 1 ciclo cumplido)")
    print(f"Resultado:")
    print(f"  - Precio base: ${precio_base:,.2f}")
    print(f"  - Porcentaje actual: {porc_actual}%")
    print(f"  - Aplica actualización: {aplica_actualizacion}")
    
    # Verificaciones
    expected_precio = 110000.0  # 100,000 * 1.10 (1 ciclo cumplido)
    assert abs(precio_base - expected_precio) < 0.01, f"Esperado ${expected_precio}, obtenido ${precio_base}"
    assert porc_actual == 0.0, f"No es mes de actualización, porcentaje debe ser 0"
    assert aplica_actualizacion == False, f"No es mes de actualización"
    
    print("✅ Test PASADO - Mes sin actualización funciona correctamente")
    print()

if __name__ == "__main__":
    print("🧪 Ejecutando tests para Step 1.1: Cálculo de precio_base acumulado")
    print("=" * 60)
    
    try:
        test_porcentaje_fijo_acumulado()
        test_sin_ciclos_cumplidos()
        test_mes_sin_actualizacion()
        
        print("🎉 TODOS LOS TESTS PASARON")
        print("✅ Step 1.1 implementado correctamente")
        
    except Exception as e:
        print(f"❌ ERROR en los tests: {e}")
        sys.exit(1)
