# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountCanal(models.Model):
    _name = 'account.canal'
    _description = 'Account Canal'

    name = fields.Char(string='Nombre', required=True, store=True)
    code = fields.Char(string='Código', compute='_compute_code',store=True)
    
    def _compute_code(self):
        for rec in self:
            rec.code = rec.name.replace(' ', '_').lower()