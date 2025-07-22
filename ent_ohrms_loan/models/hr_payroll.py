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
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Cuota de Préstamo", )


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.code == "I_PREST":
                
                loan_lines = self.env["hr.loan.line"].search([
                    ("employee_id","=",line.payslip_id.employee_id.id),
                    ("loan_id.state","=","approve"),
                    ("paid","=",False),
                    ("for_payslip","=",True)
                ])
                for loan_line in loan_lines:
                    if line.payslip_id.date_from <= loan_line.date <= line.payslip_id.date_to :
                        loan_line.paid = True
                        loan_line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()
    
    
class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    input_id = fields.Many2one('hr.salary.rule')


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    company_id = fields.Many2one('res.company', 'Compañia', copy=False, readonly=True, help="Comapny",
                                 default=lambda self: self.env.company)


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    company_id = fields.Many2one('res.company', 'Compañia', copy=False, readonly=True, help="Company",
                                 default=lambda self: self.env.company)

