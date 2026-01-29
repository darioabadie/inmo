"""
Servicio principal para generación del historial completo.
Orquesta todos los componentes y maneja el flujo principal de procesamiento.
"""
import datetime as dt
import logging
import os
from typing import List, Dict, Optional

try:
    from dateutil.relativedelta import relativedelta
except ImportError:
    # Implementación simple de relativedelta para manejar meses
    class relativedelta:
        def __init__(self, months=0, days=0):
            self.months = months
            self.days = days
        
        def __radd__(self, date):
            # Añadir meses
            year = date.year + (date.month - 1 + self.months) // 12
            month = (date.month - 1 + self.months) % 12 + 1
            day = date.day
            
            # Ajustar día si el mes tiene menos días
            import calendar
            max_day = calendar.monthrange(year, month)[1]
            if day > max_day:
                day = max_day
            
            result = dt.date(year, month, day)
            
            # Añadir días
            if self.days != 0:
                result = result + dt.timedelta(days=self.days)
            
            return result

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
    
    def __init__(self, error_logger: Optional[logging.Logger] = None):
        self.data_manager = HistoricalDataManager()
        self.record_generator = MonthlyRecordGenerator()
        self.calculations = HistoricalCalculations()
        self.summary = HistoricalSummary()
        self.error_logger = error_logger
    
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
        
        # Analizar estado de contratos
        fecha_actual = dt.date.today()
        self.analyze_contracts_status(fecha_limite, fecha_actual)
        
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
                error_msg = str(e)
                
                # Agregar al resumen
                self.summary.add_error(nombre_propiedad, error_msg)
                self.summary.incrementar_omitida()
                
                # Log a consola (como antes)
                logging.warning(f"[ERROR] {nombre_propiedad}: {e}")
                
                # Log detallado al archivo si está configurado
                if self.error_logger:
                    # Información adicional para el log de archivo
                    inquilino = fila.get("inquilino", "N/A")
                    fecha_inicio = fila.get("fecha_inicio_contrato", "N/A")
                    precio_original = fila.get("precio_original", "N/A")
                    
                    self.error_logger.error(
                        f"Propiedad: {nombre_propiedad} | "
                        f"Inquilino: {inquilino} | "
                        f"Fecha inicio: {fecha_inicio} | "
                        f"Precio original: {precio_original} | "
                        f"Error: {error_msg}"
                    )
        
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
            if field not in data or data[field] is None or (isinstance(data[field], str) and data[field].strip() == ""):
                raise ValueError(f"Campo obligatorio faltante: {field}")
        
        propiedad = Propiedad(
            nombre=str(data["nombre_inmueble"]),
            direccion=str(data["dir_inmueble"]),
            propietario=str(data["propietario"]),
            inquilino=str(data["inquilino"]),
            nis=str(data.get("N_NIS") or "0"),
            gas_nro=str(data.get("N_GAS") or "0"),
            padron=str(data.get("N_PADRON") or "0")
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
            "descuento_porcentaje": safe_percentage(data.get("descuento")),
            "monto_comision": safe_float(data.get("monto_comision"), default=None)
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
    
    def analyze_contracts_status(self, fecha_limite: dt.date, fecha_actual: dt.date):
        """
        Analiza el estado de todos los contratos y actualiza el summary.
        
        Args:
            fecha_limite: Fecha límite del procesamiento histórico
            fecha_actual: Fecha actual para determinar estado de contratos
        """
        logging.warning("[CONTRATOS] Analizando estado de contratos...")
        
        # Cargar datos del maestro para análisis de contratos
        maestro_data = self.data_manager.load_maestro_data()
        
        # Fecha límite para contratos próximos a vencer (3 meses desde fecha_actual)
        fecha_limite_proximos = fecha_actual + relativedelta(months=3)
        
        for fila in maestro_data:
            try:
                status, detalle = self._determine_contract_status(fila, fecha_actual, fecha_limite_proximos)
                
                if status == "VENCIDO":
                    self.summary.add_contract_vencido(detalle)
                elif status == "PROXIMO_VENCER":
                    self.summary.add_contract_proximo_vencer(detalle)
                    
            except Exception as e:
                nombre_propiedad = fila.get("nombre_inmueble", "Desconocido")
                logging.warning(f"[ERROR CONTRATO] No se pudo analizar {nombre_propiedad}: {e}")
        
        # Generar archivo de resumen si hay contratos relevantes
        if (self.summary.contratos_vencidos > 0 or self.summary.contratos_proximos_vencer > 0):
            self._save_contract_summary_file(fecha_actual)
        
        logging.warning(f"[CONTRATOS] Análisis completado: {self.summary.contratos_vencidos} vencidos, {self.summary.contratos_proximos_vencer} próximos a vencer")
    
    def _determine_contract_status(self, fila: Dict, fecha_actual: dt.date, fecha_limite_proximos: dt.date) -> tuple:
        """
        Determina el estado de un contrato y retorna el detalle básico.
        
        Args:
            fila: Datos del contrato del maestro
            fecha_actual: Fecha actual
            fecha_limite_proximos: Fecha límite para considerar "próximo a vencer"
            
        Returns:
            Tuple[status, detalle_basico] donde status puede ser "VENCIDO", "PROXIMO_VENCER" o "ACTIVO"
        """
        # Validar campos obligatorios
        if not fila.get("nombre_inmueble") or not fila.get("fecha_inicio_contrato") or not fila.get("duracion_meses"):
            return "ACTIVO", {}  # No se puede determinar, tratar como activo
        
        # Calcular fecha de vencimiento
        fecha_inicio = dt.datetime.strptime(fila["fecha_inicio_contrato"], "%Y-%m-%d").date()
        duracion = int(fila["duracion_meses"])
        
        # Restar 1 día porque el último día del contrato no cuenta
        fecha_vencimiento = fecha_inicio + relativedelta(months=duracion) - dt.timedelta(days=1)
        
        # Determinar estado
        if fecha_vencimiento <= fecha_actual:
            status = "VENCIDO"
        elif fecha_vencimiento <= fecha_limite_proximos:
            status = "PROXIMO_VENCER"
        else:
            status = "ACTIVO"
        
        # Crear detalle básico
        detalle = {
            'nombre_inmueble': str(fila.get("nombre_inmueble", "")),
            'inquilino': str(fila.get("inquilino", "")),
            'fecha_vencimiento': fecha_vencimiento.strftime("%Y-%m-%d")
        }
        
        return status, detalle
    
    def _save_contract_summary_file(self, fecha_actual: dt.date):
        """
        Guarda el resumen de contratos en un archivo de texto.
        
        Args:
            fecha_actual: Fecha actual para nombrar el archivo
        """
        filename = f"resumen_contratos_{fecha_actual.strftime('%Y-%m-%d')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"RESUMEN DE CONTRATOS - {fecha_actual.strftime('%Y-%m-%d')}\n")
                f.write("=" * 55 + "\n\n")
                
                # Contratos vencidos
                if self.summary.contratos_vencidos > 0:
                    f.write(f"CONTRATOS VENCIDOS: {self.summary.contratos_vencidos}\n")
                    f.write("-" * 20 + "\n")
                    for contrato in self.summary.detalle_contratos_vencidos:
                        f.write(f"- {contrato['nombre_inmueble']} ({contrato['inquilino']}) - Venció: {contrato['fecha_vencimiento']}\n")
                    f.write("\n")
                
                # Contratos próximos a vencer
                if self.summary.contratos_proximos_vencer > 0:
                    f.write(f"CONTRATOS POR VENCER (próximos 3 meses): {self.summary.contratos_proximos_vencer}\n")
                    f.write("-" * 50 + "\n")
                    for contrato in self.summary.detalle_contratos_proximos_vencer:
                        f.write(f"- {contrato['nombre_inmueble']} ({contrato['inquilino']}) - Vence: {contrato['fecha_vencimiento']}\n")
                    f.write("\n")
                
                # Total de propiedades analizadas
                total_analizadas = self.summary.contratos_vencidos + self.summary.contratos_proximos_vencer
                f.write(f"TOTAL PROPIEDADES CON CONTRATOS RELEVANTES: {total_analizadas}\n")
            
            logging.warning(f"[CONTRATOS] Resumen guardado en: {filename}")
            
        except Exception as e:
            logging.error(f"[ERROR] No se pudo guardar el archivo de resumen: {e}")
            if self.error_logger:
                self.error_logger.error(f"Error guardando resumen de contratos: {e}")
