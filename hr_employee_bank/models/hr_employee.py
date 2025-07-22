from odoo import models, fields, api
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bank_account_id = fields.Many2one('hr.bank.account', string = 'Empleado / Cuenta Bancaria',domain="[('employee_id', '=', id)]",store=True)

    acc_number = fields.Char(related='bank_account_id.acc_number',string='Número de Cuenta de Nómina',store=True)
    cts_account = fields.Char(related='bank_account_id.cts_account',string='Número de Cuenta CTS',store=True)

    @api.model
    def create(self, vals):
        employee = super().create(vals)

        # Si no se asignó banco manualmente, asignamos la primera cuenta bancaria del empleado
        if not vals.get('bank_account_id'):
            bank_account = self.env['hr.bank.account'].search([('employee_id', '=', employee.id)], limit=1)
            if bank_account:
                employee.bank_account_id = bank_account.id

        return employee
