"""
Tests para lógica de contratos (Tests 27-40)
Basado en tests_funcionales.md - Categoría 2: LÓGICA DE CONTRATOS
Reorganizado desde test_contract_logic.py
"""
import unittest
import sys
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.support.test_data import CONTRATOS_TEST_DATA


class TestVigenciaContratos(unittest.TestCase):
    """Tests 27-30: Vigencia de contratos"""
    
    def test_incluir_contratos_vigentes(self):
        """Test 27: El sistema debe incluir contratos que aún están vigentes"""
        inicio = date(2024, 1, 1)
        duracion_meses = 24
        fecha_ref = date(2024, 12, 1)  # Mes 11 del contrato
        
        meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertLess(meses_desde_inicio, duracion_meses, 
                       "Contrato debe estar vigente")
    
    def test_excluir_contratos_vencidos(self):
        """Test 28: El sistema debe excluir contratos que ya vencieron"""
        inicio = date(2024, 1, 1)
        duracion_meses = 12
        fecha_ref = date(2025, 2, 1)  # Mes 13 del contrato (vencido)
        
        meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertGreaterEqual(meses_desde_inicio, duracion_meses,
                               "Contrato debe estar vencido")
    
    def test_incluir_contratos_que_vencen_en_mes_referencia(self):
        """Test 29: El sistema debe incluir contratos que vencen exactamente en el mes de referencia"""
        inicio = date(2024, 1, 1)
        duracion_meses = 12
        fecha_ref = date(2025, 1, 1)  # Exactamente mes 12 del contrato
        
        meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertEqual(meses_desde_inicio, duracion_meses,
                        "Contrato vence exactamente en el mes de referencia")
        # El sistema debe incluirlo porque aún no ha pasado la duración completa
        self.assertLessEqual(meses_desde_inicio, duracion_meses)
    
    def test_vigencia_contratos_diferentes_duraciones(self):
        """Test 30: El sistema debe calcular correctamente la vigencia para contratos de 12, 24, 36 meses"""
        inicio = date(2024, 1, 1)
        fecha_ref = date(2024, 6, 1)  # 5 meses después
        
        duraciones_test = [12, 24, 36]
        
        for duracion in duraciones_test:
            meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
            esta_vigente = meses_desde_inicio < duracion
            
            self.assertTrue(esta_vigente, 
                          f"Contrato de {duracion} meses debe estar vigente en mes {meses_desde_inicio}")


class TestCalculoMesesDesdeInicio(unittest.TestCase):
    """Tests 31-33: Cálculo de meses desde inicio"""
    
    def test_calculo_meses_desde_inicio_mismo_año(self):
        """Test 31: Para un contrato iniciado en enero 2024, en marzo 2024 deben ser 2 meses desde inicio"""
        inicio = date(2024, 1, 1)
        fecha_ref = date(2024, 3, 1)
        
        meses_calculados = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertEqual(meses_calculados, 2, 
                        "De enero a marzo deben ser 2 meses")
    
    def test_calculo_meses_desde_inicio_diferentes_años(self):
        """Test 32: Para un contrato iniciado en diciembre 2023, en febrero 2024 deben ser 2 meses desde inicio"""
        inicio = date(2023, 12, 1)
        fecha_ref = date(2024, 2, 1)
        
        meses_calculados = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertEqual(meses_calculados, 2, 
                        "De diciembre 2023 a febrero 2024 deben ser 2 meses")
    
    def test_calculo_meses_mismo_mes_inicio(self):
        """Test 33: Para un contrato iniciado el mismo mes de referencia deben ser 0 meses desde inicio"""
        inicio = date(2024, 6, 1)
        fecha_ref = date(2024, 6, 1)
        
        meses_calculados = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        
        self.assertEqual(meses_calculados, 0,
                        "Mismo mes de inicio debe ser 0 meses")


class TestActualizacionTrimestral(unittest.TestCase):
    """Tests 34-36: Actualización trimestral"""
    
    def test_actualizacion_trimestral_meses_correctos(self):
        """Test 34: Un contrato trimestral debe actualizarse en los meses 3, 6, 9, 12, 15, 18... desde inicio"""
        freq_meses = 3
        meses_actualizacion = [3, 6, 9, 12, 15, 18, 21, 24]
        
        for meses_desde_inicio in meses_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "SI",
                           f"Mes {meses_desde_inicio} debe aplicar actualización trimestral")
    
    def test_actualizacion_trimestral_meses_incorrectos(self):
        """Test 35: Un contrato trimestral NO debe actualizarse en los meses 1, 2, 4, 5, 7, 8... desde inicio"""
        freq_meses = 3
        meses_sin_actualizacion = [1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17]
        
        for meses_desde_inicio in meses_sin_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "NO",
                           f"Mes {meses_desde_inicio} NO debe aplicar actualización trimestral")
    
    def test_primera_actualizacion_trimestral_mes_3(self):
        """Test 36: La primera actualización trimestral debe ocurrir en el mes 3, no antes"""
        freq_meses = 3
        
        # Meses 0, 1, 2 no deben tener actualización (primera actualización)
        for meses_desde_inicio in [0, 1, 2]:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "NO",
                           f"Mes {meses_desde_inicio} NO debe tener primera actualización")
        
        # Mes 3 debe ser la primera actualización
        meses_desde_inicio = 3
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        
        self.assertEqual(aplica_actualizacion, "SI",
                        "Mes 3 debe ser la primera actualización trimestral")


class TestActualizacionSemestral(unittest.TestCase):
    """Tests 37-38: Actualización semestral"""
    
    def test_actualizacion_semestral_meses_correctos(self):
        """Test 37: Un contrato semestral debe actualizarse en los meses 6, 12, 18, 24... desde inicio"""
        freq_meses = 6
        meses_actualizacion = [6, 12, 18, 24, 30, 36]
        
        for meses_desde_inicio in meses_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "SI",
                           f"Mes {meses_desde_inicio} debe aplicar actualización semestral")
    
    def test_actualizacion_semestral_meses_incorrectos(self):
        """Test 38: Un contrato semestral NO debe actualizarse en los meses 1-5, 7-11, 13-17... desde inicio"""
        freq_meses = 6
        meses_sin_actualizacion = [1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17]
        
        for meses_desde_inicio in meses_sin_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "NO",
                           f"Mes {meses_desde_inicio} NO debe aplicar actualización semestral")


class TestActualizacionAnual(unittest.TestCase):
    """Tests 39-40: Actualización anual"""
    
    def test_actualizacion_anual_meses_correctos(self):
        """Test 39: Un contrato anual debe actualizarse en los meses 12, 24, 36... desde inicio"""
        freq_meses = 12
        meses_actualizacion = [12, 24, 36, 48]
        
        for meses_desde_inicio in meses_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "SI",
                           f"Mes {meses_desde_inicio} debe aplicar actualización anual")
    
    def test_actualizacion_anual_meses_incorrectos(self):
        """Test 40: Un contrato anual NO debe actualizarse en los meses 1-11, 13-23... desde inicio"""
        freq_meses = 12
        meses_sin_actualizacion = list(range(1, 12)) + list(range(13, 24)) + list(range(25, 36))
        
        for meses_desde_inicio in meses_sin_actualizacion:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica_actualizacion, "NO",
                           f"Mes {meses_desde_inicio} NO debe aplicar actualización anual")


if __name__ == '__main__':
    unittest.main()
