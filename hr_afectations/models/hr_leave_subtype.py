# -*- coding: utf-8 -*-
from odoo import api, fields, models

class HrLeaveSubType(models.Model):
    _name = "hr.leave.subtype"
    _description = "Subtype of Afectation Types"
    
    name = fields.Char(string="Nombre Subtipo",required=True,store=True,)
    type_id = fields.Many2one("hr.leave.type",string="Tipo Principal",store=True)

    # company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    company_id = fields.Many2one('res.company', string='Compañia')


    