"""
Servicio principal para generación del historial completo.
Orquesta todos los componentes y maneja el flujo principal de procesamiento.
"""
import datetime as dt
import logging
from typing import List, Dict

from ..constants import DEFAULT_VALUES, REQUIRED_FIELDS
from ..domain.historical_models import HistoricalRecord, HistoricalSummary, PropertyHistoricalData
from ..models import Propiedad, Contrato
from .historical_data import HistoricalDataManager
from .record_generator import MonthlyRecordGenerator
from .historical_calculations import HistoricalCalculations
from ..services.inflation import traer_inflacion


class HistoricalService:
    """
    Servicio principal para generación del historial completo.
    
    Responsabilidades:
    - Orquestar el proceso completo de generación del historial
    - Manejar la lógica de continuación incremental
    - Procesar múltiples propiedades
    - Generar resúmenes y estadísticas
    """
    
    def __init__(self):
        self.data_manager = HistoricalDataManager()
        self.record_generator = MonthlyRecordGenerator()
        self.calculations = HistoricalCalculations()
        self.summary = HistoricalSummary()
    
    def generate_historical_until(self, fecha_limite: dt.date) -> HistoricalSummary:
        """
        Genera el historial completo hasta la fecha límite especificada.
        
        Args:
            fecha_limite: Fecha límite hasta donde generar el historial
            
        Returns:
            HistoricalSummary con estadísticas del procesamiento
        """
        self.summary = HistoricalSummary(fecha_limite=fecha_limite)
        
        # Cargar datos necesarios
        logging.warning("[INICIO] Cargando datos del maestro...")
        maestro_data = self.data_manager.load_maestro_data()
        
        logging.warning("[INICIO] Cargando datos de inflación...")
        inflacion_df = traer_inflacion()
        
        logging.warning("[INICIO] Leyendo historial existente...")
        historico_existente = self.data_manager.read_existing_historical()
        
        # Procesar cada propiedad
        todos_los_registros = []
        
        for fila in maestro_data:
            try:
                registros_propiedad = self.process_property(fila, fecha_limite, inflacion_df, historico_existente)
                todos_los_registros.extend(registros_propiedad)
                self.summary.incrementar_procesada()
                self.summary.add_registros(len(registros_propiedad))
                
            except Exception as e:
                nombre_propiedad = fila.get("nombre_inmueble", "Desconocido")
                self.summary.add_error(nombre_propiedad, str(e))
                self.summary.incrementar_omitida()
                logging.warning(f"[ERROR] {nombre_propiedad}: {e}")
        
        # Escribir resultados
        if todos_los_registros:
            logging.warning("[ESCRITURA] Escribiendo registros en Google Sheets...")
            self.data_manager.write_historical_records(todos_los_registros)
        
        return self.summary
    
    def process_property(self, 
                        property_data: Dict, 
                        fecha_limite: dt.date, 
                        inflacion_df,
                        historico_existente: Dict[str, PropertyHistoricalData]) -> List[HistoricalRecord]:
        """
        Procesa una propiedad individual generando todos sus registros faltantes.
        
        Args:
            property_data: Datos de la propiedad del maestro
            fecha_limite: Fecha límite hasta donde generar
            inflacion_df: DataFrame con datos de inflación
            historico_existente: Diccionario con datos históricos existentes
            
        Returns:
            Lista de HistoricalRecord generados para la propiedad
        """
        # 1. Validar y crear entidades
        propiedad, contrato = self._create_entities_from_data(property_data)
        
        # 2. Validar fechas
        fecha_inicio_dt = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
        if fecha_inicio_dt > fecha_limite:
            raise ValueError(f"Contrato inicia después de fecha límite: {fecha_inicio_dt}")
        
        # 3. Extraer servicios adicionales
        servicios = self._extract_additional_services(property_data)
        
        # 4. Determinar punto de partida
        registros_existentes, precio_base_inicial, fecha_inicial = self._determine_starting_point(
            propiedad, contrato, historico_existente
        )
        
        # 5. Generar registros faltantes
        nuevos_registros = self._generate_missing_months(
            propiedad, contrato, fecha_inicial, fecha_limite, 
            precio_base_inicial, inflacion_df, **servicios
        )
        
        # 6. Combinar registros existentes + nuevos
        todos_los_registros = registros_existentes + nuevos_registros
        
        logging.warning(f"[PROCESADO] {propiedad.nombre}: {len(nuevos_registros)} nuevos registros")
        
        return todos_los_registros
    
    def _create_entities_from_data(self, data: Dict) -> tuple:
        """Crea entidades Propiedad y Contrato desde los datos del maestro."""
        # Validar campos obligatorios
        for field in REQUIRED_FIELDS:
            if field not in data or not data[field]:
                raise ValueError(f"Campo obligatorio faltante: {field}")
        
        propiedad = Propiedad(
            nombre=str(data["nombre_inmueble"]),
            direccion=str(data["dir_inmueble"]),
            propietario=str(data["propietario"]),
            inquilino=str(data["inquilino"])
        )
        
        contrato = Contrato(
            fecha_inicio=str(data["fecha_inicio_contrato"]),
            duracion_meses=int(data["duracion_meses"]),
            precio_original=float(data["precio_original"]),
            actualizacion=str(data["actualizacion"]),
            indice=str(data["indice"]),
            comision_inmo=str(data["comision_inmo"]),
            comision=str(data.get("comision", DEFAULT_VALUES["comision"])),
            deposito=str(data.get("deposito", DEFAULT_VALUES["deposito"]))
        )
        
        return propiedad, contrato
    
    def _extract_additional_services(self, data: Dict) -> Dict:
        """Extrae servicios adicionales de los datos del maestro."""
        def safe_float(value, default=0.0):
            if value and str(value).strip():
                return float(value)
            return default
        
        def safe_percentage(value, default=0.0):
            if value and str(value).strip():
                return float(str(value).replace('%', '').replace(',', '.').strip())
            return default
        
        return {
            "municipalidad": safe_float(data.get("municipalidad")),
            "luz": safe_float(data.get("luz")),
            "gas": safe_float(data.get("gas")),
            "expensas": safe_float(data.get("expensas")),
            "descuento_porcentaje": safe_percentage(data.get("descuento"))
        }
    
    def _determine_starting_point(self, 
                                 propiedad: Propiedad, 
                                 contrato: Contrato,
                                 historico_existente: Dict[str, PropertyHistoricalData]) -> tuple:
        """
        Determina el punto de partida para generar registros.
        
        Returns:
            Tuple[registros_existentes, precio_base_inicial, fecha_inicial]
        """
        if propiedad.nombre in historico_existente:
            # Continuar desde donde se quedó
            info_historico = historico_existente[propiedad.nombre]
            registros_existentes = [HistoricalRecord(**r) for r in info_historico.registros_existentes]
            precio_base_inicial = info_historico.ultimo_precio_base
            
            # Calcular fecha inicial (mes siguiente al último registrado)
            ultima_fecha = info_historico.ultima_fecha
            if ultima_fecha:
                if ultima_fecha.month == 12:
                    fecha_inicial = dt.date(ultima_fecha.year + 1, 1, 1)
                else:
                    fecha_inicial = dt.date(ultima_fecha.year, ultima_fecha.month + 1, 1)
            else:
                fecha_inicial = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
            
            logging.warning(f"[CONTINUACIÓN] {propiedad.nombre}: desde {info_historico.ultimo_mes} con precio_base {precio_base_inicial}")
        else:
            # Empezar desde el principio
            registros_existentes = []
            precio_base_inicial = contrato.precio_original
            fecha_inicial = dt.datetime.strptime(contrato.fecha_inicio, "%Y-%m-%d").date()
            
            logging.warning(f"[NUEVO] {propiedad.nombre}: desde inicio con precio_base {precio_base_inicial}")
        
        return registros_existentes, precio_base_inicial, fecha_inicial
    
    def _generate_missing_months(self,
                                propiedad: Propiedad,
                                contrato: Contrato,
                                fecha_inicial: dt.date,
                                fecha_limite: dt.date,
                                precio_base_inicial: float,
                                inflacion_df,
                                **servicios) -> List[HistoricalRecord]:
        """Genera todos los registros mensuales faltantes."""
        registros = []
        fecha_actual = fecha_inicial
        precio_base_actual = precio_base_inicial
        
        while fecha_actual <= fecha_limite:
            # Crear contexto para este mes
            context = self.record_generator.create_context_for_month(
                propiedad=propiedad,
                contrato=contrato,
                fecha_actual=fecha_actual,
                precio_base_actual=precio_base_actual,
                inflacion_df=inflacion_df,
                **servicios
            )
            
            # Validar contexto
            if not self.record_generator.validate_context(context):
                break
            
            # Generar registro mensual
            registro = self.record_generator.generate_monthly_record(context)
            registros.append(registro)
            
            # Actualizar precio base para el próximo mes
            precio_base_actual = registro.precio_original
            
            # Avanzar al siguiente mes
            fecha_actual = self.calculations.get_next_month_date(fecha_actual)
        
        return registros
