import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime

class BonGrati(models.Model):
    _inherit = 'hr.grati'
    
    def compute_sheet(self):
        r = super(BonGrati, self).compute_sheet()
        self.child_ids._get_loan_amount()
        return r

class BonGratiLine(models.Model):
    _inherit = 'hr.grati.line'

    loan_amount = fields.Float(string="Prestamo", store=True, tracking=True)
    desc_grati = fields.Float(string="Total Descuentos", compute="_compute_desc_grati", store=True, tracking=True)

    @api.depends('loan_amount')
    def _compute_desc_grati(self):
        for record in self:
            record.desc_grati = record.loan_amount
            
    
    def _get_loan_amount(self):
        for line in self:
            amount = 0
            loan_lines = self.env["hr.loan.line"].search([
                ("employee_id","=",line.employee_id.id),
                ("loan_id.state","=","approve"),
                ("paid","=",False),
                ("for_grati","=",True)
            ])
            for loan_line in loan_lines:
                if line.date_from <= loan_line.date <= line.parent_id.payday :
                    amount += loan_line.amount
                    loan_line.paid = True
                    loan_line.loan_id._compute_loan_amount()
            line.loan_amount = amount