#!/usr/bin/env python3
"""
Test específico para verificar las nuevas funcionalidades de descuento y expensas.
"""

import unittest
import datetime as dt
from unittest.mock import patch, MagicMock
from inmobiliaria.historical import generar_meses_faltantes
from inmobiliaria.models import Propiedad, Contrato


class TestNuevasFuncionalidades(unittest.TestCase):
    
    def setUp(self):
        """Configuración para todos los tests"""
        self.propiedad_test = Propiedad(
            nombre="Casa Test",
            direccion="Calle Falsa 123",
            propietario="Juan Perez", 
            inquilino="Ana Garcia"
        )
        
        self.contrato_test = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=24,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        # Mock para inflación
        self.inflacion_df = MagicMock()
    
    def test_funcionalidad_descuento_15_porciento(self):
        """Test: Verificar que el descuento del 15% se aplica correctamente"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df,
                municipalidad=1000.0, luz=500.0, gas=300.0, expensas=2000.0, descuento_porcentaje=15.0
            )
        
        registro = registros[0]
        
        # Verificar cálculos
        self.assertEqual(registro['precio_original'], 100000.0)
        self.assertEqual(registro['descuento'], "15.0%")
        self.assertEqual(registro['precio_descuento'], 85000.0)  # 100000 * 0.85
        
        # Verificar precio final = precio_descuento + adicionales
        precio_final_esperado = 85000.0 + 0.0 + 1000.0 + 500.0 + 300.0 + 2000.0  # 88800.0
        self.assertEqual(registro['precio_final'], precio_final_esperado)
    
    def test_funcionalidad_expensas_incluidas(self):
        """Test: Verificar que las expensas se incluyen en el precio final"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df,
                municipalidad=1000.0, luz=500.0, gas=300.0, expensas=3500.0, descuento_porcentaje=0.0
            )
        
        registro = registros[0]
        
        # Sin descuento
        self.assertEqual(registro['precio_descuento'], 100000.0)
        self.assertEqual(registro['expensas'], 3500.0)
        
        # Verificar que expensas se suma al precio final
        precio_final_esperado = 100000.0 + 0.0 + 1000.0 + 500.0 + 300.0 + 3500.0  # 105300.0
        self.assertEqual(registro['precio_final'], precio_final_esperado)
    
    def test_comision_calculada_sobre_precio_descuento(self):
        """Test: Verificar que la comisión se calcula sobre el precio con descuento"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            # Mock para calcular_comision para verificar que recibe precio_descuento
            with patch('inmobiliaria.historical.calcular_comision') as mock_comision:
                mock_comision.return_value = 4250.0  # 5% de 85000
                
                registros = generar_meses_faltantes(
                    self.propiedad_test, self.contrato_test, fecha_limite,
                    100000.0, "", self.inflacion_df,
                    municipalidad=0.0, luz=0.0, gas=0.0, expensas=0.0, descuento_porcentaje=15.0
                )
                
                # Verificar que calcular_comision fue llamada con precio_descuento
                mock_comision.assert_called_with("5%", 85000.0)
        
        registro = registros[0]
        self.assertEqual(registro['comision_inmo'], 4250.0)
        self.assertEqual(registro['pago_prop'], 80750.0)  # 85000 - 4250
    
    def test_estructura_columnas_completa(self):
        """Test: Verificar que todas las columnas nuevas están presentes"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df,
                municipalidad=1000.0, luz=500.0, gas=300.0, expensas=2000.0, descuento_porcentaje=10.0
            )
        
        registro = registros[0]
        
        # Verificar presencia de todas las columnas nuevas
        self.assertIn('precio_final', registro)      # Antes precio_mes_actual
        self.assertIn('precio_original', registro)   # Antes precio_base  
        self.assertIn('precio_descuento', registro)  # Nueva
        self.assertIn('descuento', registro)         # Nueva
        self.assertIn('expensas', registro)          # Nueva
        
        # Verificar presencia de columnas existentes
        self.assertIn('luz', registro)
        self.assertIn('gas', registro)
        self.assertIn('municipalidad', registro)
    
    def test_logica_sin_descuento_ni_expensas(self):
        """Test: Verificar que funciona correctamente sin descuento ni expensas (compatibilidad)"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df,
                municipalidad=1000.0, luz=0.0, gas=0.0, expensas=0.0, descuento_porcentaje=0.0
            )
        
        registro = registros[0]
        
        # Sin descuento ni expensas, debería funcionar como antes
        self.assertEqual(registro['precio_original'], 100000.0)
        self.assertEqual(registro['precio_descuento'], 100000.0)  # Sin descuento
        self.assertEqual(registro['descuento'], "0.0%")
        self.assertEqual(registro['expensas'], 0.0)
        self.assertEqual(registro['precio_final'], 101000.0)  # 100000 + 1000 (municipalidad)


if __name__ == '__main__':
    unittest.main()
