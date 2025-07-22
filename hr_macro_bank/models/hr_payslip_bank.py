from odoo import fields, models, api, _
from datetime import datetime
import base64
from odoo.exceptions import ValidationError
from .hr_payslip_macro_bank import HrpayslipMacroBank

class Hrpayslip(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Hr payslip'

    payday = fields.Date("Fecha de pago", store=True)

    xls_filename_macro = fields.Char()
    xls_binary_macro = fields.Binary('Reporte Macro')

    def action_dowload_report_macro_payslip(self):
        if not self.payday:
            raise ValidationError(_("Por favor ingrese una fecha de pago"))
        
        for obj in self:
            data_by_bank = {}

            for child_id in obj.slip_ids:

                last_contract = child_id.employee_id.last_contract_date
                if last_contract and last_contract.year == obj.date_start.year and last_contract.month == obj.date_start.month:
                    continue

                meses_dic = {
                    1: "ENE", 2: "FEB", 3: "MAR", 4: "ABR",
                    5: "MAY", 6: "JUN", 7: "JUL", 8: "AGO",
                    9: "SEP", 10: "OCT", 11: "NOV", 12: "DIC"
                }

                bank_name = child_id.employee_id.bank_account_id.bank_id.name

                # Definir códigos y abreviaturas de los bancos
                bank_codes = {
                    "BANCO DE CREDITO DEL PERU": {"code": "BCPLPEPL", "abbr": "BCP"},
                    "BANCO BBVA PERU": {"code": "BCONPEPL", "abbr": "BBVA"},
                    "SCOTIABANK PERU S.A.A.": {"code": "BSUDPEPL", "abbr": "SCOTIABANK"},
                    # Agrega más bancos aquí
                }

                bank_info = bank_codes.get(bank_name)
                if not bank_info:
                    continue

                bank_code = bank_info['code']
                bank_abbr = bank_info['abbr']

                if bank_name == "BANCO DE CREDITO DEL PERU":
                    # Datos para BCP
                    acc_number = child_id.employee_id.bank_account_id.acc_number or ''
                    oficina = acc_number[:3]
                    cuenta = acc_number[3:]
                    name = (child_id.employee_id.name or '')[:30]
                    dni = (child_id.employee_id.identification_id or '')[:8]
                    monto = child_id.net_wage or ''
                    val1 = {
                        "TIPO DE REGISTRO": 'A',
                        "TIPO DE CUENTA DE ABONO": 'A',
                        "CUENTA DE ABONO": cuenta,
                        "TIPO DE DOCUMENTO DE IDENTIDAD": "1",
                        "NUMERO DE DOCUMENTO DE IDENTIDAD": dni,
                        "NOMBRE DEL TRABAJADOR": name,
                        "TIPO DE MONEDA DE ABONO": "S",
                        "MONTO DE ABONO": monto,
                        "VALIDACION IDC DEL PROVEEDOR VS CUENTA": "S",
                    }
                elif bank_name == "BANCO BBVA PERU":
                    # Datos para BBVA
                    acc_number = child_id.employee_id.bank_account_id.acc_number or ''
                    tipo_doc = "1"  # Asume DNI
                    num_doc = (child_id.employee_id.identification_id or '')[:15]
                    name = (child_id.employee_id.name or '')[:50]
                    tipo_cuenta = "0"  # Ajusta según sea necesario
                    monto = child_id.net_wage or ''
                    val1 = {
                        "TIPO DE DOCUMENTO": tipo_doc,
                        "NUMERO DE DOCUMENTO": num_doc,
                        "NOMBRE DEL BENEFICIARIO": name,
                        "TIPO DE CUENTA": tipo_cuenta,
                        "NUMERO DE CUENTA": acc_number,
                        "MONTO": monto,
                        # Agrega más campos si es necesario
                    }
                elif bank_name == "SCOTIABANK PERU S.A.A.":
                    # Datos para Scotiabank
                    tipo_doc = "1"  # Asume DNI
                    num_doc = (child_id.employee_id.identification_id or '')[:12]
                    name = (child_id.employee_id.name or '')[:40]
                    forma_pago = "A"  # Ajusta según sea necesario
                    cuenta_scotia = child_id.employee_id.bank_account_id.acc_number or ''
                    cuenta_interbancaria = child_id.employee_id.bank_account_id.cci or ''
                    regimen_laboral = "X"  # Ajusta según sea necesario
                    concepto = f"PAYS {meses_dic[self.date_start.month]}{str(self.date_start.year)[2:]}"
                    monto = child_id.net_wage or ''
                    val1 = {
                        "TIPO DE DOCUMENTO": tipo_doc,
                        "DOCUMENTO DE IDENTIDAD": num_doc,
                        "NOMBRE DEL EMPLEADO": name,
                        "FORMA DE PAGO": forma_pago,
                        "CUENTA SCOTIABANK": cuenta_scotia,
                        "CUENTA INTERBANCARIA": cuenta_interbancaria,
                        "REGIMEN LABORAL": regimen_laboral,
                        "CONCEPTO": concepto,
                        "IMPORTE": monto,
                    }
                else:
                    continue  # Si el banco no está

                # Agregar el registro al diccionario data_by_bank
                if bank_abbr not in data_by_bank:
                    data_by_bank[bank_abbr] = []
                data_by_bank[bank_abbr].append(val1)

            if not data_by_bank:
                raise ValidationError(_("No se encontraron datos para generar el reporte"))

            obj.generate_macro(data_by_bank)
            
    def generate_macro(self, data_by_bank):
        report_xls = HrpayslipMacroBank(data_by_bank, self)
        values = {
            'xls_filename_macro': f"MACRO PAYSLIP - {self.name}.xlsx",
            'xls_binary_macro': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)