from odoo import api, fields, models


class UitTable(models.Model):
    _name = 'uit.table'
    _description = 'Valor de la UIT'

    year = fields.Integer(string='Año', store = True)
    code = fields.Char(string='Base Legal', store = True)
    name = fields.Char(string='Nombre', store = True)
    value = fields.Float(string='Valor', store = True)
