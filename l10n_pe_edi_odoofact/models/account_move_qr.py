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

class AccountMove(models.Model): 
    _inherit = "account.move"

    qr_code = fields.Binary('QRcode', compute="_generate_qr")

    def _generate_qr(self):
        for rec in self:
            if rec.move_type in ['out_invoice','out_refund']:
                if qrcode and base64:                
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=3,
                        border=4,
                    )
                    qr.add_data(str(rec.company_id.vat)+"|")
                    qr.add_data(str(rec.l10n_latam_document_type_id.code)+"|")
                    qr.add_data(str(rec.l10n_pe_edi_serie)+"|")
                    qr.add_data(str(rec.l10n_pe_edi_number)+"|")
                    qr.add_data(str(rec.l10n_pe_edi_amount_igv)+"|")
                    qr.add_data(str(rec.amount_total)+"|")
                    qr.add_data(str(rec.invoice_date)+"|")
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
            else:
                pass