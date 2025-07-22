# -*- coding: utf-8 -*-

from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _create_analytic_lines(self):
        res = super()._create_analytic_lines()
        self._create_target_move()
        return res

    def _create_target_move(self):
        for aml in self.filtered(lambda x:x.analytic_distribution != False):
            for k, v in aml.analytic_distribution.items():
                analytic = self.env['account.analytic.account'].browse(int(k))
                check = self.env['account.move'].search_count([('origin_move','=',aml.move_id.id),('ref','=',f"{analytic.name} - {aml.name}")])
                if check == 0:
                    if analytic.have_destiny:
                        am_data = {
                            'origin_move': aml.move_id.id,
                            'ref': f"{analytic.name} - {aml.name}",
                            'date': aml.date,
                            'journal_id': analytic.destiny_journal_id.id,
                            'move_type': 'entry',
                        }
                        target_move = self.env['account.move'].create(am_data)
                        aml_debit_data = {
                            'name': aml.name,
                            'ref': f"{analytic.name} - {aml.name}",
                            'partner_id': aml.partner_id.id or False,
                            'currency_id': aml.currency_id.id or False,
                            'account_id': analytic.account_expense_id.id,
                            'debit': aml.debit * float(v)/100 if aml.debit > 0 else 0.00,
                            'credit': aml.credit * float(v)/100 if aml.credit > 0 else 0.00,
                        }
                        aml_credit_data = {
                            'name': aml.name,
                            'ref': f"{analytic.name} - {aml.name}",
                            'partner_id': aml.partner_id.id or False,
                            'currency_id': aml.currency_id.id or False,
                            'account_id': analytic.account_charge_id.id,
                            'debit': aml.credit * float(v)/100 if aml.credit > 0 else 0.00,
                            'credit': aml.debit * float(v)/100 if aml.debit > 0 else 0.00,
                        }
                        target_move.write({'line_ids': [(0, 0, aml_debit_data), (0, 0, aml_credit_data)]})
                        target_move.action_post()
        return True
    
    def unlink(self):
        for rec in self:
            if rec.analytic_distribution:
                if rec.move_id.target_move_ids:
                    rec.move_id.target_move_ids.with_context(force_delete=True).unlink()
        return super().unlink()