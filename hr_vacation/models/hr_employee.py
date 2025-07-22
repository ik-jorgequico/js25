from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date


class Employee(models.Model):
    _inherit = "hr.employee"

    vac_acum_ids = fields.One2many("hr.vacation.acum.line", 'employee_id', string="Vacaciones Acumuladas")
