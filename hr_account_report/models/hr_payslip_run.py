#-*- coding:utf-8 -*-

from odoo import api, fields, models, _
from .hr_account_rp import AccountExcelReport
from odoo.exceptions import ValidationError, UserError
import base64

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Asiento Contable XLS')

    def compute_data(self):
        # self._check_states_month(self.date_start, self.date_end)
        self.env['hr.account.xlsx'].compute_data(self.date_start, self.date_end)

    def _check_states_month(self, date_from, date_to): 
        cts_prov_count = self.env['hr.prov.cts'].search_count([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("state","=",'draft'),
        ])
        grati_prov_count = self.env['hr.prov.grati'].search_count([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("state","=",'draft'),
        ])
        vaca_prov_count = self.env['hr.prov.grati'].search_count([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("state","=",'draft'),
        ])
        if cts_prov_count > 0:
            raise UserError(_('Se encontraron Provisiones de CTS en estado Borrador, termine todos los procesos para continuar.'))
        if grati_prov_count > 0:
            raise UserError(_('Se encontraron Provisiones de GRATIFICACION en estado Borrador, termine todos los procesos para continuar.'))
        if vaca_prov_count > 0:
            raise UserError(_('Se encontraron Provisiones de Vacaciones en estado Borrador o En Espera, termine todos los procesos para continuar.'))