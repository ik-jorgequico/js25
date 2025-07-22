# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import UserError

class AccountAnalyticTag(models.Model):
    _name = "account.analytic.tag"
    _description = " Analityc tag para recursos humanos"

    name = fields.Char("Nombre",store="True")

