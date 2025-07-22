# -*- coding: utf-8 -*-
try:
   import qrcode
except ImportError:
   qrcode = None
try:
   import base64
except ImportError:
   base64 = None
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime

class StockPicking(models.Model): 
    _inherit = "stock.picking"

    qr_code = fields.Binary('QRcode', compute="_generate_qr")

    def _generate_qr(self):
        for rec in self:
            if qrcode and base64:                
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                qr.add_data(str(rec.company_id.vat)+"|")
                # qr.add_data(str(rec.l10n_latam_document_type_id.code)+"|")
                # Formatear date_done para incluir solo la fecha
                date_done = rec.date_done.strftime('%Y-%m-%d') if isinstance(rec.date_done, datetime) else rec.date_done
                qr.add_data(str(date_done)+"|")
                qr.add_data(str(rec.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code)+"|")
                qr.add_data(str(rec.partner_id.vat)+"|") 
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code':qr_image})
            else:
                raise UserError(_('Necessary Requirements To Run This Operation Is Not Satisfied'))