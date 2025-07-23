#!/usr/bin/env python3
"""
Tests para verificar las correcciones de FASE 2: Lógica ICL
- Step 2.1: Función traer_factor_icl mejorada
- Step 2.2: Cálculo ICL acumulado implementado
"""

import unittest
import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import warnings

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from inmobiliaria.services.calculations import (
    traer_factor_icl, 
    calcular_factor_icl_acumulado_detallado,
    calcular_precio_base_acumulado
)
from inmobiliaria.services.inflation import traer_inflacion


class TestFase2LogicaICL(unittest.TestCase):
    """Tests para las correcciones de FASE 2 - Lógica ICL"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.mock_icl_response = {
            "results": [
                {"fecha": "2023-04-01", "valor": "125.0"},  # Más reciente
                {"fecha": "2023-03-01", "valor": "120.0"},
                {"fecha": "2023-02-01", "valor": "115.0"},
                {"fecha": "2023-01-01", "valor": "100.0"}   # Más antiguo
            ]
        }
        
    @patch('requests.get')
    def test_traer_factor_icl_basico(self, mock_get):
        """Test básico de la función traer_factor_icl mejorada"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.json.return_value = self.mock_icl_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_fin = dt.date(2023, 4, 1)
        
        factor = traer_factor_icl(fecha_inicio, fecha_fin)
        
        # Verificaciones
        expected_factor = 125.0 / 100.0  # valor_final / valor_inicio
        self.assertAlmostEqual(factor, expected_factor, places=4)
        self.assertEqual(factor, 1.25)
    
    @patch('requests.get')
    def test_traer_factor_icl_validaciones(self, mock_get):
        """Test de validaciones de la función ICL"""
        # Test con datos vacíos
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with self.assertRaises(ValueError):
            traer_factor_icl(dt.date(2023, 1, 1), dt.date(2023, 4, 1))
    
    @patch('requests.get')
    def test_traer_factor_icl_factor_extremo(self, mock_get):
        """Test con factor fuera de rango que debería generar warning"""
        # Configurar mock con factor muy alto
        extreme_response = {
            "results": [
                {"fecha": "2023-04-01", "valor": "400.0"},  # Factor 4.0
                {"fecha": "2023-01-01", "valor": "100.0"}
            ]
        }
        
        mock_response = MagicMock()
        mock_response.json.return_value = extreme_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            factor = traer_factor_icl(dt.date(2023, 1, 1), dt.date(2023, 4, 1))
            
            # Debería generar warning por factor extremo
            self.assertTrue(len(w) > 0)
            self.assertTrue("fuera de rango esperado" in str(w[0].message))
            self.assertEqual(factor, 4.0)
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_calcular_factor_icl_acumulado_detallado(self, mock_traer_icl):
        """Test de la función de cálculo acumulado detallado"""
        # Configurar mock para retornar factores conocidos
        mock_traer_icl.side_effect = [1.15, 1.20]  # Dos ciclos
        
        precio_original = 100000.0
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_ref = dt.date(2023, 7, 1)  # 6 meses = 2 ciclos trimestrales
        freq_meses = 3
        
        precio_final, factores_por_ciclo, factor_ultimo = calcular_factor_icl_acumulado_detallado(
            precio_original, fecha_inicio, fecha_ref, freq_meses, debug=False
        )
        
        # Verificaciones
        expected_factor_total = 1.15 * 1.20  # 1.38
        expected_precio_final = precio_original * expected_factor_total
        
        self.assertAlmostEqual(precio_final, expected_precio_final, places=2)
        self.assertEqual(len(factores_por_ciclo), 2)
        self.assertEqual(factor_ultimo, 1.20)  # Último factor
        
        # Verificar estructura de factores_por_ciclo
        self.assertEqual(factores_por_ciclo[0]['ciclo'], 1)
        self.assertEqual(factores_por_ciclo[0]['factor'], 1.15)
        self.assertEqual(factores_por_ciclo[1]['ciclo'], 2)
        self.assertEqual(factores_por_ciclo[1]['factor'], 1.20)
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_integracion_icl_sistema_principal(self, mock_traer_icl):
        """Test de integración del ICL en calcular_precio_base_acumulado"""
        # Configurar mock
        mock_traer_icl.side_effect = [1.25, 1.30]  # Dos ciclos
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "ICL"
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_ref = dt.date(2023, 7, 1)  # Mes de actualización (6 % 3 = 0)
        inflacion_df = traer_inflacion()  # No se usa para ICL
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        expected_factor_total = 1.25 * 1.30  # 1.625
        expected_precio = precio_original * expected_factor_total
        expected_porc = (1.30 - 1) * 100  # 30% del último ciclo
        
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertAlmostEqual(porc_actual, expected_porc, places=2)
        self.assertTrue(aplica_actualizacion)
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_icl_mes_sin_actualizacion(self, mock_traer_icl):
        """Test ICL en mes que no es de actualización"""
        # Configurar mock
        mock_traer_icl.return_value = 1.25
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "ICL"
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_ref = dt.date(2023, 5, 1)  # 4 meses, no es múltiplo de 3
        inflacion_df = traer_inflacion()
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        expected_precio = precio_original * 1.25  # 1 ciclo cumplido
        
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertEqual(porc_actual, 0.0)  # No es mes de actualización
        self.assertFalse(aplica_actualizacion)
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_icl_manejo_errores_api(self, mock_traer_icl):
        """Test manejo de errores de API ICL"""
        # Configurar mock para generar excepción en el segundo ciclo
        mock_traer_icl.side_effect = [1.25, Exception("API Error")]
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "ICL"
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_ref = dt.date(2023, 7, 1)  # 2 ciclos
        inflacion_df = traer_inflacion()
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Verificaciones: debería usar factor 1.0 para el ciclo con error
        expected_factor_total = 1.25 * 1.0  # Segundo ciclo usa factor neutro
        expected_precio = precio_original * expected_factor_total
        
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertTrue(aplica_actualizacion)
    
    def test_sin_ciclos_cumplidos_icl(self):
        """Test ICL sin ciclos cumplidos"""
        precio_original = 100000.0
        fecha_inicio = dt.date(2023, 1, 1)
        fecha_ref = dt.date(2023, 2, 1)  # Solo 1 mes
        freq_meses = 3
        
        precio_final, factores_por_ciclo, factor_ultimo = calcular_factor_icl_acumulado_detallado(
            precio_original, fecha_inicio, fecha_ref, freq_meses, debug=False
        )
        
        # Verificaciones
        self.assertEqual(precio_final, precio_original)
        self.assertEqual(len(factores_por_ciclo), 0)
        self.assertEqual(factor_ultimo, 0.0)


class TestComparacionDatosReales(unittest.TestCase):
    """Tests de comparación con patrones de datos reales conocidos"""
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_patron_inflacion_argentina_2023_2024(self, mock_traer_icl):
        """Test con patrones similares a la inflación argentina 2023-2024"""
        # Simular factores realistas para Argentina 2023-2024
        mock_traer_icl.side_effect = [1.25, 1.35, 1.15, 1.20]  # 4 trimestres
        
        precio_original = 50000.0  # Caso similar a SUSTERSIC- NAVARRO
        actualizacion = "trimestral" 
        indice = "ICL"
        fecha_inicio = dt.date(2023, 5, 1)
        fecha_ref = dt.date(2024, 5, 1)  # 12 meses = 4 ciclos
        inflacion_df = traer_inflacion()
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Factor esperado: 1.25 * 1.35 * 1.15 * 1.20 ≈ 2.30
        factor_esperado = 1.25 * 1.35 * 1.15 * 1.20
        precio_esperado = precio_original * factor_esperado
        
        self.assertAlmostEqual(precio_base, precio_esperado, places=2)
        self.assertAlmostEqual(porc_actual, 20.0, places=1)  # Último factor: 20%
        self.assertTrue(aplica_actualizacion)


if __name__ == '__main__':
    unittest.main()
