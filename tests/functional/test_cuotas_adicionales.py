"""
Tests para cálculo de cuotas adicionales (Tests 53-65)
Basado en tests_funcionales.md - Categoría 4: CÁLCULO DE CUOTAS ADICIONALES
Reorganizado desde test_calculations.py
"""
import unittest
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inmobiliaria.services.calculations import calcular_cuotas_adicionales


class TestComisionInquilino(unittest.TestCase):
    """Tests 53-57: Comisión del inquilino"""
    
    def test_comision_pagado_no_suma(self):
        """Test 53: Con comisión "Pagado", no debe sumarse nada al alquiler"""
        precio_base = 100000.0
        comision = "Pagado"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3, 4, 5]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            self.assertEqual(cuotas, 0.0, 
                           f"Mes {mes_actual}: Con comisión 'Pagado' no debe sumar nada")
    
    def test_comision_2_cuotas_meses_1_y_2(self):
        """Test 54: Con comisión "2 cuotas", debe sumarse precio_base con recargo del 15% dividido en 2"""
        precio_base = 100000.0
        comision = "2 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = (precio_base * 1.15) / 2
            self.assertAlmostEqual(cuotas, expected, places=2,
                           msg=f"Mes {mes_actual}: Con comisión '2 cuotas' debe sumar {expected} (15% recargo)")
    
    def test_comision_2_cuotas_mes_3_en_adelante(self):
        """Test 55: Con comisión "2 cuotas", NO debe sumarse nada desde el mes 3 en adelante"""
        precio_base = 100000.0
        comision = "2 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [3, 4, 5, 6]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            self.assertEqual(cuotas, 0.0, 
                           f"Mes {mes_actual}: Con comisión '2 cuotas' NO debe sumar nada")
    
    def test_comision_3_cuotas_meses_1_2_y_3(self):
        """Test 56: Con comisión "3 cuotas", debe sumarse precio_base con recargo del 20% dividido en 3"""
        precio_base = 120000.0
        comision = "3 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = (precio_base * 1.20) / 3
            self.assertEqual(cuotas, expected, 
                           f"Mes {mes_actual}: Con comisión '3 cuotas' debe sumar {expected} (20% recargo)")
    
    def test_comision_3_cuotas_mes_4_en_adelante(self):
        """Test 57: Con comisión "3 cuotas", NO debe sumarse nada desde el mes 4 en adelante"""
        precio_base = 120000.0
        comision = "3 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [4, 5, 6, 7]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            self.assertEqual(cuotas, 0.0, 
                           f"Mes {mes_actual}: Con comisión '3 cuotas' NO debe sumar nada")


class TestDeposito(unittest.TestCase):
    """Tests 58-60: Depósito"""
    
    def test_deposito_pagado_no_suma(self):
        """Test 58: Con depósito "Pagado", no debe sumarse nada al alquiler"""
        precio_base = 100000.0
        comision = "Pagado"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3, 4, 5]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            self.assertEqual(cuotas, 0.0, 
                           f"Mes {mes_actual}: Con depósito 'Pagado' no debe sumar nada")
    
    def test_deposito_2_cuotas_meses_1_y_2(self):
        """Test 59: Con depósito "2 cuotas", debe sumarse precio_base/2 en los meses 1 y 2"""
        precio_base = 100000.0
        comision = "Pagado"
        deposito = "2 cuotas"
        
        for mes_actual in [1, 2]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = precio_base / 2  # 50,000
            self.assertEqual(cuotas, expected, 
                           f"Mes {mes_actual}: Con depósito '2 cuotas' debe sumar {expected}")
    
    def test_deposito_3_cuotas_meses_1_2_y_3(self):
        """Test 60: Con depósito "3 cuotas", debe sumarse precio_base/3 en los meses 1, 2 y 3"""
        precio_base = 120000.0
        comision = "Pagado"
        deposito = "3 cuotas"
        
        for mes_actual in [1, 2, 3]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = precio_base / 3  # 40,000
            self.assertEqual(cuotas, expected, 
                           f"Mes {mes_actual}: Con depósito '3 cuotas' debe sumar {expected}")


class TestCombinacionComisionDeposito(unittest.TestCase):
    """Tests 61-63: Combinación comisión + depósito"""
    
    def test_comision_2_cuotas_deposito_3_cuotas_mes_1(self):
        """Test 61: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 1 suma comisión con 15% + depósito"""
        precio_base = 120000.0  # Número que sea divisible por 2 y 3
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 1
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        expected = (precio_base * 1.15) / 2 + precio_base / 3
        
        self.assertEqual(cuotas, expected, 
                        f"Mes 1: Debe sumar comisión ({(precio_base * 1.15) / 2}) + depósito ({precio_base/3}) = {expected}")
    
    def test_comision_2_cuotas_deposito_3_cuotas_mes_3(self):
        """Test 62: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 3 suma solo depósito"""
        precio_base = 120000.0
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 3
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        expected = precio_base / 3
        
        self.assertEqual(cuotas, expected, 
                        f"Mes 3: Comisión ya terminó, solo debe sumar depósito ({expected})")
    
    def test_ambos_pagado_nunca_suma(self):
        """Test 63: Con ambos "Pagado", nunca debe sumarse nada adicional"""
        precio_base = 100000.0
        comision = "Pagado"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3, 4, 5, 6]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            self.assertEqual(cuotas, 0.0, 
                           f"Mes {mes_actual}: Con ambos 'Pagado' nunca debe sumar nada")


class TestInteraccionConActualizaciones(unittest.TestCase):
    """Tests 64-65: Interacción con actualizaciones"""
    
    def test_cuotas_sobre_precio_base_actualizado(self):
        """Test 64: Las cuotas adicionales deben calcularse sobre el precio_base actualizado, no el original"""
        # Caso: precio original $100,000, actualizado a $110,000
        precio_original = 100000.0
        precio_base_actualizado = 110000.0  # Después de actualización
        
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 1
        
        # Las cuotas deben calcularse sobre el precio actualizado sin interés
        cuotas = calcular_cuotas_adicionales(precio_base_actualizado, comision, deposito, mes_actual)
        expected = (precio_base_actualizado * 1.15) / 2 + precio_base_actualizado / 3
        
        self.assertAlmostEqual(cuotas, expected, places=2,
                              msg="Las cuotas deben calcularse sobre precio actualizado, no original")
        
        # Verificar que NO es sobre el precio original
        cuotas_sobre_original = (precio_original * 1.15) / 2 + precio_original / 3
        self.assertNotEqual(cuotas, cuotas_sobre_original,
                           "Las cuotas NO deben calcularse sobre precio original")
    
    def test_actualizacion_mes_3_afecta_tercera_cuota_deposito(self):
        """Test 65: Si hay actualización en el mes 3, la tercera cuota de depósito debe usar el precio actualizado"""
        # Escenario: Contrato trimestral con actualización en mes 3
        precio_base_mes_1_2 = 100000.0  # Primeros 2 meses
        precio_base_mes_3 = 110000.0    # Después de actualización en mes 3
        
        comision = "2 cuotas"  # Solo meses 1 y 2
        deposito = "3 cuotas"  # Meses 1, 2 y 3
        
        # Mes 1: cuotas sobre precio original sin interés
        cuotas_mes_1 = calcular_cuotas_adicionales(precio_base_mes_1_2, comision, deposito, 1)
        expected_mes_1 = (precio_base_mes_1_2 * 1.15) / 2 + precio_base_mes_1_2 / 3
        self.assertAlmostEqual(cuotas_mes_1, expected_mes_1, places=2)
        
        # Mes 3: solo depósito, pero sobre precio actualizado
        cuotas_mes_3 = calcular_cuotas_adicionales(precio_base_mes_3, comision, deposito, 3)
        expected_mes_3 = precio_base_mes_3 / 3  # 110,000 / 3 = 36,667
        self.assertAlmostEqual(cuotas_mes_3, expected_mes_3, places=2)
        
        # Verificar que la tercera cuota es mayor (por actualización)
        tercera_cuota_original = precio_base_mes_1_2 / 3  # 33,333
        tercera_cuota_actualizada = precio_base_mes_3 / 3  # 36,667
        
        self.assertGreater(tercera_cuota_actualizada, tercera_cuota_original,
                          "La tercera cuota debe ser mayor si hay actualización en mes 3")


if __name__ == '__main__':
    unittest.main()
