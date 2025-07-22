# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):
    _name = 'hr.salary.rule'
    _inherit = ['hr.salary.rule','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
    is_affected = fields.Boolean(string='Es afecto?', store=True, default=True, tracking=True)
    appears_on_utilities = fields.Boolean(string="Se considera para el cálculo de Utilidades",store=True, default=True, tracking=True)

    have_gratification = fields.Boolean(string="Promedio Var. Gratificaciones",store=True,help="La cuantificación de gratificaciones restaría a los 30 días.", tracking=True)
    have_cts = fields.Boolean(string="Promedio Var. CTS",store=True, tracking=True)
    have_utilities = fields.Boolean(string="Promedio Var. Utilidades",store=True, tracking=True)
    have_holiday = fields.Boolean(string="Promedio Var. Vacaciones",store=True, tracking=True)
    have_5ta = fields.Boolean(string="5ta Categoría",store=True, default=False, tracking=True)
    have_5ta_direct = fields.Boolean(string="5ta Directa",store=True, default=False, tracking=True)
    have_5ta_grati = fields.Boolean(string="Promedio Var. 5ta",store=True, default=False, tracking=True)

     
    struct_id = fields.Many2one('hr.payroll.structure', string="Salary Structure", required=True, tracking=True)
    category_id = fields.Many2one('hr.salary.rule.category', string='Category', required=True, tracking=True)

    appears_nomina = fields.Boolean(string="Aparece en Nomina",store=True, default=True, tracking=True)
    appears_lbs = fields.Boolean(string="Aparece en Liquidacion",store=True, tracking=True)



