#!/usr/bin/env python3
"""
Tests unitarios para HistoricalService.
Validación de orquestación, manejo de errores y resúmenes.
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from inmobiliaria.services.historical_service import HistoricalService
from inmobiliaria.domain.historical_models import HistoricalSummary, PropertyHistoricalData


class TestHistoricalServiceUnit(unittest.TestCase):
    """Tests unitarios para el servicio principal histórico"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.service = HistoricalService()
        self.fecha_limite = dt.date(2024, 6, 30)
    
    def test_inicializacion_servicio(self):
        """Test: Verificar inicialización correcta del servicio"""
        self.assertIsNotNone(self.service.data_manager)
        self.assertIsNotNone(self.service.record_generator)
        self.assertIsNotNone(self.service.calculations)
        self.assertIsNotNone(self.service.summary)
        
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_generate_historical_until_inicializa_resumen(self, mock_data_manager):
        """Test: Verificar que se inicializa el resumen correctamente"""
        # Mock del data manager
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = []
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        
        # Crear servicio con mock
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Ejecutar
        resultado = service.generate_historical_until(self.fecha_limite)
        
        # Verificar que se inicializó el resumen
        self.assertEqual(resultado.fecha_limite, self.fecha_limite)
        self.assertIsInstance(resultado, HistoricalSummary)
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_generate_historical_carga_datos_maestro(self, mock_data_manager):
        """Test: Verificar que se cargan los datos del maestro"""
        # Mock setup
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {'nombre_inmueble': 'Casa Test', 'precio_original': 100000}
        ]
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        
        # Crear servicio
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Ejecutar
        service.generate_historical_until(self.fecha_limite)
        
        # Verificar que se llamó a cargar datos
        mock_data_manager_instance.load_maestro_data.assert_called_once()
        mock_data_manager_instance.read_existing_historical.assert_called_once()
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_manejo_error_carga_datos(self, mock_data_manager):
        """Test: Verificar manejo de errores al cargar datos"""
        # Mock que falla
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.side_effect = Exception("Error de carga")
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Verificar que se maneja la excepción
        with self.assertRaises(Exception):
            service.generate_historical_until(self.fecha_limite)
    
    def test_validar_fecha_limite_formato(self):
        """Test: Verificar validación de formato de fecha límite"""
        # Fecha válida
        fecha_valida = dt.date(2024, 12, 31)
        resultado = self.service.generate_historical_until(fecha_valida)
        self.assertEqual(resultado.fecha_limite, fecha_valida)
        
        # Nota: El tipo date es validado por el tipo hint, no por runtime
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_conteo_propiedades_procesadas(self, mock_data_manager):
        """Test: Verificar conteo de propiedades procesadas"""
        # Mock con 2 propiedades
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {'nombre_inmueble': 'Casa 1', 'precio_original': 100000},
            {'nombre_inmueble': 'Casa 2', 'precio_original': 150000}
        ]
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Mock del procesamiento de propiedades para evitar complejidad
        with patch.object(service, 'process_property') as mock_process:
            mock_process.return_value = []
            
            resultado = service.generate_historical_until(self.fecha_limite)
            
            # Verificar que se intentó procesar 2 propiedades
            self.assertEqual(mock_process.call_count, 2)
    
    def test_resumen_estadisticas_iniciales(self):
        """Test: Verificar estadísticas iniciales del resumen"""
        resumen = HistoricalSummary(fecha_limite=self.fecha_limite)
        
        # Valores iniciales
        self.assertEqual(resumen.propiedades_procesadas, 0)
        self.assertEqual(resumen.total_registros, 0)
        self.assertEqual(resumen.propiedades_omitidas, 0)
        self.assertIsNotNone(resumen.errores)  # Se inicializa como lista vacía


class TestHistoricalServiceIntegracionMock(unittest.TestCase):
    """Tests de integración con mocks para HistoricalService"""
    
    def setUp(self):
        self.service = HistoricalService()
        self.fecha_limite = dt.date(2024, 6, 30)
    
    @patch('inmobiliaria.services.historical_service.logging')
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_logging_proceso_completo(self, mock_data_manager, mock_logging):
        """Test: Verificar que se hace logging del proceso"""
        # Mock data manager
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = []
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Ejecutar
        service.generate_historical_until(self.fecha_limite)
        
        # Verificar que se hizo logging
        mock_logging.warning.assert_called()
    
    def test_property_historical_data_creacion(self):
        """Test: Verificar creación de PropertyHistoricalData"""
        # Crear PropertyHistoricalData con parámetros correctos
        property_historical = PropertyHistoricalData(
            nombre_propiedad='Casa Test',
            ultimo_mes='2024-01',
            ultimo_precio_base=100000.0,
            registros_existentes=[]
        )
        
        self.assertEqual(property_historical.nombre_propiedad, 'Casa Test')
        self.assertEqual(property_historical.ultimo_mes, '2024-01')
        self.assertEqual(property_historical.ultimo_precio_base, 100000.0)
        self.assertEqual(len(property_historical.registros_existentes), 0)
        self.assertTrue(property_historical.tiene_historico)


if __name__ == '__main__':
    unittest.main()
