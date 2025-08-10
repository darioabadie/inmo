#!/usr/bin/env python3
"""
Tests unitarios para la funcionalidad de logging de errores en el módulo historical.
Validación de configuración, escritura y manejo de archivos de log.
"""

import unittest
import tempfile
import shutil
import os
import logging
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from inmobiliaria.historical import setup_error_logger
from inmobiliaria.services.historical_service import HistoricalService
from inmobiliaria.domain.historical_models import HistoricalSummary


class TestHistoricalErrorLogging(unittest.TestCase):
    """Tests para el sistema de logging de errores del módulo historical"""
    
    def setUp(self):
        """Setup común - crear directorio temporal para tests"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Cleanup - eliminar directorio temporal"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Limpiar handlers del logger para evitar conflictos
        error_logger = logging.getLogger('historical_errors')
        for handler in error_logger.handlers[:]:
            handler.close()  # Cerrar el archivo antes de remover
            error_logger.removeHandler(handler)
    
    def test_setup_error_logger_creates_directory(self):
        """Test: setup_error_logger crea el directorio logs/"""
        # Verificar que no existe inicialmente
        self.assertFalse(os.path.exists('logs'))
        
        # Ejecutar
        logger = setup_error_logger()
        
        # Verificar que se creó el directorio
        self.assertTrue(os.path.exists('logs'))
        self.assertTrue(os.path.isdir('logs'))
        
    def test_setup_error_logger_returns_configured_logger(self):
        """Test: setup_error_logger retorna un logger correctamente configurado"""
        logger = setup_error_logger()
        
        # Verificar propiedades del logger
        self.assertEqual(logger.name, 'historical_errors')
        self.assertEqual(logger.level, logging.ERROR)
        self.assertTrue(len(logger.handlers) > 0)
        
        # Verificar que tiene un FileHandler
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        self.assertEqual(len(file_handlers), 1)
        
    def test_setup_error_logger_writes_to_file(self):
        """Test: El logger escribe correctamente al archivo errors.log"""
        logger = setup_error_logger()
        
        # Escribir un mensaje de prueba
        test_message = "Test error message for logging"
        logger.error(test_message)
        
        # Verificar que el archivo existe y contiene el mensaje
        log_path = os.path.join('logs', 'errors.log')
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn(test_message, content)
        self.assertIn('[HISTORICAL]', content)
        self.assertIn('ERROR', content)
        
    def test_setup_error_logger_preserves_existing_logs(self):
        """Test: El logger no sobrescribe logs existentes (append mode)"""
        logger = setup_error_logger()
        
        # Escribir primer mensaje
        logger.error("Primera entrada")
        
        # Crear nuevo logger (simular nueva ejecución)
        logger2 = setup_error_logger()
        logger2.error("Segunda entrada")
        
        # Verificar que ambos mensajes están en el archivo
        log_path = os.path.join('logs', 'errors.log')
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("Primera entrada", content)
        self.assertIn("Segunda entrada", content)
        
    def test_setup_error_logger_idempotent(self):
        """Test: Múltiples llamadas a setup_error_logger no crean handlers duplicados"""
        # Llamar múltiples veces
        logger1 = setup_error_logger()
        logger2 = setup_error_logger()
        logger3 = setup_error_logger()
        
        # Verificar que es el mismo logger
        self.assertIs(logger1, logger2)
        self.assertIs(logger2, logger3)
        
        # Verificar que no se duplicaron handlers
        file_handlers = [h for h in logger1.handlers if isinstance(h, logging.FileHandler)]
        self.assertEqual(len(file_handlers), 1)


class TestHistoricalServiceErrorLogging(unittest.TestCase):
    """Tests para integración del error logging en HistoricalService"""
    
    def setUp(self):
        """Setup común"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Mock logger para capturar llamadas
        self.mock_error_logger = Mock()
        
    def tearDown(self):
        """Cleanup"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_historical_service_accepts_error_logger(self):
        """Test: HistoricalService acepta error_logger en constructor"""
        with patch('inmobiliaria.services.historical_service.HistoricalDataManager'):
            service = HistoricalService(error_logger=self.mock_error_logger)
            self.assertIs(service.error_logger, self.mock_error_logger)
    
    def test_historical_service_works_without_error_logger(self):
        """Test: HistoricalService funciona sin error_logger (None)"""
        with patch('inmobiliaria.services.historical_service.HistoricalDataManager'):
            service = HistoricalService()
            self.assertIsNone(service.error_logger)
        
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    @patch('inmobiliaria.services.historical_service.traer_inflacion')
    def test_historical_service_logs_property_errors(self, mock_inflacion, mock_data_manager):
        """Test: HistoricalService loggea errores de propiedades individuales"""
        # Configurar mocks
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {
                'nombre_inmueble': 'Test Property',
                'inquilino': 'Test Inquilino',
                'fecha_inicio_contrato': '2024-01-01',
                'precio_original': '100000'
            }
        ]
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        
        mock_inflacion.return_value = Mock()
        
        # Crear servicio con mock error logger
        service = HistoricalService(error_logger=self.mock_error_logger)
        service.data_manager = mock_data_manager_instance
        
        # Mock process_property para que falle
        def failing_process_property(*args, **kwargs):
            raise ValueError("Campo obligatorio faltante: actualizacion")
        
        service.process_property = failing_process_property
        
        # Ejecutar
        import datetime as dt
        result = service.generate_historical_until(dt.date(2024, 6, 30))
        
        # Verificar que se llamó al error logger
        self.mock_error_logger.error.assert_called()
        
        # Verificar el formato del mensaje de error
        call_args = self.mock_error_logger.error.call_args[0][0]
        self.assertIn("Propiedad: Test Property", call_args)
        self.assertIn("Inquilino: Test Inquilino", call_args)
        self.assertIn("Fecha inicio: 2024-01-01", call_args)
        self.assertIn("Precio original: 100000", call_args)
        self.assertIn("Error: Campo obligatorio faltante: actualizacion", call_args)
        
        # Verificar que el error se agregó al resumen
        self.assertIsNotNone(result.errores)
        self.assertEqual(len(result.errores), 1)
        self.assertIn("Campo obligatorio faltante: actualizacion", result.errores[0])
    
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    @patch('inmobiliaria.services.historical_service.traer_inflacion')
    def test_historical_service_works_without_logger_on_error(self, mock_inflacion, mock_data_manager):
        """Test: HistoricalService maneja errores correctamente sin error_logger"""
        # Configurar mocks (mismo setup que test anterior)
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {
                'nombre_inmueble': 'Test Property',
                'inquilino': 'Test Inquilino',  
                'fecha_inicio_contrato': '2024-01-01',
                'precio_original': '100000'
            }
        ]
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        mock_inflacion.return_value = Mock()
        
        # Crear servicio SIN error logger
        service = HistoricalService()  # Sin error_logger
        service.data_manager = mock_data_manager_instance
        
        # Mock process_property para que falle
        def failing_process_property(*args, **kwargs):
            raise ValueError("Campo obligatorio faltante: actualizacion")
        
        service.process_property = failing_process_property
        
        # Ejecutar - no debería fallar aunque no hay error_logger
        import datetime as dt
        result = service.generate_historical_until(dt.date(2024, 6, 30))
        
        # Verificar que se procesó el error correctamente en el resumen
        self.assertIsNotNone(result.errores)
        self.assertEqual(len(result.errores), 1)
        self.assertIn("Campo obligatorio faltante: actualizacion", result.errores[0])
        
    @patch('inmobiliaria.services.historical_service.HistoricalDataManager')
    @patch('inmobiliaria.services.historical_service.traer_inflacion')
    def test_error_logger_handles_missing_property_fields(self, mock_inflacion, mock_data_manager):
        """Test: Error logger maneja correctamente propiedades con campos faltantes"""
        # Configurar mock con propiedad que tiene campos faltantes
        mock_data_manager_instance = Mock()
        mock_data_manager.return_value = mock_data_manager_instance
        mock_data_manager_instance.load_maestro_data.return_value = [
            {
                'nombre_inmueble': 'Test Property',
                # 'inquilino' faltante
                # 'fecha_inicio_contrato' faltante  
                # 'precio_original' faltante
            }
        ]
        mock_data_manager_instance.load_existing_historical_data.return_value = {}
        mock_inflacion.return_value = Mock()
        
        # Crear servicio con mock error logger
        service = HistoricalService(error_logger=self.mock_error_logger)
        service.data_manager = mock_data_manager_instance
        
        # Mock process_property para que falle
        def failing_process_property(*args, **kwargs):
            raise ValueError("Campo obligatorio faltante: inquilino")
        
        service.process_property = failing_process_property
        
        # Ejecutar
        import datetime as dt
        result = service.generate_historical_until(dt.date(2024, 6, 30))
        
        # Verificar que se llamó al error logger con valores por defecto
        self.mock_error_logger.error.assert_called()
        call_args = self.mock_error_logger.error.call_args[0][0]
        
        self.assertIn("Propiedad: Test Property", call_args)
        self.assertIn("Inquilino: N/A", call_args)  # Campo faltante -> N/A
        self.assertIn("Fecha inicio: N/A", call_args)  # Campo faltante -> N/A
        self.assertIn("Precio original: N/A", call_args)  # Campo faltante -> N/A


class TestErrorLoggingIntegration(unittest.TestCase):
    """Tests de integración para el sistema completo de error logging"""
    
    def setUp(self):
        """Setup para tests de integración"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def tearDown(self):
        """Cleanup"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Limpiar handlers del logger
        error_logger = logging.getLogger('historical_errors')
        for handler in error_logger.handlers[:]:
            handler.close()  # Cerrar el archivo antes de remover
            error_logger.removeHandler(handler)
    
    def test_end_to_end_error_logging(self):
        """Test: Flujo completo de error logging desde setup hasta archivo"""
        # Setup del logger
        error_logger = setup_error_logger()
        
        # Crear servicio con el logger (usando mock para evitar dependencias)
        with patch('inmobiliaria.services.historical_service.HistoricalDataManager'):
            service = HistoricalService(error_logger=error_logger)
        
        # Simular error de propiedad
        test_data = {
            'nombre_inmueble': 'Av. Santa Fe 1234',
            'inquilino': 'María García',
            'fecha_inicio_contrato': '2024-01-15', 
            'precio_original': '100000'
        }
        
        error_msg = "Campo obligatorio faltante: actualizacion"
        
        # Simular el logging que hace el servicio real
        if service.error_logger:
            service.error_logger.error(
                f"Propiedad: {test_data['nombre_inmueble']} | "
                f"Inquilino: {test_data['inquilino']} | "
                f"Fecha inicio: {test_data['fecha_inicio_contrato']} | "
                f"Precio original: {test_data['precio_original']} | "
                f"Error: {error_msg}"
            )
        
        # Verificar que el archivo se creó con el contenido correcto
        log_path = os.path.join('logs', 'errors.log')
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar contenido
        self.assertIn("Av. Santa Fe 1234", content)
        self.assertIn("María García", content)
        self.assertIn("2024-01-15", content)
        self.assertIn("100000", content)
        self.assertIn("Campo obligatorio faltante: actualizacion", content)
        self.assertIn("[HISTORICAL]", content)
        self.assertIn("ERROR", content)
        
        # Verificar formato de timestamp (YYYY-MM-DD HH:MM:SS)
        lines = content.strip().split('\n')
        self.assertTrue(len(lines) > 0)
        # El formato debería ser: "2025-08-10 17:03:07 - ERROR - [HISTORICAL] - ..."
        first_line = lines[0]
        parts = first_line.split(' - ')
        self.assertEqual(len(parts), 4)  # timestamp, level, context, message
        
        # Verificar timestamp format
        timestamp_part = parts[0]
        self.assertEqual(len(timestamp_part), 19)  # "YYYY-MM-DD HH:MM:SS"
        self.assertRegex(timestamp_part, r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$')


if __name__ == '__main__':
    unittest.main()
