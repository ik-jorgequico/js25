# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ # type: ignore

class ExpenseConcept(models.Model):
    _name = 'expense.concept'
    _description = 'Expense Concept'

    name = fields.Char(string='Nombre', required=True, store=True)
    expense_type = fields.Many2one('expense.type', string='Tipo de Gasto', readonly=True, store=True)