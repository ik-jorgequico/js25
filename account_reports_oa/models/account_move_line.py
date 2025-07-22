# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = "Add group_id"
    
    group_id = fields.Many2one(related='account_id.group_id', string="Grupo", readonly=True, store=True)
    