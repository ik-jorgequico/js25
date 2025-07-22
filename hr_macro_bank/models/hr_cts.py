from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64

from odoo.exceptions import UserError, ValidationError

from .hr_cts_macro import HrctsMacro

class HrCTS(models.Model):
    _inherit = 'hr.cts'
    _description = 'Hr CTS'

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    def action_dowload_report_macro_cts(self):

        meses_dic = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}
    
        for obj in self:
            values = []

            for child_id in obj.child_ids:

                if(child_id.employee_id.bank_cts_id.bank_id.name == "SCOTIABANK PERU"):
                    forma = 3
                    if(child_id.employee_id.bank_cts_id.acc_number):
                        oficina = child_id.employee_id.bank_cts_id.acc_number[0:3]
                        cuenta = child_id.employee_id.bank_cts_id.acc_number[3:]
                    else:
                        oficina = ""
                        cuenta = ""
                    cci = ""
                else:
                    forma = 4
                    oficina = ""
                    cuenta = ""
                    cci = child_id.employee_id.bank_cts_id.cci or ''

                if(len(child_id.employee_id.name) <= 30):
                    name = child_id.employee_id.name
                else:
                    name = child_id.employee_id.name[0:30]

                if(len(child_id.employee_id.identification_id) <= 8):
                    dni = child_id.employee_id.identification_id
                else:
                    dni = child_id.employee_id.identification_id[0:8]

                concepto = f"CTS {meses_dic[self.date_from.month]}{str(self.date_from.year)[2:]} - {meses_dic[self.date_to.month]}{str(self.date_to.year)[2:]}"

                val1 = {
                    "Cod.":dni or '',
                    "nombre":name or '',
                    "concepto":concepto or '',
                    "pago":self.payday or '',
                    "monto":child_id.total or '',
                    "forma":forma,
                    "cod_oficina":oficina or '',
                    "cod_cuenta":cuenta or '',
                    "dni": dni or '',
                    "cci": cci or '',

                }


                val = {**val1}

                values.append(val)
            obj.generate_macro(values)
            
    def generate_macro(self,data):
        report_xls = HrctsMacro(data, self)
        values = {
            'xls_filename_macro': "MACRO CTS - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)