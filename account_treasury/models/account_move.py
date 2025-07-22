# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Move"
    
    account_zonal = fields.Many2one('account.zonal', string="Zonal",store=True)

    def button_draft(self):
        super(AccountMove, self).button_draft()
        for moves in self:
            moves.entry_id.with_context(force_delete=True).unlink()

    def button_cancel(self):
        super(AccountMove, self).button_cancel()
        for moves in self:
            moves.entry_id.with_context(force_delete=True).unlink()
    
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = "Account Move Line"
    
    expense_concept = fields.Many2one('expense.concept', string="Concepto de Gasto", store=True)
    account_zonal = fields.Many2one('account.zonal', string="Zonal",store=True)