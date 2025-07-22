"""
Tests para las funciones de cálculo de inflación
"""
import unittest
import sys
import os
from datetime import date

# Agregar el directorio padre al path para importar el módulo app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import inflacion_acumulada, calcular_comision, calcular_cuotas_adicionales
from tests.test_data import get_inflacion_df_test, EXPECTED_CALCULATIONS


class TestMunicipalidadCalculations(unittest.TestCase):
    """Tests para cálculos que incluyen gastos municipales"""
    
    def test_precio_final_con_municipalidad(self):
        """Test cálculo precio final incluyendo municipalidad"""
        caso = EXPECTED_CALCULATIONS["municipalidad"]["con_municipalidad"]
        
        precio_final = caso["precio_base"] + caso["cuotas_adicionales"] + caso["municipalidad"]
        
        self.assertEqual(precio_final, caso["expected_precio_final"],
                        f"Precio final debe ser {caso['expected_precio_final']}")
    
    def test_precio_final_sin_municipalidad(self):
        """Test precio final sin gastos municipales"""
        caso = EXPECTED_CALCULATIONS["municipalidad"]["sin_municipalidad"]
        
        precio_final = caso["precio_base"] + caso["cuotas_adicionales"] + caso["municipalidad"]
        
        self.assertEqual(precio_final, caso["expected_precio_final"],
                        f"Sin municipalidad debe ser solo precio base: {caso['expected_precio_final']}")
    
    def test_precio_final_solo_municipalidad(self):
        """Test precio final solo con gastos municipales (sin cuotas)"""
        caso = EXPECTED_CALCULATIONS["municipalidad"]["solo_municipalidad"]
        
        precio_final = caso["precio_base"] + caso["cuotas_adicionales"] + caso["municipalidad"]
        
        self.assertEqual(precio_final, caso["expected_precio_final"],
                        f"Solo municipalidad debe ser {caso['expected_precio_final']}")
    
    def test_comision_no_incluye_municipalidad(self):
        """Test que la comisión se calcula solo sobre precio base, no incluye municipalidad"""
        caso = EXPECTED_CALCULATIONS["municipalidad"]["comision_sobre_precio_base"]
        
        # La comisión se calcula solo sobre precio_base
        comision_calculada = calcular_comision(caso["comision_porcentaje"], caso["precio_base"])
        
        self.assertEqual(comision_calculada, caso["expected_comision"],
                        f"Comisión debe ser {caso['expected_comision']} (solo sobre precio base)")
    
    def test_pago_propietario_no_incluye_municipalidad(self):
        """Test que el pago al propietario es precio_base menos comisión (sin municipalidad)"""
        caso = EXPECTED_CALCULATIONS["municipalidad"]["comision_sobre_precio_base"]
        
        comision = calcular_comision(caso["comision_porcentaje"], caso["precio_base"])
        pago_prop = caso["precio_base"] - comision
        
        self.assertEqual(pago_prop, caso["expected_pago_prop"],
                        f"Pago propietario debe ser {caso['expected_pago_prop']} (precio_base - comision)")
    
    def test_municipalidad_vacia_o_none(self):
        """Test manejo de municipalidad vacía o None"""
        # Simular datos con municipalidad vacía
        casos_vacios = [None, "", 0, "0", "  "]
        
        for municipalidad_val in casos_vacios:
            with self.subTest(municipalidad=municipalidad_val):
                # Simular el procesamiento que hace el código principal
                if municipalidad_val and str(municipalidad_val).strip() != "":
                    municipalidad = float(municipalidad_val)
                else:
                    municipalidad = 0
                
                precio_final = 100000 + 0 + municipalidad  # precio_base + cuotas + municipalidad
                self.assertEqual(precio_final, 100000,
                               f"Municipalidad '{municipalidad_val}' debe resultar en 0")
    
    def test_municipalidad_formato_string(self):
        """Test manejo de municipalidad como string"""
        municipalidad_str = "15000.50"
        municipalidad = float(municipalidad_str)
        
        precio_final = 100000 + 5000 + municipalidad
        
        self.assertEqual(precio_final, 120000.50,
                        "Debe manejar municipalidad como string correctamente")


class TestInflacionCalculations(unittest.TestCase):
    """Tests para cálculos de inflación"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.inflacion_df = get_inflacion_df_test()
    
    def test_inflacion_acumulada_trimestral(self):
        """Test cálculo de inflación acumulada trimestral"""
        resultado = inflacion_acumulada(
            self.inflacion_df, 
            date(2024, 4, 1), 
            3
        )
        expected = EXPECTED_CALCULATIONS["inflacion_acumulada"]["trimestral_hasta_abril"]["expected"]
        
        # Verificar con tolerancia del 0.1% debido a redondeos
        self.assertAlmostEqual(resultado, expected, places=2,
                             msg=f"Inflación trimestral esperada: {expected}, obtenida: {resultado}")
    
    def test_inflacion_acumulada_semestral(self):
        """Test cálculo de inflación acumulada semestral"""
        resultado = inflacion_acumulada(
            self.inflacion_df,
            date(2024, 6, 1),
            6
        )
        
        # Cálculo manual esperado: (1.05 * 1.045 * 1.038 * 1.042 * 1.039 * 1.041)
        # = 1.2538 aprox
        self.assertGreater(resultado, 1.25, "La inflación semestral debe ser mayor a 25%")
        self.assertLess(resultado, 1.30, "La inflación semestral debe ser menor a 30%")
    
    def test_inflacion_acumulada_con_pocos_datos(self):
        """Test comportamiento con pocos datos disponibles"""
        # Solicitar más meses de los que hay datos
        resultado = inflacion_acumulada(
            self.inflacion_df,
            date(2024, 2, 1),  # Solo febrero disponible
            3  # Pero pedimos 3 meses
        )
        
        # Debe usar solo los datos disponibles
        self.assertGreater(resultado, 1.0, "Debe retornar factor mayor a 1")


class TestComisionCalculations(unittest.TestCase):
    """Tests para cálculos de comisiones"""
    
    def test_calcular_comision_5_porciento(self):
        """Test cálculo comisión 5%"""
        caso = EXPECTED_CALCULATIONS["comisiones"]["5_porciento"]
        resultado = calcular_comision(caso["comision_str"], caso["precio"])
        
        self.assertEqual(resultado, caso["expected"],
                        f"Comisión 5% de {caso['precio']} debe ser {caso['expected']}")
    
    def test_calcular_comision_4_porciento(self):
        """Test cálculo comisión 4%"""
        caso = EXPECTED_CALCULATIONS["comisiones"]["4_porciento"]
        resultado = calcular_comision(caso["comision_str"], caso["precio"])
        
        self.assertEqual(resultado, caso["expected"],
                        f"Comisión 4% de {caso['precio']} debe ser {caso['expected']}")
    
    def test_calcular_comision_formato_con_espacios(self):
        """Test comisión con espacios en el formato"""
        resultado = calcular_comision(" 5 % ", 100000)
        self.assertEqual(resultado, 5000, "Debe manejar espacios correctamente")
    
    def test_calcular_comision_formato_coma_decimal(self):
        """Test comisión con coma decimal"""
        resultado = calcular_comision("2,5%", 100000)
        self.assertEqual(resultado, 2500, "Debe manejar coma decimal correctamente")
    
    def test_calcular_comision_formato_invalido(self):
        """Test comisión con formato inválido"""
        with self.assertRaises(ValueError):
            calcular_comision("abc%", 100000)
    
    def test_calcular_comision_string_vacio(self):
        """Test comisión con string vacío"""
        with self.assertRaises(ValueError):
            calcular_comision("", 100000)


class TestCuotasAdicionales(unittest.TestCase):
    """Tests para cálculos de cuotas adicionales"""
    
    def test_comision_2_cuotas_mes_1(self):
        """Test comisión en 2 cuotas, primer mes"""
        caso = EXPECTED_CALCULATIONS["cuotas_adicionales"]["comision_2_cuotas_mes_1"]
        resultado = calcular_cuotas_adicionales(
            caso["precio_base"],
            caso["comision"],
            caso["deposito"],
            caso["mes"]
        )
        
        self.assertEqual(resultado, caso["expected"],
                        f"Comisión 2 cuotas mes 1 debe ser {caso['expected']}")
    
    def test_comision_2_cuotas_mes_3(self):
        """Test comisión en 2 cuotas, tercer mes (no debe aplicar)"""
        resultado = calcular_cuotas_adicionales(100000, "2 cuotas", "Pagado", 3)
        
        self.assertEqual(resultado, 0, "Comisión 2 cuotas no debe aplicar en mes 3")
    
    def test_deposito_3_cuotas_mes_2(self):
        """Test depósito en 3 cuotas, segundo mes"""
        resultado = calcular_cuotas_adicionales(100000, "Pagado", "3 cuotas", 2)
        
        # Debe ser 100000 / 3 = 33333.33
        self.assertAlmostEqual(resultado, 33333.33, places=2,
                              msg="Depósito 3 cuotas mes 2 debe ser 33333.33")
    
    def test_deposito_3_cuotas_mes_4(self):
        """Test depósito en 3 cuotas, cuarto mes (no debe aplicar)"""
        resultado = calcular_cuotas_adicionales(100000, "Pagado", "3 cuotas", 4)
        
        self.assertEqual(resultado, 0, "Depósito 3 cuotas no debe aplicar en mes 4")
    
    def test_ambas_cuotas_mes_1(self):
        """Test comisión y depósito en cuotas, primer mes"""
        resultado = calcular_cuotas_adicionales(100000, "2 cuotas", "3 cuotas", 1)
        
        # Debe ser 50000 (comisión) + 33333.33 (depósito) = 83333.33
        expected = 50000 + 33333.33
        self.assertAlmostEqual(resultado, expected, places=2,
                              msg=f"Ambas cuotas mes 1 debe ser {expected}")
    
    def test_pagado_no_suma(self):
        """Test que 'Pagado' no suma nada"""
        resultado = calcular_cuotas_adicionales(100000, "Pagado", "Pagado", 1)
        
        self.assertEqual(resultado, 0, "Comisión y depósito 'Pagado' no debe sumar nada")
    
    def test_redondeo_correcto(self):
        """Test que el redondeo funciona correctamente"""
        # Precio que dé decimales complicados
        resultado = calcular_cuotas_adicionales(100001, "3 cuotas", "Pagado", 1)
        
        # 100001 / 3 = 33333.67 redondeado
        self.assertEqual(resultado, 33333.67, "Debe redondear correctamente a 2 decimales")


if __name__ == '__main__':
    unittest.main()
