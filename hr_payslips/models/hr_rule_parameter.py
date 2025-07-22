# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class HrSalaryRuleParameter(models.Model):
    _name= 'hr.rule.parameter'
    _description = 'HrSalaryRuleParameter'
    _inherit = ['hr.rule.parameter','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade', required=True, default=lambda self: self.env.company, tracking=True)
