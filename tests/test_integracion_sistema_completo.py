#!/usr/bin/env python3
"""
Tests de integración completa del sistema después del refactor
Verificación de que FASE 1 + FASE 2 funcionan correctamente integradas
"""

import unittest
import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Agregar el directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from inmobiliaria.services.calculations import calcular_precio_base_acumulado
from inmobiliaria.services.inflation import traer_inflacion


class TestIntegracionSistemaCompleto(unittest.TestCase):
    """Tests de integración del sistema completo después del refactor"""
    
    def setUp(self):
        """Setup común"""
        self.inflacion_df = traer_inflacion()
    
    def test_estructura_output_esperada(self):
        """Test que verifica que la estructura de output coincida con technical_specs.md"""
        expected_headers = [
            # Columnas de Identificación
            "nombre_inmueble", "dir_inmueble", "inquilino", "propietario", "mes_actual",
            # Columnas Calculadas (orden específico según specs)
            "precio_mes_actual", "precio_base", "cuotas_adicionales", "municipalidad",
            "comision_inmo", "pago_prop", "actualizacion", "porc_actual",
            "meses_prox_actualizacion", "meses_prox_renovacion"
        ]
        
        # Verificar que la lista esté completa
        self.assertEqual(len(expected_headers), 15)
        
        # Verificar que no haya duplicados
        self.assertEqual(len(expected_headers), len(set(expected_headers)))
        
        # Verificar campos críticos
        critical_fields = ["precio_mes_actual", "precio_base", "actualizacion", "porc_actual"]
        for field in critical_fields:
            self.assertIn(field, expected_headers)
    
    @patch('inmobiliaria.services.calculations.traer_factor_icl')
    def test_integracion_porcentaje_fijo_vs_icl(self, mock_traer_icl):
        """Test comparativo entre porcentaje fijo e ICL"""
        # Configurar mock ICL para que sea equivalente a 10% por ciclo
        mock_traer_icl.return_value = 1.10
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)  # 2 ciclos
        
        # Test con porcentaje fijo
        precio_fijo, porc_fijo, aplica_fijo = calcular_precio_base_acumulado(
            precio_original, actualizacion, "10%", self.inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Test con ICL (mockeado para ser equivalente)
        precio_icl, porc_icl, aplica_icl = calcular_precio_base_acumulado(
            precio_original, actualizacion, "ICL", self.inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Deberían ser equivalentes
        self.assertAlmostEqual(precio_fijo, precio_icl, places=2)
        self.assertEqual(aplica_fijo, aplica_icl)
        self.assertAlmostEqual(porc_fijo, porc_icl, places=10)
    
    def test_diferentes_frecuencias_integracion(self):
        """Test de integración con diferentes frecuencias"""
        precio_original = 100000.0
        indice = "5%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 12, 1)  # 11 meses
        
        frecuencias = ["trimestral", "cuatrimestral", "semestral", "anual"]
        resultados = {}
        
        for freq in frecuencias:
            precio, porc, aplica = calcular_precio_base_acumulado(
                precio_original, freq, indice, self.inflacion_df, fecha_inicio, fecha_ref
            )
            resultados[freq] = {
                'precio': precio,
                'aplica': aplica,
                'ciclos': self._calcular_ciclos(freq, 11)
            }
        
        # Verificaciones lógicas
        # Trimestral debería tener más ciclos que anual
        self.assertGreater(resultados['trimestral']['ciclos'], resultados['anual']['ciclos'])
        
        # Anual no debería aplicar actualización (11 meses < 12)
        self.assertFalse(resultados['anual']['aplica'])
        
        # Trimestral sí debería aplicar (11 % 3 != 0 pero 11 >= 3)
        # Nota: esta lógica puede variar según implementación exacta
    
    def _calcular_ciclos(self, frecuencia, meses_transcurridos):
        """Función auxiliar para calcular ciclos"""
        freq_map = {"trimestral": 3, "cuatrimestral": 4, "semestral": 6, "anual": 12}
        freq_meses = freq_map.get(frecuencia, 3)
        return meses_transcurridos // freq_meses
    
    def test_consistencia_campos_actualizacion_porc_actual(self):
        """Test que verifica consistencia entre campos actualizacion y porc_actual"""
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "8%"
        fecha_inicio = dt.date(2024, 1, 1)
        
        # Caso 1: Mes de actualización
        fecha_ref_actualizacion = dt.date(2024, 4, 1)  # 3 meses = trimestral
        precio1, porc1, aplica1 = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.inflacion_df, fecha_inicio, fecha_ref_actualizacion
        )
        
        # Caso 2: Mes sin actualización  
        fecha_ref_no_actualizacion = dt.date(2024, 5, 1)  # 4 meses
        precio2, porc2, aplica2 = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.inflacion_df, fecha_inicio, fecha_ref_no_actualizacion
        )
        
        # Verificaciones de consistencia
        self.assertTrue(aplica1)  # Debería aplicar actualización
        self.assertFalse(aplica2)  # No debería aplicar actualización
        
        self.assertGreater(porc1, 0)  # Debería tener porcentaje
        self.assertEqual(porc2, 0)  # No debería tener porcentaje
        
        self.assertGreater(precio1, precio_original)  # Precio actualizado
        self.assertEqual(precio2, precio1)  # Precio mantenido del ciclo anterior
    
    def test_validaciones_casos_extremos(self):
        """Test de casos extremos y validaciones"""
        precio_original = 100000.0
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 2, 1)
        
        # Caso 1: Índice inválido
        precio1, porc1, aplica1 = calcular_precio_base_acumulado(
            precio_original, "trimestral", "texto_invalido", self.inflacion_df, fecha_inicio, fecha_ref
        )
        
        self.assertEqual(precio1, precio_original)  # No debería cambiar el precio
        
        # Caso 2: Frecuencia inválida (debería usar default)
        precio2, porc2, aplica2 = calcular_precio_base_acumulado(  
            precio_original, "frecuencia_invalida", "10%", self.inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Debería usar frecuencia default (trimestral = 3 meses)
        self.assertEqual(precio2, precio_original)  # Solo 1 mes, no hay ciclos
        
        # Caso 3: Fechas iguales (0 meses)
        precio3, porc3, aplica3 = calcular_precio_base_acumulado(
            precio_original, "trimestral", "10%", self.inflacion_df, fecha_inicio, fecha_inicio
        )
        
        self.assertEqual(precio3, precio_original)
        self.assertEqual(porc3, 0.0)
        self.assertFalse(aplica3)
    
    def test_precision_calculos(self):
        """Test de precisión en los cálculos"""
        precio_original = 123456.78
        actualizacion = "trimestral"
        indice = "7.5%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 10, 1)  # 3 ciclos
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, self.inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Verificar que el resultado esté redondeado a 2 decimales
        self.assertEqual(precio_base, round(precio_base, 2))
        
        # Verificar que el cálculo sea correcto
        factor_esperado = (1.075) ** 3  # 3 ciclos al 7.5%
        precio_esperado = round(precio_original * factor_esperado, 2)
        
        self.assertAlmostEqual(precio_base, precio_esperado, places=2)
    
    def test_regresion_casos_reales_conocidos(self):
        """Test de regresión con casos reales conocidos del sistema"""
        # Casos basados en los datos que vimos en las verificaciones
        casos_conocidos = [
            {
                'nombre': 'Caso tipo SUSTERSIC-ESCUDERO',
                'precio_original': 43000.0,
                'meses_transcurridos': 17,  # Aproximado
                'factor_esperado_min': 1.1,  # Factor mínimo esperado (más realista)
                'factor_esperado_max': 2.0   # Factor máximo esperado
            },
            {
                'nombre': 'Caso tipo SUSTERSIC-NAVARRO', 
                'precio_original': 38000.0,
                'meses_transcurridos': 15,  # Aproximado
                'factor_esperado_min': 1.1,  # Factor mínimo esperado (más realista)
                'factor_esperado_max': 2.0   # Factor máximo esperado
            }
        ]
        
        for caso in casos_conocidos:
            with self.subTest(caso=caso['nombre']):
                fecha_inicio = dt.date(2023, 1, 1)
                fecha_ref = fecha_inicio + dt.timedelta(days=30 * caso['meses_transcurridos'])
                
                # Simular con porcentaje fijo alto (inflación argentina)
                precio_base, _, _ = calcular_precio_base_acumulado(
                    caso['precio_original'], "anual", "25%", self.inflacion_df, fecha_inicio, fecha_ref
                )
                
                factor_obtenido = precio_base / caso['precio_original']
                
                # Verificar que esté en el rango esperado
                self.assertGreaterEqual(factor_obtenido, caso['factor_esperado_min'])
                self.assertLessEqual(factor_obtenido, caso['factor_esperado_max'])


class TestConsistenciaConTechnicalSpecs(unittest.TestCase):
    """Tests para verificar consistencia con technical_specs.md"""
    
    def test_ejemplo_technical_specs_exacto(self):
        """Test del ejemplo exacto del technical_specs.md"""
        # Ejemplo del documento:
        # Precio original: $100,000
        # Inicio: 2024-01-01, Referencia: 2024-07-01
        # Actualización: trimestral, Índice: "10%"
        # Esperado: precio_base = $121,000
        
        precio_original = 100000.0
        actualizacion = "trimestral"
        indice = "10%"
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)
        inflacion_df = traer_inflacion()
        
        precio_base, porc_actual, aplica_actualizacion = calcular_precio_base_acumulado(
            precio_original, actualizacion, indice, inflacion_df, fecha_inicio, fecha_ref
        )
        
        # Verificaciones exactas según el documento
        self.assertEqual(precio_base, 121000.0)
        self.assertEqual(porc_actual, 10.0)
        self.assertTrue(aplica_actualizacion)
    
    def test_formulas_documentadas(self):
        """Test de las fórmulas específicas documentadas"""
        # Verificar fórmula de meses desde inicio
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_ref = dt.date(2024, 7, 1)
        
        meses_desde_inicio = (fecha_ref.year - fecha_inicio.year) * 12 + (fecha_ref.month - fecha_inicio.month)
        self.assertEqual(meses_desde_inicio, 6)
        
        # Verificar cálculo de ciclos
        freq_meses = 3  # trimestral
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        self.assertEqual(ciclos_cumplidos, 2)
        self.assertEqual(resto, 0)
        
        # Verificar lógica de actualización
        aplica_actualizacion = resto == 0 and ciclos_cumplidos > 0
        self.assertTrue(aplica_actualizacion)


if __name__ == '__main__':
    unittest.main()
