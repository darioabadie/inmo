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
    """Generador de recibos de alquiler en PDF con secciones para inquilino y propietario."""
    
    def __init__(self, mes_periodo: str):
        self.mes_periodo = mes_periodo
        self.output_dir = Path("recibos") / mes_periodo
        
        # Crear carpetas separadas para inquilino y propietario
        self.inquilino_dir = self.output_dir / "inquilino"
        self.propietario_dir = self.output_dir / "propietario"
        
        self.inquilino_dir.mkdir(parents=True, exist_ok=True)
        self.propietario_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración de estilos
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        # Dimensiones de página A4
        self.page_width, self.page_height = A4
        
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

    def _create_inquilino_section(self, data: Dict) -> List:
        """Crea el contenido de la sección del inquilino."""
        story = []
        
        # Membrete
        membrete_path = self._get_membrete_path()
        if membrete_path and os.path.exists(membrete_path):
            try:
                img = Image(membrete_path, width=4*inch, height=1*inch)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 8))
            except Exception as e:
                logging.warning(f"No se pudo cargar el membrete: {e}")
        
        # Título
        story.append(Paragraph("RECIBO DE ALQUILER - INQUILINO", self.styles['TituloRecibo']))
        
        # Información básica
        info_data = [
            ["Dirección:", data.get('dir_inmueble', '')],
            ["Inquilino:", data.get('inquilino', '')],
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
        desglose_data.append(["Precio original:", self._format_currency(precio_original)])
        
        # Descuento (solo si aplica)
        descuento = data.get('descuento', '0%')
        if descuento and descuento != '0%' and descuento != '0.0%':
            precio_descuento = float(data.get('precio_descuento', 0))
            descuento_monto = precio_original - precio_descuento
            desglose_data.append(["Descuento:", f"-{self._format_currency(descuento_monto)} ({descuento})"])
            desglose_data.append(["Subtotal con descuento:", self._format_currency(precio_descuento)])
        
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
        
        story.append(Spacer(1, 15))
        
        # Sección de firmas
        story.append(Paragraph("FIRMAS", self.styles['Subtitulo']))
        
        firmas_data = [
            ["Inquilino (Locatario)", "Inmobiliaria"],
            ["_" * 30, "_" * 30],
            ["", ""],
            ["Firma y aclaración", "Firma y aclaración"]
        ]
        
        firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch])
        firmas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(firmas_table)
        
        return story

    def _create_propietario_section(self, data: Dict) -> List:
        """Crea el contenido de la sección del propietario."""
        story = []
        
        # Membrete
        membrete_path = self._get_membrete_path()
        if membrete_path and os.path.exists(membrete_path):
            try:
                img = Image(membrete_path, width=4*inch, height=1*inch)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 8))
            except Exception as e:
                logging.warning(f"No se pudo cargar el membrete: {e}")
        
        # Título
        story.append(Paragraph("RECIBO DE ALQUILER - PROPIETARIO", self.styles['TituloRecibo']))
        
        # Información básica
        info_data = [
            ["Dirección:", data.get('dir_inmueble', '')],
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
        
        # Desglose completo para propietario
        story.append(Paragraph("LIQUIDACIÓN DEL PROPIETARIO", self.styles['Subtitulo']))
        
        liquidacion_data = []
        
        # Ingresos
        precio_original = float(data.get('precio_original', 0))
        precio_descuento = float(data.get('precio_descuento', 0))
        
        liquidacion_data.append(["INGRESOS:", ""])
        liquidacion_data.append(["Precio base actualizado:", self._format_currency(precio_original)])
        
        # Mostrar descuento si aplica
        descuento = data.get('descuento', '0%')
        if descuento and descuento != '0%' and descuento != '0.0%':
            descuento_monto = precio_original - precio_descuento
            liquidacion_data.append(["Descuento aplicado:", f"-{self._format_currency(descuento_monto)} ({descuento})"])
            liquidacion_data.append(["Base para comisión:", self._format_currency(precio_descuento)])
        else:
            liquidacion_data.append(["Base para comisión:", self._format_currency(precio_descuento)])
        
        liquidacion_data.append(["", ""])  # Separador
        
        # Deducciones
        liquidacion_data.append(["DEDUCCIONES:", ""])
        comision_inmo = float(data.get('comision_inmo', 0))
        liquidacion_data.append(["Comisión inmobiliaria:", f"-{self._format_currency(comision_inmo)}"])
        
        liquidacion_data.append(["", ""])  # Separador
        
        # Servicios adicionales que recibe el propietario
        liquidacion_data.append(["SERVICIOS ADICIONALES:", ""])
        
        luz = float(data.get('luz', 0))
        if luz > 0:
            liquidacion_data.append(["Luz:", self._format_currency(luz)])
            
        gas = float(data.get('gas', 0))
        if gas > 0:
            liquidacion_data.append(["Gas:", self._format_currency(gas)])
            
        municipalidad = float(data.get('municipalidad', 0))
        if municipalidad > 0:
            liquidacion_data.append(["Municipalidad:", self._format_currency(municipalidad)])
            
        expensas = float(data.get('expensas', 0))
        if expensas > 0:
            liquidacion_data.append(["Expensas:", self._format_currency(expensas)])
            
        # Solo mostrar depósito (no comisión, que va a la inmobiliaria)
        cuotas_deposito = float(data.get('cuotas_deposito', 0))
        detalle_cuotas = data.get('detalle_cuotas', '')
        if cuotas_deposito > 0 and 'Depósito en garantía' in detalle_cuotas:
            # Extraer descripción de depósito del detalle
            if ' + ' in detalle_cuotas:
                detalle_deposito = detalle_cuotas.split(' + ')[1] if detalle_cuotas.startswith('Comisión') else detalle_cuotas.split(' + ')[0]
            else:
                detalle_deposito = detalle_cuotas
            liquidacion_data.append([detalle_deposito + ":", self._format_currency(cuotas_deposito)])
        
        liquidacion_data.append(["", ""])  # Separador
        
        # Total a recibir (usar cálculo corregido)
        pago_prop = self._calcular_pago_propietario_corregido(data)
        liquidacion_data.append(["TOTAL A RECIBIR:", self._format_currency(pago_prop)])
        
        liquidacion_table = Table(liquidacion_data, colWidths=[3*inch, 2*inch])
        liquidacion_table.setStyle(TableStyle([
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
        story.append(liquidacion_table)
        story.append(Spacer(1, 12))
        
        # Información adicional (igual que para inquilino)
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
        
        story.append(Spacer(1, 10))
        
        # Sección de firmas (igual que para inquilino)
        story.append(Paragraph("FIRMAS", self.styles['Subtitulo']))
        
        firmas_data = [
            ["Propietario (Locador)", "Inmobiliaria"],
            ["_" * 30, "_" * 30],
            ["", ""],
            ["Firma y aclaración", "Firma y aclaración"]
        ]
        
        firmas_table = Table(firmas_data, colWidths=[3*inch, 3*inch])
        firmas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(firmas_table)
        
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

    def generar_recibo_inquilino(self, data: Dict) -> str:
        """Genera un recibo PDF completo solo para el inquilino."""
        
        # Crear nombre del archivo
        propietario = self._sanitize_filename(data.get('propietario', 'Sin_Propietario'))
        inquilino = self._sanitize_filename(data.get('inquilino', 'Sin_Inquilino'))
        filename = f"{propietario}_{inquilino}.pdf"
        filepath = self.inquilino_dir / filename
        
        # Crear documento PDF simple
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        
        # Crear contenido completo para inquilino
        story = self._create_inquilino_section(data)
        
        # Generar PDF
        try:
            doc.build(story)
            logging.info(f"✓ Recibo inquilino generado: {filepath}")
            return str(filepath)
        except Exception as e:
            logging.error(f"Error generando recibo inquilino para {filename}: {e}")
            raise

    def generar_recibo_propietario(self, data: Dict) -> str:
        """Genera un recibo PDF completo solo para el propietario."""
        
        # Crear nombre del archivo
        propietario = self._sanitize_filename(data.get('propietario', 'Sin_Propietario'))
        inquilino = self._sanitize_filename(data.get('inquilino', 'Sin_Inquilino'))
        filename = f"{propietario}_{inquilino}.pdf"
        filepath = self.propietario_dir / filename
        
        # Crear documento PDF simple
        doc = SimpleDocTemplate(str(filepath), pagesize=A4)
        
        # Crear contenido completo para propietario
        story = self._create_propietario_section(data)
        
        # Generar PDF
        try:
            doc.build(story)
            logging.info(f"✓ Recibo propietario generado: {filepath}")
            return str(filepath)
        except Exception as e:
            logging.error(f"Error generando recibo propietario para {filename}: {e}")
            raise

    def generar_recibos(self, data: Dict) -> Tuple[str, str]:
        """Genera ambos recibos (inquilino y propietario) para una propiedad."""
        inquilino_path = self.generar_recibo_inquilino(data)
        propietario_path = self.generar_recibo_propietario(data)
        return inquilino_path, propietario_path


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
    
    # Generar recibos para cada propiedad
    total_generados = 0
    errores = 0
    
    for data in datos_periodo:
        try:
            generator.generar_recibos(data)
            total_generados += 1
        except Exception as e:
            logging.error(f"Error generando recibos para {data.get('nombre_inmueble', 'Desconocido')}: {e}")
            errores += 1
    
    # Resumen final
    logging.info(f"\n=== RESUMEN ===")
    logging.info(f"Propiedades procesadas: {total_generados}")
    logging.info(f"Errores: {errores}")
    logging.info(f"Directorio inquilinos: {generator.inquilino_dir.absolute()}")
    logging.info(f"Directorio propietarios: {generator.propietario_dir.absolute()}")
    
    print(f"Proceso completado. {total_generados} propiedades procesadas.")
    print(f"Recibos inquilinos en: {generator.inquilino_dir.absolute()}")
    print(f"Recibos propietarios en: {generator.propietario_dir.absolute()}")


if __name__ == "__main__":
    main()
