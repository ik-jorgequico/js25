from odoo import api, fields, models


class Tramo5ta(models.Model):
    _name = 'tramo.5ta'
    _description = 'Tramo 5ta categoria'

    code = fields.Char(string='Secuencia', store = True)
    name = fields.Char(string='Nombre', store = True)
    uit_from = fields.Float(string='Desde (UIT)', store = True)
    uit_to = fields.Float(string='Hasta (UIT)', store = True)
    percentage = fields.Float(string='Porcentaje (%)', store = True)
