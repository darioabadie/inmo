"""
Servicio para manejo de datos históricos.
Responsable de leer y escribir datos en Google Sheets.
"""
import logging
from typing import Dict, List, Optional

from ..constants import SHEET_CONFIG
from ..domain.historical_models import PropertyHistoricalData, HistoricalRecord
from .. import config
from ..services.google_sheets import get_gspread_client


class HistoricalDataManager:
    """
    Maneja la lectura y escritura de datos históricos en Google Sheets.
    
    Responsabilidades:
    - Leer historial existente de la hoja 'historico'
    - Escribir nuevos registros históricos
    - Cargar datos del maestro desde la hoja 'administracion'
    """
    
    def __init__(self):
        self.gc = get_gspread_client()
        self.sheet = self.gc.open_by_key(config.SHEET_ID)
    
    def read_existing_historical(self) -> Dict[str, PropertyHistoricalData]:
        """
        Lee el sheet 'historico' existente y retorna datos por propiedad.
        
        Returns:
            Dict con estructura: {nombre_inmueble: PropertyHistoricalData}
        """
        try:
            ws_historico = self.sheet.worksheet(SHEET_CONFIG["historico_sheet_name"])
            registros_existentes = ws_historico.get_all_records()
            
            historico_por_propiedad = {}
            
            for registro in registros_existentes:
                nombre = str(registro.get("nombre_inmueble", ""))
                mes = str(registro.get("mes_actual", ""))
                # Intentar leer precio_original primero, si no existe usar precio_base (compatibilidad)
                precio_base = float(registro.get("precio_original", 0)) or float(registro.get("precio_base", 0))
                
                if nombre not in historico_por_propiedad:
                    historico_por_propiedad[nombre] = PropertyHistoricalData(
                        nombre_propiedad=nombre,
                        ultimo_mes=mes,
                        ultimo_precio_base=precio_base,
                        registros_existentes=[]
                    )
                
                # Mantener el último mes cronológicamente
                if mes > historico_por_propiedad[nombre].ultimo_mes:
                    historico_por_propiedad[nombre].ultimo_mes = mes
                    historico_por_propiedad[nombre].ultimo_precio_base = precio_base
                
                historico_por_propiedad[nombre].registros_existentes.append(registro)
            
            logging.warning(f"[HISTORICO] Se encontraron {len(registros_existentes)} registros históricos")
            return historico_por_propiedad
            
        except Exception as e:
            logging.warning(f"[HISTORICO] No se pudo leer historico existente: {e}")
            return {}

    def reset_historical_sheet(self) -> None:
        """Elimina la hoja 'historico' si existe para regenerar desde cero."""
        sheet_name = SHEET_CONFIG["historico_sheet_name"]

        try:
            ws_historico = self.sheet.worksheet(sheet_name)
            self.sheet.del_worksheet(ws_historico)
            logging.warning(f"[HISTORICO] Hoja '{sheet_name}' eliminada para regenerar desde cero")
        except Exception as e:
            logging.warning(f"[HISTORICO] No se pudo eliminar hoja '{sheet_name}': {e}")
    
    def write_historical_records(self, records: List[HistoricalRecord]) -> None:
        """
        Escribe registros históricos en la hoja 'historico'.
        
        Args:
            records: Lista de registros históricos a escribir
        """
        sheet_name = SHEET_CONFIG["historico_sheet_name"]
        
        try:
            # Intentar crear la hoja si no existe
            self.sheet.add_worksheet(
                title=sheet_name, 
                rows=len(records) + 10, 
                cols=SHEET_CONFIG["expected_columns"]
            )
            logging.warning(f"[SHEET] Creada nueva hoja '{sheet_name}'")
        except Exception:
            logging.warning(f"[SHEET] Hoja '{sheet_name}' ya existe, se sobrescribirá")
        
        ws_historico = self.sheet.worksheet(sheet_name)
        ws_historico.clear()
        
        if records:
            # Convertir records a diccionarios y ordenar
            records_dict = [record.to_dict() for record in records]
            records_dict.sort(key=lambda x: (x['nombre_inmueble'], x['mes_actual']))
            
            # Escribir headers y datos
            headers = list(records_dict[0].keys())
            datos = [list(r.values()) for r in records_dict]
            ws_historico.update([headers] + datos)
            
            logging.warning(f"[SHEET] Escritos {len(records)} registros en '{sheet_name}'")
    
    def load_maestro_data(self) -> List[Dict]:
        """
        Carga los datos del maestro desde Google Sheets.
        
        Returns:
            Lista de diccionarios con los datos de cada propiedad
        """
        try:
            # Usar el nombre de sheet configurado en config o el por defecto
            sheet_name = getattr(config, 'SHEET_MAESTRO', SHEET_CONFIG["maestro_sheet_name"])
            ws = self.sheet.worksheet(sheet_name)
            maestro = ws.get_all_records()
            
            logging.warning(f"[MAESTRO] Cargados {len(maestro)} registros desde '{sheet_name}'")
            return maestro
            
        except Exception as e:
            logging.error(f"[MAESTRO] Error cargando datos del maestro: {e}")
            raise
    
    def property_exists_in_historical(self, nombre_propiedad: str) -> bool:
        """
        Verifica si una propiedad ya tiene registros históricos.
        
        Args:
            nombre_propiedad: Nombre de la propiedad a verificar
            
        Returns:
            True si la propiedad tiene registros históricos
        """
        historico = self.read_existing_historical()
        return nombre_propiedad in historico and historico[nombre_propiedad].tiene_historico
    
    def get_last_price_for_property(self, nombre_propiedad: str) -> Optional[float]:
        """
        Obtiene el último precio base registrado para una propiedad.
        
        Args:
            nombre_propiedad: Nombre de la propiedad
            
        Returns:
            Último precio base o None si no hay registros
        """
        historico = self.read_existing_historical()
        if nombre_propiedad in historico:
            return historico[nombre_propiedad].ultimo_precio_base
        return None
