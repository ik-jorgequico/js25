from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayrollStructureType(models.Model):
    _name = 'hr.payroll.structure.type'
    _description = 'HrPayrollStructureType'
    _inherit = ['hr.payroll.structure.type','portal.mixin', 'mail.thread', 'mail.activity.mixin']

    abbr = fields.Char(string="Abreviatura",store=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
