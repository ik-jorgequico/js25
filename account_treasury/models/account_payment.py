# -*- coding: utf-8 -*-
from odoo import fields, models

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    
    mass_id = fields.Many2one('account.payment.mass', 'payment_ids',store=True)
    det_mass_id = fields.Many2one('acc.detrac.mass', 'payment_ids',store=True)
    
