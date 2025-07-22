from odoo import models, _
from PyPDF2 import PdfFileReader, PdfFileWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import base64
from reportlab.lib.utils import ImageReader

class HrContractWatermark(models.Model):
    _inherit = 'hr.contract'

    from reportlab.lib.utils import ImageReader

    def crear_marca_agua(self, company_logo):
        logo_data = base64.b64decode(company_logo)
        logo_stream = BytesIO(logo_data)

        watermark_stream = BytesIO()
        c = canvas.Canvas(watermark_stream, pagesize=letter)
        page_width, page_height = letter

        image = ImageReader(logo_stream)
        img_width, img_height = image.getSize()

        # Máximo tamaño permitido para la marca de agua
        max_width, max_height = 717, 365  # Ajusta estos valores si es necesario

        # Calcular el factor de escalado para mantener la relación de aspecto
        scale = min(max_width / img_width, max_height / img_height)

        image_width = img_width * scale
        image_height = img_height * scale

        x = (page_width - image_width) / 2
        y = (page_height - image_height) / 2

        # Configurar la transparencia (0.0 es completamente transparente, 1.0 es opaco)
        c.setFillAlpha(0)

        c.drawImage(image, x, y, width=image_width, height=image_height)
        c.save()
        watermark_stream.seek(0)
        return PdfFileReader(watermark_stream)

    def aplicar_marca_agua(self, pdf_data, watermark_pdf):
        pdf_reader = PdfFileReader(BytesIO(pdf_data))
        pdf_writer = PdfFileWriter()

        watermark_page = watermark_pdf.getPage(0)

        for page_num in range(pdf_reader.numPages):
            original_page = pdf_reader.getPage(page_num)

            # Mezclar la marca de agua con la página original
            original_page.mergePage(watermark_page)

            # Añadir la página combinada al pdf_writer
            pdf_writer.addPage(original_page)

        output_stream = BytesIO()
        pdf_writer.write(output_stream)
        return output_stream.getvalue()

    def compute_contract_format(self):
        original_pdf_data = super(HrContractWatermark, self).compute_contract_format()
        
        company_logo = self.employee_id.company_id.logo
        
        if not company_logo:
            raise ValueError("No Existe Logo")

        watermark_pdf = self.crear_marca_agua(company_logo)
        pdf_with_watermark = self.aplicar_marca_agua(original_pdf_data, watermark_pdf)
        
        self.pdf_binary = base64.b64encode(pdf_with_watermark)
        return pdf_with_watermark
