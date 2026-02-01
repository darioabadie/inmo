#!/usr/bin/env python3
"""
Tests unitarios para MonthlyRecordGenerator.
"""

import unittest
import datetime as dt
from unittest.mock import patch

from inmobiliaria.services.record_generator import MonthlyRecordGenerator
from inmobiliaria.domain.historical_models import CalculationContext, HistoricalRecord
from inmobiliaria.models import Propiedad, Contrato


class TestMonthlyRecordGeneratorUnit(unittest.TestCase):
    """Tests unitarios para el generador de registros mensuales"""

    def setUp(self):
        self.generator = MonthlyRecordGenerator()

        self.propiedad = Propiedad(
            nombre="Casa Test",
            direccion="Calle Test 123",
            propietario="Ana Test",
            inquilino="Juan Test",
            nis="0",
            gas_nro="0",
            padron="0",
        )

        self.contrato = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="IPC",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado",
        )

        self.context = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2024, 1, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=0,
            precio_base_actual=100000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            monto_comision=None,
            inflacion_df=None,
        )

    def test_inicializacion_generator(self):
        self.assertIsNotNone(self.generator.calculations)

    def test_generate_monthly_record_estructura_basica(self):
        with patch.object(self.generator.calculations, "calculate_price_update") as mock_calc:
            mock_calc.return_value = (100000.0, "0%", False)

            with patch.object(self.generator.calculations, "calculate_proximity_months") as mock_prox:
                mock_prox.return_value = (3, 12)

                record = self.generator.generate_monthly_record(self.context)

        self.assertIsInstance(record, HistoricalRecord)
        self.assertEqual(record.nombre_inmueble, "Casa Test")
        self.assertEqual(record.dir_inmueble, "Calle Test 123")
        self.assertEqual(record.inquilino, "Juan Test")
        self.assertEqual(record.propietario, "Ana Test")
        self.assertEqual(record.mes_actual, "2024-01")
        self.assertEqual(record.precio_final, 100000.0)
        self.assertEqual(record.comision_inmo, 5000.0)
        self.assertEqual(record.pago_prop, 95000.0)

    def test_validate_context_valido(self):
        self.assertTrue(self.generator.validate_context(self.context))

    def test_validate_context_fecha_invalida(self):
        context_invalido = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2023, 12, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=-1,
            precio_base_actual=100000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            monto_comision=None,
            inflacion_df=None,
        )

        self.assertFalse(self.generator.validate_context(context_invalido))

    def test_validate_context_contrato_vencido(self):
        context_vencido = CalculationContext(
            propiedad=self.propiedad,
            contrato=self.contrato,
            fecha_actual=dt.date(2025, 1, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=12,
            precio_base_actual=100000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            monto_comision=None,
            inflacion_df=None,
        )

        self.assertFalse(self.generator.validate_context(context_vencido))

    def test_comision_inmo_sobre_deposito(self):
        contrato = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=450000.0,
            actualizacion="trimestral",
            indice="IPC",
            comision_inmo="6%",
            comision="Pagado",
            deposito="2 cuotas",
        )

        context = CalculationContext(
            propiedad=self.propiedad,
            contrato=contrato,
            fecha_actual=dt.date(2024, 1, 1),
            fecha_inicio_contrato=dt.date(2024, 1, 1),
            meses_desde_inicio=0,
            precio_base_actual=450000.0,
            municipalidad=0.0,
            luz=0.0,
            gas=0.0,
            expensas=0.0,
            descuento_porcentaje=0.0,
            monto_comision=None,
            inflacion_df=None,
        )

        with patch.object(self.generator.calculations, "calculate_price_update") as mock_calc:
            mock_calc.return_value = (450000.0, "0%", False)

            with patch.object(self.generator.calculations, "calculate_proximity_months") as mock_prox:
                mock_prox.return_value = (3, 12)

                record = self.generator.generate_monthly_record(context)

        self.assertEqual(record.cuotas_deposito, 225000.0)
        self.assertEqual(record.comision_inmo, 40500.0)
        self.assertEqual(record.pago_prop, 634500.0)


if __name__ == "__main__":
    unittest.main()
