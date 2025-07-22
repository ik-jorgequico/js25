from odoo import api, fields, models

class PeruEmployeeRegime(models.Model): 
    _name = 'peru.employee.regime'
    _description = 'Regimenes laborales en Peru'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char('Regimen Laboral', tracking=True)
    structure_type_id = fields.Many2one('hr.payroll.structure.type',string='Tipo de Estructura', required = True, tracking=True)
    abbr = fields.Char('Abreviatura', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
