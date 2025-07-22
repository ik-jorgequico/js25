# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountGroup(models.Model):
    _inherit = "account.group"
    _description = "Add Formato EEFF"
    
    list_formats = [
        ('0', 'Ninguno'),
        ('1', 'Balance General'),
        ('2', 'Resultado por Funcion'),
        ('3', 'Resultado por Naturaleza'),
        ('4', 'Naturaleza y Funcion'),
    ]
    eeff_format = fields.Selection(list_formats, "Formatos de EEFF", default='0')
    