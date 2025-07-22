from odoo import fields, models, api

# class HrContract(models.Model):
#     _inherit = 'hr.contract'
#     _description = 'Beneficio extra'

#     extra_benefits_ids = fields.Many2many('hr.salary.rule', string="Otros Beneficios")

#     regime_name = fields.Char( compute="_compute_regime_name",store=True)
#     benefit_company = fields.Char(compute="_compute_benefit_company", string="Compañía")

#     @api.depends('peru_employee_regime')
#     def _compute_regime_name(self):
#         for record in self:
#             record.regime_name = record.peru_employee_regime.name if record.peru_employee_regime else False

#     @api.depends('extra_benefits_ids')
#     def _compute_benefit_company(self):
#         for record in self:
#             company = record.extra_benefits_ids.mapped('company_id.name')
#             record.benefit_company = ', '.join(company) if company else "No asignado"


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Beneficio extra'

    extra_benefits_ids = fields.Many2many(
        'hr.salary.rule',
        string="Otros Beneficios",
        domain="[('is_extra_benefit', '=', True)]"
    )

    regime_name = fields.Char(compute="_compute_regime_name", store=True)
    benefit_company = fields.Char(compute="_compute_benefit_company", string="Compañía")
    peru_employee_regime = fields.Many2one('peru.employee.regime',string='Regimen Laboral', required = True, tracking=True)

    @api.depends('peru_employee_regime')
    def _compute_regime_name(self): 
        for record in self:
            if record.peru_employee_regime:
                record.regime_name = record.peru_employee_regime.name if record.peru_employee_regime else False

    @api.depends('extra_benefits_ids')
    def _compute_benefit_company(self):
        for record in self:
            company = record.extra_benefits_ids.mapped('company_id.name')
            record.benefit_company = ', '.join(company) if company else "No asignado"
