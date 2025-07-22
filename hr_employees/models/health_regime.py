from odoo import fields, models


class HealthRegime(models.Model):
    _name = 'health.regime'
    _description = 'Régimen de Aseguramiento de Salud'

    code = fields.Char(string='Código')
    health_description = fields.Char(string='Descripción')
    name = fields.Char(string='Abreviatura')
    company_id = fields.Many2one('res.company', string='Company', ondelete='cascade')
