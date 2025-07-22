# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class HrPayslipInputType(models.Model):
    _name = 'hr.payslip.input.type'
    _description = 'HrPayslipInputType'
    _inherit = ['hr.payslip.input.type','portal.mixin', 'mail.thread', 'mail.activity.mixin']

    is_affected = fields.Boolean(string='Es afecto?', store=True, default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
