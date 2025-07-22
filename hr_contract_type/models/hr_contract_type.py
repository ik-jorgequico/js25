from odoo import fields, models


class ContractType(models.Model):
    _inherit = 'hr.contract.type'
    _description = 'Contract Type'

    cod = fields.Char(store=True, string="Código" )
    description = fields.Char(store=True, string="Descripción" )