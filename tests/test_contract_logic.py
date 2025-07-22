"""
Tests para la lógica de actualización de contratos y cálculo de ciclos
"""
import unittest
import sys
import os
from datetime import date
from dateutil.relativedelta import relativedelta
import pandas as pd

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_data import CONTRATOS_TEST_DATA


class TestContractLogic(unittest.TestCase):
    """Tests para lógica de contratos y actualizaciones"""
    
    def test_calculo_meses_desde_inicio(self):
        """Test cálculo correcto de meses desde inicio del contrato"""
        inicio = date(2024, 1, 1)
        
        # Casos de prueba
        test_cases = [
            (date(2024, 1, 1), 0),   # Mismo mes de inicio
            (date(2024, 2, 1), 1),   # Un mes después
            (date(2024, 4, 1), 3),   # Tres meses después
            (date(2024, 12, 1), 11), # Once meses después
            (date(2025, 1, 1), 12),  # Un año después
        ]
        
        for fecha_actual, meses_esperados in test_cases:
            y, m = fecha_actual.year, fecha_actual.month
            inicio_y, inicio_m = inicio.year, inicio.month
            meses_calculados = (y - inicio_y) * 12 + (m - inicio_m)
            
            self.assertEqual(meses_calculados, meses_esperados,
                           f"Para fecha {fecha_actual} con inicio {inicio}, "
                           f"esperado: {meses_esperados}, calculado: {meses_calculados}")
    
    def test_ciclos_cumplidos_trimestral(self):
        """Test cálculo de ciclos cumplidos para contrato trimestral"""
        freq_meses = 3  # Trimestral
        
        test_cases = [
            (0, 0),   # Mes 0: 0 ciclos
            (1, 0),   # Mes 1: 0 ciclos
            (2, 0),   # Mes 2: 0 ciclos
            (3, 1),   # Mes 3: 1 ciclo completo
            (5, 1),   # Mes 5: 1 ciclo completo
            (6, 2),   # Mes 6: 2 ciclos completos
            (11, 3),  # Mes 11: 3 ciclos completos
            (12, 4),  # Mes 12: 4 ciclos completos
        ]
        
        for meses_desde_inicio, ciclos_esperados in test_cases:
            ciclos_calculados = meses_desde_inicio // freq_meses
            
            self.assertEqual(ciclos_calculados, ciclos_esperados,
                           f"Meses {meses_desde_inicio}: esperado {ciclos_esperados} ciclos, "
                           f"calculado {ciclos_calculados}")
    
    def test_ciclos_cumplidos_semestral(self):
        """Test cálculo de ciclos cumplidos para contrato semestral"""
        freq_meses = 6  # Semestral
        
        test_cases = [
            (0, 0),   # Mes 0: 0 ciclos
            (5, 0),   # Mes 5: 0 ciclos
            (6, 1),   # Mes 6: 1 ciclo completo
            (11, 1),  # Mes 11: 1 ciclo completo
            (12, 2),  # Mes 12: 2 ciclos completos
            (23, 3),  # Mes 23: 3 ciclos completos
            (24, 4),  # Mes 24: 4 ciclos completos
        ]
        
        for meses_desde_inicio, ciclos_esperados in test_cases:
            ciclos_calculados = meses_desde_inicio // freq_meses
            
            self.assertEqual(ciclos_calculados, ciclos_esperados,
                           f"Meses {meses_desde_inicio}: esperado {ciclos_esperados} ciclos, "
                           f"calculado {ciclos_calculados}")
    
    def test_ciclos_cumplidos_cuatrimestral(self):
        """Test cálculo de ciclos cumplidos para contrato cuatrimestral"""
        freq_meses = 4  # Cuatrimestral
        
        test_cases = [
            (0, 0),   # Mes 0: 0 ciclos
            (3, 0),   # Mes 3: 0 ciclos
            (4, 1),   # Mes 4: 1 ciclo completo
            (7, 1),   # Mes 7: 1 ciclo completo
            (8, 2),   # Mes 8: 2 ciclos completos
            (12, 3),  # Mes 12: 3 ciclos completos
            (16, 4),  # Mes 16: 4 ciclos completos
            (20, 5),  # Mes 20: 5 ciclos completos
            (24, 6),  # Mes 24: 6 ciclos completos
        ]
        
        for meses_desde_inicio, ciclos_esperados in test_cases:
            ciclos_calculados = meses_desde_inicio // freq_meses
            
            self.assertEqual(ciclos_calculados, ciclos_esperados,
                           f"Meses {meses_desde_inicio}: esperado {ciclos_esperados} ciclos, "
                           f"calculado {ciclos_calculados}")
    
    def test_aplicacion_actualizacion_trimestral(self):
        """Test lógica de aplicación de actualización trimestral"""
        freq_meses = 3
        
        # Casos donde DEBE aplicar actualización (resto = 0 y ciclos > 0)
        casos_si = [3, 6, 9, 12, 15, 18, 21, 24]
        
        for meses in casos_si:
            ciclos_cumplidos = meses // freq_meses
            resto = meses % freq_meses
            aplica = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica, "SI",
                           f"Mes {meses} trimestral debe aplicar actualización")
        
        # Casos donde NO DEBE aplicar actualización
        casos_no = [0, 1, 2, 4, 5, 7, 8, 10, 11, 13, 14]
        
        for meses in casos_no:
            ciclos_cumplidos = meses // freq_meses
            resto = meses % freq_meses
            aplica = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica, "NO",
                           f"Mes {meses} trimestral NO debe aplicar actualización")
    
    def test_aplicacion_actualizacion_cuatrimestral(self):
        """Test lógica de aplicación de actualización cuatrimestral"""
        freq_meses = 4
        
        # Casos donde DEBE aplicar actualización (resto = 0 y ciclos > 0)
        casos_si = [4, 8, 12, 16, 20, 24]
        
        for meses in casos_si:
            ciclos_cumplidos = meses // freq_meses
            resto = meses % freq_meses
            aplica = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica, "SI",
                           f"Mes {meses} cuatrimestral debe aplicar actualización")
        
        # Casos donde NO DEBE aplicar actualización
        casos_no = [0, 1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19, 21, 22, 23]
        
        for meses in casos_no:
            ciclos_cumplidos = meses // freq_meses
            resto = meses % freq_meses
            aplica = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(aplica, "NO",
                           f"Mes {meses} cuatrimestral NO debe aplicar actualización")
    
    def test_meses_proxima_actualizacion_trimestral(self):
        """Test cálculo de meses hasta próxima actualización trimestral"""
        freq_meses = 3
        
        test_cases = [
            (0, 3),   # Mes 0: faltan 3 meses para primera actualización
            (1, 2),   # Mes 1: faltan 2 meses
            (2, 1),   # Mes 2: falta 1 mes
            (3, 3),   # Mes 3 (actualización): próxima en 3 meses
            (4, 2),   # Mes 4: faltan 2 meses
            (5, 1),   # Mes 5: falta 1 mes
            (6, 3),   # Mes 6 (actualización): próxima en 3 meses
        ]
        
        for meses_desde_inicio, meses_esperados in test_cases:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            
            if resto == 0 and ciclos_cumplidos > 0:
                # Estamos en mes de actualización
                meses_prox_actualizacion = freq_meses
            else:
                # Faltan meses para próxima actualización
                meses_prox_actualizacion = freq_meses - resto
            
            self.assertEqual(meses_prox_actualizacion, meses_esperados,
                           f"Mes {meses_desde_inicio}: esperado {meses_esperados} meses "
                           f"hasta próxima actualización, calculado {meses_prox_actualizacion}")
    
    def test_meses_proxima_actualizacion_cuatrimestral(self):
        """Test cálculo de meses hasta próxima actualización cuatrimestral"""
        freq_meses = 4
        
        test_cases = [
            (0, 4),   # Mes 0: faltan 4 meses para primera actualización
            (1, 3),   # Mes 1: faltan 3 meses
            (2, 2),   # Mes 2: faltan 2 meses
            (3, 1),   # Mes 3: falta 1 mes
            (4, 4),   # Mes 4 (actualización): próxima en 4 meses
            (5, 3),   # Mes 5: faltan 3 meses
            (6, 2),   # Mes 6: faltan 2 meses
            (7, 1),   # Mes 7: falta 1 mes
            (8, 4),   # Mes 8 (actualización): próxima en 4 meses
        ]
        
        for meses_desde_inicio, meses_esperados in test_cases:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            
            if resto == 0 and ciclos_cumplidos > 0:
                # Estamos en mes de actualización
                meses_prox_actualizacion = freq_meses
            else:
                # Faltan meses para próxima actualización
                meses_prox_actualizacion = freq_meses - resto
            
            self.assertEqual(meses_prox_actualizacion, meses_esperados,
                           f"Mes {meses_desde_inicio}: esperado {meses_esperados} meses "
                           f"hasta próxima actualización, calculado {meses_prox_actualizacion}")
    
    def test_meses_proxima_renovacion(self):
        """Test cálculo de meses hasta renovación del contrato"""
        duracion_meses = 24  # Contrato de 24 meses
        
        test_cases = [
            (0, 24),   # Mes 0: faltan 24 meses
            (1, 23),   # Mes 1: faltan 23 meses
            (12, 12),  # Mes 12: faltan 12 meses
            (23, 1),   # Mes 23: falta 1 mes
            (24, 0),   # Mes 24: contrato finalizado
        ]
        
        for meses_desde_inicio, meses_esperados in test_cases:
            meses_prox_renovacion = duracion_meses - meses_desde_inicio
            
            self.assertEqual(meses_prox_renovacion, meses_esperados,
                           f"Mes {meses_desde_inicio} de contrato de {duracion_meses} meses: "
                           f"esperado {meses_esperados} meses hasta renovación")
    
    def test_contrato_vigente(self):
        """Test verificación de vigencia del contrato"""
        inicio = date(2024, 1, 1)
        duracion_meses = 24
        
        # Casos donde el contrato ESTÁ vigente
        fechas_vigentes = [
            date(2024, 1, 1),   # Mes de inicio
            date(2024, 6, 1),   # Medio contrato
            date(2025, 12, 1),  # Último mes
        ]
        
        for fecha_ref in fechas_vigentes:
            meses_transcurridos = ((fecha_ref - inicio).days // 30)
            esta_vigente = meses_transcurridos < duracion_meses
            
            self.assertTrue(esta_vigente,
                          f"Contrato debe estar vigente en {fecha_ref}")
        
        # Casos donde el contrato NO ESTÁ vigente
        fechas_vencidas = [
            date(2026, 1, 1),   # Mes siguiente al vencimiento
            date(2026, 6, 1),   # Varios meses después
        ]
        
        for fecha_ref in fechas_vencidas:
            meses_transcurridos = ((fecha_ref - inicio).days // 30)
            esta_vigente = meses_transcurridos < duracion_meses
            
            self.assertFalse(esta_vigente,
                           f"Contrato NO debe estar vigente en {fecha_ref}")


class TestContractValidation(unittest.TestCase):
    """Tests para validación de campos de contratos"""
    
    def test_campos_requeridos_completos(self):
        """Test contrato con todos los campos requeridos"""
        contrato = CONTRATOS_TEST_DATA[0]  # Casa Palermo - completo
        campos_requeridos = [
            "precio_original", "fecha_inicio_contrato", "duracion_meses",
            "actualizacion", "indice", "comision_inmo"
        ]
        
        fila = pd.Series(contrato)
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if campo not in fila or pd.isna(fila[campo]) or str(fila[campo]).strip() == "":
                campos_faltantes.append(campo)
        
        self.assertEqual(len(campos_faltantes), 0,
                        f"No deben faltar campos. Faltantes: {campos_faltantes}")
    
    def test_campos_requeridos_faltantes(self):
        """Test contrato con campos faltantes"""
        contrato = CONTRATOS_TEST_DATA[4]  # Casa Incompleta - con campos faltantes
        campos_requeridos = [
            "precio_original", "fecha_inicio_contrato", "duracion_meses",
            "actualizacion", "indice", "comision_inmo"
        ]
        
        fila = pd.Series(contrato)
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if campo not in fila or pd.isna(fila[campo]) or str(fila[campo]).strip() == "":
                campos_faltantes.append(campo)
        
        # Deben faltar: precio_original, indice, fecha_inicio_contrato
        self.assertGreater(len(campos_faltantes), 0,
                         "Deben detectarse campos faltantes")
        self.assertIn("precio_original", campos_faltantes)
        self.assertIn("indice", campos_faltantes)
        self.assertIn("fecha_inicio_contrato", campos_faltantes)
    
    def test_valores_frecuencia_validos(self):
        """Test valores válidos para frecuencia de actualización"""
        valores_validos = ["trimestral", "semestral", "anual"]
        diccionario_freq = {"trimestral": 3, "semestral": 6, "anual": 12}
        
        for valor in valores_validos:
            try:
                freq_meses = diccionario_freq[valor]
                self.assertIn(freq_meses, [3, 6, 12],
                            f"Frecuencia {valor} debe mapear a 3, 6 o 12")
            except KeyError:
                self.fail(f"Valor {valor} debe ser válido")
    
    def test_valores_frecuencia_invalidos(self):
        """Test valores inválidos para frecuencia de actualización"""
        valores_invalidos = ["mensual", "bimestral", "quincenal", ""]
        diccionario_freq = {"trimestral": 3, "semestral": 6, "anual": 12}
        
        for valor in valores_invalidos:
            with self.assertRaises(KeyError,
                                 msg=f"Valor inválido {valor} debe generar KeyError"):
                freq_meses = diccionario_freq[valor]


if __name__ == '__main__':
    unittest.main()
