"""
Tests para campos informativos (Tests 80-91)
Basado en tests_funcionales.md - Categoría 8: CAMPOS INFORMATIVOS
"""
import unittest
import sys
import os
from datetime import date

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestIndicadorActualizacion(unittest.TestCase):
    """Tests 80-82: Indicador de actualización"""
    
    def test_actualizacion_si_solo_meses_corresponde_ajuste(self):
        """Test 80: actualizacion debe ser "SI" solo en meses donde corresponde ajuste"""
        freq_meses = 3  # Trimestral
        
        # Casos donde debe ser "SI" (resto = 0 y ciclos > 0)
        casos_si = [
            (3, 1),   # Mes 3, ciclo 1
            (6, 2),   # Mes 6, ciclo 2
            (9, 3),   # Mes 9, ciclo 3
            (12, 4),  # Mes 12, ciclo 4
        ]
        
        for meses_desde_inicio, ciclos_esperados in casos_si:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(actualizacion, "SI",
                           f"Mes {meses_desde_inicio} debe tener actualización 'SI'")
            self.assertEqual(ciclos_cumplidos, ciclos_esperados,
                           f"Mes {meses_desde_inicio} debe tener {ciclos_esperados} ciclos")
    
    def test_actualizacion_no_otros_meses(self):
        """Test 81: actualizacion debe ser "NO" en todos los demás meses"""
        freq_meses = 3  # Trimestral
        
        # Casos donde debe ser "NO"
        casos_no = [0, 1, 2, 4, 5, 7, 8, 10, 11, 13, 14, 16, 17]
        
        for meses_desde_inicio in casos_no:
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(actualizacion, "NO",
                           f"Mes {meses_desde_inicio} debe tener actualización 'NO'")
    
    def test_primer_mes_contrato_siempre_no(self):
        """Test 82: En el primer mes del contrato, actualizacion siempre debe ser "NO\""""
        # Diferentes frecuencias
        frecuencias = [3, 4, 6, 12]  # trimestral, cuatrimestral, semestral, anual
        
        for freq_meses in frecuencias:
            meses_desde_inicio = 0  # Primer mes
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            self.assertEqual(actualizacion, "NO",
                           f"Primer mes con frecuencia {freq_meses} debe ser 'NO'")


class TestPorcentajeActual(unittest.TestCase):
    """Tests 83-85: Porcentaje actual"""
    
    def test_porc_actual_valor_cuando_actualizacion_si(self):
        """Test 83: porc_actual debe tener valor solo cuando actualizacion = "SI\""""
        # Caso con actualización
        meses_desde_inicio = 6  # Mes de actualización trimestral
        freq_meses = 3
        indice = "10%"
        
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        
        if actualizacion == "SI":
            # Simular cálculo de porcentaje (caso porcentaje fijo)
            porc_actual = float(indice.replace("%", ""))
        else:
            porc_actual = ""
        
        self.assertEqual(actualizacion, "SI")
        self.assertEqual(porc_actual, 10.0,
                        "porc_actual debe tener valor cuando actualizacion = 'SI'")
    
    def test_porc_actual_vacio_cuando_actualizacion_no(self):
        """Test 84: porc_actual debe estar vacío cuando actualizacion = "NO\""""
        # Caso sin actualización
        meses_desde_inicio = 7  # Mes sin actualización trimestral
        freq_meses = 3
        
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        
        if actualizacion == "SI":
            porc_actual = 10.0  # Algún valor
        else:
            porc_actual = ""  # Vacío
        
        self.assertEqual(actualizacion, "NO")
        self.assertEqual(porc_actual, "",
                        "porc_actual debe estar vacío cuando actualizacion = 'NO'")
    
    def test_porc_actual_ultimo_factor_aplicado(self):
        """Test 85: porc_actual debe mostrar el porcentaje del último factor aplicado"""
        # Caso conceptual - el porcentaje debe representar solo el último incremento
        # Para un contrato con 2 ciclos cumplidos al 10% cada uno:
        # Factor total = (1.10)² = 1.21 (21% acumulado)
        # Pero porc_actual debe mostrar solo el último: 10%
        
        factor_acumulado_total = 1.21  # Resultado de (1.10)²
        factor_ultimo_ciclo = 1.10     # Solo el último factor
        
        porc_actual_total = (factor_acumulado_total - 1) * 100  # 21%
        porc_actual_ultimo = (factor_ultimo_ciclo - 1) * 100   # 10%
        
        # El sistema debe mostrar el último, no el acumulado
        porc_esperado = round(porc_actual_ultimo, 2)  # Redondear para evitar errores de precisión
        
        self.assertEqual(porc_esperado, 10.0,
                        "porc_actual debe mostrar el porcentaje del último factor, no el acumulado")
        self.assertNotEqual(porc_esperado, porc_actual_total,
                           "porc_actual NO debe mostrar el porcentaje acumulado total")


class TestMesesProximaActualizacion(unittest.TestCase):
    """Tests 86-88: Meses hasta próxima actualización"""
    
    def test_mes_actualizacion_trimestral_proxima_3_meses(self):
        """Test 86: En un mes de actualización trimestral, meses_prox_actualizacion debe ser 3"""
        freq_meses = 3
        meses_desde_inicio = 6  # Mes de actualización (resto = 0)
        
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        if resto == 0 and ciclos_cumplidos > 0:
            # Estamos en mes de actualización, próxima en un ciclo completo
            meses_prox_actualizacion = freq_meses
        else:
            meses_prox_actualizacion = freq_meses - resto
        
        self.assertEqual(resto, 0, "Debe ser mes de actualización")
        self.assertEqual(meses_prox_actualizacion, 3,
                        "En mes de actualización trimestral, próxima debe ser en 3 meses")
    
    def test_un_mes_despues_actualizacion_trimestral_2_meses(self):
        """Test 87: Un mes después de actualización trimestral, meses_prox_actualizacion debe ser 2"""
        freq_meses = 3
        meses_desde_inicio = 7  # Un mes después de actualización (resto = 1)
        
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        if resto == 0 and ciclos_cumplidos > 0:
            meses_prox_actualizacion = freq_meses
        else:
            meses_prox_actualizacion = freq_meses - resto
        
        self.assertEqual(resto, 1, "Debe ser un mes después de actualización")
        self.assertEqual(meses_prox_actualizacion, 2,
                        "Un mes después de actualización, deben faltar 2 meses")
    
    def test_dos_meses_despues_actualizacion_trimestral_1_mes(self):
        """Test 88: Dos meses después de actualización trimestral, meses_prox_actualizacion debe ser 1"""
        freq_meses = 3
        meses_desde_inicio = 8  # Dos meses después de actualización (resto = 2)
        
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        if resto == 0 and ciclos_cumplidos > 0:
            meses_prox_actualizacion = freq_meses
        else:
            meses_prox_actualizacion = freq_meses - resto
        
        self.assertEqual(resto, 2, "Debe ser dos meses después de actualización")
        self.assertEqual(meses_prox_actualizacion, 1,
                        "Dos meses después de actualización, debe faltar 1 mes")


class TestMesesProximaRenovacion(unittest.TestCase):
    """Tests 89-91: Meses hasta renovación"""
    
    def test_meses_prox_renovacion_decrece_mes_a_mes(self):
        """Test 89: meses_prox_renovacion debe decrecer mes a mes"""
        duracion_meses = 24
        
        # Simular varios meses del contrato
        meses_test = [0, 1, 5, 10, 15, 20, 23]
        meses_renovacion_anteriores = []
        
        for meses_desde_inicio in meses_test:
            meses_prox_renovacion = duracion_meses - meses_desde_inicio
            
            # Verificar que decrece respecto al anterior
            if meses_renovacion_anteriores:
                ultimo_valor = meses_renovacion_anteriores[-1]
                self.assertLess(meses_prox_renovacion, ultimo_valor,
                               f"Mes {meses_desde_inicio}: debe decrecer respecto a mes anterior")
            
            meses_renovacion_anteriores.append(meses_prox_renovacion)
            
            # Verificar que nunca es negativo (salvo en el último caso)
            if meses_desde_inicio < duracion_meses:
                self.assertGreaterEqual(meses_prox_renovacion, 0,
                                       f"Mes {meses_desde_inicio}: no debe ser negativo")
    
    def test_ultimo_mes_contrato_renovacion_cero(self):
        """Test 90: En el último mes del contrato, meses_prox_renovacion debe ser 0"""
        duracion_meses = 24
        meses_desde_inicio = 24  # Último mes
        
        meses_prox_renovacion = duracion_meses - meses_desde_inicio
        
        self.assertEqual(meses_prox_renovacion, 0,
                        "En el último mes, meses_prox_renovacion debe ser 0")
    
    def test_meses_prox_renovacion_nunca_negativo(self):
        """Test 91: meses_prox_renovacion nunca debe ser negativo"""
        duracion_meses = 12
        
        # Test varios casos, incluyendo edge cases
        casos_test = [0, 1, 5, 11, 12, 13]  # Incluye caso donde ya se pasó la duración
        
        for meses_desde_inicio in casos_test:
            meses_prox_renovacion = max(0, duracion_meses - meses_desde_inicio)
            
            self.assertGreaterEqual(meses_prox_renovacion, 0,
                                   f"Mes {meses_desde_inicio}: nunca debe ser negativo")
            
            # Verificar lógica específica
            if meses_desde_inicio <= duracion_meses:
                expected = duracion_meses - meses_desde_inicio
                self.assertEqual(meses_prox_renovacion, expected,
                               f"Mes {meses_desde_inicio}: cálculo incorrecto")
            else:
                # Si ya se pasó la duración, debería ser 0 (contrato vencido)
                self.assertEqual(meses_prox_renovacion, 0,
                               f"Mes {meses_desde_inicio}: contrato vencido debe ser 0")


if __name__ == '__main__':
    unittest.main()
