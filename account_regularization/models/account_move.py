# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Regularizations and Account Move"

    reg_am_id = fields.Many2one('account.regularizations', string='Account Regularization', copy=False, store = True)
    
class AccountMoveLin(models.Model):
    _inherit = "account.move.line"
    _description = "Account Regularizations and Account Move"

    reg_aml_id = fields.Many2one('account.regularizations.line', string='Account Regularization Line', copy=False, store = True)