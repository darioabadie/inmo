#!/usr/bin/env python3
"""
Script para ejecutar todos los tests de la aplicación inmobiliaria
"""
import unittest
import sys
import os
from io import StringIO

# Agregar el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_all_tests():
    """Ejecuta todos los tests y muestra un reporte"""
    
    print("=" * 60)
    print("EJECUTANDO TESTS PARA APLICACIÓN INMOBILIARIA")
    print("=" * 60)
    
    # Descubrir y ejecutar todos los tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir, pattern='test_*.py')
    
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
    print("\n" + "=" * 60)
    print("RESUMEN DE RESULTADOS")
    print("=" * 60)
    
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
        'calculations': 'test_calculations.py',
        'contract': 'test_contract_logic.py', 
        'integration': 'test_integration.py',
        'data': 'test_data.py',
        # Nuevos tests del refactor
        'fase1': 'test_fase1_logica_critica.py',
        'fase2': 'test_fase2_logica_icl.py',
        'sistema_completo': 'test_integracion_sistema_completo.py',
        # Shortcuts para ejecutar grupos
        'refactor': ['test_fase1_logica_critica.py', 'test_fase2_logica_icl.py', 'test_integracion_sistema_completo.py'],
        'legacy': ['test_calculations.py', 'test_contract_logic.py', 'test_integration.py', 'test_data.py']
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
