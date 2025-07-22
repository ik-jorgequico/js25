from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    peru_employee_regime = fields.Many2one('peru.employee.regime',string='Regimen Laboral', required = True, tracking=True)

    # @api.model
    # def set_default_peru_employee_regime(self):
    #     default_value = 'RLP'
    #     contracts = self.search([])
    #     contracts.write({'peru_employee_regime': default_value})
    #     return True