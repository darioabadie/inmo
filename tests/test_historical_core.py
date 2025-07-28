#!/usr/bin/env python3
"""
Tests funcionales para el módulo historical.py - Funcionalidad núcleo
Tests 111-135: Validación del núcleo de generación de historial
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inmobiliaria.models import Propiedad, Contrato
from inmobiliaria.historical import (
    calcular_actualizacion_mes,
    generar_meses_faltantes,
    leer_historico_existente
)


class TestHistoricalCore(unittest.TestCase):
    """Tests del núcleo de funcionalidad del historial"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.propiedad_test = Propiedad(
            nombre="Casa Test",
            direccion="Calle Falsa 123",
            propietario="Juan Perez",
            inquilino="Ana Garcia"
        )
        
        self.contrato_icl = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=24,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="ICL",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        self.contrato_porcentaje = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=24,
            precio_original=100000.0,
            actualizacion="semestral",
            indice="10%",
            comision_inmo="5%",
            comision="2 cuotas",
            deposito="3 cuotas"
        )
        
        self.inflacion_df = pd.DataFrame({
            'año': [2024, 2024, 2024],
            'mes': [1, 2, 3],
            'ipc_mensual': [2.0, 1.5, 1.8]
        })

    # Test 111: Cálculo de actualización ICL básico
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_111_actualizacion_icl_basico(self, mock_icl):
        """Test 111: Verificar cálculo básico de actualización ICL"""
        mock_icl.return_value = 1.15  # 15% de incremento
        
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 4, 1)  # 3 meses después (trimestral)
        
        precio_nuevo, porcentaje, aplica = calcular_actualizacion_mes(
            100000.0, self.contrato_icl, self.inflacion_df, 
            fecha_actual, 3, fecha_inicio
        )
        
        self.assertEqual(precio_nuevo, 115000.0)
        self.assertEqual(porcentaje, "15.00%")
        self.assertTrue(aplica)
        mock_icl.assert_called_once()

    # Test 112: Cálculo de actualización porcentaje fijo
    def test_112_actualizacion_porcentaje_fijo(self):
        """Test 112: Verificar cálculo de actualización con porcentaje fijo"""
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 7, 1)  # 6 meses después (semestral)
        
        precio_nuevo, porcentaje, aplica = calcular_actualizacion_mes(
            100000.0, self.contrato_porcentaje, self.inflacion_df,
            fecha_actual, 6, fecha_inicio
        )
        
        self.assertEqual(precio_nuevo, 110000.0)
        self.assertEqual(porcentaje, "10.00%")
        self.assertTrue(aplica)

    # Test 113: No actualización en mes intermedio
    def test_113_no_actualizacion_mes_intermedio(self):
        """Test 113: Verificar que no se actualiza en meses intermedios"""
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 2, 1)  # 1 mes después (no trimestral)
        
        precio_nuevo, porcentaje, aplica = calcular_actualizacion_mes(
            100000.0, self.contrato_icl, self.inflacion_df,
            fecha_actual, 1, fecha_inicio
        )
        
        self.assertEqual(precio_nuevo, 100000.0)
        self.assertEqual(porcentaje, "")
        self.assertFalse(aplica)

    # Test 114: Generación de meses desde inicio de contrato
    def test_114_generar_meses_desde_inicio(self):
        """Test 114: Verificar generación de meses desde inicio de contrato"""
        fecha_limite = dt.date(2024, 6, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)  # Sin actualización
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_icl, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Debería generar 6 meses (enero a junio 2024)
        self.assertEqual(len(registros), 6)
        self.assertEqual(registros[0]['mes_actual'], "2024-01")
        self.assertEqual(registros[-1]['mes_actual'], "2024-06")

    # Test 115: Generación incremental desde mes específico
    def test_115_generar_meses_incremental(self):
        """Test 115: Verificar generación incremental desde mes específico"""
        fecha_limite = dt.date(2024, 6, 1)
        mes_inicial = "2024-03"  # Continuar desde marzo
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_icl, fecha_limite,
                100000.0, mes_inicial, self.inflacion_df, 0.0
            )
        
        # Debería generar 3 meses (abril a junio 2024)
        self.assertEqual(len(registros), 3)
        self.assertEqual(registros[0]['mes_actual'], "2024-04")
        self.assertEqual(registros[-1]['mes_actual'], "2024-06")

    # Test 116: Inclusión de municipalidad en precio final
    def test_116_inclusion_municipalidad(self):
        """Test 116: Verificar inclusión de gastos municipales"""
        fecha_limite = dt.date(2024, 2, 1)
        municipalidad = 5000.0
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_icl, fecha_limite,
                100000.0, "", self.inflacion_df, municipalidad, 0.0, 0.0, 0.0, 0.0
            )
        
        # Verificar que municipalidad se suma al precio final
        self.assertEqual(registros[0]['municipalidad'], 5000.0)
        self.assertEqual(registros[0]['precio_original'], 100000.0)
        # precio_final = precio_descuento + cuotas_adicionales + municipalidad + luz + gas + expensas
        self.assertGreaterEqual(registros[0]['precio_final'], 105000.0)

    # Test 117: Cálculo de cuotas adicionales en primeros meses
    def test_117_cuotas_adicionales_primeros_meses(self):
        """Test 117: Verificar cálculo de cuotas adicionales en primeros meses"""
        fecha_limite = dt.date(2024, 4, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_porcentaje, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Mes 1 y 2: comisión (2 cuotas) + depósito (3 cuotas)
        self.assertGreater(registros[0]['cuotas_adicionales'], 0)  # Mes 1
        self.assertGreater(registros[1]['cuotas_adicionales'], 0)  # Mes 2
        
        # Mes 3: solo depósito (última cuota)
        self.assertGreater(registros[2]['cuotas_adicionales'], 0)  # Mes 3
        
        # Mes 4: sin cuotas adicionales
        self.assertEqual(registros[3]['cuotas_adicionales'], 0)    # Mes 4

    # Test 118: Respeto de vigencia de contrato
    def test_118_vigencia_contrato(self):
        """Test 118: Verificar que se respeta la vigencia del contrato"""
        # Contrato de solo 3 meses
        contrato_corto = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=3,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="ICL",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        fecha_limite = dt.date(2024, 6, 1)  # 6 meses después
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, contrato_corto, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Solo debería generar 3 meses (enero, febrero, marzo)
        self.assertEqual(len(registros), 3)
        self.assertEqual(registros[-1]['mes_actual'], "2024-03")

    # Test 119: Cálculo de meses próxima actualización
    def test_119_meses_proxima_actualizacion(self):
        """Test 119: Verificar cálculo de meses hasta próxima actualización"""
        fecha_limite = dt.date(2024, 3, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            # Mes 1: sin actualización, Mes 2: sin actualización, Mes 3: sin actualización
            # La primera actualización trimestral debe ser en el mes 4 (meses_desde_inicio = 3)
            mock_calc.side_effect = [
                (100000.0, "", False),    # Mes 1 (meses_desde_inicio = 0)
                (100000.0, "", False),    # Mes 2 (meses_desde_inicio = 1)
                (100000.0, "", False)     # Mes 3 (meses_desde_inicio = 2)
            ]
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_icl, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Mes 1: faltan 3 meses para actualización (próxima en mes 4)
        self.assertEqual(registros[0]['meses_prox_actualizacion'], 3)
        
        # Mes 2: faltan 2 meses para actualización (próxima en mes 4)
        self.assertEqual(registros[1]['meses_prox_actualizacion'], 2)
        
        # Mes 3: falta 1 mes para actualización (próxima en mes 4)
        self.assertEqual(registros[2]['meses_prox_actualizacion'], 1)

    # Test 120: Lectura de histórico vacío
    def test_120_lectura_historico_vacio(self):
        """Test 120: Verificar manejo de histórico vacío o inexistente"""
        mock_sheet = Mock()
        mock_sheet.worksheet.side_effect = Exception("Worksheet not found")
        
        resultado = leer_historico_existente(mock_sheet)
        
        self.assertEqual(resultado, {})

    # Test 121: Lectura de histórico con datos
    def test_121_lectura_historico_con_datos(self):
        """Test 121: Verificar lectura correcta de histórico existente"""
        mock_worksheet = Mock()
        mock_worksheet.get_all_records.return_value = [
            {
                'nombre_inmueble': 'Casa Test',
                'mes_actual': '2024-02',
                'precio_base': 105000.0
            },
            {
                'nombre_inmueble': 'Casa Test',
                'mes_actual': '2024-01',
                'precio_base': 100000.0
            }
        ]
        
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        resultado = leer_historico_existente(mock_sheet)
        
        # Debería retornar el último mes cronológicamente
        self.assertIn('Casa Test', resultado)
        self.assertEqual(resultado['Casa Test']['ultimo_mes'], '2024-02')
        self.assertEqual(resultado['Casa Test']['ultimo_precio_base'], 105000.0)

    # Test 122: Manejo de errores en API ICL
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_122_error_api_icl(self, mock_icl):
        """Test 122: Verificar manejo de errores en consulta ICL"""
        mock_icl.side_effect = Exception("API Error")
        
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 4, 1)
        
        precio_nuevo, porcentaje, aplica = calcular_actualizacion_mes(
            100000.0, self.contrato_icl, self.inflacion_df,
            fecha_actual, 3, fecha_inicio
        )
        
        # En caso de error, debería retornar valores sin cambio
        self.assertEqual(precio_nuevo, 100000.0)
        self.assertEqual(porcentaje, "")
        self.assertFalse(aplica)

    # Test 123: Formato de porcentajes en diferentes índices
    def test_123_formato_porcentajes_variados(self):
        """Test 123: Verificar manejo de diferentes formatos de porcentaje"""
        contratos_test = [
            ("10%", 10.0),
            ("7.5%", 7.5),
            ("10,5%", 10.5),
            ("15", 15.0)
        ]
        
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 7, 1)  # 6 meses (semestral)
        
        for indice_str, porcentaje_esperado in contratos_test:
            contrato = Contrato(
                fecha_inicio="2024-01-01",
                duracion_meses=24,
                precio_original=100000.0,
                actualizacion="semestral",
                indice=indice_str,
                comision_inmo="5%",
                comision="Pagado",
                deposito="Pagado"
            )
            
            precio_nuevo, porcentaje_calc, aplica = calcular_actualizacion_mes(
                100000.0, contrato, self.inflacion_df,
                fecha_actual, 6, fecha_inicio
            )
            
            precio_esperado = 100000.0 * (1 + porcentaje_esperado / 100)
            self.assertAlmostEqual(precio_nuevo, precio_esperado, places=2)
            self.assertTrue(aplica)

    # Test 124: Actualización anual vs trimestral
    def test_124_frecuencias_actualizacion(self):
        """Test 124: Verificar diferentes frecuencias de actualización"""
        contrato_anual = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=24,
            precio_original=100000.0,
            actualizacion="anual",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        fecha_inicio = dt.date(2024, 1, 1)
        
        # A los 6 meses (anual): NO debería actualizar
        precio_6m, _, aplica_6m = calcular_actualizacion_mes(
            100000.0, contrato_anual, self.inflacion_df,
            dt.date(2024, 7, 1), 6, fecha_inicio
        )
        self.assertFalse(aplica_6m)
        
        # A los 12 meses (anual): SÍ debería actualizar
        precio_12m, _, aplica_12m = calcular_actualizacion_mes(
            100000.0, contrato_anual, self.inflacion_df,
            dt.date(2025, 1, 1), 12, fecha_inicio
        )
        self.assertTrue(aplica_12m)

    # Test 125: Integridad de registros generados
    def test_125_integridad_registros(self):
        """Test 125: Verificar integridad de todos los campos en registros"""
        fecha_limite = dt.date(2024, 2, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (105000.0, "5.00%", True)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_icl, fecha_limite,
                100000.0, "", self.inflacion_df, 1000.0, 0.0, 0.0, 0.0, 0.0
            )
        
        registro = registros[0]
        
        # Verificar que todos los campos requeridos están presentes
        campos_requeridos = [
            'nombre_inmueble', 'dir_inmueble', 'inquilino', 'propietario',
            'mes_actual', 'precio_final', 'precio_original', 'precio_descuento', 'descuento',
            'cuotas_adicionales', 'municipalidad', 'luz', 'gas', 'expensas',
            'comision_inmo', 'pago_prop', 'actualizacion',
            'porc_actual', 'meses_prox_actualizacion', 'meses_prox_renovacion'
        ]
        
        for campo in campos_requeridos:
            self.assertIn(campo, registro)
            self.assertIsNotNone(registro[campo])


if __name__ == '__main__':
    unittest.main()
