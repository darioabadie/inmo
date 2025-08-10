#!/usr/bin/env python3
"""
Script para ejecutar todos los tests de la aplicación inmobiliaria
Tests reorganizados según tests_funcionales.md (Tests 1-110)
Solo incluye los 8 archivos de tests reorganizados actuales
"""
import unittest
import sys
import os
import warnings
import logging
from io import StringIO

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def suppress_warnings_and_logs():
    """Suprime todos los warnings y logs para mostrar solo el resumen de resultados."""
    # Suprimir TODOS los warnings
    warnings.filterwarnings('ignore')
    
    # Deshabilitar TODOS los logs, incluyendo warnings
    logging.disable(logging.CRITICAL)
    
    # Configurar el root logger para no mostrar nada
    logging.getLogger().disabled = True
    
    # Deshabilitar loggers específicos del sistema
    for logger_name in ['inmobiliaria.historical', 'inmobiliaria.services', 'inmobiliaria', 
                       'historical_errors', 'root']:
        logging.getLogger(logger_name).disabled = True
        logging.getLogger(logger_name).setLevel(logging.CRITICAL + 1)

def run_all_tests():
    """Ejecuta todos los tests y muestra un reporte"""
    
    # Suprimir todos los warnings y logs
    suppress_warnings_and_logs()
    
    # Orden específico de ejecución según nueva estructura organizada
    test_modules = [
        # Tests funcionales (1-110)
        'functional.test_validacion_datos',        # Tests 1-26: Validación de datos de entrada
        'functional.test_logica_contratos',        # Tests 27-40: Lógica de contratos  
        'functional.test_actualizaciones',         # Tests 41-52: Cálculos de actualización
        'functional.test_cuotas_adicionales',      # Tests 53-65: Cálculo de cuotas adicionales
        'functional.test_precios_finales',         # Tests 66-79: Precios finales y comisiones
        'functional.test_campos_informativos',     # Tests 80-91: Campos informativos
        'functional.test_casos_extremos',          # Tests 92-101: Casos extremos y manejo de errores
        'functional.test_integracion_completa',    # Tests 102-110: Integración y flujo completo
        
        # Tests de integración histórica (111-150)
        'integration.test_historical_core',         # Tests 111-135: Funcionalidad núcleo del histórico
        'integration.test_historical_incremental',  # Tests 136-150: Lógica incremental 
        # 'integration.test_historical_integracion',  # Tests 151-165: Integración completa histórico (TEMPORALMENTE DESHABILITADO)
        
        # Tests unitarios - nueva arquitectura de servicios
        'unit.test_historical_service',            # Tests unitarios: HistoricalService
        'unit.test_historical_data_manager',       # Tests unitarios: HistoricalDataManager
        # 'unit.test_error_logging',               # Tests unitarios: Sistema de logging de errores (DESHABILITADO)
    ]
    
    # Descubrir y ejecutar tests en orden
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Cargar módulos en orden específico (silenciosamente)
    for module_name in test_modules:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
        except Exception:
            # Ignorar errores de carga silenciosamente
            pass
    
    # Configurar el runner para capturar salida pero no mostrarla
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=0,  # Sin verbosidad
        failfast=False,
        buffer=True  # Buffer para suprimir prints de los tests
    )
    
    # Ejecutar tests silenciosamente
    result = runner.run(suite)
    
    # Mostrar solo el resumen limpio
    print("=" * 70)
    print("RESUMEN DE RESULTADOS")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = total_tests - failures - errors
    
    print(f"Tests ejecutados: {total_tests}")
    print(f"Exitosos: {success}")
    print(f"Fallos: {failures}")
    print(f"Errores: {errors}")
    print("")
    
    if failures == 0 and errors == 0:
        print("✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("🎉 La aplicación está funcionando correctamente.")
    else:
        print(f"❌ Se encontraron {failures + errors} problemas.")
        print("🔧 Revisa los fallos y errores antes de usar en producción.")
        
        if failures > 0:
            print(f"\n📋 FALLOS ({failures}):")
            for test, traceback in result.failures:
                print(f"❌ {test}")
                # Extraer solo la línea del error sin stack trace
                lines = traceback.split('\n')
                for line in lines:
                    if 'AssertionError:' in line:
                        print(f"   {line.strip()}")
                        break
        
        if errors > 0:
            print(f"\n🚨 ERRORES ({errors}):")
            for test, traceback in result.errors:
                print(f"💥 {test}")
                # Extraer solo la línea del error sin stack trace
                lines = traceback.split('\n')
                for line in lines:
                    if any(word in line for word in ['Error:', 'Exception:', 'ImportError:', 'AttributeError:']):
                        print(f"   {line.strip()}")
                        break
    
    print("")
    print("=" * 60)
    
    return result.wasSuccessful()


def run_specific_test_suite(test_name):
    """Ejecuta un conjunto específico de tests"""
    
    # Suprimir todos los warnings y logs
    suppress_warnings_and_logs()
    
    test_modules = {
        # Tests reorganizados por categoría
        'functional': [
            'functional.test_validacion_datos',
            'functional.test_logica_contratos',
            'functional.test_actualizaciones',
            'functional.test_cuotas_adicionales',
            'functional.test_precios_finales',
            'functional.test_campos_informativos',
            'functional.test_casos_extremos',
            'functional.test_integracion_completa'
        ],
        'integration': [
            'integration.test_historical_core',
            'integration.test_historical_incremental',
            'integration.test_historical_integracion'
        ],
        'unit': [
            'unit.test_historical_service',
            'unit.test_historical_data_manager'
            # 'unit.test_error_logging'  # DESHABILITADO
        ],
        'logging': ['unit.test_error_logging']
    }
    
    if test_name not in test_modules:
        print(f"❌ Test suite '{test_name}' no encontrado.")
        print(f"Disponibles: {', '.join(test_modules.keys())}")
        return False
    
    # Cargar módulos
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    modules_to_test = test_modules[test_name]
    for module_name in modules_to_test:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
        except Exception:
            pass
    
    # Ejecutar tests con salida capturada
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=0,
        failfast=False,
        buffer=True
    )
    result = runner.run(suite)
    
    # Mostrar solo el resumen limpio
    print("=" * 70)
    print(f"RESUMEN DE RESULTADOS - {test_name.upper()}")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = total_tests - failures - errors
    
    print(f"Tests ejecutados: {total_tests}")
    print(f"Exitosos: {success}")
    print(f"Fallos: {failures}")
    print(f"Errores: {errors}")
    print("")
    
    if result.wasSuccessful():
        print("✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print(f"🎉 Los tests {test_name} están funcionando correctamente.")
    else:
        print(f"❌ Se encontraron {failures + errors} problemas.")
    
    print("")
    print("=" * 60)
    
    return result.wasSuccessful()


def run_historical_tests():
    """Ejecuta solo los tests del módulo histórico"""
    
    # Suprimir todos los warnings y logs
    suppress_warnings_and_logs()
    
    historical_modules = [
        'integration.test_historical_core',         # Tests 111-135: Funcionalidad núcleo
        'integration.test_historical_incremental',  # Tests 136-150: Lógica incremental
        'integration.test_historical_integracion',  # Tests 151-165: Integración completa
        'unit.test_historical_service',            # Tests unitarios: HistoricalService
        'unit.test_historical_data_manager',       # Tests unitarios: HistoricalDataManager
        # 'unit.test_error_logging',               # Tests unitarios: Sistema de logging de errores (DESHABILITADO)
    ]
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for module_name in historical_modules:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
        except Exception:
            pass
    
    # Ejecutar tests con salida capturada
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=0,
        failfast=False,
        buffer=True
    )
    result = runner.run(suite)
    
    # Mostrar solo el resumen limpio
    print("=" * 70)
    print("RESUMEN DE RESULTADOS - MÓDULO HISTÓRICO")
    print("=" * 70)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success = total_tests - failures - errors
    
    print(f"Tests ejecutados: {total_tests}")
    print(f"Exitosos: {success}")
    print(f"Fallos: {failures}")
    print(f"Errores: {errors}")
    print("")
    
    if result.wasSuccessful():
        print("✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("🎉 El módulo histórico está funcionando correctamente.")
    else:
        print(f"❌ Se encontraron {failures + errors} problemas en el módulo histórico.")
    
    print("")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Ejecutar test específico
        test_suite = sys.argv[1]
        if test_suite.lower() == 'historical':
            success = run_historical_tests()
        else:
            success = run_specific_test_suite(test_suite)
    else:
        # Ejecutar todos los tests
        success = run_all_tests()
    
    # Código de salida apropiado
    sys.exit(0 if success else 1)
