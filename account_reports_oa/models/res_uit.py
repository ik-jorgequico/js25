# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from datetime import datetime


class ResUit(models.Model):
    _name = "res.uit"
    _description = "Tabla de uit por año"
    
    name = fields.Char("Nombre")
    
    current_year = int(datetime.now().date().strftime("%Y"))
    list_year = [(str(year), year) for year in range(current_year - 10, current_year + 1)]
    
    year = fields.Selection(selection=list_year, string="Periodo", default=str(current_year), required=True, store=True)
    amount = fields.Integer("Valor de UIT", required=True, store=True)
    
    @api.onchange('year', 'amount')
    def _get_name(self):
        if self.year and self.amount:
            self.name = f"Año {self.year} - S/{self.amount}"
    
    def write(self, vals):
        result = super(ResUit, self).write(vals)
        if 'year' in vals:
            moves = self.env['res.uit'].search([('year', '=', vals['year'])])
            if len(moves) > 1:
                raise UserError("No puedes duplicar los periodos")
        return result