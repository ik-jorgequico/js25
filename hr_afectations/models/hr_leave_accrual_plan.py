
from odoo import api, fields, models, _

class AccrualPlan(models.Model):
    _inherit = "hr.leave.accrual.plan"
    _description = "Accrual Plan"
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)