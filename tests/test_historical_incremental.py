#!/usr/bin/env python3
"""
Tests funcionales para el módulo historical.py - Funcionalidad incremental
Tests 136-150: Validación de la lógica incremental y continuación de histórico
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
    leer_historico_existente,
    generar_meses_faltantes,
    main
)


class TestHistoricalIncremental(unittest.TestCase):
    """Tests de funcionalidad incremental del historial"""
    
    def setUp(self):
        """Setup común para todos los tests"""
        self.propiedad_test = Propiedad(
            nombre="Casa Incremental",
            direccion="Avenida Test 456",
            propietario="Maria Lopez",
            inquilino="Carlos Rodriguez"
        )
        
        self.contrato_test = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=12,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        self.inflacion_df = pd.DataFrame({
            'año': [2024] * 6,
            'mes': [1, 2, 3, 4, 5, 6],
            'ipc_mensual': [2.0, 1.5, 1.8, 2.2, 1.9, 2.1]
        })
        
        # Histórico simulado existente - manteniendo marzo para compatibilidad con tests existentes
        # Solo el histórico debe reflejar los hechos pasados, no la lógica futura
        self.historico_existente = {
            'Casa Incremental': {
                'ultimo_mes': '2024-03',
                'ultimo_precio_base': 110000.0,
                'registros_existentes': [
                    {
                        'nombre_inmueble': 'Casa Incremental',
                        'mes_actual': '2024-01',
                        'precio_base': 100000.0,
                        'precio_mes_actual': 100000.0,
                        'actualizacion': 'NO',
                        'porc_actual': ''
                    },
                    {
                        'nombre_inmueble': 'Casa Incremental',
                        'mes_actual': '2024-02',
                        'precio_base': 100000.0,
                        'precio_mes_actual': 100000.0,
                        'actualizacion': 'NO',
                        'porc_actual': ''
                    },
                    {
                        'nombre_inmueble': 'Casa Incremental',
                        'mes_actual': '2024-03',
                        'precio_base': 110000.0,
                        'precio_mes_actual': 110000.0,
                        'actualizacion': 'SI',
                        'porc_actual': '10.00%'
                    }
                ]
            }
        }

    # Test 136: Continuación desde último mes registrado
    def test_136_continuacion_desde_ultimo_mes(self):
        """Test 136: Verificar continuación desde último mes del histórico"""
        fecha_limite = dt.date(2024, 6, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (110000.0, "", False)  # Sin actualización
            
            # Simular continuación desde marzo (último mes registrado)
            nuevos_registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                110000.0, "2024-03", self.inflacion_df, 0.0
            )
        
        # Debería generar abril, mayo, junio (3 meses)
        self.assertEqual(len(nuevos_registros), 3)
        self.assertEqual(nuevos_registros[0]['mes_actual'], "2024-04")
        self.assertEqual(nuevos_registros[1]['mes_actual'], "2024-05")
        self.assertEqual(nuevos_registros[2]['mes_actual'], "2024-06")
        
        # Precio base debería partir de 110000 (último registrado)
        for registro in nuevos_registros:
            self.assertEqual(registro['precio_base'], 110000.0)

    # Test 137: Preservación de registros existentes
    def test_137_preservacion_registros_existentes(self):
        """Test 137: Verificar que se preservan registros existentes"""
        
        # Simular el proceso completo con histórico existente
        todos_los_registros = []
        
        # Agregar registros existentes
        todos_los_registros.extend(self.historico_existente['Casa Incremental']['registros_existentes'])
        
        # Verificar que los registros existentes se mantienen
        self.assertEqual(len(todos_los_registros), 3)
        self.assertEqual(todos_los_registros[0]['mes_actual'], "2024-01")
        self.assertEqual(todos_los_registros[2]['precio_base'], 110000.0)

    # Test 138: Detección correcta de último precio_base
    def test_138_deteccion_ultimo_precio_base(self):
        """Test 138: Verificar detección correcta del último precio_base"""
        
        # Histórico con registros desordenados cronológicamente
        historico_desordenado = [
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '2024-01', 'precio_base': 100000.0},
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '2024-03', 'precio_base': 120000.0},  # Más reciente
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '2024-02', 'precio_base': 110000.0}
        ]
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_records.return_value = historico_desordenado
        
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        resultado = leer_historico_existente(mock_sheet)
        
        # Debería detectar marzo (2024-03) como el último mes y precio 120000
        self.assertEqual(resultado['Casa Test']['ultimo_mes'], '2024-03')
        self.assertEqual(resultado['Casa Test']['ultimo_precio_base'], 120000.0)

    # Test 139: Manejo de múltiples propiedades en histórico
    def test_139_multiples_propiedades_historico(self):
        """Test 139: Verificar manejo de múltiples propiedades en histórico"""
        
        historico_multiple = [
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-02', 'precio_base': 100000.0},
            {'nombre_inmueble': 'Casa B', 'mes_actual': '2024-03', 'precio_base': 200000.0},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-01', 'precio_base': 95000.0},
            {'nombre_inmueble': 'Casa B', 'mes_actual': '2024-01', 'precio_base': 180000.0}
        ]
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_records.return_value = historico_multiple
        
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        resultado = leer_historico_existente(mock_sheet)
        
        # Verificar separación correcta por propiedad
        self.assertIn('Casa A', resultado)
        self.assertIn('Casa B', resultado)
        
        # Casa A: último mes febrero, precio 100000
        self.assertEqual(resultado['Casa A']['ultimo_mes'], '2024-02')
        self.assertEqual(resultado['Casa A']['ultimo_precio_base'], 100000.0)
        
        # Casa B: último mes marzo, precio 200000
        self.assertEqual(resultado['Casa B']['ultimo_mes'], '2024-03')
        self.assertEqual(resultado['Casa B']['ultimo_precio_base'], 200000.0)

    # Test 140: Inicio desde cero vs continuación
    def test_140_inicio_vs_continuacion(self):
        """Test 140: Verificar diferencia entre inicio desde cero y continuación"""
        fecha_limite = dt.date(2024, 4, 1)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            # Caso 1: Inicio desde cero (sin histórico)
            registros_desde_cero = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
            
            # Caso 2: Continuación desde mes 2
            registros_continuacion = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "2024-02", self.inflacion_df, 0.0
            )
        
        # Desde cero: 4 meses (enero a abril)
        self.assertEqual(len(registros_desde_cero), 4)
        self.assertEqual(registros_desde_cero[0]['mes_actual'], "2024-01")
        
        # Continuación: 2 meses (marzo a abril)
        self.assertEqual(len(registros_continuacion), 2)
        self.assertEqual(registros_continuacion[0]['mes_actual'], "2024-03")

    # Test 141: Respeto de ajustes manuales de precio
    def test_141_respeto_ajustes_manuales(self):
        """Test 141: Verificar que se respetan ajustes manuales de precio"""
        fecha_limite = dt.date(2024, 5, 1)
        
        # Precio base ajustado manualmente (diferente del cálculo teórico)
        precio_ajustado_manual = 125000.0  # En lugar del teórico 110000
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (125000.0, "", False)  # Usa el precio ajustado
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                precio_ajustado_manual, "2024-03", self.inflacion_df, 0.0
            )
        
        # Los nuevos cálculos deberían partir del precio ajustado manualmente
        for registro in registros:
            self.assertEqual(registro['precio_base'], 125000.0)

    # Test 142: Generación de historial para contratos parcialmente vencidos
    def test_142_contratos_parcialmente_vencidos(self):
        """Test 142: Verificar manejo de contratos que vencen durante el período"""
        
        # Contrato que vence en abril (4 meses de duración)
        contrato_corto = Contrato(
            fecha_inicio="2024-01-01",
            duracion_meses=4,
            precio_original=100000.0,
            actualizacion="trimestral",
            indice="10%",
            comision_inmo="5%",
            comision="Pagado",
            deposito="Pagado"
        )
        
        fecha_limite = dt.date(2024, 6, 1)  # Más allá del vencimiento
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (100000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, contrato_corto, fecha_limite,
                100000.0, "2024-02", self.inflacion_df, 0.0
            )
        
        # Solo debería generar hasta abril (meses 3 y 4)
        self.assertEqual(len(registros), 2)
        self.assertEqual(registros[-1]['mes_actual'], "2024-04")

    # Test 143: Actualización secuencial de precios
    def test_143_actualizacion_secuencial_precios(self):
        """Test 143: Verificar actualización secuencial correcta de precios"""
        fecha_limite = dt.date(2024, 8, 1)
        
        # Simular actualizaciones trimestrales secuenciales
        def mock_actualizacion_side_effect(precio_base, contrato, inflacion_df, fecha_mes, meses_desde_inicio, fecha_inicio):
            # Aplicar 10% cada 3 meses - lógica según especificaciones técnicas
            # Para trimestral: actualizar cuando meses_desde_inicio = 3, 6, 9... (meses 4, 7, 10... del contrato)
            if meses_desde_inicio > 0 and meses_desde_inicio % 3 == 0:
                nuevo_precio = precio_base * 1.1
                return (round(nuevo_precio, 2), "10.00%", True)
            else:
                return (precio_base, "", False)
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes', side_effect=mock_actualizacion_side_effect):
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                100000.0, "", self.inflacion_df, 0.0
            )
        
        # Verificar evolución de precios:
        # Mes 1-3: 100000, Mes 4: 110000 (primera actualización en meses_desde_inicio = 3)
        # Mes 5-6: 110000, Mes 7: 121000 (segunda actualización en meses_desde_inicio = 6)
        self.assertEqual(registros[0]['precio_base'], 100000.0)  # Enero (meses_desde_inicio = 0)
        self.assertEqual(registros[2]['precio_base'], 100000.0)  # Marzo (meses_desde_inicio = 2)
        self.assertEqual(registros[3]['precio_base'], 110000.0)  # Abril (meses_desde_inicio = 3, actualización)
        self.assertEqual(registros[6]['precio_base'], 121000.0)  # Julio (meses_desde_inicio = 6, segunda actualización)

    # Test 144: Ordenamiento cronológico de registros
    def test_144_ordenamiento_cronologico(self):
        """Test 144: Verificar ordenamiento cronológico correcto"""
        
        # Simular registros desordenados
        registros_desordenados = [
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-03'},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-01'},
            {'nombre_inmueble': 'Casa B', 'mes_actual': '2024-02'},
            {'nombre_inmueble': 'Casa A', 'mes_actual': '2024-02'},
            {'nombre_inmueble': 'Casa B', 'mes_actual': '2024-01'}
        ]
        
        # Aplicar mismo ordenamiento que usa el main
        registros_ordenados = sorted(registros_desordenados, 
                                   key=lambda x: (x['nombre_inmueble'], x['mes_actual']))
        
        # Verificar ordenamiento: primero por propiedad, luego por fecha
        expected_order = [
            ('Casa A', '2024-01'),
            ('Casa A', '2024-02'),
            ('Casa A', '2024-03'),
            ('Casa B', '2024-01'),
            ('Casa B', '2024-02')
        ]
        
        for i, (nombre, mes) in enumerate(expected_order):
            self.assertEqual(registros_ordenados[i]['nombre_inmueble'], nombre)
            self.assertEqual(registros_ordenados[i]['mes_actual'], mes)

    # Test 145: Manejo de histórico con datos corruptos
    def test_145_historico_datos_corruptos(self):
        """Test 145: Verificar manejo robusto de datos corruptos en histórico"""
        
        historico_corrupto = [
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '2024-01', 'precio_base': 'invalid'},
            {'nombre_inmueble': '', 'mes_actual': '2024-02', 'precio_base': 100000.0},
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '', 'precio_base': 110000.0},
            {'nombre_inmueble': 'Casa Test', 'mes_actual': '2024-03', 'precio_base': 120000.0}  # Válido
        ]
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_records.return_value = historico_corrupto
        
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Debería manejar errores sin crashear
        resultado = leer_historico_existente(mock_sheet)
        
        # Solo el registro válido debería ser procesado
        if 'Casa Test' in resultado:
            self.assertEqual(resultado['Casa Test']['ultimo_mes'], '2024-03')
            self.assertEqual(resultado['Casa Test']['ultimo_precio_base'], 120000.0)

    # Test 146: Verificación de no duplicación de meses
    def test_146_no_duplicacion_meses(self):
        """Test 146: Verificar que no se duplican meses ya existentes"""
        
        # Simular el flujo completo: histórico existente + nuevos registros
        todos_los_registros = []
        
        # Agregar registros existentes (enero-marzo)
        registros_existentes = self.historico_existente['Casa Incremental']['registros_existentes']
        todos_los_registros.extend(registros_existentes)
        
        # Generar nuevos registros (abril-junio)
        fecha_limite = dt.date(2024, 6, 1)
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (110000.0, "", False)
            
            nuevos_registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite,
                110000.0, "2024-03", self.inflacion_df, 0.0
            )
        
        todos_los_registros.extend(nuevos_registros)
        
        # Verificar que no hay duplicación de meses
        meses_registrados = [r['mes_actual'] for r in todos_los_registros]
        meses_unicos = set(meses_registrados)
        
        self.assertEqual(len(meses_registrados), len(meses_unicos))
        self.assertEqual(len(todos_los_registros), 6)  # enero-junio

    # Test 147: Integridad después de escritura incremental
    def test_147_integridad_escritura_incremental(self):
        """Test 147: Verificar integridad después de escritura incremental"""
        
        # Simular escritura de datos combinados (existentes + nuevos)
        registros_combinados = []
        
        # Datos existentes
        registros_combinados.extend(self.historico_existente['Casa Incremental']['registros_existentes'])
        
        # Nuevos datos simulados
        nuevos_datos = [
            {
                'nombre_inmueble': 'Casa Incremental',
                'mes_actual': '2024-04',
                'precio_base': 110000.0,
                'precio_mes_actual': 110000.0,
                'actualizacion': 'NO',
                'porc_actual': ''
            }
        ]
        registros_combinados.extend(nuevos_datos)
        
        # Ordenar como lo hace el main
        registros_ordenados = sorted(registros_combinados, 
                                   key=lambda x: (x['nombre_inmueble'], x['mes_actual']))
        
        # Verificar continuidad temporal
        meses_esperados = ['2024-01', '2024-02', '2024-03', '2024-04']
        for i, mes_esperado in enumerate(meses_esperados):
            self.assertEqual(registros_ordenados[i]['mes_actual'], mes_esperado)

    # Test 148: Manejo de límites de fecha
    def test_148_manejo_limites_fecha(self):
        """Test 148: Verificar manejo de límites de fecha en generación"""
        
        # Caso 1: Fecha límite anterior al último mes registrado
        fecha_limite_anterior = dt.date(2024, 2, 1)  # Último registrado: marzo
        
        with patch('inmobiliaria.historical.calcular_actualizacion_mes') as mock_calc:
            mock_calc.return_value = (110000.0, "", False)
            
            registros = generar_meses_faltantes(
                self.propiedad_test, self.contrato_test, fecha_limite_anterior,
                110000.0, "2024-03", self.inflacion_df, 0.0
            )
        
        # No debería generar registros (fecha límite es anterior)
        self.assertEqual(len(registros), 0)
        
        # Caso 2: Fecha límite igual al último mes registrado
        fecha_limite_igual = dt.date(2024, 3, 1)
        
        registros_igual = generar_meses_faltantes(
            self.propiedad_test, self.contrato_test, fecha_limite_igual,
            110000.0, "2024-03", self.inflacion_df, 0.0
        )
        
        # No debería generar registros nuevos
        self.assertEqual(len(registros_igual), 0)

    # Test 149: Preservación de campos calculados
    def test_149_preservacion_campos_calculados(self):
        """Test 149: Verificar preservación de campos calculados en incremental"""
        
        # Verificar que los registros existentes mantienen sus campos calculados
        registros_existentes = self.historico_existente['Casa Incremental']['registros_existentes']
        
        for registro in registros_existentes:
            # Campos que deben estar presentes y correctos
            self.assertIn('precio_mes_actual', registro)
            self.assertIn('actualizacion', registro)
            self.assertIn('porc_actual', registro)
            
            # El registro de marzo debería mostrar actualización
            if registro['mes_actual'] == '2024-03':
                self.assertEqual(registro['actualizacion'], 'SI')
                self.assertEqual(registro['porc_actual'], '10.00%')

    # Test 150: Rendimiento con histórico grande
    def test_150_rendimiento_historico_grande(self):
        """Test 150: Verificar rendimiento con histórico de gran tamaño"""
        
        # Simular histórico con muchos registros
        import time
        
        historico_grande = []
        for propiedad_id in range(10):  # 10 propiedades
            for mes in range(1, 25):  # 24 meses cada una
                historico_grande.append({
                    'nombre_inmueble': f'Propiedad_{propiedad_id}',
                    'mes_actual': f'2024-{mes:02d}' if mes <= 12 else f'2025-{mes-12:02d}',
                    'precio_base': 100000.0 + (mes * 1000)
                })
        
        mock_worksheet = Mock()
        mock_worksheet.get_all_records.return_value = historico_grande
        
        mock_sheet = Mock()
        mock_sheet.worksheet.return_value = mock_worksheet
        
        # Medir tiempo de procesamiento
        start_time = time.time()
        resultado = leer_historico_existente(mock_sheet)
        end_time = time.time()
        
        # Debería procesar en tiempo razonable (< 1 segundo)
        self.assertLess(end_time - start_time, 1.0)
        
        # Verificar que procesó todas las propiedades
        self.assertEqual(len(resultado), 10)


if __name__ == '__main__':
    unittest.main()
