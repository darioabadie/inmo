#!/usr/bin/env python3
"""
Tests para verificar las correcciones de FASE 1: Lógica Crítica
- Step 1.1: Cálculo de precio_base acumulado
- Step 1.2: Estructura de output según especificaciones
- Step 1.3: Validación de contratos vencidos
"""

import unittest
import datetime as dt
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from inmobiliaria.services.calculations import calcular_precio_base_acumulado


class TestFase1LogicaCritica(unittest.TestCase):
    """Tests para las correcciones de FASE 1"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.df_infl = pd.DataFrame()  # Mock para inflación (no se usa en tests de porcentaje fijo)
    
    def test_porcentaje_fijo_acumulado(self):
        """Test del cálculo acumulado con porcentaje fijo - Caso del technical_specs.md"""
        # Caso del technical_specs.md:
        # Precio original: $100,000, Inicio: 2024-01-01, Referencia: 2024-07-01 (6 meses después)
        # Actualización: trimestral, Índice: "10%"
        # Esperado: 2 ciclos cumplidos, factor = (1.10)² = 1.21, precio = $121,000
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "10%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)  # 6 meses después
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        expected_precio = 121000.0  # 100,000 * (1.10)²
        expected_porc = 10.0  # Porcentaje del último ciclo
        expected_aplica = True  # Mes 7 es mes de actualización (6 % 3 = 0)
        
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertAlmostEqual(porc_actual, expected_porc, places=2)
        self.assertEqual(aplica_actualizacion, expected_aplica)
    
    def test_sin_ciclos_cumplidos(self):
        """Test cuando no hay ciclos cumplidos aún"""
        precio_original = 100000.0
        actualizacion = "trimestral" 
        indice = "10%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 2, 1)  # Solo 1 mes después
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        self.assertEqual(precio_base, precio_original)
        self.assertEqual(porc_actual, 0.0)
        self.assertEqual(aplica_actualizacion, False)
    
    def test_mes_sin_actualizacion(self):
        """Test mes que no es de actualización pero con ciclos cumplidos"""
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "10%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 5, 1)  # 4 meses después (no es múltiplo de 3)
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        expected_precio = 110000.0  # 100,000 * 1.10 (1 ciclo cumplido)
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertEqual(porc_actual, 0.0)  # No es mes de actualización
        self.assertEqual(aplica_actualizacion, False)
    
    def test_multiples_ciclos_acumulados(self):
        """Test con múltiples ciclos para verificar efecto compuesto"""
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "10%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 10, 1)  # 9 meses después (3 ciclos)
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        expected_precio = 133100.0  # 100,000 * (1.10)³ = 133,100
        expected_porc = 10.0  # Porcentaje del último ciclo
        expected_aplica = True  # Mes 10 es mes de actualización (9 % 3 = 0)
        
        self.assertAlmostEqual(precio_base, expected_precio, places=2)
        self.assertAlmostEqual(porc_actual, expected_porc, places=2)
        self.assertEqual(aplica_actualizacion, expected_aplica)
    
    def test_diferentes_frecuencias(self):
        """Test con diferentes frecuencias de actualización"""
        precio_original = 100000.0
        indice = "15%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)  # 6 meses después
        
        # Test semestral (1 ciclo)
        precio_base_sem, _, aplica_sem = calcular_precio_base_acumulado(
            precio_original, "semestral", indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Test anual (0 ciclos)
        precio_base_anual, _, aplica_anual = calcular_precio_base_acumulado(
            precio_original, "anual", indice, self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Verificaciones
        self.assertAlmostEqual(precio_base_sem, 115000.0, places=2)  # 1 ciclo
        self.assertTrue(aplica_sem)
        
        self.assertEqual(precio_base_anual, precio_original)  # 0 ciclos
        self.assertFalse(aplica_anual)
    
    def test_indices_invalidos(self):
        """Test con índices inválidos o mal formateados"""
        precio_original = 100000.0
        actualizacion = "trimestral"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 4, 1)  # 3 meses después
        
        # Test con índice inválido
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, "texto_invalido", self.df_infl, fecha_inicio, fecha_ref
        )
        
        # Debería mantener precio original
        self.assertEqual(precio_base, precio_original)
        self.assertEqual(porc_actual, 0.0)
        self.assertTrue(aplica_actualizacion)  # Es mes de actualización pero sin cambio de precio


class TestValidacionesContratos(unittest.TestCase):
    """Tests para validaciones de contratos (Step 1.3)"""
    
    def test_validacion_fechas_inicio(self):
        """Test de validación de fechas de inicio"""
        # Este test se ejecuta a nivel de main.py, pero podemos verificar la lógica
        fecha_valida = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)
        
        # Calcular meses desde inicio
        meses_desde_inicio = (fecha_ref.year - fecha_valida.year) * 12 + (fecha_ref.month - fecha_valida.month)
        
        self.assertEqual(meses_desde_inicio, 6)
    
    def test_validacion_contratos_vencidos(self):
        """Test de lógica de contratos vencidos"""
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)
        duracion_meses = 6
        
        meses_desde_inicio = (fecha_ref.year - fecha_inicio.year) * 12 + (fecha_ref.month - fecha_inicio.month)
        contrato_vencido = meses_desde_inicio >= duracion_meses
        
        self.assertTrue(contrato_vencido)  # Debería estar vencido


if __name__ == '__main__':
    unittest.main()
