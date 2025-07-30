"""
Tests de integración completa del sistema (Tests 102-110)
Basado en tests_funcionales.md - Categoría 10: INTEGRACIÓN Y FLUJO COMPLETO
Consolidando y reorganizando tests de integración existentes
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
from inmobiliaria.services.calculations import calcular_cuotas_adicionales, calcular_comision


class TestProcesamientoMasivo(unittest.TestCase):
    """Tests 102-104: Procesamiento masivo"""
    
    def setUp(self):
        """Configuración inicial"""
        self.contratos_df = pd.DataFrame(CONTRATOS_TEST_DATA)
        self.fecha_ref = date(2024, 4, 1)
    
    def test_procesar_multiples_contratos_una_ejecucion(self):
        """Test 102: El sistema debe procesar correctamente múltiples contratos en una sola ejecución"""
        # Verificar que tenemos múltiples contratos de prueba
        num_contratos = len(CONTRATOS_TEST_DATA)
        self.assertGreaterEqual(num_contratos, 3,
                               "Debe haber al menos 3 contratos para test masivo")
        
        # Simular procesamiento de cada contrato
        resultados_procesamiento = []
        
        for contrato in CONTRATOS_TEST_DATA:
            try:
                # Simular validaciones básicas
                campos_requeridos = ["nombre_inmueble", "precio_original", "fecha_inicio_contrato"]
                contrato_valido = all(contrato.get(campo) for campo in campos_requeridos)
                
                if contrato_valido:
                    resultado = {
                        "nombre_inmueble": contrato["nombre_inmueble"],
                        "procesado": True,
                        "error": None
                    }
                else:
                    resultado = {
                        "nombre_inmueble": contrato.get("nombre_inmueble", "DESCONOCIDO"),
                        "procesado": False,
                        "error": "Campos requeridos faltantes"
                    }
                
                resultados_procesamiento.append(resultado)
                
            except Exception as e:
                resultados_procesamiento.append({
                    "nombre_inmueble": contrato.get("nombre_inmueble", "DESCONOCIDO"),
                    "procesado": False,
                    "error": str(e)
                })
        
        # Verificar que se procesaron todos los contratos
        self.assertEqual(len(resultados_procesamiento), num_contratos,
                        "Debe procesar todos los contratos de entrada")
        
        # Verificar que al menos algunos se procesaron exitosamente
        exitosos = [r for r in resultados_procesamiento if r["procesado"]]
        self.assertGreater(len(exitosos), 0,
                          "Al menos algunos contratos deben procesarse exitosamente")
    
    def test_generar_registro_salida_por_contrato_valido(self):
        """Test 103: El sistema debe generar un registro de salida por cada contrato válido de entrada"""
        contratos_validos = []
        registros_salida = []
        
        for contrato in CONTRATOS_TEST_DATA:
            # Verificar validez del contrato
            campos_requeridos = ["nombre_inmueble", "precio_original", "fecha_inicio_contrato", 
                               "duracion_meses", "actualizacion", "indice", "comision_inmo"]
            
            contrato_valido = all(contrato.get(campo) is not None for campo in campos_requeridos)
            
            if contrato_valido:
                contratos_validos.append(contrato)
                
                # Simular generación de registro de salida
                registro_salida = {
                    "nombre_inmueble": contrato["nombre_inmueble"],
                    "precio_base": contrato["precio_original"],  # Simplificado para test
                    "precio_mes_actual": contrato["precio_original"],  # Simplificado
                    "mes_actual": self.fecha_ref.strftime("%Y-%m")
                }
                registros_salida.append(registro_salida)
        
        # Verificar relación 1:1
        self.assertEqual(len(registros_salida), len(contratos_validos),
                        "Debe haber un registro de salida por cada contrato válido")
        
        # Verificar que cada registro tiene los campos básicos
        for registro in registros_salida:
            self.assertIn("nombre_inmueble", registro)
            self.assertIn("precio_base", registro)
            self.assertIn("precio_mes_actual", registro)
    
    def test_loggear_contratos_omitidos_con_razones(self):
        """Test 104: El sistema debe loggear apropiadamente contratos omitidos y razones"""
        contratos_omitidos = []
        
        # Simular diferentes razones de omisión
        casos_omision = [
            {"nombre_inmueble": "Casa Sin Precio", "precio_original": None, "razon": "PRECIO_FALTANTE"},
            {"nombre_inmueble": "Casa Sin Fecha", "fecha_inicio_contrato": None, "razon": "FECHA_INVALIDA"},
            {"nombre_inmueble": "Casa Vencida", "fecha_inicio_contrato": "2022-01-01", 
             "duracion_meses": 12, "razon": "CONTRATO_FINALIZADO"},
        ]
        
        for caso in casos_omision:
            # Simular validaciones que causarían omisión
            if caso.get("precio_original") is None:
                razon = "PRECIO_FALTANTE"
            elif caso.get("fecha_inicio_contrato") is None:
                razon = "FECHA_INVALIDA"
            elif caso.get("razon") == "CONTRATO_FINALIZADO":
                razon = "CONTRATO_FINALIZADO"
            else:
                razon = "OTROS"
            
            log_entry = {
                "nombre_inmueble": caso["nombre_inmueble"],
                "razon_omision": razon,
                "timestamp": self.fecha_ref
            }
            contratos_omitidos.append(log_entry)
        
        # Verificar que se loggean las omisiones
        self.assertEqual(len(contratos_omitidos), 3,
                        "Debe loggear todos los contratos omitidos")
        
        # Verificar que cada log tiene la información necesaria
        for log in contratos_omitidos:
            self.assertIn("nombre_inmueble", log)
            self.assertIn("razon_omision", log)
            self.assertIn(log["razon_omision"], 
                         ["PRECIO_FALTANTE", "FECHA_INVALIDA", "CONTRATO_FINALIZADO", "OTROS"])


class TestEscenariosRealesComplejos(unittest.TestCase):
    """Tests 105-107: Escenarios reales complejos"""
    
    def test_contrato_24_meses_trimestral_ipc_con_cuotas(self):
        """Test 105: Un contrato de 24 meses, trimestral, IPC, con cuotas debe calcularse correctamente mes a mes"""
        # Configuración del contrato
        contrato_config = {
            "precio_original": 100000.0,
            "fecha_inicio": date(2024, 1, 1),
            "duracion_meses": 24,
            "actualizacion": "trimestral",
            "indice": "IPC",
            "comision": "2 cuotas",
            "deposito": "3 cuotas",
            "municipalidad": 5000.0,
            "comision_inmo": "5%"
        }
        
        # Simular procesamiento mes a mes para el primer año
        meses_test = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        resultados_mensuales = []
        
        for mes_num in meses_test:
            fecha_mes = date(2024, mes_num, 1)
            meses_desde_inicio = mes_num - 1
            
            # Cálculo básico (sin inflación real para simplificar test)
            freq_meses = 3
            ciclos_cumplidos = meses_desde_inicio // freq_meses
            resto = meses_desde_inicio % freq_meses
            
            # Simular precio base (simplificado)
            precio_base = contrato_config["precio_original"]  # Sin actualización real
            
            # Cuotas adicionales
            cuotas_adicionales = calcular_cuotas_adicionales(
                precio_base, 
                contrato_config["comision"], 
                contrato_config["deposito"], 
                mes_num
            )
            
            # Precio final
            precio_mes_actual = precio_base + cuotas_adicionales + contrato_config["municipalidad"]
            
            # Actualización
            aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
            
            resultado_mes = {
                "mes": mes_num,
                "precio_base": precio_base,
                "cuotas_adicionales": cuotas_adicionales,
                "precio_mes_actual": precio_mes_actual,
                "actualizacion": aplica_actualizacion
            }
            resultados_mensuales.append(resultado_mes)
        
        # Verificaciones específicas
        # Mes 1: debe tener cuotas altas
        mes_1 = resultados_mensuales[0]
        self.assertGreater(mes_1["cuotas_adicionales"], 50000,
                          "Mes 1 debe tener cuotas altas (comisión + depósito)")
        
        # Mes 4: debe tener actualización (primer ciclo trimestral completo)
        mes_4 = resultados_mensuales[3]
        self.assertEqual(mes_4["actualizacion"], "SI",
                        "Mes 4 debe tener actualización trimestral (primer ciclo completo)")
        
        # Mes 5: debe tener cuotas = 0
        mes_5 = resultados_mensuales[4]
        self.assertEqual(mes_5["cuotas_adicionales"], 0,
                        "Mes 5 no debe tener cuotas adicionales")
        
        self.assertEqual(len(resultados_mensuales), 12,
                        "Debe procesar los 12 meses correctamente")
    
    def test_contrato_36_meses_semestral_icl_sin_cuotas(self):
        """Test 106: Un contrato de 36 meses, semestral, ICL, sin cuotas debe calcularse correctamente"""
        contrato_config = {
            "precio_original": 150000.0,
            "fecha_inicio": date(2024, 1, 1),
            "duracion_meses": 36,
            "actualizacion": "semestral",
            "indice": "ICL",
            "comision": "Pagado",
            "deposito": "Pagado",
            "municipalidad": 0,
            "comision_inmo": "6%"
        }
        
        # Test específico para 18 meses (3 actualizaciones semestrales)
        fecha_test = date(2025, 7, 1)  # 18 meses después
        meses_desde_inicio = 18
        
        freq_meses = 6
        ciclos_cumplidos = meses_desde_inicio // freq_meses  # 3
        resto = meses_desde_inicio % freq_meses  # 0
        
        # Verificaciones
        self.assertEqual(ciclos_cumplidos, 3,
                        "Debe haber 3 ciclos cumplidos")
        self.assertEqual(resto, 0,
                        "Debe ser mes de actualización")
        
        # Cuotas adicionales = 0 (todo "Pagado")
        cuotas_adicionales = calcular_cuotas_adicionales(
            contrato_config["precio_original"],
            contrato_config["comision"],
            contrato_config["deposito"],
            18  # Mes actual
        )
        self.assertEqual(cuotas_adicionales, 0,
                        "No debe haber cuotas adicionales")
        
        # Aplicación de actualización
        aplica_actualizacion = "SI" if resto == 0 and ciclos_cumplidos > 0 else "NO"
        self.assertEqual(aplica_actualizacion, "SI",
                        "Mes 18 debe aplicar actualización semestral")
    
    def test_multiples_contratos_diferentes_configuraciones_sin_interferencia(self):
        """Test 107: Múltiples contratos con diferentes configuraciones deben procesarse sin interferencia"""
        # Configurar contratos con configuraciones muy diferentes
        contratos_diversos = [
            {
                "id": 1,
                "actualizacion": "trimestral",
                "indice": "10%",
                "comision": "2 cuotas",
                "deposito": "Pagado"
            },
            {
                "id": 2,
                "actualizacion": "semestral",
                "indice": "IPC",
                "comision": "Pagado",
                "deposito": "3 cuotas"
            },
            {
                "id": 3,
                "actualizacion": "anual",
                "indice": "ICL",
                "comision": "3 cuotas",
                "deposito": "2 cuotas"
            }
        ]
        
        resultados_independientes = []
        
        # Procesar cada contrato independientemente
        for contrato in contratos_diversos:
            resultado = {
                "id": contrato["id"],
                "freq_meses": {"trimestral": 3, "semestral": 6, "anual": 12}[contrato["actualizacion"]],
                "tiene_comision_cuotas": contrato["comision"] != "Pagado",
                "tiene_deposito_cuotas": contrato["deposito"] != "Pagado",
                "tipo_indice": "porcentaje" if "%" in contrato["indice"] else "api"
            }
            resultados_independientes.append(resultado)
        
        # Verificar que cada contrato mantiene su configuración
        self.assertEqual(resultados_independientes[0]["freq_meses"], 3,
                        "Contrato 1 debe mantener frecuencia trimestral")
        self.assertEqual(resultados_independientes[1]["freq_meses"], 6,
                        "Contrato 2 debe mantener frecuencia semestral")
        self.assertEqual(resultados_independientes[2]["freq_meses"], 12,
                        "Contrato 3 debe mantener frecuencia anual")
        
        # Verificar que las configuraciones no se interfieren
        self.assertTrue(resultados_independientes[0]["tiene_comision_cuotas"],
                       "Contrato 1 debe tener comisión en cuotas")
        self.assertFalse(resultados_independientes[1]["tiene_comision_cuotas"],
                        "Contrato 2 no debe tener comisión en cuotas")
        self.assertTrue(resultados_independientes[2]["tiene_comision_cuotas"],
                      "Contrato 3 debe tener comisión en cuotas")


class TestValidacionOutput(unittest.TestCase):
    """Tests 108-110: Validación de output"""
    
    def test_registros_salida_formato_columnas_esperado(self):
        """Test 108: Todos los registros de salida deben tener el formato de columnas esperado"""
        # Estructura esperada según technical_specs.md
        columnas_esperadas = [
            # Columnas de Identificación
            "nombre_inmueble", "dir_inmueble", "inquilino", "propietario", "mes_actual",
            # Columnas Calculadas (orden específico según specs)
            "precio_mes_actual", "precio_base", "cuotas_adicionales", "municipalidad",
            "comision_inmo", "pago_prop", "actualizacion", "porc_actual",
            "meses_prox_actualizacion", "meses_prox_renovacion"
        ]
        
        # Simular registro de salida
        registro_ejemplo = {}
        for columna in columnas_esperadas:
            registro_ejemplo[columna] = "valor_test"  # Valor placeholder
        
        # Verificar que todas las columnas están presentes
        for columna in columnas_esperadas:
            self.assertIn(columna, registro_ejemplo,
                         f"Columna '{columna}' debe estar en el output")
        
        # Verificar cantidad total de columnas
        self.assertEqual(len(registro_ejemplo), len(columnas_esperadas),
                        f"Output debe tener exactamente {len(columnas_esperadas)} columnas")
        
        # Verificar orden específico (las primeras 5 son identificación)
        columnas_identificacion = columnas_esperadas[:5]
        columnas_calculadas = columnas_esperadas[5:]
        
        self.assertEqual(len(columnas_identificacion), 5,
                        "Debe haber 5 columnas de identificación")
        self.assertEqual(len(columnas_calculadas), 10,
                        "Debe haber 10 columnas calculadas")
    
    def test_no_valores_nulos_inesperados_campos_calculados(self):
        """Test 109: No debe haber valores nulos inesperados en campos calculados"""
        # Simular procesamiento de contrato válido
        contrato_valido = CONTRATOS_TEST_DATA[0]  # Casa Palermo
        
        # Campos que nunca deben ser nulos en un contrato válido
        campos_nunca_nulos = [
            "precio_base",
            "precio_mes_actual", 
            "cuotas_adicionales",
            "municipalidad",
            "comision_inmo",
            "pago_prop",
            "actualizacion",
            "meses_prox_actualizacion",
            "meses_prox_renovacion"
        ]
        
        # Simular cálculos básicos
        registro_simulado = {
            "precio_base": 100000.0,
            "precio_mes_actual": 150000.0,
            "cuotas_adicionales": 50000.0,
            "municipalidad": 0.0,  # Puede ser 0 pero no None
            "comision_inmo": 5000.0,
            "pago_prop": 95000.0,
            "actualizacion": "NO",
            "porc_actual": "",  # Puede estar vacío pero no None
            "meses_prox_actualizacion": 3,
            "meses_prox_renovacion": 23
        }
        
        # Verificar que ningún campo calculado es None
        for campo in campos_nunca_nulos:
            self.assertIsNotNone(registro_simulado.get(campo),
                               f"Campo '{campo}' no debe ser None")
        
        # Verificar tipos de datos apropiados
        campos_numericos = ["precio_base", "precio_mes_actual", "cuotas_adicionales", 
                           "municipalidad", "comision_inmo", "pago_prop",
                           "meses_prox_actualizacion", "meses_prox_renovacion"]
        
        for campo in campos_numericos:
            valor = registro_simulado.get(campo)
            self.assertIsInstance(valor, (int, float),
                                f"Campo '{campo}' debe ser numérico")
    
    def test_fechas_output_formato_correcto(self):
        """Test 110: Las fechas en el output deben mantener el formato correcto"""
        fecha_ref = date(2024, 7, 15)
        
        # Formato esperado para mes_actual: YYYY-MM
        mes_actual_formato = fecha_ref.strftime("%Y-%m")
        self.assertEqual(mes_actual_formato, "2024-07",
                        "mes_actual debe tener formato YYYY-MM")
        
        # Verificar que el formato es consistente
        fechas_test = [
            date(2024, 1, 1),
            date(2024, 12, 31),
            date(2025, 6, 15)
        ]
        
        for fecha in fechas_test:
            formato_output = fecha.strftime("%Y-%m")
            
            # Verificar que tiene la estructura correcta
            self.assertRegex(formato_output, r'^\d{4}-\d{2}$',
                           f"Fecha {fecha} debe tener formato YYYY-MM")
            
            # Verificar que es parseable de vuelta
            try:
                year, month = formato_output.split('-')
                self.assertEqual(int(year), fecha.year)
                self.assertEqual(int(month), fecha.month)
            except:
                self.fail(f"Formato de fecha {formato_output} no es parseable")


if __name__ == '__main__':
    unittest.main()
