from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    peru_employee_regime = fields.Many2one('peru.employee.regime',string='Regimen Laboral', required = True, tracking=True)

    # @api.model
    # def set_default_peru_employee_regime(self):
    #     str_default = self.env['hr.payroll.structure.type'].search([('abbr','=','RLP'),('company_id','=',self.company_id.id)])
    #     regime_default = self.env['peru.employee.regime'].search([('abbr','=','RG'),('company_id','=',self.company_id.id)])
    #     contracts = self.search([])
    #     contracts.write({'structure_type_id':str_default,'peru_employee_regime': regime_default,})
    #     return True
    
    @api.depends('company_id')
    def _compute_structure_type_id(self):
        default_structure_by_country = {}

        def _default_salary_structure(country_id):
            default_structure = default_structure_by_country.get(country_id)
            if default_structure is None:
                default_structure = default_structure_by_country[country_id] = (
                    self.env['hr.payroll.structure.type'].search([('abbr','=','RLP'),('country_id', '=', country_id),('company_id','=',self.company_id.id)], limit=1)
                    or self.env['hr.payroll.structure.type'].search([('abbr','=','RLP'),('country_id', '=', False),('company_id','=',self.company_id.id)], limit=1)
                )
            return default_structure

        for contract in self:
            if not contract.structure_type_id or (contract.structure_type_id.country_id and contract.structure_type_id.country_id != contract.company_id.country_id):
                contract.structure_type_id = _default_salary_structure(contract.company_id.country_id.id)