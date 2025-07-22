#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .hr_account_rp import AccountExcelReport, AccountExcelReportProv
from odoo.exceptions import ValidationError, UserError
from datetime import  timedelta, datetime, date
from datetime import datetime
from odoo.exceptions import UserError
import base64

class HrAccountXlsx(models.Model):
    _name = 'hr.account.xlsx'
    _description = 'Cuenta Contable'

    date_start = fields.Date(string="Dia Inicio", store=True,)
    date_end = fields.Date(string="Dia Fin", store=True,)
    name = fields.Char(string="Nombre")
    account_code = fields.Char(string="Codigo Cuenta Contable",store=True)
    rule = fields.Char(string="Regla",store=True)
    account_code_name = fields.Char(string="Nombre Cuenta Contable",store=True)
    ref = fields.Char(string="Referencia",store=True)
    analytic_tag = fields.Char(string="Etiqueta Analitica",store=True)
    analytic_ac = fields.Char(string="Cuenta Analitica",store=True)
    amount = fields.Float(string="Importe en Soles",store=True)
    currency = fields.Char(string="Moneda",store=True, default = 'PEN')
    debit = fields.Float(string="Debito",store=True)
    credit = fields.Float(string="Credito",store=True)

    @api.model
    def compute_data(self, date_from, date_to):
        account_dict = {}
        data = self.env['hr.payslip.line'].search([
            ('date_from', '=', date_from),
            ('date_to', '=', date_to),
            ('total', '!=', 0),
        ])
        run_cur = self.env['hr.payslip.run'].search([
            ('date_start', '=', date_from),
            ('date_end', '=', date_to),
        ])			
        val_list = []
        data_d = data.filtered(lambda x: x.salary_rule_id.account_debit)
        data_c = data.filtered(lambda x: x.salary_rule_id.account_credit)
        period= date_from.strftime("%m")+ " - " + date_to.strftime("%Y")
        
        val1=[]
        for line in data_d:
            account_code_d, account_cod_name_d = self._get_account_code_d(line)
            analytic_tag, analytic_ac = self._get_analytic_tag(line)

            total = 0
            if line.total > 0:
                total = line.total
            else:
                total = line.total * -1

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key = (account_code_d,  line.code, analytic_tag, analytic_ac)

            if key in account_dict:
                account_dict[key]['amount'] += total
                if line.salary_rule_id.account_debit:
                    account_dict[key]['debit'] += total
            else:
                account_dict[key] = {
                    'account_code': account_code_d,
                    'rule': line.code,
                    'account_code_name': account_cod_name_d,
                    'ref': line.slip_id.payslip_run_id.name,
                    'analytic_tag': line.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(line.employee_id),
                    'amount': total,
                    'currency': 'PEN',
                    'debit': total if line.salary_rule_id.account_debit else 0,
                    'credit': 0,
                    'period': period,
            }
            val1 = list(account_dict.values())
        val_list.extend(val1)
        
        account_dict_1 = {}
        val2=[]
        for lines in data_c:
            account_code_c, account_cod_name_c = self._get_account_code_c(lines)
            analytic_tag, analytic_ac = self._get_analytic_tag(lines)

            total = 0
            if lines.total > 0:
                total = lines.total
            else:
                total = lines.total * -1

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key_2 = (account_code_c, lines.code, analytic_tag, analytic_ac)

            if key_2 in account_dict_1:
                account_dict_1[key_2]['amount'] += total
                if lines.salary_rule_id.account_credit:
                    account_dict_1[key_2]['credit'] += total
            else:
                account_dict_1[key_2] = {
                    'account_code': account_code_c,
                    'rule': lines.code,
                    'account_code_name': account_cod_name_c,
                    'ref': lines.slip_id.payslip_run_id.name,
                    'analytic_tag': lines.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(lines.employee_id),
                    'amount': total,
                    'currency': 'PEN',
                    'debit': 0,
                    'credit': total if lines.salary_rule_id.account_credit else 0,
                    'period': period,
                        }
            val2 = list(account_dict_1.values())
        val_list.extend(val2)
        self.generate_excel(val_list, run_cur)
        return val_list

    @api.model
    def _get_analytic_tag(self,line):
        analytic_tag = line.employee_id.cod_coste_center.name
        analytic_ac = ''
        for cc in line.employee_id.cod_coste_center_account:
            if cc.is_active:
                analytic_ac = cc.account_analytic_account_id.name
        return analytic_tag, analytic_ac


    @api.model
    def _get_account_code_d(self,line):
        account_cod_d = "introduce cuenta contable"
        account_cod_name_d = "introduce nombre de cuenta contable"
        if line.salary_rule_id.account_debit :
            account_cod_d = line.salary_rule_id.account_debit.code
            account_cod_name_d = line.salary_rule_id.account_debit.name
        return account_cod_d, account_cod_name_d
    
    @api.model
    def _get_account_code_c(self,line):
        account_cod_c = "introduce cuenta contable"
        account_cod_name_c = "introduce nombre de cuenta contable"
        if line.salary_rule_id.account_credit :
            account_cod_c = line.salary_rule_id.account_credit.code
            account_cod_name_c = line.salary_rule_id.account_credit.name
        return account_cod_c, account_cod_name_c

    @api.model
    def get_active_analytic_account(self,employee):
        active_accounts = employee.cod_coste_center_account.filtered(lambda x: x.is_active)
        if len(active_accounts) == 0:
            raise UserError(_('No se encontró ninguna cuenta de centro de costos activa para el empleado %s') % employee.name)
        elif len(active_accounts) > 1:
            raise UserError(_('El empleado %s tiene más de una cuenta de centro de costos activa. Por favor, modifique las cuentas para que sólo haya una activa.') % employee.name)
        return active_accounts.account_analytic_account_id.name

    @api.model
    def generate_excel(self, data, id):
        report_xls = AccountExcelReport(data, self,self.date_start, self.date_end)
        tittle =  id.name.split('-')[0]
        values = {
            'xls_filename': "Asiento Contable " + tittle + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        id.write(values)

    @api.model
    def compute_entry_cts(self, date_from, date_to):
        account_dict = {}
        data = self.env['hr.prov.cts.line'].search([('date_from', '=', date_from),
                                                ('date_to', '=', date_to),
                                                ('total', '!=', 0)])
        run_cur = self.env['hr.prov.cts'].search([('date_from', '=', date_from),
                                                  ('date_to', '=', date_to)])			
        val_list = []
        period= date_from.strftime("%m")+ " - " + date_to.strftime("%Y")
        
        val1=[]
        for line in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(line)

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key = (run_cur.account_debit.code, analytic_tag, analytic_ac)

            if key in account_dict:
                account_dict[key]['amount'] += line.prov_mes_adjust
                account_dict[key]['debit'] += line.prov_mes_adjust
            else:
                account_dict[key] = {
                    'account_code': run_cur.account_debit.code,
                    'account_code_name': run_cur.account_debit.name,
                    'ref': run_cur.name,
                    'analytic_tag': line.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(line.employee_id),
                    'amount': line.prov_mes_adjust,
                    'currency': 'PEN',
                    'debit': line.prov_mes_adjust,
                    'credit': 0,
                    'period': period,
            }
            val1 = list(account_dict.values())
        val_list.extend(val1)
        
        account_dict_1 = {}
        val2=[]
        for lines in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(lines)

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key_2 = (run_cur.account_credit.code, analytic_tag, analytic_ac)

            if key_2 in account_dict_1:
                account_dict_1[key_2]['amount'] += lines.prov_mes_adjust
                account_dict_1[key_2]['credit'] += lines.prov_mes_adjust
            else:
                account_dict_1[key_2] = {
                    'account_code': run_cur.account_credit.code,
                    'account_code_name': run_cur.account_credit.name,
                    'ref': run_cur.name,
                    'analytic_tag': lines.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(lines.employee_id),
                    'amount': lines.prov_mes_adjust,
                    'currency': 'PEN',
                    'debit': 0,
                    'credit': lines.prov_mes_adjust,
                    'period': period,
                        }
            val2 = list(account_dict_1.values())
        val_list.extend(val2)
        self.generate_excel_prov(val_list, run_cur)
        return val_list
    

    @api.model
    def compute_entry_vaca(self, date_from, date_to):
        account_dict = {}
        data = self.env['hr.prov.vaca.line'].search([('date_from', '=', date_from),
                                                ('date_to', '=', date_to),
                                                ('total', '!=', 0)])
        run_cur = self.env['hr.prov.vaca'].search([('date_from', '=', date_from),
                                                  ('date_to', '=', date_to)])			
        val_list = []
        period= date_from.strftime("%m")+ " - " + date_to.strftime("%Y")
        
        val1=[]
        for line in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(line)
            key = (run_cur.account_debit.code, analytic_tag, analytic_ac)

            if key in account_dict:
                account_dict[key]['amount'] += line.prov_mes_adjust
                account_dict[key]['debit'] += line.prov_mes_adjust
            else:
                account_dict[key] = {
                    'account_code': run_cur.account_debit.code,
                    'account_code_name': run_cur.account_debit.name,
                    'ref': run_cur.name,
                    'analytic_tag': line.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(line.employee_id),
                    'amount': line.prov_mes_adjust,
                    'currency': 'PEN',
                    'debit': line.prov_mes_adjust,
                    'credit': 0,
                    'period': period,
            }
            val1 = list(account_dict.values())
        val_list.extend(val1)
        
        account_dict_1 = {}
        val2=[]
        for lines in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(lines)

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key_2 = (run_cur.account_credit.code, analytic_tag, analytic_ac)

            if key_2 in account_dict_1:
                account_dict_1[key_2]['amount'] += lines.prov_mes_adjust
                account_dict_1[key_2]['credit'] += lines.prov_mes_adjust
            else:
                account_dict_1[key_2] = {
                    'account_code': run_cur.account_credit.code,
                    'account_code_name': run_cur.account_credit.name,
                    'ref': run_cur.name,
                    'analytic_tag': lines.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(lines.employee_id),
                    'amount': lines.prov_mes_adjust,
                    'currency': 'PEN',
                    'debit': 0,
                    'credit': lines.prov_mes_adjust,
                    'period': period,
                        }
            val2 = list(account_dict_1.values())
        val_list.extend(val2)
        self.generate_excel_prov(val_list, run_cur)
        return val_list
    
    @api.model
    def compute_entry_grati(self, date_from, date_to):
        account_dict = {}
        data = self.env['hr.prov.grati.line'].search([('date_from', '=', date_from),
                                                ('date_to', '=', date_to),
                                                ('total', '!=', 0)])
        run_cur = self.env['hr.prov.grati'].search([('date_from', '=', date_from),
                                                  ('date_to', '=', date_to)])			
        val_list = []
        period= date_from.strftime("%m")+ " - " + date_to.strftime("%Y")
        
        val1=[]
        for line in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(line)
            key = (run_cur.account_debit.code, analytic_tag, analytic_ac)

            if key in account_dict:
                account_dict[key]['amount'] += line.prov_mes_adjust + line.prov_bonf_adjust
                account_dict[key]['debit'] += line.prov_mes_adjust + line.prov_bonf_adjust
            else:
                account_dict[key] = {
                    'account_code': run_cur.account_debit.code,
                    'account_code_name': run_cur.account_debit.name,
                    'ref': run_cur.name,
                    'analytic_tag': line.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(line.employee_id),
                    'amount': line.prov_mes_adjust + line.prov_bonf_adjust,
                    'currency': 'PEN',
                    'debit': line.prov_mes_adjust + line.prov_bonf_adjust,
                    'credit': 0,
                    'period': period,
            }
            val1 = list(account_dict.values())
        val_list.extend(val1)
        
        account_dict_1 = {}
        val2=[]
        for lines in data:
            analytic_tag, analytic_ac = self._get_analytic_tag(lines)

            # Sumar el importe según el account_code, analytic_tag y analytic_ac
            key_2 = (run_cur.account_credit.code, analytic_tag, analytic_ac)

            if key_2 in account_dict_1:
                account_dict_1[key_2]['amount'] += lines.prov_mes_adjust + lines.prov_bonf_adjust
                account_dict_1[key_2]['credit'] += lines.prov_mes_adjust + lines.prov_bonf_adjust
            else:
                account_dict_1[key_2] = {
                    'account_code': run_cur.account_credit.code,
                    'account_code_name': run_cur.account_credit.name,
                    'ref': run_cur.name,
                    'analytic_tag': lines.employee_id.cod_coste_center.name,
                    'analytic_ac': self.get_active_analytic_account(lines.employee_id),
                    'amount': lines.prov_mes_adjust + lines.prov_bonf_adjust,
                    'currency': 'PEN',
                    'debit': 0,
                    'credit': lines.prov_mes_adjust + lines.prov_bonf_adjust,
                    'period': period,
                        }
            val2 = list(account_dict_1.values())
        val_list.extend(val2)
        self.generate_excel_prov(val_list, run_cur)
        return val_list
    
    
    @api.model
    def generate_excel_prov(self, data, id):
        report_xls = AccountExcelReportProv(data, self,self.date_start, self.date_end)
        tittle =  id.name.split('-')[0]
        values = {
            'xls_filename_entry': "Asiento Contable " + tittle + ".xlsx",
            'xls_binary_entry': base64.encodebytes(report_xls.get_content()),
        }
        id.write(values)

