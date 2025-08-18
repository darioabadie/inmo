#!/usr/bin/env python3
"""
Generador de recibos de alquiler en PDF.
Lee el historial generado por historical.py y crea recibos individuales para cada propiedad.
"""

import argparse
import datetime as dt
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

from . import config
from .services.google_sheets import get_gspread_client

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ReciboGenerator:
    """Generador de recibos de alquiler en PDF unificados."""
    
    def __init__(self, mes_periodo: str):
        self.mes_periodo = mes_periodo
        self.output_dir = Path("recibos") / mes_periodo
        
        # Crear carpetas para recibos sin firmar y firmados
        self.output_dir_sin_firmar = self.output_dir / "sin_firmar"
        self.output_dir_firmados = self.output_dir / "firmados"
        
        self.output_dir_sin_firmar.mkdir(parents=True, exist_ok=True)
        self.output_dir_firmados.mkdir(parents=True, exist_ok=True)
        
        # Configuración de estilos
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Dimensiones de página A4
        self.page_width, self.page_height = A4
        
        # Caché de medios de pago para evitar múltiples llamadas a la API
        self._medios_pago_cache = None
        
    def _setup_custom_styles(self):
        """Configura estilos personalizados para los recibos."""
        
        # Estilo para títulos principales
        self.styles.add(ParagraphStyle(
            name='TituloRecibo',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            alignment=1,  # Centrado
            textColor=colors.darkblue
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            textColor=colors.darkblue
        ))
        
        # Estilo para texto normal con espaciado
        self.styles.add(ParagraphStyle(
            name='TextoRecibo',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=4,
            leading=12
        ))
        
        # Estilo para montos importantes
        self.styles.add(ParagraphStyle(
            name='MontoDestacado',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.darkgreen,
            alignment=1,  # Centrado
            spaceAfter=6
        ))
        
        # Estilo para firmas
        self.styles.add(ParagraphStyle(
            name='Firma',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=1,  # Centrado
            spaceAfter=20
        ))

    def _get_membrete_path(self) -> Optional[str]:
        """Obtiene la ruta del archivo de membrete."""
        img_dir = Path(__file__).parent / "img"
        
        # Buscar archivos de imagen comunes
        for ext in ['.png', '.jpg', '.jpeg']:
            for pattern in ['membrete', 'logo', 'Screenshot']:
                membrete_files = list(img_dir.glob(f"{pattern}*{ext}"))
                if membrete_files:
                    return str(membrete_files[0])
        
        return None

    def _get_firma_path(self) -> Optional[str]:
        """Obtiene la ruta del archivo de firma digital."""
        img_dir = Path(__file__).parent / "img"
        firma_path = img_dir / "firma.png"
        
        if firma_path.exists():
            return str(firma_path)
        
        # Buscar otros formatos de firma
        for ext in ['.jpg', '.jpeg', '.png']:
            firma_file = img_dir / f"firma{ext}"
            if firma_file.exists():
                return str(firma_file)
        
        return None

    def _format_currency(self, amount: float) -> str:
        """Formatea un monto como moneda argentina (punto para miles, coma para decimales)."""
        # Formatear con coma para miles primero
        formatted = f"{amount:,.2f}"
        # Intercambiar: coma por punto para miles, punto por coma para decimales
        # Primero reemplazar coma por un placeholder temporal
        formatted = formatted.replace(",", "TEMP")
        # Reemplazar punto por coma (decimales)
        formatted = formatted.replace(".", ",")
        # Reemplazar placeholder por punto (miles)
        formatted = formatted.replace("TEMP", ".")
        return f"$ {formatted}"

    def _format_percentage(self, percentage: str) -> str:
        """Formatea un porcentaje para mostrar."""
        if not percentage or percentage == "":
            return ""
        return f"{percentage}"

    def _calcular_pago_propietario_corregido(self, data: Dict) -> float:
        """
        Calcula el pago correcto al propietario incluyendo servicios adicionales.
        
        Fórmula: precio_descuento - comision_inmo + luz + gas + municipalidad + expensas + cuotas_deposito
        
        Los servicios adicionales y el depósito van al propietario.
        La comisión fraccionada va a la inmobiliaria.
        """
        precio_descuento = float(data.get('precio_descuento', 0))
        comision_inmo = float(data.get('comision_inmo', 0))
        
        # Servicios adicionales que van al propietario
        luz = float(data.get('luz', 0))
        gas = float(data.get('gas', 0))
        municipalidad = float(data.get('municipalidad', 0))
        expensas = float(data.get('expensas', 0))
        
        # Solo el depósito va al propietario (la comisión va a la inmobiliaria)
        cuotas_deposito = float(data.get('cuotas_deposito', 0))
        
        pago_total = precio_descuento - comision_inmo + luz + gas + municipalidad + expensas + cuotas_deposito
        
        return round(pago_total, 2)

    def _cargar_medios_pago(self) -> Dict[str, str]:
        """Carga todos los medios de pago en una sola llamada a la API."""
        if self._medios_pago_cache is not None:
            return self._medios_pago_cache
            
        try:
            logging.info("[CACHE] Cargando medios de pago desde Google Sheets...")
            gc = get_gspread_client()
            sh = gc.open_by_key(config.SHEET_ID)
            ws_admin = sh.worksheet(config.SHEET_MAESTRO)
            registros = ws_admin.get_all_records()
            
            # Crear diccionario de medios de pago
            medios_pago = {}
            for registro in registros:
                nombre_inmueble = registro.get('nombre_inmueble', '')
                medio_pago = str(registro.get('medio_pago', 'efectivo')).lower().strip()
                if nombre_inmueble:
                    medios_pago[nombre_inmueble] = medio_pago
            
            self._medios_pago_cache = medios_pago
            logging.info(f"[CACHE] ✓ Cargados {len(medios_pago)} medios de pago")
            return medios_pago
            
        except Exception as e:
            logging.error(f"Error cargando medios de pago: {e}")
            return {}

    def _obtener_medio_pago(self, nombre_inmueble: str) -> str:
        """Obtiene el medio de pago desde el caché para una propiedad."""
        try:
            medios_pago = self._cargar_medios_pago()
            medio_pago = medios_pago.get(nombre_inmueble, 'efectivo')
            
            if medio_pago == 'efectivo' and nombre_inmueble not in medios_pago:
                logging.warning(f"[CACHE] ✗ No se encontró medio_pago para '{nombre_inmueble}', usando 'efectivo'")
            else:
                logging.debug(f"[CACHE] ✓ {nombre_inmueble} -> {medio_pago}")
                
            return medio_pago
            
        except Exception as e:
            logging.error(f"Error obteniendo medio_pago para {nombre_inmueble}: {e}")
            return 'efectivo'  # Fallback a efectivo

    def _create_recibo_unificado(self, data: Dict, medio_pago: str, incluir_firma: bool = False) -> List:
        """Crea el contenido del recibo unificado según el medio de pago."""
        story = []
        
        # Para efectivo, crear recibo con dos talones sin membrete (van físicamente al local)
        if medio_pago == 'efectivo':
            return self._create_recibo_efectivo_doble_talon(data)
        
        # Para transferencia, mantener formato original con membrete
        membrete_path = self._get_membrete_path()
        if membrete_path and os.path.exists(membrete_path):
            try:
                # Membrete a todo el ancho disponible (entre márgenes)
                img = Image(membrete_path, width=6*inch, height=None)  # height=None mantiene proporciones
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 8))
            except Exception as e:
                logging.warning(f"No se pudo cargar el membrete: {e}")
        
        # Título
        story.append(Paragraph("RECIBO DE ALQUILER", self.styles['TituloRecibo']))
        
        # Información básica
        info_data = [
            ["Dirección:", data.get('dir_inmueble', '')],
            ["Inquilino:", data.get('inquilino', '')],
            ["Propietario:", data.get('propietario', '')],
            ["Mes:", self.mes_periodo],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 12))
        
        # Desglose de pagos
        story.append(Paragraph("DETALLE DEL PAGO", self.styles['Subtitulo']))
        
        desglose_data = []
        
        # Precio original
        precio_original = float(data.get('precio_original', 0))
        desglose_data.append(["Alquiler mensual:", self._format_currency(precio_original)])
        
        # Descuento (solo si aplica)
        descuento = data.get('descuento', '0%')
        if descuento and descuento != '0%' and descuento != '0.0%':
            precio_descuento = float(data.get('precio_descuento', 0))
            descuento_monto = precio_original - precio_descuento
            desglose_data.append(["Descuento:", f"-{self._format_currency(descuento_monto)} ({descuento})"])
        
        # Cuotas adicionales con detalle (solo si aplica)
        cuotas_comision = float(data.get('cuotas_comision', 0))
        cuotas_deposito = float(data.get('cuotas_deposito', 0))
        detalle_cuotas = data.get('detalle_cuotas', '')
        
        if cuotas_comision > 0:
            # Extraer descripción de comisión del detalle
            if 'Comisión inmobiliaria' in detalle_cuotas:
                detalle_comision = detalle_cuotas.split(' + ')[0] if ' + ' in detalle_cuotas else detalle_cuotas
                desglose_data.append([detalle_comision + ":", self._format_currency(cuotas_comision)])
        
        if cuotas_deposito > 0:
            # Extraer descripción de depósito del detalle
            if 'Depósito en garantía' in detalle_cuotas:
                if ' + ' in detalle_cuotas:
                    detalle_deposito = detalle_cuotas.split(' + ')[1] if detalle_cuotas.startswith('Comisión') else detalle_cuotas.split(' + ')[0]
                else:
                    detalle_deposito = detalle_cuotas
                desglose_data.append([detalle_deposito + ":", self._format_currency(cuotas_deposito)])
        
        # Servicios adicionales (solo si aplican)
        municipalidad = float(data.get('municipalidad', 0))
        if municipalidad > 0:
            desglose_data.append(["Municipalidad:", self._format_currency(municipalidad)])
            
        luz = float(data.get('luz', 0))
        if luz > 0:
            desglose_data.append(["Luz:", self._format_currency(luz)])
            
        gas = float(data.get('gas', 0))
        if gas > 0:
            desglose_data.append(["Gas:", self._format_currency(gas)])
            
        expensas = float(data.get('expensas', 0))
        if expensas > 0:
            desglose_data.append(["Expensas:", self._format_currency(expensas)])
        
        # Precio final
        precio_final = float(data.get('precio_final', 0))
        desglose_data.append(["", ""])  # Línea separadora
        desglose_data.append(["TOTAL A PAGAR:", self._format_currency(precio_final)])
        
        desglose_table = Table(desglose_data, colWidths=[2.5*inch, 2*inch])
        desglose_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
            ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),  # Total en negrita
            ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),  # Total en negrita
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),  # Total más grande
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),  # Línea arriba del total
        ]))
        story.append(desglose_table)
        story.append(Spacer(1, 12))
        
        # Lógica condicional según medio de pago
        if medio_pago == 'transferencia':
            story.append(Paragraph("INSTRUCCIONES DE TRANSFERENCIA", self.styles['Subtitulo']))
            
            # Calcular montos para transferencias
            pago_propietario = float(data.get('pago_prop', 0))
            comision_inmo = float(data.get('comision_inmo', 0))
            
            # Solo incluir la comisión fraccionada en la transferencia a la inmobiliaria
            cuotas_comision = float(data.get('cuotas_comision', 0))
            transferencia_inmobiliaria = comision_inmo + cuotas_comision
            
            transferencias_data = [
                [f"Transferir a PROPIETARIO ({data.get('propietario', '')}):", self._format_currency(pago_propietario)],
                ["Transferir a INMOBILIARIA:", self._format_currency(transferencia_inmobiliaria)],
                ["", ""],  # Separador
                ["TOTAL TRANSFERENCIAS:", self._format_currency(precio_final)]
            ]
            
            transferencias_table = Table(transferencias_data, colWidths=[3.5*inch, 1.5*inch])
            transferencias_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
                ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),  # Total en negrita
                ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),  # Total en negrita
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTSIZE', (0, -1), (-1, -1), 11),  # Total un poco más grande
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),  # Línea arriba del total
            ]))
            story.append(transferencias_table)
            
        else:  # efectivo
            story.append(Paragraph("FORMA DE PAGO: EFECTIVO", self.styles['Subtitulo']))
            story.append(Paragraph("Entregar el total en efectivo a la inmobiliaria.", self.styles['TextoRecibo']))
        
        story.append(Spacer(1, 15))
        
        # Información de actualización
        actualizacion = data.get('actualizacion', 'NO')
        if actualizacion == 'SI':
            porc_actual = self._format_percentage(data.get('porc_actual', ''))
            story.append(Paragraph(f"✓ Este mes se aplicó actualización: {porc_actual}", self.styles['TextoRecibo']))
        
        meses_prox_act = data.get('meses_prox_actualizacion', '')
        if meses_prox_act:
            story.append(Paragraph(f"Próxima actualización en: {meses_prox_act} meses", self.styles['TextoRecibo']))
        
        meses_prox_ren = data.get('meses_prox_renovacion', '')
        if meses_prox_ren:
            story.append(Paragraph(f"Meses hasta vencimiento: {meses_prox_ren} meses", self.styles['TextoRecibo']))
        
        story.append(Spacer(1, 8))  # Reducido de 15
        
        # Sección de firmas
        story.append(Paragraph("FIRMAS", self.styles['Subtitulo']))
        
        if incluir_firma:
            # Crear tabla con firma digital para la inmobiliaria
            firma_path = self._get_firma_path()
            
            if firma_path and os.path.exists(firma_path):
                try:
                    # Cargar imagen de firma (más grande)
                    firma_img = Image(firma_path, width=2.4*inch, height=0.8*inch)
                    firma_img.hAlign = 'CENTER'
                    
                    # Crear tabla interna con firma arriba y aclaración abajo, bien separadas
                    firma_content = Table([
                        [firma_img],           # Firma arriba
                        ["Victor Abadie"],     # Aclaración en el medio
                        ["_" * 20]            # Línea abajo
                    ], colWidths=[3*inch], rowHeights=[0.8*inch, 0.25*inch, 0.15*inch])
                    
                    firma_content.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (0, 0), 'BOTTOM'),    # Firma alineada abajo de su celda
                        ('VALIGN', (0, 1), (0, 1), 'BOTTOM'),    # Aclaración alineada abajo de su celda
                        ('VALIGN', (0, 2), (0, 2), 'TOP'),       # Línea alineada arriba de su celda
                        ('FONTSIZE', (0, 1), (0, 1), 10),        # Tamaño para "Victor Abadie"
                        ('FONTNAME', (0, 1), (0, 1), 'Helvetica'), # Nombre normal
                        ('FONTSIZE', (0, 2), (0, 2), 9),         # Tamaño para la línea
                        ('TOPPADDING', (0, 0), (-1, -1), 2),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0)
                    ]))
                    
                    firmas_data = [
                        ["Inquilino (Locatario)", ""],
                        ["_" * 30, firma_content],
                        ["Firma y aclaración", "Firma y aclaración"]
                    ]
                except Exception as e:
                    logging.warning(f"No se pudo cargar la firma digital: {e}")
                    # Fallback a firmas normales
                    firmas_data = [
                        ["Inquilino (Locatario)", "Inmobiliaria"],
                        ["_" * 30, "_" * 30],
                        ["Firma y aclaración", "Firma y aclaración"]
                    ]
            else:
                logging.warning("No se encontró archivo de firma digital en img/firma.png")
                # Fallback a firmas normales
                firmas_data = [
                    ["Inquilino (Locatario)", "Inmobiliaria"],
                    ["_" * 30, "_" * 30],
                    ["Firma y aclaración", "Firma y aclaración"]
                ]
        else:
            # Firmas sin firma digital (recibo sin firmar)
            firmas_data = [
                ["Inquilino (Locatario)", "Inmobiliaria"],
                ["_" * 30, "_" * 30],
                ["Firma y aclaración", "Firma y aclaración"]
            ]
        
        firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch], rowHeights=[0.3*inch, 0.5*inch, 0.3*inch])
        firmas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),  # Reducido de 8
            ('TOPPADDING', (0, 0), (-1, -1), 2),     # Añadido para controlar espacios
        ]))
        story.append(firmas_table)
        
        return story

    def _create_recibo_efectivo_doble_talon(self, data: Dict) -> List:
        """Crea un recibo con dos talones para efectivo (con membrete solo para inquilino)."""
        story = []
        
        # Crear cada talón
        for destinatario in ["INQUILINO", "INMOBILIARIA"]:
            # Agregar membrete solo para el talón del inquilino
            if destinatario == "INQUILINO":
                membrete_path = self._get_membrete_path()
                if membrete_path and os.path.exists(membrete_path):
                    try:
                        # Membrete más pequeño para ahorrar espacio
                        img = Image(membrete_path, width=6*inch, height=1*inch)  # Reducido de 6 a 4 inch
                        img.hAlign = 'CENTER'
                        story.append(img)
                        story.append(Spacer(1, 4))  # Espaciado reducido
                    except Exception as e:
                        logging.warning(f"No se pudo cargar el membrete: {e}")
            # Título del talón
            story.append(Paragraph(f"RECIBO DE ALQUILER - TALÓN PARA {destinatario}", self.styles['TituloRecibo']))
            
            # Información básica en 2 columnas para ahorrar espacio
            info_data = [
                ["Dirección:", data.get('dir_inmueble', ''), "Mes:", self.mes_periodo],
                ["Inquilino:", data.get('inquilino', ''), "Propietario:", data.get('propietario', '')]
            ]
            
            info_table = Table(info_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2.5*inch])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Centrado en todas las celdas
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Primera columna en negrita
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),  # Tercera columna en negrita
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alineación superior
            ]))
            story.append(info_table)
            story.append(Spacer(1, 6))  # Reducido de 8 a 6
            
            # Desglose de pagos (más compacto)
            story.append(Paragraph("DETALLE DEL PAGO", self.styles['Subtitulo']))
            
            desglose_data = []
            
            # Precio original
            precio_original = float(data.get('precio_original', 0))
            desglose_data.append(["Alquiler mensual:", self._format_currency(precio_original)])
            
            # Descuento (solo si aplica)
            descuento = data.get('descuento', '0%')
            if descuento and descuento != '0%' and descuento != '0.0%':
                precio_descuento = float(data.get('precio_descuento', 0))
                descuento_monto = precio_original - precio_descuento
                desglose_data.append(["Descuento:", f"-{self._format_currency(descuento_monto)} ({descuento})"])
            
            # Cuotas adicionales (solo si aplican)
            cuotas_comision = float(data.get('cuotas_comision', 0))
            cuotas_deposito = float(data.get('cuotas_deposito', 0))
            detalle_cuotas = data.get('detalle_cuotas', '')
            
            if cuotas_comision > 0:
                if 'Comisión inmobiliaria' in detalle_cuotas:
                    detalle_comision = detalle_cuotas.split(' + ')[0] if ' + ' in detalle_cuotas else detalle_cuotas
                    desglose_data.append([detalle_comision + ":", self._format_currency(cuotas_comision)])
            
            if cuotas_deposito > 0:
                if 'Depósito en garantía' in detalle_cuotas:
                    if ' + ' in detalle_cuotas:
                        detalle_deposito = detalle_cuotas.split(' + ')[1] if detalle_cuotas.startswith('Comisión') else detalle_cuotas.split(' + ')[0]
                    else:
                        detalle_deposito = detalle_cuotas
                    desglose_data.append([detalle_deposito + ":", self._format_currency(cuotas_deposito)])
            
            # Servicios adicionales (solo si aplican)
            municipalidad = float(data.get('municipalidad', 0))
            if municipalidad > 0:
                desglose_data.append(["Municipalidad:", self._format_currency(municipalidad)])
                
            luz = float(data.get('luz', 0))
            if luz > 0:
                desglose_data.append(["Luz:", self._format_currency(luz)])
                
            gas = float(data.get('gas', 0))
            if gas > 0:
                desglose_data.append(["Gas:", self._format_currency(gas)])
                
            expensas = float(data.get('expensas', 0))
            if expensas > 0:
                desglose_data.append(["Expensas:", self._format_currency(expensas)])
            
            # Precio final
            precio_final = float(data.get('precio_final', 0))
            desglose_data.append(["", ""])  # Línea separadora
            desglose_data.append(["TOTAL A PAGAR:", self._format_currency(precio_final)])
            
            desglose_table = Table(desglose_data, colWidths=[2.5*inch, 2*inch])
            desglose_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
                ('FONTNAME', (0, -1), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTSIZE', (0, -1), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
            ]))
            story.append(desglose_table)
            story.append(Spacer(1, 6))  # Reducido de 8 a 6
            
            # Información de actualización (más compacta)
            actualizacion = data.get('actualizacion', 'NO')
            if actualizacion == 'SI':
                porc_actual = self._format_percentage(data.get('porc_actual', ''))
                story.append(Paragraph(f"✓ Actualización aplicada: {porc_actual}", self.styles['TextoRecibo']))
            
            # Firmas (sin firma digital para talones dobles, más compactas)
            story.append(Paragraph("FIRMAS", self.styles['Subtitulo']))
            firmas_data = [
                ["Inquilino (Locatario)", "Inmobiliaria"],
                ["_" * 30, "_" * 30]
            ]
            
            firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch], rowHeights=[0.3*inch, 0.4*inch])
            firmas_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(firmas_table)
            
            # Separador entre talones (excepto después del último)
            if destinatario == "INQUILINO":
                story.append(Spacer(1, 8))  # Reducido de 10 a 8
                # Línea divisoria
                line_data = [["─" * 100]]
                line_table = Table(line_data, colWidths=[7*inch])
                line_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                ]))
                story.append(line_table)
                story.append(Spacer(1, 12))  # Reducido de 15 a 12
        
        return story

    def _sanitize_filename(self, text: str) -> str:
        """Sanitiza un texto para usarlo como nombre de archivo."""
        # Reemplazar caracteres problemáticos
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '')
        
        # Reemplazar espacios con guiones bajos y limitar longitud
        text = text.replace(' ', '_').strip()
        return text[:50]  # Limitar a 50 caracteres

    def generar_recibo(self, data: Dict) -> Tuple[str, str]:
        """Genera un recibo PDF unificado para una propiedad en ambas versiones."""
        
        # Obtener medio de pago desde la hoja administración
        nombre_inmueble = data.get('nombre_inmueble', '')
        medio_pago = self._obtener_medio_pago(nombre_inmueble)
        
        # Crear nombre del archivo
        propietario = self._sanitize_filename(data.get('propietario', 'Sin_Propietario'))
        inquilino = self._sanitize_filename(data.get('inquilino', 'Sin_Inquilino'))
        filename = f"{propietario}_{inquilino}.pdf"
        
        # Rutas para ambas versiones
        filepath_sin_firmar = self.output_dir_sin_firmar / filename
        filepath_firmado = self.output_dir_firmados / filename
        
        try:
            # Generar versión SIN FIRMAR con márgenes ajustados según medio de pago
            if medio_pago == 'efectivo':
                # Márgenes reducidos para talones dobles
                doc_sin_firmar = SimpleDocTemplate(
                    str(filepath_sin_firmar), 
                    pagesize=A4,
                    topMargin=0.3*inch,     # Reducido de default (1 inch)
                    bottomMargin=0.3*inch,  # Reducido de default (1 inch)
                    leftMargin=0.75*inch,   # Mantenemos márgenes laterales
                    rightMargin=0.75*inch
                )
            else:
                # Márgenes normales para transferencias
                doc_sin_firmar = SimpleDocTemplate(str(filepath_sin_firmar), pagesize=A4)
            
            story_sin_firmar = self._create_recibo_unificado(data, medio_pago, incluir_firma=False)
            doc_sin_firmar.build(story_sin_firmar)
            
            # Para efectivo, NO generar versión firmada (solo talones dobles)
            if medio_pago == 'efectivo':
                logging.info(f"✓ Recibo de efectivo generado (doble talón):")
                logging.info(f"  Sin firmar: {filepath_sin_firmar}")
                return str(filepath_sin_firmar), ""  # Retorna string vacío para firmado
            else:
                # Para transferencia, generar versión FIRMADA
                doc_firmado = SimpleDocTemplate(str(filepath_firmado), pagesize=A4)
                story_firmado = self._create_recibo_unificado(data, medio_pago, incluir_firma=True)
                doc_firmado.build(story_firmado)
                
                logging.info(f"✓ Recibos generados ({medio_pago}):")
                logging.info(f"  Sin firmar: {filepath_sin_firmar}")
                logging.info(f"  Firmado: {filepath_firmado}")
                
                return str(filepath_sin_firmar), str(filepath_firmado)
            
        except Exception as e:
            logging.error(f"Error generando recibos para {filename}: {e}")
            raise


def leer_datos_historico(mes_periodo: str) -> List[Dict]:
    """Lee los datos del historial para el período especificado."""
    
    try:
        gc = get_gspread_client()
        sh = gc.open_by_key(config.SHEET_ID)
        ws_historico = sh.worksheet("historico")
        registros = ws_historico.get_all_records()
        
        # Filtrar registros del período solicitado
        registros_periodo = [
            registro for registro in registros 
            if registro.get('mes_actual', '') == mes_periodo
        ]
        
        logging.info(f"Encontrados {len(registros_periodo)} registros para {mes_periodo}")
        return registros_periodo
        
    except Exception as e:
        logging.error(f"Error leyendo datos del historial: {e}")
        raise


def main():
    """Función principal del generador de recibos."""
    
    parser = argparse.ArgumentParser(description="Genera recibos de alquiler en PDF")
    parser.add_argument(
        "--mes", 
        help="Mes para generar recibos en formato AAAA-MM",
        default=f"{dt.date.today().year}-{dt.date.today().month:02d}"
    )
    
    args = parser.parse_args()
    mes_periodo = args.mes
    
    try:
        # Validar formato del mes
        dt.datetime.strptime(mes_periodo, "%Y-%m")
    except ValueError:
        logging.error("Formato de mes inválido. Use AAAA-MM (ej: 2025-08)")
        return
    
    logging.info(f"Generando recibos para el período: {mes_periodo}")
    
    # Leer datos del historial
    try:
        datos_periodo = leer_datos_historico(mes_periodo)
        if not datos_periodo:
            logging.warning(f"No se encontraron datos para el período {mes_periodo}")
            return
    except Exception as e:
        logging.error(f"Error accediendo a los datos: {e}")
        return
    
    # Crear generador de recibos
    generator = ReciboGenerator(mes_periodo)
    
    # Pre-cargar medios de pago una sola vez
    medios_pago = generator._cargar_medios_pago()
    
    # Generar recibos para cada propiedad
    total_generados = 0
    errores = 0
    contador_medios = {'transferencia': 0, 'efectivo': 0}
    
    for data in datos_periodo:
        try:
            # Obtener medio de pago del caché para estadísticas
            nombre_inmueble = data.get('nombre_inmueble', '')
            medio_pago = medios_pago.get(nombre_inmueble, 'efectivo')
            contador_medios[medio_pago] = contador_medios.get(medio_pago, 0) + 1
            
            generator.generar_recibo(data)
            total_generados += 1
        except Exception as e:
            logging.error(f"Error generando recibo para {data.get('nombre_inmueble', 'Desconocido')}: {e}")
            errores += 1
    
    # Resumen final
    logging.info(f"\n=== RESUMEN ===")
    logging.info(f"Propiedades procesadas: {total_generados}")
    logging.info(f"Medios de pago procesados:")
    for medio, count in contador_medios.items():
        logging.info(f"  {medio}: {count}")
    logging.info(f"Errores: {errores}")
    logging.info(f"Directorios de recibos:")
    logging.info(f"  Sin firmar: {generator.output_dir_sin_firmar.absolute()}")
    logging.info(f"  Firmados: {generator.output_dir_firmados.absolute()}")
    
    print(f"Proceso completado. {total_generados} propiedades procesadas.")
    print(f"Recibos generados en:")
    print(f"  Sin firmar: {generator.output_dir_sin_firmar.absolute()}")
    print(f"  Firmados: {generator.output_dir_firmados.absolute()}")


if __name__ == "__main__":
    main()
