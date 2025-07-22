from odoo import fields, models

class AccountAnalyticPlan(models.Model):
    _inherit = 'account.analytic.plan'
    _description = 'Analytic Plans'
    
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
