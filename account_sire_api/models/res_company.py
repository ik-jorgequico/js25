# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"
    
    username_sunat = fields.Char("Usuario SUNAT")
    password_sunat = fields.Char("Clave SOL")