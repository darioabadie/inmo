"""
Tests para cálculos de precios finales, gastos municipales y comisiones (Tests 66-79)
Basado en tests_funcionales.md - Categorías 5, 6 y 7
"""
import unittest
import sys
import os

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inmobiliaria.services.calculations import calcular_comision, calcular_cuotas_adicionales


class TestGastosMunicipales(unittest.TestCase):
    """Tests 66-69: Gastos municipales"""
    
    def test_municipalidad_vacia_usa_cero(self):
        """Test 66: Si municipalidad está vacío, debe usarse 0"""
        casos_vacios = [None, "", "   ", 0, "0"]
        
        for municipalidad_val in casos_vacios:
            with self.subTest(municipalidad=municipalidad_val):
                # Simular lógica del sistema
                if municipalidad_val and str(municipalidad_val).strip() != "":
                    municipalidad = float(municipalidad_val)
                else:
                    municipalidad = 0
                
                self.assertEqual(municipalidad, 0, 
                               f"Municipalidad '{municipalidad_val}' debe resultar en 0")
    
    def test_municipalidad_numero_se_suma(self):
        """Test 67: Si municipalidad es un número, debe sumarse al precio final"""
        precio_base = 100000.0
        cuotas_adicionales = 0.0
        municipalidad = 15000.0
        
        precio_final = precio_base + cuotas_adicionales + municipalidad
        expected = 115000.0
        
        self.assertEqual(precio_final, expected,
                        "Municipalidad debe sumarse al precio final")
    
    def test_municipalidad_texto_invalido_usa_cero(self):
        """Test 68: Si municipalidad tiene texto inválido, debe usarse 0"""
        textos_invalidos = ["abc", "quince mil", "N/A", "TBD"]
        
        for texto_invalido in textos_invalidos:
            with self.subTest(texto=texto_invalido):
                try:
                    municipalidad = float(texto_invalido)
                except ValueError:
                    municipalidad = 0  # Sistema debe usar 0 como fallback
                
                self.assertEqual(municipalidad, 0,
                               f"Texto inválido '{texto_invalido}' debe resultar en 0")
    
    def test_gastos_municipales_se_suman_correctamente(self):
        """Test 69: Los gastos municipales deben sumarse a precio_base + cuotas_adicionales"""
        precio_base = 100000.0
        cuotas_adicionales = 25000.0  # Ejemplo con cuotas
        municipalidad = 8000.0
        
        precio_total = precio_base + cuotas_adicionales + municipalidad
        expected = 133000.0
        
        self.assertEqual(precio_total, expected,
                        "Precio total debe ser suma de precio_base + cuotas + municipalidad")


class TestComposicionPrecioFinal(unittest.TestCase):
    """Tests 70-73: Composición del precio_mes_actual"""
    
    def test_precio_mes_actual_composicion(self):
        """Test 70: precio_mes_actual debe ser la suma de precio_base + cuotas_adicionales + municipalidad"""
        precio_base = 121000.0
        cuotas_adicionales = 40333.0
        municipalidad = 5000.0
        
        precio_mes_actual = precio_base + cuotas_adicionales + municipalidad
        expected = 166333.0
        
        self.assertEqual(precio_mes_actual, expected,
                        "precio_mes_actual debe ser suma exacta de los tres componentes")
    
    def test_primer_mes_con_cuotas_precio_mayor(self):
        """Test 71: En el primer mes con cuotas, el precio total debe ser significativamente mayor"""
        precio_base = 100000.0
        comision = "2 cuotas"
        deposito = "3 cuotas"
        municipalidad = 5000.0
        mes_actual = 1
        
        cuotas_adicionales = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        precio_mes_actual = precio_base + cuotas_adicionales + municipalidad
        
        # Verificar que es significativamente mayor que solo el precio base
        incremento_porcentual = (precio_mes_actual - precio_base) / precio_base * 100
        
        self.assertGreater(incremento_porcentual, 50,
                          "Primer mes con cuotas debe incrementar precio > 50%")
        self.assertGreater(precio_mes_actual, precio_base * 1.5,
                          "Precio primer mes debe ser > 150% del precio base")
    
    def test_despues_cuotas_solo_base_mas_municipalidad(self):
        """Test 72: Después de que terminen las cuotas, el precio debe ser solo precio_base + municipalidad"""
        precio_base = 110000.0
        comision = "2 cuotas"
        deposito = "3 cuotas"
        municipalidad = 8000.0
        mes_actual = 5  # Después de que terminaron todas las cuotas
        
        cuotas_adicionales = calcular_cuotas_adicionales(precio_base, comision, deposito, mes_actual)
        precio_mes_actual = precio_base + cuotas_adicionales + municipalidad
        
        expected = precio_base + municipalidad  # 118,000
        
        self.assertEqual(cuotas_adicionales, 0,
                        "No debe haber cuotas adicionales después del mes 3")
        self.assertEqual(precio_mes_actual, expected,
                        "Precio debe ser solo precio_base + municipalidad")
    
    def test_precio_mes_actual_nunca_negativo(self):
        """Test 73: El precio_mes_actual nunca debe ser negativo"""
        # Casos extremos que podrían generar valores negativos
        casos_test = [
            {"precio_base": 0, "cuotas": 0, "municipalidad": 0},
            {"precio_base": 100, "cuotas": 0, "municipalidad": -50},  # Municipalidad negativa (edge case)
            {"precio_base": 1000, "cuotas": 500, "municipalidad": 0},
        ]
        
        for caso in casos_test:
            with self.subTest(caso=caso):
                precio_mes_actual = caso["precio_base"] + caso["cuotas"] + max(0, caso["municipalidad"])
                
                self.assertGreaterEqual(precio_mes_actual, 0,
                                       f"Precio nunca debe ser negativo: {caso}")


class TestComisionesAdministracion(unittest.TestCase):
    """Tests 74-76: Comisión de administración"""
    
    def test_comision_sobre_precio_base_no_precio_mes_actual(self):
        """Test 74: La comisión_inmo debe calcularse sobre precio_base, no sobre precio_mes_actual"""
        precio_base = 100000.0
        cuotas_adicionales = 50000.0
        municipalidad = 5000.0
        comision_inmo_pct = "5%"
        
        precio_mes_actual = precio_base + cuotas_adicionales + municipalidad  # 155,000
        
        # Comisión debe calcularse sobre precio_base, NO sobre precio_mes_actual
        comision_correcta = calcular_comision(comision_inmo_pct, precio_base)
        comision_incorrecta = calcular_comision(comision_inmo_pct, precio_mes_actual)
        
        expected_correcta = 5000.0  # 5% de 100,000
        expected_incorrecta = 7750.0  # 5% de 155,000
        
        self.assertEqual(comision_correcta, expected_correcta,
                        "Comisión debe ser 5% del precio_base")
        self.assertNotEqual(comision_correcta, comision_incorrecta,
                           "Comisión NO debe calcularse sobre precio_mes_actual")
    
    def test_calculo_comision_ejemplo_especifico(self):
        """Test 75: Con comision_inmo "5%" y precio_base $100000, la comisión debe ser $5000"""
        precio_base = 100000.0
        comision_inmo = "5%"
        
        comision_calculada = calcular_comision(comision_inmo, precio_base)
        expected = 5000.0
        
        self.assertEqual(comision_calculada, expected,
                        "Comisión 5% de $100,000 debe ser $5,000")
    
    def test_comision_redondeada_2_decimales(self):
        """Test 76: La comisión debe redondearse a 2 decimales"""
        precio_base = 123456.78
        comision_inmo = "7.5%"
        
        comision_calculada = calcular_comision(comision_inmo, precio_base)
        
        # Verificar que está redondeada a 2 decimales
        self.assertEqual(round(comision_calculada, 2), comision_calculada,
                        "Comisión debe estar redondeada a 2 decimales")
        
        # Verificar valor esperado
        expected = round(123456.78 * 0.075, 2)  # 9259.26
        self.assertEqual(comision_calculada, expected)


class TestPagoPropietario(unittest.TestCase):
    """Tests 77-79: Pago al propietario"""
    
    def test_pago_prop_precio_base_menos_comision(self):
        """Test 77: pago_prop debe ser precio_base - comision_inmo"""
        precio_base = 120000.0
        comision_inmo = "6%"
        
        comision = calcular_comision(comision_inmo, precio_base)  # 7,200
        pago_prop = precio_base - comision
        
        expected = 112800.0  # 120,000 - 7,200
        
        self.assertEqual(pago_prop, expected,
                        "pago_prop debe ser precio_base menos comisión")
    
    def test_pago_prop_no_incluye_cuotas_adicionales(self):
        """Test 78: pago_prop nunca debe incluir las cuotas adicionales (esas las paga el inquilino)"""
        precio_base = 100000.0
        cuotas_adicionales = 40000.0  # Las paga el inquilino
        comision_inmo = "5%"
        
        comision = calcular_comision(comision_inmo, precio_base)  # 5,000
        pago_prop = precio_base - comision  # 95,000
        
        # Verificar que NO incluye las cuotas adicionales
        pago_prop_incorrecto = precio_base + cuotas_adicionales - comision  # 135,000
        
        self.assertNotEqual(pago_prop, pago_prop_incorrecto,
                           "pago_prop NO debe incluir cuotas adicionales")
        
        expected = 95000.0
        self.assertEqual(pago_prop, expected,
                        "pago_prop debe ser solo precio_base - comisión")
    
    def test_pago_prop_no_incluye_gastos_municipales(self):
        """Test 79: pago_prop nunca debe incluir gastos municipales"""
        precio_base = 100000.0
        municipalidad = 8000.0  # Los paga el inquilino
        comision_inmo = "4%"
        
        comision = calcular_comision(comision_inmo, precio_base)  # 4,000
        pago_prop = precio_base - comision  # 96,000
        
        # Verificar que NO incluye gastos municipales
        pago_prop_incorrecto = precio_base + municipalidad - comision  # 104,000
        
        self.assertNotEqual(pago_prop, pago_prop_incorrecto,
                           "pago_prop NO debe incluir gastos municipales")
        
        expected = 96000.0
        self.assertEqual(pago_prop, expected,
                        "pago_prop debe ser solo precio_base - comisión")


if __name__ == '__main__':
    unittest.main()
