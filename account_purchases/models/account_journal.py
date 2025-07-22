# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    have_purchase = fields.Boolean("Va a Compras")
    have_sale = fields.Boolean("Va a Ventas")
    is_detraction = fields.Boolean("Diario de Detraccion")
    account_det = fields.Many2one('account.account', "Cuenta de Detraccion", store=True)