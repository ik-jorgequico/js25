from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64

from odoo.exceptions import UserError, ValidationError

from .hr_utilities_macro import HrUtilitiesMacro

class Hrutilities(models.Model):
    _inherit = 'hr.utilities'
    _description = 'Hr utilities'

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    def action_dowload_report_macro_utilities(self):

        for obj in self:
            values = []

            for child_id in obj.child_ids:

                if(child_id.employee_id.bank_account_id.bank_id.name == "SCOTIABANK PERU"):
                    forma = 3
                    if(child_id.employee_id.bank_account_id.acc_number):
                        oficina = child_id.employee_id.bank_account_id.acc_number[0:3]
                        cuenta = child_id.employee_id.bank_account_id.acc_number[3:]
                    else:
                        oficina = ""
                        cuenta = ""
                    cci = ""
                else:
                    forma = 4
                    oficina = ""
                    cuenta = ""
                    cci = child_id.employee_id.bank_account_id.cci or ''

                if(len(child_id.employee_id.name) <= 30):
                    name = child_id.employee_id.name
                else:
                    name = child_id.employee_id.name[0:30]

                if(len(child_id.employee_id.identification_id) <= 8):
                    dni = child_id.employee_id.identification_id
                else:
                    dni = child_id.employee_id.identification_id[0:8]

                concepto = f"UTI ENE{str(self.anio)[2:]}-DIC{str(self.anio)[2:]}"

                val1 = {
                    "Cod.":dni or '',
                    "nombre":name,
                    "concepto":concepto or '',
                    "pago":self.date_pay or '',
                    "monto":child_id.utilities_total_amount_neta or '',
                    "forma":forma,
                    "cod_oficina":oficina or "",
                    "cod_cuenta":cuenta or "",
                    "dni": dni or '',
                    "cci": cci,

                }


                val = {**val1}

                values.append(val)
            obj.generate_macro(values)
            
    def generate_macro(self,data):
        report_xls = HrUtilitiesMacro(data, self)
        values = {
            'xls_filename_macro': "MACRO UTILIDADES - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)