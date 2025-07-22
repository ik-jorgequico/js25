from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError

# import locale
import base64

class LBSIncomesPayslip(models.Model):

    _name = "hr.lbs.incomes"
    _description = "Ingresos del Lote"

    name = fields.Char(string="Nombre Ingreso", store=True,)
    total = fields.Float( string="Monto",store=True,)
    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado",)
