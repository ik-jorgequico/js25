from odoo import fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_extra_benefit = fields.Boolean(string="Es Beneficio Extra")
