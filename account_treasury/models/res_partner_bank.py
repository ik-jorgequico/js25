# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    # cci_number = fields.Char("CCI",store=True) se repite por eso lo cancele, deberia ser cci_bank
    # cci_bank = fields.Char("Cuenta Interbancaria (CCI)", store=True)
    # cci_number = fields.Char("Cuenta Interbancaria (CCI)", store=True)
    is_account_vendor = fields.Boolean("Es cuenta de pagos proveedores", default=False, store=True)
    account_type = fields.Selection([
        ('C', 'Cuenta Corriente'),
        ('M', 'Cuenta Maestra'),
        ('A', 'Ahorros'),
    ], 'Tipo de Cuenta', default='A',store=True)
    is_det_bank = fields.Boolean("Cuenta de detracción", default=False, store=True)
    