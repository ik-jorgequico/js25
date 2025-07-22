from odoo import api, fields, models, _

class HrPayrollStructure(models.Model):
    _name = 'hr.payroll.structure'
    _description = 'HrPayrollStructure'
    _inherit = ['hr.payroll.structure','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    

    abbr = fields.Char(string="Abreviatura", store=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
    type_id = fields.Many2one('hr.payroll.structure.type', required=True, tracking=True)