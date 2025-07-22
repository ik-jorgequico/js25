from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64

from odoo.exceptions import UserError, ValidationError

from .hr_lbs_macro import HrlbsMacro

class Hrlbs(models.Model):
    _inherit = 'hr.lbs.line'
    _description = 'Hr lbs'

    payday = fields.Date("Fecha de pago", store=True)

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    def action_dowload_report_macro_lbs(self):

        if(self.payday == False):
            raise ValidationError(_("Por favor ingrese una fecha de pago"))
    
        for obj in self:
            values = []

            # child_lbs = obj.child_ids.filtered(lambda x: x.payday and x.payday == obj.payday and x.paid == False)

            # for child_id in child_lbs:

            ##################################

            meses_dic = {1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR", 5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO", 9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"}

            if(obj.employee_id.bank_account_id.bank_id.name == "SCOTIABANK PERU"):
                forma = 3
                if(obj.employee_id.bank_account_id.acc_number):
                    oficina = obj.employee_id.bank_account_id.acc_number[0:3]
                    cuenta = obj.employee_id.bank_account_id.acc_number[3:]
                else:
                    oficina = ""
                    cuenta = ""
                cci = ""
            else:
                forma = 4
                oficina = ""
                cuenta = ""
                cci = obj.employee_id.bank_account_id.cci or ''
            
            if(len(obj.employee_id.name) <= 30):
                name = obj.employee_id.name
            else:
                name = obj.employee_id.name[0:30]

            if(len(obj.employee_id.identification_id) <= 8):
                dni = obj.employee_id.identification_id
            else:
                dni = obj.employee_id.identification_id[0:8]

            concepto = f"LBS {meses_dic[self.date_from.month]}{str(self.date_from.year)[2:]} - {meses_dic[self.date_to.month]}{str(self.date_to.year)[2:]}"

            val1 = {
                "dni":dni or '',
                "nombre":name or '',
                "concepto":concepto or '',
                "pago":obj.payday or '',
                "monto":obj.net or '',
                "forma":forma,
                "cod_oficina":oficina or '',
                "cod_cuenta":cuenta or '',
                "referencia": 'LIQUIDACION',
                "cci": cci or '',

            }


            val = {**val1}

            values.append(val)

            ###############################
            obj.generate_macro(values)#, child_lbs)
            
    def generate_macro(self,data):#,child_lbs):
        report_xls = HrlbsMacro(data, self)
        values = {
            'xls_filename_macro': "MACRO LBS - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        # values_child = {
        #     'xls_filename_macro': "MACRO LBS - " + self.name + ".xlsx",
        #     'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        #     'paid': True,
        # }
        self.write(values)
        # child_lbs.write(values_child)