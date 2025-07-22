from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64
from datetime import date
from datetime import datetime

from odoo.exceptions import UserError, ValidationError

class HrVacaLine(models.Model):
    _inherit = 'hr.vacation.calculate.line'
    _description = 'hr vacation calculate line'

    payday = fields.Date("Fecha de pago", store=True)
    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')
    paid = fields.Boolean('Pagado', default=False, store=True)

    def action_compute_payment(self):
        for record in self:
            now = datetime.now().date()
            
            record.deduction_payments_ids.unlink()
            record.write({
                "deduction_payments_ids" : [(0,0,adv_payment) for adv_payment in self._compute_deduction_payments(record.employee_id,record.date_from_eval,record.date_to_eval,record.bruto_amount)],
                "state_payment": '1',
                "payday": now,
                }
            )

            record.compute_sheet_import()