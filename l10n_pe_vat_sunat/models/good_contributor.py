# -*- coding: utf-8 -*-
from odoo import models, fields


class GoodContributor(models.Model):
    _name = 'good.contributor'
    _description = 'Buenos Contribuyentes'

    ruc = fields.Char(required=True)
    razon_social = fields.Char()
    a_partir_del = fields.Date()
    resolucion = fields.Char()
