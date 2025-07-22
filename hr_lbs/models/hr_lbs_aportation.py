from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64

class LBSAportation(models.Model):
    _name = "hr.lbs.input"
    _description = "Aportaciones"

    name = fields.Char(string="Nombre Ingreso", store=True,)
    amount_lbs = fields.Float(string="Monto LBS", store=True, compute="compute_lbs")
    amount_report = fields.Float(string="Monto para Nomina", store=True,)
    total = fields.Float( string="Monto Plame",store=True,)
    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado",)

    @api.depends('amount_report','total')
    def compute_lbs(self):
        for record in self:
            record.amount_lbs = record.total - record.amount_report
