# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountZonal(models.Model):
    _name = 'account.zonal'
    _description = 'Account Zonal'

    name = fields.Char(string='Nombre', required=True, store=True)
    code = fields.Char(string='Código', compute='_compute_code',store=True)
    
    def _compute_code(self):
        for rec in self:
            rec.code = rec.name.replace(' ', '_').lower()