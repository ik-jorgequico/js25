from .lbs_reports import LBSExcelReport
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64


class LBSInterface(models.Model):
    _name = 'lbs.interface'
    _description = 'Reporte Liquidaciones'

    name = fields.Char(string="Nombre")
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    payslip_run_id = fields.Many2one('hr.payslip.run',
                                     string="LBS LOTE",
                                     store=True,
                                     )

    @api.onchange('payslip_run_id')
    def _payslip_run_id_name(self):
        if self.payslip_run_id:
            self.name = "REPORTE LBS " + \
                        self.payslip_run_id.date_start.strftime("%Y %b") + \
                        " " + \
                        self.payslip_run_id.date_end.strftime("%Y %b")

    def get_amount_line(self,pay,code):
        for line in pay.line_ids.filtered(lambda input: input.code == code):
            return abs(line.total) if (line and line.total is not None) else 0
        return 0

    def action_generate_report(self):

        hr_salary_rule = self.env["hr.salary.rule"].search([
                                ("active","=",True),
                                ("appears_report_lbs",'=',True)
                            ], order="sequence asc")
        
        for obj in self:
            values = [] 
            
            if obj.payslip_run_id is False:
                raise ValidationError('Se tiene que escoger un Lote')

            payslip = self.env['hr.payslip'].search([
                ('payslip_run_id', '=', obj.payslip_run_id.id),
                ('employee_id.last_contract_date',"!=",False)
            ])
            contador = 1

            codes = hr_salary_rule.mapped("code")
            list_codes = [code for code in codes if  sum([self.get_amount_line(pay,code) for pay in payslip]) > 0 ]
            
            for pay in payslip:
                if pay.employee_id :
                    SISTEMA_DE_SALUD = pay.employee_id.health_regime_id.name if pay.employee_id.health_regime_id else ""
                    SALARIO_BASICO = pay.employee_id.contract_id.wage if pay.employee_id.contract_id else 0
                    val1 = {
                        "ID":contador,
                        "CODIGO":pay.employee_id.cod_ref or '',
                        "TIPO DOCUMENTO":pay.employee_id.l10n_latam_identification_type_id.name or '',
                        "NUM DOCUMENTO":pay.employee_id.identification_id or '',
                        "PRIMER APELLIDO":pay.employee_id.first_last_name or '',
                        "SEGUNDO APELLIDO":pay.employee_id.second_last_name or '',
                        "PRIMER NOMBRE":pay.employee_id.first_name or '',
                        "SEGUNDO NOMBRE":pay.employee_id.second_name or '',
                        "CENTRO DE COSTO":pay.employee_id.cod_coste_center or '',
                        "LOCALIDAD": pay.employee_id.location_id.name or '',
                        "AREA/DEPARTAMENTO":pay.employee_id.department_id.name or '',
                        "CARGO/PUESTO DE TRABAJO":pay.employee_id.job_id.name or '',
                        "AFP":pay.employee_id.pension_system_id.name if pay.employee_id.pension_system_id else '',
                        "TIPO COMISION AFP": str(pay.employee_id.pension_mode).upper() or '',
                        "CUSPP":pay.employee_id.cod_cuspp or '',
                        "BANCO HABERES":pay.employee_id.bank_account_id.bank_id.name or '',
                        "CUENTA HABERES":pay.employee_id.bank_account_id.acc_number or '',
                        "FECHA INGRESO":pay.employee_id.first_contract_date or '',
                        "FECHA CESE":pay.employee_id.last_contract_date or '',
                        "SISTEMA DE SALUD":SISTEMA_DE_SALUD,
                        "SALARIO BASICO":SALARIO_BASICO,
                    }
                    """
                        TODA INFORMACION DE LAS REGLAS
                    """
                    val2 = {}
                    for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes).sorted(key=lambda r: r.sequence):
                        val2[rule.name.upper()] = self.get_amount_line(pay,rule.code)
                    
                    val = {**val1, **val2}

                    values.append(val)
                    contador += 1
            obj.generate_excel(values)

    def generate_excel(self, data):
        report_xls = LBSExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE LBS "+self.payslip_run_id.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)
