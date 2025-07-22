# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    account_expense_id = fields.Many2one('account.account', string='Cuenta de Gasto')
    account_charge_id = fields.Many2one('account.account', string='Cuenta de Cargo')
    have_destiny = fields.Boolean(string='Tiene Destino', default=False)
    destiny_journal_id = fields.Many2one('account.journal', string='Diario Destino')

    def _get_analytic_accounts(self):
        return {
            'charge': self.account_charge_id,
            'expense': self.account_expense_id
                }

    def get_analytic_accounts(self, fiscal_pos=None):
        accounts = self._get_analytic_accounts()
        if not fiscal_pos:
            fiscal_pos = self.env['account.fiscal.position']
        return fiscal_pos.map_accounts(accounts)