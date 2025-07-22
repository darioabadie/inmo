"""
Datos de prueba y configuración para los tests
"""
import datetime as dt
import pandas as pd

# Datos de inflación de prueba
INFLACION_TEST_DATA = [
    {"fecha": "2024-01-01", "valor": 5.0},   # Enero 2024: 5%
    {"fecha": "2024-02-01", "valor": 4.5},   # Febrero 2024: 4.5%
    {"fecha": "2024-03-01", "valor": 3.8},   # Marzo 2024: 3.8%
    {"fecha": "2024-04-01", "valor": 4.2},   # Abril 2024: 4.2%
    {"fecha": "2024-05-01", "valor": 3.9},   # Mayo 2024: 3.9%
    {"fecha": "2024-06-01", "valor": 4.1},   # Junio 2024: 4.1%
    {"fecha": "2024-07-01", "valor": 3.7},   # Julio 2024: 3.7%
    {"fecha": "2024-08-01", "valor": 4.3},   # Agosto 2024: 4.3%
    {"fecha": "2024-09-01", "valor": 3.6},   # Septiembre 2024: 3.6%
    {"fecha": "2024-10-01", "valor": 4.0},   # Octubre 2024: 4.0%
    {"fecha": "2024-11-01", "valor": 3.5},   # Noviembre 2024: 3.5%
    {"fecha": "2024-12-01", "valor": 4.4},   # Diciembre 2024: 4.4%
]

def get_inflacion_df_test():
    """Retorna DataFrame de inflación para tests"""
    df = pd.DataFrame(INFLACION_TEST_DATA)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df.sort_values("fecha", inplace=True)
    return df

# Casos de prueba para contratos
CONTRATOS_TEST_DATA = [
    {
        "nombre_inmueble": "Casa Palermo",
        "dir_inmueble": "Av. Santa Fe 1234",
        "inquilino": "Juan Pérez",
        "in_dni": "12345678",
        "propietario": "María García",
        "prop_dni": "87654321",
        "precio_original": 100000.0,
        "actualizacion": "trimestral",
        "indice": "IPC",
        "fecha_inicio_contrato": "2024-01-01",
        "duracion_meses": 24,
        "comision_inmo": "5%",
        "comision": "2 cuotas",
        "deposito": "3 cuotas",
        "municipalidad": 15000.0
    },
    {
        "nombre_inmueble": "Casa Caballito",
        "dir_inmueble": "Rivadavia 5678",
        "inquilino": "Roberto Sánchez",
        "in_dni": "22334455",
        "propietario": "Laura Martínez",
        "prop_dni": "55443322",
        "precio_original": 120000.0,
        "actualizacion": "cuatrimestral",
        "indice": "IPC",
        "fecha_inicio_contrato": "2024-02-01",
        "duracion_meses": 24,
        "comision_inmo": "4.5%",
        "comision": "Pagado",
        "deposito": "2 cuotas",
        "municipalidad": 12000.0
    },
    {
        "nombre_inmueble": "Depto Belgrano",
        "dir_inmueble": "Cabildo 567",
        "inquilino": "Ana López",
        "in_dni": "11223344",
        "propietario": "Carlos Ruiz",
        "prop_dni": "44332211",
        "precio_original": 150000.0,
        "actualizacion": "semestral",
        "indice": "10%",
        "fecha_inicio_contrato": "2024-03-01",
        "duracion_meses": 36,
        "comision_inmo": "4%",
        "comision": "Pagado",
        "deposito": "2 cuotas",
        "municipalidad": 8500.0
    },
    {
        "nombre_inmueble": "Local Comercial",
        "dir_inmueble": "Corrientes 890",
        "inquilino": "Comercial SA",
        "in_dni": "20-12345678-9",
        "propietario": "Inversiones SRL",
        "prop_dni": "30-87654321-4",
        "precio_original": 200000.0,
        "actualizacion": "anual",
        "indice": "ICL",
        "fecha_inicio_contrato": "2024-06-01",
        "duracion_meses": 60,
        "comision_inmo": "3%",
        "comision": "3 cuotas",
        "deposito": "Pagado",
        "municipalidad": 0.0  # Sin gastos municipales
    },
    # Caso con campos faltantes para probar validación
    {
        "nombre_inmueble": "Casa Incompleta",
        "dir_inmueble": "Sin Dirección",
        "inquilino": "Inquilino Test",
        "propietario": "Propietario Test",
        "precio_original": "",  # Campo faltante
        "actualizacion": "trimestral",
        "indice": "",  # Campo faltante
        "fecha_inicio_contrato": "",  # Campo faltante
        "duracion_meses": 24,
        "comision_inmo": "5%",
        "comision": "Pagado",
        "deposito": "Pagado",
        "municipalidad": 5000.0  # Municipalidad presente aunque otros campos falten
    }
]

# Casos de prueba esperados para cálculos específicos
EXPECTED_CALCULATIONS = {
    "inflacion_acumulada": {
        # Inflación trimestral (3 meses) hasta abril 2024
        # (1.05 * 1.045 * 1.038) = 1.13026782 exacto
        "trimestral_hasta_abril": {
            "hasta": dt.date(2024, 4, 1),
            "meses": 3,
            "expected": 1.13026782
        },
        # Inflación semestral (6 meses) hasta junio 2024
        "semestral_hasta_junio": {
            "hasta": dt.date(2024, 6, 1),
            "meses": 6,
            "expected": 1.254  # Aproximado
        }
    },
    "comisiones": {
        "5_porciento": {
            "comision_str": "5%",
            "precio": 100000,
            "expected": 5000
        },
        "4_porciento": {
            "comision_str": "4%",
            "precio": 150000,
            "expected": 6000
        }
    },
    "cuotas_adicionales": {
        "comision_2_cuotas_mes_1": {
            "precio_base": 100000,
            "comision": "2 cuotas",
            "deposito": "Pagado",
            "mes": 1,
            "expected": 50000  # 100000 / 2
        },
        "deposito_3_cuotas_mes_2": {
            "precio_base": 100000,
            "comision": "Pagado",
            "deposito": "3 cuotas",
            "mes": 2,
            "expected": 33333.33  # 100000 / 3
        },
        "ambos_mes_1": {
            "precio_base": 100000,
            "comision": "2 cuotas",
            "deposito": "3 cuotas",
            "mes": 1,
            "expected": 83333.33  # 50000 + 33333.33
        }
    },
    "municipalidad": {
        "con_municipalidad": {
            "precio_base": 100000,
            "cuotas_adicionales": 10000,
            "municipalidad": 15000,
            "expected_precio_final": 125000  # 100000 + 10000 + 15000
        },
        "sin_municipalidad": {
            "precio_base": 80000,
            "cuotas_adicionales": 0,
            "municipalidad": 0,
            "expected_precio_final": 80000  # Solo precio base
        },
        "solo_municipalidad": {
            "precio_base": 150000,
            "cuotas_adicionales": 0,
            "municipalidad": 8500,
            "expected_precio_final": 158500  # 150000 + 8500
        },
        "comision_sobre_precio_base": {
            "precio_base": 100000,
            "municipalidad": 15000,
            "comision_porcentaje": "5%",
            "expected_comision": 5000,  # Solo sobre precio_base (100000 * 5%)
            "expected_pago_prop": 95000  # precio_base - comision (100000 - 5000)
        }
    }
}
