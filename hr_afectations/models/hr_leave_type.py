# -*- coding: utf-8 -*-
from odoo import api, fields, models

class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"
    
    have_gratification = fields.Boolean(string="Gratificaciones",store=True,help="La cuantificación de gratificaciones restaría a los 30 días.")
    have_cts = fields.Boolean(string="CTS",store=True,)
    have_utilities = fields.Boolean(string="Utilidades",store=True,)
    have_holiday = fields.Boolean(string="Vacaciones",store=True,)
    code = fields.Char(string='Código Principal', store=True,)

    add_basic_salary = fields.Boolean(string="¿Suma al Salario Basico?",store=True)

    # company_id = fields.Many2one('res.company', string='Company', default=None)
    company_id = False

