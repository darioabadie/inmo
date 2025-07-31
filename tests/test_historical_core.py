#!/usr/bin/env python3
"""
Tests funcionales para el módulo historical.py - Funcionalidad núcleo
Tests 111-135: Validación del núcleo de generación de historial

ACTUALIZADO: Para usar la nueva arquitectura de servicios
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inmobiliaria.models import Propiedad, Contrato
from inmobiliaria.services.historical_service import HistoricalService
from inmobiliaria.services.historical_calculations import HistoricalCalculations
from inmobiliaria.services.record_generator import MonthlyRecordGenerator
from inmobiliaria.services.historical_data import HistoricalDataManager
from inmobiliaria.domain.historical_models import CalculationContext


class TestHistoricalServiceCore(unittest.TestCase):
    """Tests del servicio principal del historial"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.service = HistoricalService()
        self.calculations = HistoricalCalculations()
        self.record_generator = MonthlyRecordGenerator()
        
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
            actualizacion="trimestral",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )

    def test_111_servicio_historico_inicializacion(self):
        """Test 111: Verificar inicialización correcta del servicio histórico"""
        service = HistoricalService()
        
        # Verificar que los componentes se inicializan correctamente
        self.assertIsNotNone(service.data_manager)
        self.assertIsNotNone(service.record_generator)
        self.assertIsNotNone(service.calculations)
        self.assertIsNotNone(service.summary)

    @patch('inmobiliaria.services.historical_data.HistoricalDataManager.load_maestro_data')
    @patch('inmobiliaria.services.inflation.traer_inflacion')
    @patch('inmobiliaria.services.historical_data.HistoricalDataManager.read_existing_historical')
    @patch('inmobiliaria.services.historical_data.HistoricalDataManager.write_historical_records')
    def test_112_generacion_historial_flujo_completo(self, mock_write, mock_read, mock_inflacion, mock_maestro):
        """Test 112: Verificar flujo completo de generación de historial"""
        # Mock de datos de entrada
        mock_maestro.return_value = [{
            "nombre_inmueble": "Casa Test",
            "dir_inmueble": "Calle Falsa 123",
            "propietario": "Juan Perez",
            "inquilino": "Ana Garcia",
            "precio_original": 100000.0,
            "fecha_inicio_contrato": "2024-01-01",
            "duracion_meses": 24,
            "actualizacion": "trimestral",
            "indice": "10%",
            "comision_inmo": "5%",
            "comision": "Pagado",
            "deposito": "Pagado"
        }]
        
        mock_inflacion.return_value = MagicMock()
        mock_read.return_value = {}
        
        # Ejecutar
        fecha_limite = dt.date(2024, 3, 1)
        summary = self.service.generate_historical_until(fecha_limite)
        
        # Verificar
        self.assertGreater(summary.total_registros, 0)
        self.assertEqual(summary.propiedades_procesadas, 1)
        mock_write.assert_called_once()

    def test_113_calculo_meses_desde_inicio(self):
        """Test 113: Verificar cálculo correcto de meses desde inicio"""
        fecha_inicio = dt.date(2024, 1, 1)
        fecha_actual = dt.date(2024, 4, 1)
        
        meses = self.calculations.calculate_months_since_start(fecha_actual, fecha_inicio)
        
        # 3 meses completos (enero -> abril)
        self.assertEqual(meses, 3)

    def test_114_validacion_contexto(self):
        """Test 114: Verificar validación de contexto para generación de registros"""
        # Crear contexto válido
        context = CalculationContext(
            propiedad=self.propiedad_test,
            contrato=self.contrato_porcentaje,
            fecha_actual=dt.date(2024, 2, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=1,
            precio_base_actual=100000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            inflacion_df=MagicMock()
        )
        
        # Debe ser válido
        is_valid = self.record_generator.validate_context(context)
        self.assertTrue(is_valid)

    def test_115_validacion_contexto_fecha_invalida(self):
        """Test 115: Verificar validación de contexto con fecha inválida"""
        # Crear contexto con fecha anterior al inicio del contrato
        context = CalculationContext(
            propiedad=self.propiedad_test,
            contrato=self.contrato_porcentaje,
            fecha_actual=dt.date(2023, 12, 1),  # Antes del inicio
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=-1,
            precio_base_actual=100000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            inflacion_df=MagicMock()
        )
        
        # No debe ser válido
        is_valid = self.record_generator.validate_context(context)
        self.assertFalse(is_valid)

    def test_116_generacion_registro_mensual(self):
        """Test 116: Verificar generación de registro mensual individual"""
        context = CalculationContext(
            propiedad=self.propiedad_test,
            contrato=self.contrato_porcentaje,
            fecha_actual=dt.date(2024, 2, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=1,
            precio_base_actual=100000.0,
            municipalidad=1000.0,
            luz=500.0,
            gas=300.0,
            expensas=2000.0,
            descuento_porcentaje=0.0,
            inflacion_df=MagicMock()
        )
        
        # Generar registro
        registro = self.record_generator.generate_monthly_record(context)
        
        # Verificar campos básicos
        self.assertEqual(registro.nombre_inmueble, "Casa Test")
        self.assertEqual(registro.precio_original, 100000.0)
        self.assertEqual(registro.municipalidad, 1000.0)
        self.assertEqual(registro.luz, 500.0)
        self.assertEqual(registro.gas, 300.0)
        self.assertEqual(registro.expensas, 2000.0)

    def test_117_calculo_fecha_siguiente_mes(self):
        """Test 117: Verificar cálculo de fecha del siguiente mes"""
        fecha_actual = dt.date(2024, 1, 1)
        fecha_siguiente = self.calculations.get_next_month_date(fecha_actual)
        
        self.assertEqual(fecha_siguiente, dt.date(2024, 2, 1))
        
        # Caso especial: diciembre -> enero del siguiente año
        fecha_diciembre = dt.date(2024, 12, 1)
        fecha_enero = self.calculations.get_next_month_date(fecha_diciembre)
        
        self.assertEqual(fecha_enero, dt.date(2025, 1, 1))

    @patch('inmobiliaria.services.historical_data.HistoricalDataManager.load_maestro_data')
    def test_118_manejo_errores_propiedad_individual(self, mock_maestro):
        """Test 118: Verificar manejo de errores en propiedades individuales"""
        # Mock de datos con un registro inválido
        mock_maestro.return_value = [{
            "nombre_inmueble": "Casa Inválida",
            # Faltan campos obligatorios
            "precio_original": 100000.0
        }]
        
        with patch('inmobiliaria.services.inflation.traer_inflacion'):
            with patch('inmobiliaria.services.historical_data.HistoricalDataManager.read_existing_historical', return_value={}):
                fecha_limite = dt.date(2024, 3, 1)
                summary = self.service.generate_historical_until(fecha_limite)
                
                # Debe haber errores
                self.assertTrue(len(summary.errores or []) > 0)
                self.assertEqual(summary.propiedades_omitidas, 1)

    def test_119_creation_context_for_month(self):
        """Test 119: Verificar creación de contexto para un mes específico"""
        fecha_actual = dt.date(2024, 2, 1)
        precio_base = 100000.0
        inflacion_df = MagicMock()
        
        context = self.record_generator.create_context_for_month(
            propiedad=self.propiedad_test,
            contrato=self.contrato_porcentaje,
            fecha_actual=fecha_actual,
            precio_base_actual=precio_base,
            inflacion_df=inflacion_df,
            municipalidad=1000.0,
            luz=500.0,
            gas=300.0,
            expensas=2000.0,
            descuento_porcentaje=15.0
        )
        
        # Verificar contexto
        self.assertEqual(context.fecha_actual, fecha_actual)
        self.assertEqual(context.precio_base_actual, precio_base)
        self.assertEqual(context.municipalidad, 1000.0)
        self.assertEqual(context.descuento_porcentaje, 15.0)

    def test_120_datos_historicos_manager_creacion(self):
        """Test 120: Verificar creación del data manager"""
        data_manager = HistoricalDataManager()
        
        # Verificar que se puede instanciar
        self.assertIsNotNone(data_manager)
        self.assertIsNotNone(data_manager.gc)
        self.assertIsNotNone(data_manager.sheet)


if __name__ == '__main__':
    unittest.main()
