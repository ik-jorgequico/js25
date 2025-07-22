from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64

from odoo.exceptions import UserError, ValidationError

from .hr_vaca_macro import HrVacaMacro

class HrVaca(models.Model):
    _inherit = 'hr.vacation.calculate'
    _description = 'hr vacation calculate'

    
    payday = fields.Date("Fecha de pago", store=True,tracking=True)

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro',tracking=True)

    def action_dowload_report_macro_vaca(self):
        if(self.payday == False):
            raise ValidationError(_("Por favor ingrese una fecha de pago"))
        for obj in self:
            values = []
            
            child_vaca = obj.child_ids.filtered(lambda x: x.payday and x.payday == obj.payday and x.paid == False)

            for child_id in child_vaca:

                meses_dic = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}

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

                concepto = f"VACA {meses_dic[self.date_from_eval.month]}{str(self.date_from_eval.year)[2:]}"

                val1 = {
                    "Cod.":dni or '',
                    "nombre":name or '',
                    "concepto":concepto or '',
                    "pago":child_id.payday or '',
                    "monto":child_id.net_amount or '',
                    "forma":forma,
                    "cod_oficina":oficina or '',
                    "cod_cuenta":cuenta or '',
                    "dni": dni or '',
                    "cci": cci or '',

                }


                val = {**val1}

                values.append(val)
            obj.generate_macro(values, child_vaca)
            
    def generate_macro(self,data,child_vaca):
        report_xls = HrVacaMacro(data, self)
        values = {
            'xls_filename_macro': "MACRO Vacaciones - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        values_child = {
            'xls_filename_macro': "MACRO LBS - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
            'paid': True,
        }
        self.write(values)
        child_vaca.write(values_child)
    
    
        