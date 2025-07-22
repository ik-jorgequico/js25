# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    origin_move = fields.Many2one('account.move', string='Origin entry', copy=False)
    target_move_ids = fields.One2many('account.move', 'origin_move', string='Target entries', copy=False)
    destiny_move_count = fields.Integer('Target move count', compute='_compute_count_destiny_move')

   # def action_post(self):
   #     for rec in self:
   #         accounts = rec.line_ids.filtered(lambda x:x.account_id.account_type == 'expense')
   #         for l in accounts:
   #             if not l.analytic_distribution:
   #                 raise UserError('No puedes confirmar si una cuenta de gasto no tiene Destino.')
   #     res = super().action_post()
   #     return res

    def _compute_count_destiny_move(self):
        account_move = self.env['account.move']
        for record in self:
            record.destiny_move_count = account_move.search_count([('origin_move', '=', record.id)])

    def open_destiny_move_view(self):
        [action] = self.env.ref('account.action_move_line_form').read()
        idsd = self.target_move_ids.ids
        action['domain'] = [('id', 'in', idsd)]
        action['name'] = 'Target entries'
        return action

    def button_draft(self):
        super(AccountMove, self).button_draft()
        for moves in self:
            moves.target_move_ids.with_context(force_delete=True).unlink()

    def button_cancel(self):
        super(AccountMove, self).button_cancel()
        for moves in self:
            moves.target_move_ids.with_context(force_delete=True).unlink()

    @api.depends('move_type', 'company_id')
    def _compute_l10n_pe_edi_operation_type(self):
        res = super()._compute_l10n_pe_edi_operation_type()
        for move in self:
            move.l10n_pe_edi_operation_type = '1' if move.country_code == 'PE' and move.is_sale_document() else False
        return res
