import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime

class HrUtilities(models.Model):
    _inherit = 'hr.utilities'
    
    def after_create_values(self):
        super(HrUtilities, self).after_create_values()
        self.child_ids._get_loan_amount()


class HrUtilitiesIncomes(models.Model):
    _inherit = 'hr.utilities.incomes'

    def _get_loan_amount(self):
        for line in self:
            amount = 0
            loan_lines = self.env["hr.loan.line"].search([
                ("employee_id","=",line.employee_id.id),
                ("loan_id.state","=","approve"),
                ("paid","=",False),
                ("for_utility","=",True)
            ])
            for loan_line in loan_lines:
                if loan_line :
                    amount += loan_line.amount
                    loan_line.paid = True
                    loan_line.loan_id._compute_loan_amount()
            line.loan = amount
                    
