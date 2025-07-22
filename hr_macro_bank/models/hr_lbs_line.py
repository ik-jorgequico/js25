from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64
from datetime import date
from datetime import datetime

from odoo.exceptions import UserError, ValidationError

class HrbsLine(models.Model):
    _inherit = 'hr.lbs.line'
    _description = 'hr vacation calculate line'

    payday = fields.Date("Fecha de pago", store=True)
    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    paid = fields.Boolean('Pagado', default=False, store=True)

    def write(self, vals):
        now = datetime.now().date()
        if vals.get('state') == 'paid':
            if any(slip.state == 'done' for slip in self):
                self.payday = now
            
        res = super(HrbsLine, self).write(vals)
        return res

