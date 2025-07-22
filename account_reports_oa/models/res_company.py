# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"
    _description = "Res Company for Taxes SUNAT Page"
    
    income_regime = fields.Selection([
        ("general", "General"),
        ("mype", "MYPE"),
        ("special", "Especial"),
    ], "Régimen de renta", store=True)
    part_workers = fields.Float("Participación de los trabajadores", store=True)
    uit_id = fields.Many2one('res.uit', "UIT", store=True)
    