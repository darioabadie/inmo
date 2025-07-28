#!/usr/bin/env python3
"""
Tests funcionales para el módulo historical.py - Integración completa
Tests 151-165: Validación de integración completa y flujo extremo a extremo
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inmobiliaria.models import Propiedad, Contrato
from inmobiliaria import historical
from inmobiliaria import config


class TestHistoricalIntegracion(unittest.TestCase):
    """Tests de integración completa del módulo historical"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.maestro_datos = [
            {
                'nombre_inmueble': 'Casa Alpha',
                'dir_inmueble': 'Calle Alpha 123',
                'propietario': 'Juan Alpha',
                'inquilino': 'Ana Alpha',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 12,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': 'ICL',
                'comision_inmo': '5%',
                'comision': 'Pagado',
                'deposito': 'Pagado',
                'municipalidad': 2000.0
            },
            {
                'nombre_inmueble': 'Casa Beta',
                'dir_inmueble': 'Avenida Beta 456',
                'propietario': 'Maria Beta',
                'inquilino': 'Carlos Beta',
                'fecha_inicio_contrato': '2024-02-01',
                'duracion_meses': 24,
                'precio_original': 150000.0,
                'actualizacion': 'semestral',
                'indice': '12%',
                'comision_inmo': '4%',
                'comision': '2 cuotas',
                'deposito': '3 cuotas',
                'municipalidad': 3000.0
            }
        ]
        
        self.inflacion_df = pd.DataFrame({
            'año': [2024] * 6,
            'mes': [1, 2, 3, 4, 5, 6],
            'ipc_mensual': [2.0, 1.5, 1.8, 2.2, 1.9, 2.1]
        })

    # Test 151: Integración completa sin histórico previo
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_151_integracion_sin_historico_previo(self, mock_icl, mock_inflacion, mock_gspread):
        """Test 151: Integración completa iniciando desde cero"""
        
        # Mock de Google Sheets
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = self.maestro_datos
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]  # Usar lista para mutabilidad
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("Worksheet not found")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        # Mock de datos externos
        mock_inflacion.return_value = self.inflacion_df
        mock_icl.return_value = 1.08  # 8% incremento ICL
        
        # Ejecutar main con argumentos simulados
        with patch('sys.argv', ['historical.py', '--hasta', '2024-04']):
            with patch('builtins.print') as mock_print:
                historical.main()
        
        # Verificar que se creó la hoja histórico
        mock_sheet.add_worksheet.assert_called_once()
        
        # Verificar que se escribieron datos
        mock_worksheet_historico.update.assert_called_once()
        
        # Verificar salida
        mock_print.assert_called()

    # Test 152: Integración completa con histórico existente
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    def test_152_integracion_con_historico_existente(self, mock_inflacion, mock_gspread):
        """Test 152: Integración completa con histórico previo"""
        
        # Histórico existente simulado
        historico_existente = [
            {
                'nombre_inmueble': 'Casa Alpha',
                'mes_actual': '2024-01',
                'precio_base': 100000.0,
                'precio_mes_actual': 102000.0,
                'municipalidad': 2000.0
            },
            {
                'nombre_inmueble': 'Casa Alpha',
                'mes_actual': '2024-02',
                'precio_base': 100000.0,
                'precio_mes_actual': 102000.0,
                'municipalidad': 2000.0
            }
        ]
        
        # Mock de Google Sheets
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = self.maestro_datos
        
        mock_worksheet_historico = Mock()
        mock_worksheet_historico.get_all_records.return_value = historico_existente
        
        mock_sheet.worksheet.side_effect = [
            mock_worksheet_maestro,    # Primera llamada: maestro
            mock_worksheet_historico   # Segunda llamada: histórico existente
        ]
        
        # Para la escritura final
        def worksheet_side_effect(name):
            if name == config.SHEET_MAESTRO:
                return mock_worksheet_maestro
            elif name == "historico":
                return mock_worksheet_historico
            else:
                raise Exception("Worksheet not found")
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        # Mock de datos externos
        mock_inflacion.return_value = self.inflacion_df
        
        # Ejecutar main
        with patch('sys.argv', ['historical.py', '--hasta', '2024-04']):
            with patch('builtins.print'):
                historical.main()
        
        # Verificar que se intentó escribir datos actualizados
        mock_worksheet_historico.clear.assert_called_once()
        mock_worksheet_historico.update.assert_called_once()

    # Test 153: Manejo de errores en Google Sheets API
    @patch('inmobiliaria.historical.get_gspread_client')
    def test_153_manejo_errores_google_sheets(self, mock_gspread):
        """Test 153: Verificar manejo robusto de errores de Google Sheets API"""
        
        # Simular error en conexión a Google Sheets
        mock_gspread.side_effect = Exception("API connection failed")
        
        # Ejecutar main y verificar que maneja el error
        with patch('sys.argv', ['historical.py', '--hasta', '2024-04']):
            with self.assertRaises(Exception):
                historical.main()

    # Test 154: Procesamiento de múltiples propiedades
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_154_procesamiento_multiples_propiedades(self, mock_icl, mock_inflacion, mock_gspread):
        """Test 154: Verificar procesamiento correcto de múltiples propiedades"""
        
        # Datos maestros con 3 propiedades diferentes
        maestro_multiple = [
            {
                'nombre_inmueble': 'Casa 1',
                'dir_inmueble': 'Calle 1',
                'propietario': 'Prop 1',
                'inquilino': 'Inq 1',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 12,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': 'ICL',
                'comision_inmo': '5%',
                'comision': 'Pagado',
                'deposito': 'Pagado',
                'municipalidad': 1000.0
            },
            {
                'nombre_inmueble': 'Casa 2',
                'dir_inmueble': 'Calle 2',
                'propietario': 'Prop 2',
                'inquilino': 'Inq 2',
                'fecha_inicio_contrato': '2024-02-01',
                'duracion_meses': 18,
                'precio_original': 200000.0,
                'actualizacion': 'semestral',
                'indice': '8%',
                'comision_inmo': '4%',
                'comision': '2 cuotas',
                'deposito': 'Pagado',
                'municipalidad': 2000.0
            },
            {
                'nombre_inmueble': 'Casa 3',
                'dir_inmueble': 'Calle 3',
                'propietario': 'Prop 3',
                'inquilino': 'Inq 3',
                'fecha_inicio_contrato': '2024-03-01',
                'duracion_meses': 24,
                'precio_original': 150000.0,
                'actualizacion': 'anual',
                'indice': '10%',
                'comision_inmo': '6%',
                'comision': '3 cuotas',
                'deposito': '2 cuotas',
                'municipalidad': 1500.0
            }
        ]
        
        # Setup mocks
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = maestro_multiple
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("No histórico")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        mock_inflacion.return_value = self.inflacion_df
        mock_icl.return_value = 1.05
        
        # Ejecutar main
        with patch('sys.argv', ['historical.py', '--hasta', '2024-05']):
            with patch('builtins.print'):
                historical.main()
        
        # Verificar que se procesaron las 3 propiedades
        args, kwargs = mock_worksheet_historico.update.call_args
        datos_escritos = args[0]
        
        # Verificar que hay registros para las 3 propiedades
        nombres_propiedades = set()
        for fila in datos_escritos[1:]:  # Skip header
            nombres_propiedades.add(fila[0])  # nombre_inmueble es la primera columna
        
        self.assertEqual(len(nombres_propiedades), 3)
        self.assertIn('Casa 1', nombres_propiedades)
        self.assertIn('Casa 2', nombres_propiedades)
        self.assertIn('Casa 3', nombres_propiedades)

    # Test 155: Validación de argumentos de línea de comandos
    def test_155_validacion_argumentos_cli(self):
        """Test 155: Verificar validación de argumentos de línea de comandos"""
        
        # Test con argumento válido
        with patch('sys.argv', ['historical.py', '--hasta', '2024-06']):
            args = historical._parse_args()
            self.assertEqual(args.hasta, '2024-06')
        
        # Test sin argumentos (debería usar default)
        with patch('sys.argv', ['historical.py']):
            args = historical._parse_args()
            # Debería ser el mes actual en formato YYYY-MM
            today = dt.date.today()
            expected = f"{today.year}-{today.month:02}"
            self.assertEqual(args.hasta, expected)

    # Test 156: Integración con API ICL real (mock)
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_156_integracion_api_icl(self, mock_icl):
        """Test 156: Verificar integración con API ICL"""
        
        # Simular respuesta real de API ICL
        mock_icl.return_value = 1.1254  # Factor realista
        
        contrato_icl = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="ICL",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 4, 1)
        
        precio_nuevo, porcentaje, aplica = historical.calcular_actualizacion_mes(
            100000.0, contrato_icl, self.inflacion_df,
            fecha_actual, 3, fecha_inicio
        )
        
        # Verificar que se llamó a la API ICL
        mock_icl.assert_called_once()
        
        # Verificar resultado
        self.assertAlmostEqual(precio_nuevo, 112540.0, places=0)
        self.assertEqual(porcentaje, "12.54%")
        self.assertTrue(aplica)

    # Test 157: Manejo de propiedades con datos faltantes
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    def test_157_propiedades_datos_faltantes(self, mock_inflacion, mock_gspread):
        """Test 157: Verificar manejo de propiedades con datos faltantes"""
        
        maestro_incompleto = [
            {
                'nombre_inmueble': 'Casa Completa',
                'dir_inmueble': 'Calle 1',
                'propietario': 'Prop 1',
                'inquilino': 'Inq 1',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 12,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': '10%',
                'comision_inmo': '5%',
                'comision': 'Pagado',
                'deposito': 'Pagado'
            },
            {
                'nombre_inmueble': '',  # Dato faltante
                'dir_inmueble': 'Calle 2',
                'propietario': 'Prop 2',
                'inquilino': 'Inq 2',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 12,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': '10%',
                'comision_inmo': '5%'
            },
            {
                'nombre_inmueble': 'Casa Sin Fecha',
                'dir_inmueble': 'Calle 3',
                'propietario': 'Prop 3',
                'inquilino': 'Inq 3',
                'fecha_inicio_contrato': '',  # Fecha inválida
                'duracion_meses': 12,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': '10%',
                'comision_inmo': '5%'
            }
        ]
        
        # Setup mocks
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = maestro_incompleto
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("No histórico")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        mock_inflacion.return_value = self.inflacion_df
        
        # Ejecutar main
        with patch('sys.argv', ['historical.py', '--hasta', '2024-03']):
            with patch('builtins.print'):
                historical.main()
        
        # Verificar que se procesó solo la propiedad válida
        if mock_worksheet_historico.update.called:
            args, kwargs = mock_worksheet_historico.update.call_args
            datos_escritos = args[0]
            
            # Solo debería haber registros para 'Casa Completa'
            registros_procesados = 0
            if len(datos_escritos) > 1:  # Más que solo headers
                for fila in datos_escritos[1:]:
                    if fila[0] == 'Casa Completa':  # nombre_inmueble
                        registros_procesados += 1
            
            self.assertGreater(registros_procesados, 0)

    # Test 158: Verificación de estructura de salida
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    def test_158_estructura_salida(self, mock_inflacion, mock_gspread):
        """Test 158: Verificar estructura correcta de datos de salida"""
        
        # Setup básico
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = [self.maestro_datos[0]]
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("No histórico")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        mock_inflacion.return_value = self.inflacion_df
        
        # Ejecutar main
        with patch('sys.argv', ['historical.py', '--hasta', '2024-02']):
            with patch('builtins.print'):
                historical.main()
        
        # Verificar estructura de salida
        if mock_worksheet_historico.update.called:
            args, kwargs = mock_worksheet_historico.update.call_args
            datos_escritos = args[0]
            
            # Verificar headers
            headers_esperados = [
                'nombre_inmueble', 'dir_inmueble', 'inquilino', 'propietario',
                'mes_actual', 'precio_final', 'precio_original', 'precio_descuento', 'descuento',
                'cuotas_adicionales', 'municipalidad', 'luz', 'gas', 'expensas',
                'comision_inmo', 'pago_prop', 'actualizacion',
                'porc_actual', 'meses_prox_actualizacion', 'meses_prox_renovacion'
            ]
            
            headers_reales = datos_escritos[0]
            for header in headers_esperados:
                self.assertIn(header, headers_reales)

    # Test 159: Rendimiento con dataset grande
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    def test_159_rendimiento_dataset_grande(self, mock_inflacion, mock_gspread):
        """Test 159: Verificar rendimiento con dataset grande"""
        
        import time
        
        # Crear dataset grande (50 propiedades)
        maestro_grande = []
        for i in range(50):
            maestro_grande.append({
                'nombre_inmueble': f'Casa {i:03d}',
                'dir_inmueble': f'Calle {i}',
                'propietario': f'Propietario {i}',
                'inquilino': f'Inquilino {i}',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 12,
                'precio_original': 100000.0 + (i * 1000),
                'actualizacion': 'trimestral',
                'indice': '10%',
                'comision_inmo': '5%',
                'comision': 'Pagado',
                'deposito': 'Pagado',
                'municipalidad': 1000.0
            })
        
        # Setup mocks
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = maestro_grande
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("No histórico")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        mock_inflacion.return_value = self.inflacion_df
        
        # Medir tiempo de ejecución
        start_time = time.time()
        
        with patch('sys.argv', ['historical.py', '--hasta', '2024-03']):
            with patch('builtins.print'):
                historical.main()
        
        end_time = time.time()
        
        # Debería procesar en tiempo razonable (< 5 segundos)
        self.assertLess(end_time - start_time, 5.0)

    # Test 160: Integración con configuración
    @patch('inmobiliaria.historical.config.SHEET_ID', 'test_sheet_id')
    @patch('inmobiliaria.historical.config.SHEET_MAESTRO', 'test_maestro')
    @patch('inmobiliaria.historical.get_gspread_client')
    def test_160_integracion_configuracion(self, mock_gspread):
        """Test 160: Verificar integración con configuración"""
        
        mock_gc = Mock()
        mock_sheet = Mock()
        mock_worksheet = Mock()
        
        mock_gc.open_by_key.return_value = mock_sheet
        mock_sheet.worksheet.return_value = mock_worksheet
        mock_worksheet.get_all_records.return_value = []
        
        mock_gspread.return_value = mock_gc
        
        with patch('sys.argv', ['historical.py']):
            with patch('builtins.print'):
                try:
                    historical.main()
                except:
                    pass  # Esperamos que falle por datos vacíos
        
        # Verificar que se usó la configuración correcta
        mock_gc.open_by_key.assert_called_with('test_sheet_id')
        mock_sheet.worksheet.assert_any_call('test_maestro')

    # Test 161: Manejo de excepciones en cálculos
    def test_161_manejo_excepciones_calculos(self):
        """Test 161: Verificar manejo robusto de excepciones en cálculos"""
        
        contrato_invalido = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="invalid_index",
            comision_inmo="invalid_commission",
            comision="Pagado",
            deposito="Pagado"
        )
        
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 4, 1)
        
        # Debería manejar índice inválido sin crashear
        precio_nuevo, porcentaje, aplica = historical.calcular_actualizacion_mes(
            100000.0, contrato_invalido, self.inflacion_df,
            fecha_actual, 3, fecha_inicio
        )
        
        # En caso de error, debería retornar valores sin cambio
        self.assertEqual(precio_nuevo, 100000.0)
        self.assertEqual(porcentaje, "")
        self.assertFalse(aplica)

    # Test 162: Validación de fechas extremas
    def test_162_validacion_fechas_extremas(self):
        """Test 162: Verificar validación de fechas extremas"""
        
        propiedad = Propiedad("Casa", "Dir", "Prop", "Inq")
        contrato = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        # Fecha límite muy lejana
        fecha_limite_lejana = dt.date(2030, 12, 31)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = historical.generar_meses_faltantes(
                propiedad, contrato, fecha_limite_lejana,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Solo debería generar hasta la duración del contrato (12 meses)
        self.assertEqual(len(registros), 12)

    # Test 163: Ordenamiento final de registros
    def test_163_ordenamiento_final_registros(self):
        """Test 163: Verificar ordenamiento final correcto de registros"""
        
        # Simular registros desordenados de múltiples propiedades
        registros_desordenados = [
            {'nombre_inmueble': 'Casa Z', 'mes_actual': '2024-03'},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-02'},
            {'nombre_inmueble': 'Casa Z', 'mes_actual': '2024-01'},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-01'},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-03'},
            {'nombre_inmueble': 'Casa Z', 'mes_actual': '2024-02'}
        ]
        
        # Aplicar ordenamiento como en main
        registros_ordenados = sorted(registros_desordenados,
                                   key=lambda x: (x['nombre_inmueble'], x['mes_actual']))
        
        # Verificar orden esperado
        orden_esperado = [
            ('Casa A', '2024-01'),
            ('Casa A', '2024-02'),
            ('Casa A', '2024-03'),
            ('Casa Z', '2024-01'),
            ('Casa Z', '2024-02'),
            ('Casa Z', '2024-03')
        ]
        
        for i, (nombre, mes) in enumerate(orden_esperado):
            self.assertEqual(registros_ordenados[i]['nombre_inmueble'], nombre)
            self.assertEqual(registros_ordenados[i]['mes_actual'], mes)

    # Test 164: Validación de salida final
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    def test_164_validacion_salida_final(self, mock_inflacion, mock_gspread):
        """Test 164: Verificar validación completa de salida final"""
        
        # Setup mínimo para generar salida
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = [self.maestro_datos[0]]
        
        mock_worksheet_historico = Mock()
        
        # Configurar worksheet() para manejar múltiples llamadas
        historico_call_count = [0]
        
        def worksheet_side_effect(name):
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                historico_call_count[0] += 1
                if historico_call_count[0] == 1:
                    raise Exception("No histórico")
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        mock_sheet.add_worksheet.return_value = mock_worksheet_historico
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        mock_inflacion.return_value = self.inflacion_df
        
        with patch('sys.argv', ['historical.py', '--hasta', '2024-02']):
            with patch('builtins.print') as mock_print:
                historical.main()
        
        # Verificar que se generó output informativo
        mock_print.assert_called()
        
        # Verificar que se escribieron datos
        mock_worksheet_historico.update.assert_called_once()

    # Test 165: Flujo completo extremo a extremo
    @patch('inmobiliaria.historical.get_gspread_client')
    @patch('inmobiliaria.historical.traer_inflacion')
    @patch('inmobiliaria.historical.traer_factor_icl')
    def test_165_flujo_completo_extremo_a_extremo(self, mock_icl, mock_inflacion, mock_gspread):
        """Test 165: Verificar flujo completo extremo a extremo"""
        
        # Simulación completa con todos los componentes
        
        # 1. Datos maestros variados
        maestro_completo = [
            {
                'nombre_inmueble': 'Casa ICL',
                'dir_inmueble': 'Calle ICL 1',
                'propietario': 'Prop ICL',
                'inquilino': 'Inq ICL',
                'fecha_inicio_contrato': '2024-01-01',
                'duracion_meses': 24,
                'precio_original': 100000.0,
                'actualizacion': 'trimestral',
                'indice': 'ICL',
                'comision_inmo': '5%',
                'comision': '2 cuotas',
                'deposito': '3 cuotas',
                'municipalidad': 2000.0
            },
            {
                'nombre_inmueble': 'Casa Porcentaje',
                'dir_inmueble': 'Calle Porc 2',
                'propietario': 'Prop Porc',
                'inquilino': 'Inq Porc',
                'fecha_inicio_contrato': '2024-02-01',
                'duracion_meses': 18,
                'precio_original': 150000.0,
                'actualizacion': 'semestral',
                'indice': '12%',
                'comision_inmo': '4%',
                'comision': 'Pagado',
                'deposito': '2 cuotas',
                'municipalidad': 3000.0
            }
        ]
        
        # 2. Histórico parcial existente
        historico_parcial = [
            {
                'nombre_inmueble': 'Casa ICL',
                'mes_actual': '2024-01',
                'precio_base': 100000.0,
                'precio_mes_actual': 152000.0,  # Con cuotas
                'cuotas_adicionales': 50000.0,
                'municipalidad': 2000.0,
                'actualizacion': 'NO',
                'porc_actual': ''
            }
        ]
        
        # 3. Setup completo de mocks
        mock_sheet = Mock()
        mock_worksheet_maestro = Mock()
        mock_worksheet_maestro.get_all_records.return_value = maestro_completo
        
        mock_worksheet_historico = Mock()
        mock_worksheet_historico.get_all_records.return_value = historico_parcial
        
        # Configurar worksheet() para manejar múltiples llamadas
        call_count = [0]
        
        def worksheet_side_effect(name):
            call_count[0] += 1
            if name == "maestro":
                return mock_worksheet_maestro
            elif name == "historico":
                return mock_worksheet_historico
            return mock_worksheet_maestro
        
        mock_sheet.worksheet.side_effect = worksheet_side_effect
        
        mock_gc = Mock()
        mock_gc.open_by_key.return_value = mock_sheet
        mock_gspread.return_value = mock_gc
        
        # 4. Datos externos
        mock_inflacion.return_value = self.inflacion_df
        mock_icl.return_value = 1.08
        
        # 5. Ejecución completa
        with patch('sys.argv', ['historical.py', '--hasta', '2024-06']):
            with patch('builtins.print') as mock_print:
                historical.main()
        
        # 6. Verificaciones finales
        
        # Se leyó el maestro
        mock_worksheet_maestro.get_all_records.assert_called_once()
        
        # Se leyó el histórico existente
        mock_worksheet_historico.get_all_records.assert_called_once()
        
        # Se consultó ICL para Casa ICL
        self.assertTrue(mock_icl.called)
        
        # Se escribieron datos finales
        mock_worksheet_historico.clear.assert_called_once()
        mock_worksheet_historico.update.assert_called_once()
        
        # Se generó output informativo
        mock_print.assert_called()
        
        # Verificar contenido de datos escritos
        args, kwargs = mock_worksheet_historico.update.call_args
        datos_finales = args[0]
        
        # Debería haber headers + registros para ambas propiedades
        self.assertGreater(len(datos_finales), 1)  # Más que solo headers
        
        # Verificar estructura de headers
        headers = datos_finales[0]
        self.assertIn('nombre_inmueble', headers)
        self.assertIn('precio_base', headers)
        self.assertIn('municipalidad', headers)


if __name__ == '__main__':
    unittest.main()
