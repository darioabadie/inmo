#!/usr/bin/env python3
"""
Tests unitarios para MonthlyRecordGenerator.
Validación de generación de registros, validación de contexto y cálculos precisos.
"""

import unittest
import datetime as dt
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from inmobiliaria.services.record_generator import MonthlyRecordGenerator
from inmobiliaria.domain.historical_models import CalculationContext, HistoricalRecord
from inmobiliaria.models import Propiedad, Contrato


class TestMonthlyRecordGeneratorUnit(unittest.TestCase):
    """Tests unitarios para el generador de registros mensuales"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.generator = MonthlyRecordGenerator()
        
        # Crear objetos de prueba
        self.propiedad = Propiedad(
            nombre_inmueble='Casa Test',
            dir_inmueble='Calle Test 123',
            propietario='Ana Test',
            inquilino='Juan Test',
            municipalidad=2000.0
        )
        
        self.contrato = Contrato(
            precio_original=100000.0,
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            duracion_meses=12,
            actualizacion='trimestral',
            indice='IPC',
            comision_inmo='5%',
            comision='Pagado',
            deposito='Pagado'
        )
        
        self.context = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2024, 1, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=0,
            precio_base_actual=100000.0
        )
    
    def test_inicializacion_generator(self):
        """Test: Verificar inicialización correcta del generador"""
        self.assertIsNotNone(self.generator.calculations)
    
    def test_generate_record_estructura_basica(self):
        """Test: Verificar estructura básica del registro generado"""
        # Mock de cálculos para evitar complejidad
        with patch.object(self.generator.calculations, 'calculate_price_update') as mock_calc:
            mock_calc.return_value = (100000.0, "0%", False)
            
            with patch.object(self.generator.calculations, 'calculate_proximity_months') as mock_prox:
                mock_prox.return_value = (3, 12)
                
                record = self.generator.generate_record(self.context)
                
                # Verificar que es un HistoricalRecord
                self.assertIsInstance(record, HistoricalRecord)
                
                # Verificar campos básicos
                self.assertEqual(record.nombre_inmueble, 'Casa Test')
                self.assertEqual(record.dir_inmueble, 'Calle Test 123')
                self.assertEqual(record.inquilino, 'Juan Test')
                self.assertEqual(record.propietario, 'Ana Test')
                self.assertEqual(record.mes_actual, '2024-01')
    
    def test_validate_context_fecha_valida(self):
        """Test: Verificar validación de contexto con fecha válida"""
        # Fecha posterior al inicio del contrato
        context_valido = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2024, 2, 1),  # Un mes después
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=1,
            precio_base_actual=100000.0
        )
        
        resultado = self.generator.validate_context(context_valido)
        self.assertEqual(resultado, "Válido")
    
    def test_validate_context_fecha_invalida(self):
        """Test: Verificar validación de contexto con fecha inválida"""
        # Fecha anterior al inicio del contrato
        context_invalido = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2023, 12, 1),  # Un mes antes del inicio
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=-1,
            precio_base_actual=100000.0
        )
        
        resultado = self.generator.validate_context(context_invalido)
        self.assertEqual(resultado, "Fecha inválida")
    
    def test_validate_context_contrato_vencido(self):
        """Test: Verificar validación de contexto con contrato vencido"""
        # Fecha posterior al vencimiento del contrato
        context_vencido = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2025, 2, 1),  # 13 meses después (contrato de 12 meses)
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=13,
            precio_base_actual=100000.0
        )
        
        resultado = self.generator.validate_context(context_vencido)
        self.assertEqual(resultado, "Contrato vencido")
    
    def test_calculate_cuotas_adicionales_pagado(self):
        """Test: Verificar cálculo de cuotas cuando comisión y depósito están pagados"""
        cuotas_comision, cuotas_deposito = self.generator._calculate_cuotas_adicionales(
            self.context, 100000.0  # precio_base
        )
        
        # Con "Pagado", no debe haber cuotas adicionales
        self.assertEqual(cuotas_comision, 0.0)
        self.assertEqual(cuotas_deposito, 0.0)
    
    def test_calculate_cuotas_adicionales_2_cuotas(self):
        """Test: Verificar cálculo de cuotas con comisión en 2 cuotas"""
        # Modificar contrato para tener 2 cuotas de comisión
        contrato_2_cuotas = Contrato(
            precio_original=100000.0,
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            duracion_meses=12,
            actualizacion='trimestral',
            indice='IPC',
            comision_inmo='5%',
            comision='2 cuotas',  # 2 cuotas
            deposito='Pagado'
        )
        
        context_2_cuotas = CalculationContext(
            propiedad=self.propiedad,
            contrato=contrato_2_cuotas,
            fecha_actual=dt.date(2024, 1, 1),  # Primer mes
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=0,
            precio_base_actual=100000.0
        )
        
        cuotas_comision, cuotas_deposito = self.generator._calculate_cuotas_adicionales(
            context_2_cuotas, 100000.0
        )
        
        # En el primer mes debe haber cuota de comisión
        # (precio_base * 1.10) / 2 = (100000 * 1.10) / 2 = 55000
        expected_comision = (100000.0 * 1.10) / 2
        self.assertEqual(cuotas_comision, expected_comision)
        self.assertEqual(cuotas_deposito, 0.0)  # Depósito pagado
    
    def test_calculate_commission_percentage(self):
        """Test: Verificar cálculo de comisión en porcentaje"""
        comision = self.generator._calculate_commission(100000.0, '5%')
        expected = 100000.0 * 0.05
        self.assertEqual(comision, expected)
    
    def test_calculate_commission_fixed_amount(self):
        """Test: Verificar cálculo de comisión con monto fijo"""
        # Si no es porcentaje, debería ser 0 (comportamiento por defecto)
        comision = self.generator._calculate_commission(100000.0, '5000')
        self.assertEqual(comision, 0.0)  # Monto fijo no se procesa como porcentaje
    
    def test_calculate_pago_propietario(self):
        """Test: Verificar cálculo del pago al propietario"""
        precio_base = 100000.0
        comision = 5000.0  # 5%
        
        pago_prop = self.generator._calculate_pago_propietario(precio_base, comision)
        expected = precio_base - comision
        self.assertEqual(pago_prop, expected)
    
    def test_create_detail_cuotas_string(self):
        """Test: Verificar creación del string detalle de cuotas"""
        detalle = self.generator._create_detail_cuotas(5000.0, 2000.0)
        
        # Debe incluir ambos valores
        self.assertIn('5000', detalle)
        self.assertIn('2000', detalle)
        self.assertIn('Comisión', detalle)
        self.assertIn('Depósito', detalle)
    
    def test_create_detail_cuotas_solo_comision(self):
        """Test: Verificar creación del string solo con comisión"""
        detalle = self.generator._create_detail_cuotas(5000.0, 0.0)
        
        self.assertIn('5000', detalle)
        self.assertIn('Comisión', detalle)
        self.assertNotIn('Depósito', detalle)
    
    def test_format_percentage_display(self):
        """Test: Verificar formateo de porcentaje para display"""
        # Test con porcentaje normal
        formatted = self.generator._format_percentage('12.5%')
        self.assertEqual(formatted, '12.5%')
        
        # Test con porcentaje sin %
        formatted_no_percent = self.generator._format_percentage('12.5')
        self.assertEqual(formatted_no_percent, '12.5%')
        
        # Test con string vacío
        formatted_empty = self.generator._format_percentage('')
        self.assertEqual(formatted_empty, '')


class TestMonthlyRecordGeneratorIntegration(unittest.TestCase):
    """Tests de integración con mocks para MonthlyRecordGenerator"""
    
    def setUp(self):
        self.generator = MonthlyRecordGenerator()
        
        self.propiedad = Propiedad(
            nombre_inmueble='Casa Integration',
            dir_inmueble='Calle Integration 456',
            propietario='Maria Test',
            inquilino='Carlos Test',
            municipalidad=3000.0
        )
        
        self.contrato = Contrato(
            precio_original=150000.0,
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            duracion_meses=24,
            actualizacion='semestral',
            indice='ICL',
            comision_inmo='4%',
            comision='3 cuotas',
            deposito='2 cuotas'
        )
    
    @patch('inmobiliaria.services.record_generator.HistoricalCalculations')
    def test_generate_record_con_actualizacion(self, mock_calculations_class):
        """Test: Verificar generación de registro con actualización de precio"""
        # Mock de la clase de cálculos
        mock_calculations = Mock()
        mock_calculations_class.return_value = mock_calculations
        
        # Mock de los métodos de cálculo
        mock_calculations.calculate_price_update.return_value = (165000.0, "10%", True)
        mock_calculations.calculate_proximity_months.return_value = (6, 18)
        
        generator = MonthlyRecordGenerator()
        
        context = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2024, 7, 1),  # 6 meses después (actualización semestral)
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=6,
            precio_base_actual=150000.0
        )
        
        record = generator.generate_record(context)
        
        # Verificar que se aplicó la actualización
        self.assertEqual(record.actualizacion, "SI")
        self.assertEqual(record.porc_actual, "10%")
        self.assertEqual(record.precio_original, 165000.0)
    
    def test_generate_record_mes_con_cuotas(self):
        """Test: Verificar generación de registro en mes con cuotas adicionales"""
        context = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2024, 1, 1),  # Primer mes
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=0,
            precio_base_actual=150000.0
        )
        
        with patch.object(self.generator.calculations, 'calculate_price_update') as mock_calc:
            mock_calc.return_value = (150000.0, "0%", False)
            
            with patch.object(self.generator.calculations, 'calculate_proximity_months') as mock_prox:
                mock_prox.return_value = (6, 24)
                
                record = self.generator.generate_record(context)
                
                # En el primer mes debe haber cuotas adicionales
                self.assertGreater(record.cuotas_adicionales, 0)
                self.assertGreater(record.cuotas_comision, 0)  # 3 cuotas de comisión
                self.assertGreater(record.cuotas_deposito, 0)   # 2 cuotas de depósito
                self.assertIn('Comisión', record.detalle_cuotas)
                self.assertIn('Depósito', record.detalle_cuotas)


if __name__ == '__main__':
    unittest.main()
