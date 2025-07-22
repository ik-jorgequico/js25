from odoo import models, fields, api
from odoo.exceptions import UserError

class HrBankAccount(models.Model):
    _name = 'hr.bank.account'
    _description = 'Cuenta Bancaria'

    name = fields.Char(string='Cuenta Bancaria' , compute='_compute_name', store=True)
    acc_number = fields.Char(string='Cuenta Bancaria para el pago de nómina', required=True)
    cts_account = fields.Char(string='Cuenta Bancaria para el pago de CTS')  # bank_cts_id

    account_type = fields.Selection([
        ('C', 'Cuenta Corriente'),
        ('M', 'Cuenta Maestra'),
        ('A', 'Ahorros'),
    ], 'Tipo de Cuenta', default='C',store=True)

    cci = fields.Char(string='Cuenta Interbancaria (CCI)')

    bank_id = fields.Many2one('res.bank', string='Banco')
    employee_id = fields.Many2one('hr.employee', string='Empleado', domain="[('company_id', '=', company_id)]")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company, readonly=True)

    @api.depends('acc_number', 'employee_id')
    def _compute_name(self):
        for rec in self:
            emp_name = rec.employee_id.name or ''
            acc_number = rec.acc_number or ''
            rec.name = f'{emp_name} - {acc_number}' if emp_name or acc_number else ''
            
    @api.constrains('acc_number')
    def _check_unique_acc_number(self):
        for rec in self:
            if rec.acc_number:
                domain = [('acc_number', '=', rec.acc_number)]
                if rec.id:
                    domain.append(('id', '!=', rec.id))
                exists = self.search_count(domain)
                if exists:
                    raise UserError("El número de cuenta bancaria ya está en uso. Debe ser único.")
