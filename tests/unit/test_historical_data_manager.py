#!/usr/bin/env python3
"""
Tests unitarios para HistoricalDataManager.
Validación de lectura/escritura de Google Sheets y manejo de errores de API.
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from inmobiliaria.services.historical_data import HistoricalDataManager
from inmobiliaria.domain.historical_models import PropertyHistoricalData, HistoricalRecord


class TestHistoricalDataManagerUnit(unittest.TestCase):
    """Tests unitarios para el manager de datos históricos"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.data_manager = HistoricalDataManager()
        self.spreadsheet_key = "test_key_123"
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_inicializacion_cliente_gspread(self, mock_get_client):
        """Test: Verificar inicialización correcta del cliente de Google Sheets"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        manager = HistoricalDataManager()
        
        mock_get_client.assert_called_once()
        self.assertIsNotNone(manager.gc)
        self.assertIsNotNone(manager.sheet)
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_load_maestro_data_estructura_basica(self, mock_get_client):
        """Test: Verificar carga básica de datos del maestro"""
        # Mock del cliente y worksheet
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        
        # Datos de prueba
        datos_maestro = [
            {
                'nombre_inmueble': 'Casa Alpha',
                'precio_original': 100000,
                'actualizacion': 'trimestral',
                'fecha_inicio_contrato': '2024-01-01'
            }
        ]
        
        mock_worksheet.get_all_records.return_value = datos_maestro
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_get_client.return_value = mock_client
        
        # Ejecutar
        manager = HistoricalDataManager()
        resultado = manager.load_maestro_data()
        
        # Verificar
        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado[0]['nombre_inmueble'], 'Casa Alpha')
        mock_worksheet.get_all_records.assert_called_once()
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_load_maestro_data_error_hoja_no_existe(self, mock_get_client):
        """Test: Verificar manejo de error cuando hoja maestro no existe"""
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_spreadsheet.worksheet.side_effect = Exception("Worksheet not found")
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_get_client.return_value = mock_client
        
        manager = HistoricalDataManager()
        
        # Verificar que se propaga la excepción
        with self.assertRaises(Exception):
            manager.load_maestro_data()
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_read_existing_historical_vacia(self, mock_get_client):
        """Test: Verificar lectura cuando no hay datos históricos"""
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        
        # Primera llamada falla (hoja no existe), segunda retorna datos vacíos
        def worksheet_side_effect(name):
            if name == "historico":
                raise Exception("Worksheet not found")
            return mock_worksheet
        
        mock_spreadsheet.worksheet.side_effect = worksheet_side_effect
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_get_client.return_value = mock_client
        
        manager = HistoricalDataManager()
        
        # Como el método maneja excepciones internamente y retorna {}
        resultado = manager.read_existing_historical()
        
        # Debe retornar un diccionario vacío cuando no hay datos
        self.assertEqual(resultado, {})
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_read_existing_historical_con_datos(self, mock_get_client):
        """Test: Verificar lectura de datos históricos existentes"""
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_worksheet = Mock()
        
        datos_historicos = [
            {
                'nombre_inmueble': 'Casa Alpha',
                'mes_actual': '2024-01',
                'precio_original': 102000,
                'precio_final': 115000
            },
            {
                'nombre_inmueble': 'Casa Alpha',
                'mes_actual': '2024-02',
                'precio_original': 102000,
                'precio_final': 115000
            }
        ]
        
        mock_worksheet.get_all_records.return_value = datos_historicos
        mock_spreadsheet.worksheet.return_value = mock_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_get_client.return_value = mock_client
        
        manager = HistoricalDataManager()
        resultado = manager.read_existing_historical()
        
        # Verificar que agrupa por propiedad
        self.assertIn('Casa Alpha', resultado)
        property_data = resultado['Casa Alpha']
        self.assertIsInstance(property_data, PropertyHistoricalData)
        self.assertEqual(property_data.nombre_propiedad, 'Casa Alpha')
    
    @patch('inmobiliaria.services.historical_data.get_gspread_client')
    def test_write_historical_records_nueva_hoja(self, mock_get_client):
        """Test: Verificar escritura de registros cuando se crea nueva hoja"""
        mock_client = Mock()
        mock_spreadsheet = Mock()
        mock_new_worksheet = Mock()
        
        # Mock que simula creación exitosa de nueva hoja
        mock_spreadsheet.add_worksheet.return_value = mock_new_worksheet
        mock_spreadsheet.worksheet.return_value = mock_new_worksheet
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_get_client.return_value = mock_client
        
        # Crear registros de prueba
        registros = [
            HistoricalRecord(
                nombre_inmueble='Casa Test',
                dir_inmueble='Calle Test 123',
                inquilino='Juan Test',
                propietario='Ana Test',
                mes_actual='2024-01',
                precio_final=115000.0,
                precio_original=100000.0,
                precio_descuento=100000.0,
                descuento='0%',
                cuotas_adicionales=15000.0,
                cuotas_comision=10000.0,
                cuotas_deposito=5000.0,
                detalle_cuotas='Comisión: $10000, Depósito: $5000',
                municipalidad=2000.0,
                luz=0.0,
                gas=0.0,
                expensas=0.0,
                comision_inmo=5000.0,
                pago_prop=95000.0,
                actualizacion='NO',
                porc_actual='',
                meses_prox_actualizacion=3,
                meses_prox_renovacion=11
            )
        ]
        
        manager = HistoricalDataManager()
        manager.write_historical_records(registros)
        
        # Verificar que se intentó crear nueva hoja
        mock_spreadsheet.add_worksheet.assert_called_once()
        mock_new_worksheet.clear.assert_called_once()
        # Verificar que se escribieron los datos
        mock_new_worksheet.update.assert_called()
    
    def test_property_exists_in_historical_metodo(self):
        """Test: Verificar método de verificación de existencia de propiedad"""
        # Test básico del método público
        manager = HistoricalDataManager()
        
        # Test con mock para evitar llamadas reales a Google Sheets
        with patch.object(manager, 'read_existing_historical') as mock_read:
            mock_read.return_value = {
                'Casa Alpha': PropertyHistoricalData(
                    nombre_propiedad='Casa Alpha',
                    ultimo_mes='2024-01',
                    ultimo_precio_base=100000.0,
                    registros_existentes=[]
                )
            }
            
            # Verificar que existe
            existe = manager.property_exists_in_historical('Casa Alpha')
            self.assertTrue(existe)
            
            # Verificar que no existe
            no_existe = manager.property_exists_in_historical('Casa Beta')
            self.assertFalse(no_existe)
    
    def test_get_last_price_for_property_metodo(self):
        """Test: Verificar obtención del último precio de una propiedad"""
        manager = HistoricalDataManager()
        
        # Test con mock
        with patch.object(manager, 'read_existing_historical') as mock_read:
            mock_read.return_value = {
                'Casa Alpha': PropertyHistoricalData(
                    nombre_propiedad='Casa Alpha',
                    ultimo_mes='2024-01',
                    ultimo_precio_base=105000.0,
                    registros_existentes=[]
                )
            }
            
            # Verificar obtención de precio
            precio = manager.get_last_price_for_property('Casa Alpha')
            self.assertEqual(precio, 105000.0)
            
            # Verificar propiedad inexistente
            precio_inexistente = manager.get_last_price_for_property('Casa Beta')
            self.assertIsNone(precio_inexistente)


if __name__ == '__main__':
    unittest.main()
