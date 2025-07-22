# -*- coding: utf-8 -*-
from odoo import fields, models


class TxtFileSave(models.TransientModel):
    _name = 'txt.file.save'
    _description = "Txt File Save"
    
    output_name = fields.Char('Output filename', size=128)
    output_file = fields.Binary('Output file', readonly=True)
    