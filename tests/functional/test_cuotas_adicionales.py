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
        """Test 54: Con comisión "2 cuotas", debe sumarse precio_base/2 en los meses 1 y 2 (SIN interés)"""
        precio_base = 100000.0
        comision = "2 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = precio_base / 2  # 50,000 sin interés
            self.assertAlmostEqual(cuotas, expected, places=2,
                           msg=f"Mes {mes_actual}: Con comisión '2 cuotas' debe sumar {expected} (sin interés)")
    
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
        """Test 56: Con comisión "3 cuotas", debe sumarse precio_base/3 en los meses 1, 2 y 3 (SIN interés)"""
        precio_base = 120000.0
        comision = "3 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
            expected = precio_base / 3  # 40,000 sin interés
            self.assertEqual(cuotas, expected, 
                           f"Mes {mes_actual}: Con comisión '3 cuotas' debe sumar {expected} (sin interés)")
    
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
        """Test 61: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 1 debe sumarse precio_base/2 + precio_base/3 (SIN interés)"""
        precio_base = 120000.0  # Número que sea divisible por 2 y 3
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 1
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        expected = precio_base / 2 + precio_base / 3  # 60,000 + 40,000 = 100,000
        
        self.assertEqual(cuotas, expected, 
                        f"Mes 1: Debe sumar comisión ({precio_base/2}) + depósito ({precio_base/3}) = {expected}")
    
    def test_comision_2_cuotas_deposito_3_cuotas_mes_3(self):
        """Test 62: Con comisión "2 cuotas" y depósito "3 cuotas", en el mes 3 debe sumarse solo precio_base/3"""
        precio_base = 120000.0
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 3
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        expected = precio_base / 3  # Solo depósito: 40,000 (sin interés)
        
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
        """Test 64: Las cuotas adicionales deben calcularse sobre el precio_base actualizado, no el original (SIN interés)"""
        # Caso: precio original $100,000, actualizado a $110,000
        precio_original = 100000.0
        precio_base_actualizado = 110000.0  # Después de actualización
        
        comision = "2 cuotas"
        deposito = "3 cuotas"
        mes_actual = 1
        
        # Las cuotas deben calcularse sobre el precio actualizado sin interés
        cuotas = calcular_cuotas_adicionales(precio_base_actualizado, comision, deposito, mes_actual)
        expected = precio_base_actualizado / 2 + precio_base_actualizado / 3  # 55,000 + 36,667
        
        self.assertAlmostEqual(cuotas, expected, places=2,
                              msg="Las cuotas deben calcularse sobre precio actualizado, no original")
        
        # Verificar que NO es sobre el precio original
        cuotas_sobre_original = precio_original / 2 + precio_original / 3
        self.assertNotEqual(cuotas, cuotas_sobre_original,
                           "Las cuotas NO deben calcularse sobre precio original")
    
    def test_actualizacion_mes_3_afecta_tercera_cuota_deposito(self):
        """Test 65: Si hay actualización en el mes 3, la tercera cuota de depósito debe usar el precio actualizado (SIN interés)"""
        # Escenario: Contrato trimestral con actualización en mes 3
        precio_base_mes_1_2 = 100000.0  # Primeros 2 meses
        precio_base_mes_3 = 110000.0    # Después de actualización en mes 3
        
        comision = "2 cuotas"  # Solo meses 1 y 2
        deposito = "3 cuotas"  # Meses 1, 2 y 3
        
        # Mes 1: cuotas sobre precio original sin interés
        cuotas_mes_1 = calcular_cuotas_adicionales(precio_base_mes_1_2, comision, deposito, 1)
        expected_mes_1 = precio_base_mes_1_2 / 2 + precio_base_mes_1_2 / 3  # 50,000 + 33,333
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


class TestMontoComisionFijo(unittest.TestCase):
    """Tests adicionales: Monto comisión fijo"""
    
    def test_monto_comision_fijo_2_cuotas(self):
        """Test: Con monto_comision fijo en 2 cuotas, debe usar ese monto en lugar del precio_base"""
        precio_base = 300000.0
        monto_comision = 250000.0  # Monto negociado
        comision = "2 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual, monto_comision)
            expected = monto_comision / 2  # 125,000
            self.assertEqual(cuotas, expected,
                           f"Mes {mes_actual}: Debe usar monto_comision ({monto_comision}) dividido en 2 = {expected}")
    
    def test_monto_comision_fijo_3_cuotas(self):
        """Test: Con monto_comision fijo en 3 cuotas, debe usar ese monto"""
        precio_base = 300000.0
        monto_comision = 400000.0  # Monto mayor negociado
        comision = "3 cuotas"
        deposito = "Pagado"
        
        for mes_actual in [1, 2, 3]:
            cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual, monto_comision)
            expected = monto_comision / 3  # 133,333.33
            self.assertAlmostEqual(cuotas, expected, places=2,
                                 msg=f"Mes {mes_actual}: Debe usar monto_comision ({monto_comision}) dividido en 3 = {expected}")
    
    def test_monto_comision_con_deposito(self):
        """Test: Con monto_comision y depósito, el depósito sigue usando precio_base"""
        precio_base = 300000.0
        monto_comision = 200000.0
        comision = "2 cuotas"
        deposito = "2 cuotas"
        
        cuotas_mes_1 = calcular_cuotas_adicionales(precio_base, comision, deposito, 1, monto_comision)
        expected = (monto_comision / 2) + (precio_base / 2)  # 100,000 + 150,000 = 250,000
        self.assertEqual(cuotas_mes_1, expected,
                       "Debe usar monto_comision para comisión pero precio_base para depósito")
    
    def test_sin_monto_comision_usa_precio_base(self):
        """Test: Sin monto_comision, debe usar precio_base como antes"""
        precio_base = 300000.0
        monto_comision = None  # No especificado
        comision = "2 cuotas"
        deposito = "Pagado"
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, 1, monto_comision)
        expected = precio_base / 2  # 150,000
        self.assertEqual(cuotas, expected,
                       "Sin monto_comision debe usar precio_base")
    
    def test_monto_comision_cero_usa_precio_base(self):
        """Test: Con monto_comision en 0, debe usar precio_base"""
        precio_base = 300000.0
        monto_comision = 0.0  # Explícitamente 0
        comision = "2 cuotas"
        deposito = "Pagado"
        
        cuotas = calcular_cuotas_adicionales(precio_base, comision, deposito, 1, monto_comision)
        expected = precio_base / 2  # 150,000
        self.assertEqual(cuotas, expected,
                       "Con monto_comision=0 debe usar precio_base")


if __name__ == '__main__':
    unittest.main()
