import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from inmobiliaria.services.historical_service import HistoricalService
from inmobiliaria.domain.historical_models import HistoricalSummary


class TestHistoricalServiceUnit(unittest.TestCase):
    """Tests unitarios para HistoricalService - Aislando dependencias externas"""
    
    def setUp(self):
        self.fecha_limite = "2024-12"
    
    def test_inicializacion_servicio(self):
        """Test: Verificar inicialización correcta del servicio"""
        service = HistoricalService()
        self.assertIsNotNone(service.data_manager)
        self.assertEqual(service.data_manager.__class__.__name__, 'HistoricalDataManager')
    
    def test_validar_fecha_limite_formato(self):
        """Test: Verificar validación de formato de fecha límite"""
        service = HistoricalService()
        
        # Formato válido
        resultado = service._validar_fecha_limite("2024-12")
        self.assertEqual(resultado, "2024-12")
        
        # Formato inválido
        with self.assertRaises(ValueError):
            service._validar_fecha_limite("diciembre-2024")
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_generate_historical_until_inicializa_resumen(self, mock_data_manager):
        """Test: Verificar que se inicializa el resumen correctamente"""
        # Mock del data manager
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = []
        mock_data_manager_instance.read_existing_historical.return_value = {}
        
        # Crear servicio con mock
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Ejecutar
        resultado = service.generate_historical_until(self.fecha_limite)
        
        # Verificar que se inicializó el resumen
        self.assertIsInstance(resultado, HistoricalSummary)
        self.assertEqual(resultado.fecha_limite, self.fecha_limite)
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_generate_historical_carga_datos_maestro(self, mock_data_manager):
        """Test: Verificar que se cargan los datos del maestro"""
        # Mock básico
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {'nombre_inmueble': 'Casa Test', 'precio_original': 100000}
        ]
        mock_data_manager_instance.read_existing_historical.return_value = {}
        
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
        mock_data_manager_instance.load_maestro_data.side_effect = Exception("Error de conexión")
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Debería fallar graciosamente
        with self.assertRaises(Exception) as context:
            service.generate_historical_until(self.fecha_limite)
        
        self.assertIn("Error de conexión", str(context.exception))
    
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
        mock_data_manager_instance.read_existing_historical.return_value = {}
        
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


class TestHistoricalServiceIntegracionMock(unittest.TestCase):
    """Tests de integración con mocks para componentes dependientes"""
    
    def setUp(self):
        self.fecha_limite = "2024-12"
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    @patch('inmobiliaria.services.historical_service.logging')
    def test_logging_proceso_completo(self, mock_logging, mock_data_manager):
        """Test: Verificar que se hace logging del proceso"""
        # Mock básico
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {'nombre_inmueble': 'Casa Test', 'precio_original': 100000}
        ]
        mock_data_manager_instance.read_existing_historical.return_value = {}
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Mock del procesamiento
        with patch.object(service, 'process_property') as mock_process:
            mock_process.return_value = []
            
            service.generate_historical_until(self.fecha_limite)
        
        # Verificar que se hace logging
        mock_logging.warning.assert_called()
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    def test_property_historical_data_creacion(self, mock_data_manager):
        """Test: Verificar creación de PropertyHistoricalData"""
        # Mock básico
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {'nombre_inmueble': 'Casa Test', 'precio_original': 100000}
        ]
        mock_data_manager_instance.read_existing_historical.return_value = {}
        
        service = HistoricalService()
        service.data_manager = mock_data_manager_instance
        
        # Mock simple del process_property
        with patch.object(service, 'process_property') as mock_process:
            from inmobiliaria.domain.historical_models import PropertyHistoricalData
            mock_process.return_value = [PropertyHistoricalData(
                propiedad={'nombre_inmueble': 'Test'},
                registros_generados=[]
            )]
            
            resultado = service.generate_historical_until(self.fecha_limite)
            
            # Verificar que se ejecutó
            self.assertIsInstance(resultado, HistoricalSummary)


if __name__ == '__main__':
    unittest.main()
