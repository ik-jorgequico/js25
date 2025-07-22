from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64

from odoo.exceptions import UserError, ValidationError

from .hr_loan_macro import HrloanMacro

class Hrloan(models.Model):
    _inherit = 'hr.loan'
    _description = 'Hr loan'

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    def action_dowload_report_macro_loan(self):
    
        for obj in self:
            values = []

            # pagado = 0
            # count = 0
            # cuota_n = ""

            # for child_id in obj.loan_lines:
            #     if(child_id.paid):
            #         pagado += child_id.amount
            #         count += 1
            #     cuota_n = child_id.date

            # if(self.state != "approve"):
            #     estado = "Rechazado"
            
            # else:
            #     if(round(obj.loan_amount - pagado,2) <= 0 ):
            #         estado = "Pagado"
            #     else:
            #         estado = "Aprobado"
            

            # val1 = {
            #     "Cod.":obj.employee_id.cod_ref or '',
            #     "dni": obj.employee_id.identification_id or '',
            #     "nombre":obj.employee_id.name or '',
            #     "centro":'Prepago',
            #     "localidad":obj.employee_id.location_id.name or '',
            #     "area":obj.department_id.name or '',
            #     "first":obj.employee_id.first_contract_date or '',
            #     "puesto":obj.job_position.name or '',
            #     "solicitud": obj.date or '', 
            #     "cuota_1":obj.payment_date or '',
            #     "cuota_n": cuota_n or '',
            #     "n_cuotas": obj.installment or '',
            #     "importe": obj.loan_amount or '',
            #     "val_cuota": '',
            #     "cuotas_pagadas": count,
            #     "cuotas_pendientes": obj.installment - count or '',
            #     "importe_pagado": pagado or '',
            #     "importe_pendiente": obj.loan_amount - pagado or  '',
            #     "estado": estado or '',

            # }

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

            concepto = "PRESTAMO"

            val1 = {
                "dni":dni or '',
                "nombre":name or '',
                "concepto":concepto or '',
                "pago":obj.date or '',
                "monto":obj.loan_amount or '',
                "forma":forma,
                "cod_oficina":oficina or '',
                "cod_cuenta":cuenta or '',
                "referencia": 'PRESTAMO',
                "cci": cci or '',

            }


            val = {**val1}

            values.append(val)

            obj.generate_macro(values)
            
    def generate_macro(self,data):
        report_xls = HrloanMacro(data, self)
        values = {
            'xls_filename_macro': "MACRO PRESTAMOS - " + self.name + ".xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)