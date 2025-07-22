from odoo import fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    have_lbs = fields.Boolean(string="Asignar a LBS", help="Si esta activo, el monto irá directamente a la columna Monto LBS.")
