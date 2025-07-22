# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    id_token_sunat = fields.Char("Credenciales API Sunat - ID ")
    clave_token_sunat = fields.Char("Credenciales API Sunat - CLAVE")