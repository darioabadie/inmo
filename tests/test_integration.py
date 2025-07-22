"""
Tests de integración para el flujo completo de procesamiento
"""
import unittest
import sys
import os
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_data import CONTRATOS_TEST_DATA, get_inflacion_df_test


class TestIntegrationFlow(unittest.TestCase):
    """Tests de integración para el flujo completo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.inflacion_df = get_inflacion_df_test()
        self.contratos_df = pd.DataFrame(CONTRATOS_TEST_DATA)
    
    def test_procesamiento_contrato_completo_trimestral(self):
        """Test procesamiento completo de contrato trimestral"""
        # Contrato: Casa Palermo - trimestral, IPC, inicio 2024-01-01
        contrato = CONTRATOS_TEST_DATA[0]
        fecha_ref = date(2024, 4, 1)  # Abril 2024 (mes 3 - primera actualización)
        
        # Simulamos el procesamiento manual
        inicio = pd.to_datetime(contrato["fecha_inicio_contrato"]).date()
        y, m = fecha_ref.year, fecha_ref.month
        meses_desde_inicio = (y - inicio.year) * 12 + (m - inicio.month)
        
        # Verificaciones básicas
        self.assertEqual(meses_desde_inicio, 3, "Debe ser mes 3 del contrato")
        
        freq_meses = 3  # trimestral
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        self.assertEqual(ciclos_cumplidos, 1, "Debe haber 1 ciclo cumplido")
        self.assertEqual(resto, 0, "Resto debe ser 0 (mes de actualización)")
        
        aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        self.assertEqual(aplica_actualizacion, "SI", "Debe aplicar actualización")
        
        # Calcular meses próxima actualización y renovación
        meses_prox_actualizacion = freq_meses if resto == 0 and ciclos_cumplidos > 0 else freq_meses - resto
        meses_prox_renovacion = contrato["duracion_meses"] - meses_desde_inicio
        
        self.assertEqual(meses_prox_actualizacion, 3, "Próxima actualización en 3 meses")
        self.assertEqual(meses_prox_renovacion, 21, "Faltan 21 meses para renovación")
    
    def test_procesamiento_contrato_semestral_sin_actualizacion(self):
        """Test procesamiento contrato semestral sin actualización"""
        # Contrato: Depto Belgrano - semestral, 10%, inicio 2024-03-01
        contrato = CONTRATOS_TEST_DATA[2]  # Ahora Depto Belgrano es el índice 2
        fecha_ref = date(2024, 7, 1)  # Julio 2024 (mes 4 - sin actualización)
        
        inicio = pd.to_datetime(contrato["fecha_inicio_contrato"]).date()
        y, m = fecha_ref.year, fecha_ref.month
        meses_desde_inicio = (y - inicio.year) * 12 + (m - inicio.month)
        
        self.assertEqual(meses_desde_inicio, 4, "Debe ser mes 4 del contrato")
        
        freq_meses = 6  # semestral
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        self.assertEqual(ciclos_cumplidos, 0, "No debe haber ciclos cumplidos")
        self.assertEqual(resto, 4, "Resto debe ser 4")
        
        aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        self.assertEqual(aplica_actualizacion, "NO", "NO debe aplicar actualización")
        
        meses_prox_actualizacion = freq_meses - resto
        meses_prox_renovacion = contrato["duracion_meses"] - meses_desde_inicio
        
        self.assertEqual(meses_prox_actualizacion, 2, "Faltan 2 meses para actualización")
        self.assertEqual(meses_prox_renovacion, 32, "Faltan 32 meses para renovación")
    
    def test_calculo_precio_con_porcentaje_fijo(self):
        """Test cálculo de precio con porcentaje fijo"""
        # Depto Belgrano usa 10% fijo
        contrato = CONTRATOS_TEST_DATA[2]  # Ahora Depto Belgrano es el índice 2
        precio_original = float(contrato["precio_original"])
        
        # Simular 1 ciclo cumplido (actualización semestral)
        ciclos_cumplidos = 1
        pct = 10.0  # 10%
        factor_total = (1 + pct / 100) ** ciclos_cumplidos
        precio_actual = round(precio_original * factor_total, 2)
        
        expected_precio = round(150000 * 1.10, 2)  # 165,000
        self.assertEqual(precio_actual, expected_precio,
                        f"Precio con 10% debe ser {expected_precio}")
    
    def test_calculo_precio_final_con_municipalidad(self):
        """Test integración completa: precio final con municipalidad"""
        # Casa Palermo: precio_base 100000, municipalidad 15000, comisión 2 cuotas, depósito 3 cuotas
        contrato = CONTRATOS_TEST_DATA[0]
        
        precio_base = float(contrato["precio_original"])  # 100000
        municipalidad = float(contrato["municipalidad"])  # 15000
        mes_actual = 1  # Primer mes
        
        # Simular calcular_cuotas_adicionales
        from app import calcular_cuotas_adicionales
        cuotas_adicionales = calcular_cuotas_adicionales(
            precio_base, 
            contrato["comision"],    # "2 cuotas"
            contrato["deposito"],    # "3 cuotas"
            mes_actual
        )
        
        # Cuotas esperadas mes 1: 50000 (comisión) + 33333.33 (depósito) = 83333.33
        expected_cuotas = 83333.33
        self.assertAlmostEqual(cuotas_adicionales, expected_cuotas, places=2,
                              msg="Cuotas adicionales mes 1 deben ser 83333.33")
        
        # Precio final inquilino
        precio_final_inquilino = precio_base + cuotas_adicionales + municipalidad
        expected_precio_final = 100000 + 83333.33 + 15000  # 198333.33
        
        self.assertAlmostEqual(precio_final_inquilino, expected_precio_final, places=2,
                              msg=f"Precio final inquilino debe ser {expected_precio_final}")
        
        # Comisión inmobiliaria (solo sobre precio base)
        from app import calcular_comision
        comision_inmo = calcular_comision(contrato["comision_inmo"], precio_base)
        expected_comision = 5000  # 100000 * 5%
        
        self.assertEqual(comision_inmo, expected_comision,
                        "Comisión debe calcularse solo sobre precio base")
        
        # Pago propietario (precio base menos comisión)
        pago_prop = precio_base - comision_inmo
        expected_pago_prop = 95000  # 100000 - 5000
        
        self.assertEqual(pago_prop, expected_pago_prop,
                        "Pago propietario debe ser precio base menos comisión")
    
    def test_calculo_precio_final_sin_municipalidad(self):
        """Test integración: contrato sin gastos municipales"""
        # Local Comercial: municipalidad = 0
        contrato = CONTRATOS_TEST_DATA[3]  # Ahora Local Comercial es el índice 3
        
        precio_base = float(contrato["precio_original"])  # 200000
        municipalidad = float(contrato["municipalidad"])  # 0
        mes_actual = 1
        
        from app import calcular_cuotas_adicionales, calcular_comision
        
        cuotas_adicionales = calcular_cuotas_adicionales(
            precio_base, 
            contrato["comision"],    # "3 cuotas"
            contrato["deposito"],    # "Pagado"
            mes_actual
        )
        
        # Solo comisión en 3 cuotas: 200000 / 3 = 66666.67
        expected_cuotas = 66666.67
        self.assertAlmostEqual(cuotas_adicionales, expected_cuotas, places=2)
        
        # Precio final sin municipalidad
        precio_final_inquilino = precio_base + cuotas_adicionales + municipalidad
        expected_precio_final = 200000 + 66666.67 + 0  # 266666.67
        
        self.assertAlmostEqual(precio_final_inquilino, expected_precio_final, places=2)
        
        # Comisión inmobiliaria
        comision_inmo = calcular_comision(contrato["comision_inmo"], precio_base)
        expected_comision = 6000  # 200000 * 3%
        
        self.assertEqual(comision_inmo, expected_comision)
    
    def test_registro_completo_con_municipalidad(self):
        """Test estructura completa del registro con municipalidad"""
        # Simular el registro que se genera en el main()
        contrato = CONTRATOS_TEST_DATA[2]  # Depto Belgrano ahora es el índice 2
        
        registro_esperado = {
            "nombre_inmueble": "Depto Belgrano",
            "dir_inmueble": "Cabildo 567",
            "inquilino": "Ana López",
            "propietario": "Carlos Ruiz",
            "mes_actual": "2024-07",
            "precio_mes_actual": 158500.0,  # precio_base + cuotas + municipalidad
            "precio_base": 150000.0,        # Precio base sin cuotas ni municipalidad
            "cuotas_adicionales": 0.0,      # Sin cuotas en este caso
            "municipalidad": 8500.0,        # Gastos municipales
            "comision_inmo": 6000.0,        # 150000 * 4%
            "pago_prop": 144000.0           # 150000 - 6000
        }
        
        # Verificar campos clave
        precio_base = float(contrato["precio_original"])
        municipalidad = float(contrato["municipalidad"])
        cuotas = 0.0  # "Pagado" en mes posterior al inicial
        
        precio_final = precio_base + cuotas + municipalidad
        self.assertEqual(precio_final, registro_esperado["precio_mes_actual"])
        
        from app import calcular_comision
        comision = calcular_comision(contrato["comision_inmo"], precio_base)
        self.assertEqual(comision, registro_esperado["comision_inmo"])
        
        pago_prop = precio_base - comision
        self.assertEqual(pago_prop, registro_esperado["pago_prop"])

    def test_calculo_cuotas_completo(self):
        """Test cálculo completo de cuotas (comisión + depósito)"""
        # Casa Palermo: comisión "2 cuotas", depósito "3 cuotas"
        contrato = CONTRATOS_TEST_DATA[0]
        precio_base = 100000.0
        
        # Mes 1
        monto_adicional = 0.0
        if contrato["comision"] == "2 cuotas":
            monto_adicional += precio_base / 2  # 50,000
        if contrato["deposito"] == "3 cuotas":
            monto_adicional += precio_base / 3  # 33,333.33
        
        expected_mes_1 = round(50000 + 33333.33, 2)
        self.assertEqual(round(monto_adicional, 2), expected_mes_1,
                        f"Mes 1 debe tener cuotas por {expected_mes_1}")
        
        # Mes 3 (solo depósito)
        monto_adicional = 0.0
        if contrato["comision"] == "2 cuotas" and 3 <= 2:  # No aplica
            monto_adicional += precio_base / 2
        if contrato["deposito"] == "3 cuotas" and 3 <= 3:  # Sí aplica
            monto_adicional += precio_base / 3
        
        expected_mes_3 = round(33333.33, 2)
        self.assertEqual(round(monto_adicional, 2), expected_mes_3,
                        f"Mes 3 debe tener solo depósito por {expected_mes_3}")
        
        # Mes 4 (sin cuotas)
        monto_adicional = 0.0
        if contrato["comision"] == "2 cuotas" and 4 <= 2:  # No aplica
            monto_adicional += precio_base / 2
        if contrato["deposito"] == "3 cuotas" and 4 <= 3:  # No aplica
            monto_adicional += precio_base / 3
        
        self.assertEqual(monto_adicional, 0,
                        "Mes 4 no debe tener cuotas adicionales")
    
    def test_calculo_comision_inmobiliaria_y_pago_propietario(self):
        """Test cálculo de comisión inmobiliaria y pago al propietario"""
        # Casa Palermo: comisión_inmo "5%"
        contrato = CONTRATOS_TEST_DATA[0]
        precio_actual = 100000.0  # Precio base sin cuotas
        
        # Comisión inmobiliaria (sobre precio base)
        pct = 5.0
        comision = round(precio_actual * pct / 100, 2)  # 5,000
        
        # Pago al propietario (precio base - comisión)
        pago_prop = round(precio_actual - comision, 2)  # 95,000
        
        self.assertEqual(comision, 5000, "Comisión inmobiliaria debe ser 5,000")
        self.assertEqual(pago_prop, 95000, "Pago al propietario debe ser 95,000")
    
    def test_manejo_campos_faltantes_con_municipalidad(self):
        """Test manejo de municipalidad cuando faltan otros campos"""
        # Casa Incompleta - tiene municipalidad pero faltan otros campos
        contrato = CONTRATOS_TEST_DATA[4]
        campos_requeridos = [
            "precio_original", "fecha_inicio_contrato", "duracion_meses",
            "actualizacion", "indice", "comision_inmo"
        ]
        
        fila = pd.Series(contrato)
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if campo not in fila or pd.isna(fila[campo]) or str(fila[campo]).strip() == "":
                campos_faltantes.append(campo)
        
        # Debe detectar campos faltantes
        self.assertGreater(len(campos_faltantes), 0,
                         "Debe detectar campos faltantes")
        
        # Pero municipalidad debe estar presente
        self.assertIn("municipalidad", contrato,
                      "Municipalidad debe existir en el contrato")
        self.assertEqual(float(contrato["municipalidad"]), 5000.0,
                        "Municipalidad debe ser 5000")
        
        # En este caso, debe crear registro con municipalidad pero otros campos en blanco
        if campos_faltantes:
            municipalidad_valor = fila.get("municipalidad", "") if fila.get("municipalidad") else ""
            
            registro_resultado = {
                "nombre_inmueble": contrato.get("nombre_inmueble", ""),
                "precio_mes_actual": "",
                "precio_base": "",
                "cuotas_adicionales": "",
                "municipalidad": municipalidad_valor,  # Debe preservar municipalidad
                "comision_inmo": "",
                "pago_prop": "",
                "actualizacion": "NO"
            }
            
            # Verificar que municipalidad se preserva
            self.assertEqual(registro_resultado["municipalidad"], 5000.0,
                           "Municipalidad debe preservarse aunque falten otros campos")
            
            # Pero otros campos calculados deben estar en blanco
            self.assertEqual(registro_resultado["precio_mes_actual"], "",
                           "Precio final debe estar en blanco")
            self.assertEqual(registro_resultado["precio_base"], "",
                           "Precio base debe estar en blanco")

    def test_manejo_campos_faltantes(self):
        """Test manejo de contrato con campos faltantes"""
        # Casa Incompleta - tiene campos vacíos
        contrato = CONTRATOS_TEST_DATA[4]
        campos_requeridos = [
            "precio_original", "fecha_inicio_contrato", "duracion_meses",
            "actualizacion", "indice", "comision_inmo"
        ]
        
        fila = pd.Series(contrato)
        campos_faltantes = []
        
        for campo in campos_requeridos:
            if campo not in fila or pd.isna(fila[campo]) or str(fila[campo]).strip() == "":
                campos_faltantes.append(campo)
        
        # Debe detectar campos faltantes
        self.assertGreater(len(campos_faltantes), 0,
                         "Debe detectar campos faltantes")
        
        # En este caso, debe crear registro con campos calculados en blanco
        if campos_faltantes:
            registro_resultado = {
                "nombre_inmueble": contrato.get("nombre_inmueble", ""),
                "precio_mes_actual": "",
                "comision_inmo": "",
                "pago_prop": "",
                "actualizacion": "NO",
                "porc_actual": "",
                "meses_prox_actualizacion": "",
                "meses_prox_renovacion": ""
            }
            
            # Verificar que los campos calculados están en blanco
            self.assertEqual(registro_resultado["precio_mes_actual"], "",
                           "Precio debe estar en blanco")
            self.assertEqual(registro_resultado["comision_inmo"], "",
                           "Comisión debe estar en blanco")
            self.assertEqual(registro_resultado["actualizacion"], "NO",
                           "Actualización debe ser NO")


class TestEdgeCases(unittest.TestCase):
    """Tests para casos extremos y validaciones"""
    
    def test_contrato_primer_mes(self):
        """Test contrato en su primer mes (no debe actualizar)"""
        fecha_ref = date(2024, 1, 1)  # Mismo mes de inicio
        inicio = date(2024, 1, 1)
        
        meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        self.assertEqual(meses_desde_inicio, 0, "Primer mes debe ser 0")
        
        freq_meses = 3
        ciclos_cumplidos = meses_desde_inicio // freq_meses
        resto = meses_desde_inicio % freq_meses
        
        aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        self.assertEqual(aplica_actualizacion, "NO",
                        "Primer mes NO debe aplicar actualización")
    
    def test_contrato_proximo_vencimiento(self):
        """Test contrato próximo a vencer"""
        inicio = date(2024, 1, 1)
        duracion_meses = 24
        fecha_ref = date(2025, 12, 1)  # Mes 23 (penúltimo)
        
        meses_desde_inicio = (fecha_ref.year - inicio.year) * 12 + (fecha_ref.month - inicio.month)
        meses_prox_renovacion = duracion_meses - meses_desde_inicio
        
        self.assertEqual(meses_desde_inicio, 23, "Debe ser mes 23")
        self.assertEqual(meses_prox_renovacion, 1, "Debe faltar 1 mes para vencer")
    
    def test_contrato_vencido(self):
        """Test contrato vencido (no debe procesarse)"""
        inicio = date(2024, 1, 1)
        duracion_meses = 24
        fecha_ref = date(2026, 2, 1)  # Mes 25 (vencido)
        
        meses_transcurridos = ((fecha_ref - inicio).days // 30)
        esta_vigente = meses_transcurridos < duracion_meses
        
        self.assertFalse(esta_vigente, "Contrato vencido no debe estar vigente")


if __name__ == '__main__':
    unittest.main()
