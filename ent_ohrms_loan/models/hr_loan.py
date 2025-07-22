# -*- coding: utf-8 -*-
######################################################################################
#
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _description = "Loans Employees"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    name = fields.Char(string="Nombre Préstamo", default="/", readonly=True, help="Nombre del préstamo", tracking=True)
    date = fields.Date(string="Fecha", default=fields.Date.today(), readonly=True, tracking=True )
    employee_id = fields.Many2one('hr.employee', string="Empleado", required=True, tracking=True )
    
    identification =  fields.Char(string="DNI", related="employee_id.identification_id", readonly=True, help="Empleado", tracking=True)
    
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Departamento", help="Employee", tracking=True)
    installment = fields.Integer(string="Cuotas", default=1, help="Número de cuotas", tracking=True)
    payment_date = fields.Date(string="Fecha Inicio", required=True, default=fields.Date.today(), help="Fecha del pago", tracking=True)
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Línea de préstamo", index=True , tracking=True)
    company_id = fields.Many2one('res.company', 'Compañia', readonly=True,
                                 default=lambda self: self.env.company , tracking=True)

                                 
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id, tracking=True)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Puesto de trabajo", tracking=True)
    loan_amount = fields.Float(string="Préstamo", required=True, tracking=True)
    total_amount = fields.Float(string="Total Préstamo", store=True, readonly=True, compute='_compute_loan_amount', tracking=True)
    balance_amount = fields.Float(string="Saldo", store=True, compute='_compute_loan_amount', tracking=True)
    total_paid_amount = fields.Float(string="Pagado", store=True, compute='_compute_loan_amount', tracking=True)

    state = fields.Selection([
        ('draft', 'Borrador'),
        ('waiting_approval_1', 'Enviado'),
        ('approve', 'Aprobado'),
        ('refuse', 'Rechazado'),
        ('cancel', 'Cancelado'),
    ], string="Estado", default='draft', tracking=True, copy=False, )

    # @api.model
    # def create(self, values):
        
    #     values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
    #     res = super(HrLoan, self).create(values)
    #     return res
    

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True
    
    def compute_loan_payment_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    date = fields.Date(string="Fecha de pago", required=True, help="Date of the payment", tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Empleado", help="Employee", tracking=True)
    amount = fields.Float(string="Cantidad", required=True, help="Amount", tracking=True)
    paid = fields.Boolean(string="Pagado", help="Paid",default=False, tracking=True)
    loan_id = fields.Many2one('hr.loan', string="Préstamo Ref.", help="Loan", tracking=True)
    payslip_id = fields.Many2one('hr.payslip', string="Nómina Ref.", help="Payslip", tracking=True)
    for_payslip = fields.Boolean(string="Para Nomina", help="El préstamo se pagará en la nómina",default=True, tracking=True)
    for_grati = fields.Boolean(string="Para Grati", help="El préstamo se pagará en la gratificación",default=False, tracking=True)
    for_utility = fields.Boolean(string="Para Utilidad", help="El préstamo se pagará en la utilidad",default=False, tracking=True)

    # @api.onchange('for_payslip',)
    # def _onchange_for_payslip(self):
    #     self.for_grati = False
    #     self.for_utility = False
        
    @api.onchange('for_grati',)
    def _onchange_for_grati(self):
        self.for_payslip = True
        self.for_utility = False
        
    @api.onchange('for_utility',)
    def _onchange_for_utility(self):
        self.for_payslip = True
        self.for_grati = False

    @api.onchange('loan_id',)
    def _onchange_loan_id(self):
        self.employee_id = self.loan_id.employee_id
        
class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Recuento de préstamos", compute='_compute_employee_loans')
