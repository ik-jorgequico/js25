# -*- coding: utf-8 -*-
from odoo import models, fields, api, _ # type: ignore

class ExpenseType(models.Model):
    _name = 'expense.type'
    _description = 'Expense Type'

    name = fields.Char(string='Nombre', required=True, store=True)
    concept_ids = fields.One2many('expense.concept', 'expense_type', string='Concepto de Gasto', store=True)