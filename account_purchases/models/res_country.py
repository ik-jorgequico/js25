# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCountry(models.Model):
    _inherit = "res.country"
    
    code_sunat = fields.Many2one('l10n_pe_edi.table.35', "Codigo Pais", store=True)