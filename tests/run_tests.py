#!/usr/bin/env python3
"""
Script para ejecutar todos los tests de la aplicación inmobiliaria
Tests reorganizados según tests_funcionales.md (Tests 1-110)
Solo incluye los 8 archivos de tests reorganizados actuales
"""
import unittest
import sys
import os
from io import StringIO

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Ejecuta todos los tests y muestra un reporte"""
    
    print("=" * 70)
    print("EJECUTANDO TESTS FUNCIONALES - SISTEMA INMOBILIARIO")
    print("Tests reorganizados según tests_funcionales.md (110 tests)")
    print("=" * 70)
    
    # Orden específico de ejecución según categorías funcionales
    test_modules = [
        'test_validacion_datos',        # Tests 1-26: Validación de datos de entrada
        'test_logica_contratos',        # Tests 27-40: Lógica de contratos  
        'test_actualizaciones',         # Tests 41-52: Cálculos de actualización
        'test_cuotas_adicionales',      # Tests 53-65: Cálculo de cuotas adicionales
        'test_precios_finales',         # Tests 66-79: Precios finales y comisiones
        'test_campos_informativos',     # Tests 80-91: Campos informativos
        'test_casos_extremos',          # Tests 92-101: Casos extremos y manejo de errores
        'test_integracion_completa',    # Tests 102-110: Integración y flujo completo
    ]
    
    # Descubrir y ejecutar tests en orden
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Cargar módulos en orden específico
    for module_name in test_modules:
        try:
            module_suite = loader.loadTestsFromName(module_name)
            suite.addTest(module_suite)
            print(f"✓ Cargado: {module_name}")
        except Exception as e:
            print(f"✗ Error cargando {module_name}: {e}")
    
    print(f"\nTotal módulos cargados: {len(test_modules)}")
    print("-" * 70)
    
    # Configurar el runner con verbosidad
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        failfast=False,
        buffer=True
    )
    
    # Ejecutar tests
    result = runner.run(suite)
    
    # Mostrar resultados
    output = stream.getvalue()
    print(output)
    
    # Resumen final
    print("\n" + "=" * 70)
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
    
    if failures > 0:
        print(f"\n📋 FALLOS ({failures}):")
        print("-" * 40)
        for test, traceback in result.failures:
            print(f"❌ {test}")
            print(f"   {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}")
    
    if errors > 0:
        print(f"\n🚨 ERRORES ({errors}):")
        print("-" * 40)
        for test, traceback in result.errors:
            print(f"💥 {test}")
            print(f"   {traceback.split(chr(10))[-2] if traceback else 'Error desconocido'}")
    
    if failures == 0 and errors == 0:
        print("\n✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("🎉 La aplicación está funcionando correctamente.")
    else:
        print(f"\n⚠️  Se encontraron {failures + errors} problemas.")
        print("🔧 Revisa los fallos y errores antes de usar en producción.")
    
    print("\n" + "=" * 60)
    
    return result.wasSuccessful()


def run_specific_test_suite(test_name):
    """Ejecuta un conjunto específico de tests"""
    
    test_modules = {
        # Tests reorganizados por categoría
        'validacion': 'test_validacion_datos.py',
        'contratos': 'test_logica_contratos.py', 
        'actualizaciones': 'test_actualizaciones.py',
        'cuotas': 'test_cuotas_adicionales.py',
        'precios': 'test_precios_finales.py',
        'informativos': 'test_campos_informativos.py',
        'extremos': 'test_casos_extremos.py',
        'integracion': 'test_integracion_completa.py',
        
        # Shortcuts para ejecutar grupos
        'basicos': ['test_validacion_datos.py', 'test_logica_contratos.py'],
        'calculos': ['test_actualizaciones.py', 'test_cuotas_adicionales.py', 'test_precios_finales.py'],
        'avanzados': ['test_campos_informativos.py', 'test_casos_extremos.py', 'test_integracion_completa.py']
    }
    
    if test_name not in test_modules:
        print(f"❌ Test suite '{test_name}' no encontrado.")
        print(f"Disponibles: {', '.join(test_modules.keys())}")
        return False
    
    print(f"Ejecutando tests: {test_name}")
    print("-" * 40)
    
    # Manejar múltiples módulos
    test_files = test_modules[test_name]
    if isinstance(test_files, str):
        test_files = [test_files]
    
    all_results = []
    
    for test_file in test_files:
        print(f"\n📋 Ejecutando: {test_file}")
        print("-" * 30)
        
        # Cargar y ejecutar el módulo específico
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromName(f'tests.{test_file[:-3]}')
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        all_results.append(result.wasSuccessful())
    
    return all(all_results)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Ejecutar test específico
        test_suite = sys.argv[1]
        success = run_specific_test_suite(test_suite)
    else:
        # Ejecutar todos los tests
        success = run_all_tests()
    
    # Código de salida apropiado
    sys.exit(0 if success else 1)
