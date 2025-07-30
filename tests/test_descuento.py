#!/usr/bin/env python3
"""
Script de prueba para verificar la nueva lógica de descuentos.
"""

def test_logica_descuento():
    """
    Prueba la nueva lógica de cálculo con descuentos.
    """
    # Simulación de valores
    precio_base_actual = 100000  # precio original
    descuento_porcentaje = 15.0  # 15% de descuento
    cuotas_adicionales = 5000
    municipalidad = 1000
    luz = 500
    gas = 300
    
    # Aplicar la lógica implementada
    factor_descuento = 1 - (descuento_porcentaje / 100)
    precio_descuento = round(precio_base_actual * factor_descuento, 2)
    precio_final = precio_descuento + cuotas_adicionales + municipalidad + luz + gas
    
    print("=== PRUEBA DE LÓGICA DE DESCUENTOS ===")
    print(f"Precio Original (sin descuento): ${precio_base_actual:,.2f}")
    print(f"Descuento aplicado: {descuento_porcentaje}%")
    print(f"Factor de descuento: {factor_descuento}")
    print(f"Precio con descuento: ${precio_descuento:,.2f}")
    print(f"Cuotas adicionales: ${cuotas_adicionales:,.2f}")
    print(f"Municipalidad: ${municipalidad:,.2f}")
    print(f"Luz: ${luz:,.2f}")
    print(f"Gas: ${gas:,.2f}")
    print(f"PRECIO FINAL: ${precio_final:,.2f}")
    
    # Verificaciones
    descuento_esperado = 100000 * 0.85  # 85000
    assert precio_descuento == descuento_esperado, f"Error: precio_descuento debe ser {descuento_esperado}"
    
    precio_final_esperado = 85000 + 5000 + 1000 + 500 + 300  # 91800
    assert precio_final == precio_final_esperado, f"Error: precio_final debe ser {precio_final_esperado}"
    
    print("\n✅ Todas las verificaciones pasaron correctamente!")
    
    # Mostrar estructura de columnas
    print("\n=== ESTRUCTURA DE COLUMNAS DE SALIDA ===")
    registro_ejemplo = {
        "precio_final": precio_final,           # Nuevo nombre (antes precio_mes_actual)
        "precio_original": precio_base_actual,  # Nuevo nombre (antes precio_base)
        "precio_descuento": precio_descuento,   # Nueva columna
        "descuento": f"{descuento_porcentaje:.1f}%",  # Nueva columna
        "cuotas_adicionales": cuotas_adicionales,
        "municipalidad": municipalidad,
        "luz": luz,
        "gas": gas,
    }
    
    for key, value in registro_ejemplo.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    test_logica_descuento()
