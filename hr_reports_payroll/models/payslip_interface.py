from .payslip_reports import PayslipExcelReport
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64
from dateutil.relativedelta import relativedelta

from datetime import  timedelta, datetime, date

class PayslipInterface(models.Model):
    _name = 'payslip.interface'
    _description = 'Reporte Nomina'

    name = fields.Char(store=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote", store=True)
    
    @api.onchange('payslip_run_id')
    #Nombre del reporte de la Planilla
    def _payslip_run_id_name(self):
        if self.payslip_run_id:
            self.name = "REPORTE PLANILLA " + self.payslip_run_id.name
    #Filtra los dias trabajados que coincidan con el codigo, de las reglas, si es asi 
    #devolvera los dias trabajados 
    def get_day_worked_days(self,pay,code):
        input_line = pay.worked_days_line_ids.filtered(lambda input: input.code == code)
        if input_line and len(input_line) == 1:
            return input_line.number_of_days
        return 0
    def get_amount_line(self,pay,code):
        for line in pay.line_ids.filtered(lambda input: input.code == code):
            return abs(line.total) if (line and line.total is not None) else 0
        return 0
        
    
    @staticmethod    
    def _first_day_of_month(any_day):
        return any_day - timedelta(days=(any_day.day  - 1))
    
    @staticmethod    
    def _last_day_of_month(any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        # this will never fail 
        return next_month - timedelta(days=next_month.day)

    def _is_last_day_of_month(self,date):
            if date:
                return self._last_day_of_month(date) ==  date
            return False
    
    def action_generate_report(self):

        hr_salary_rule = self.env["hr.salary.rule"].search([
                                ("active","=",True),
                            ], order="sequence asc")
        
        for obj in self:
            
            if obj.payslip_run_id is False:
                raise ValidationError('Se tiene que escoger un Lote')
            
            payslip = self.env['hr.payslip'].search([
                    ('payslip_run_id', '=', obj.payslip_run_id.id),
                ])
            contador = 1
            codes = hr_salary_rule.mapped("code")
            list_codes = [code for code in codes if  sum([self.get_amount_line(pay,code) for pay in payslip]) > 0 ]
            
            payslip_pay = payslip.filtered(lambda x: not x.lbs_id or (x.lbs_id and self._is_last_day_of_month(x.employee_id.last_contract_date)) ).sorted(key = lambda r:r.employee_id.name)
            payslip_lbs = payslip.filtered(lambda x: x.lbs_id ).sorted(key = lambda r:r.employee_id.name)
            data = {}

            """
                GET INFORMATION PAYSLIP
            """
            values = [] 
            for pay in payslip_pay:
                if pay.employee_id :
                    DIAS_TRABAJADOS =    self.get_day_worked_days(pay,'WORK100')
                    DIAS_VAC    =   self.get_day_worked_days(pay,'LEAVE23')
                    DIAS_LIC_SIN_GOCE   =  self.get_day_worked_days(pay,'LEAVE05')
                    DIAS_LIC_CON_GOCE   =  self.get_day_worked_days(pay,'LEAVE35') +\
                        self.get_day_worked_days(pay,'LEAVE29') +\
                        self.get_day_worked_days(pay,'LEAVE26') +\
                        self.get_day_worked_days(pay,'LEAVE25')
                    INASIST  = self.get_day_worked_days(pay,'LEAVE07')
                    DIAS_LIC_POR_PATERNIDAD =    self.get_day_worked_days(pay,'LEAVE28')
                    DIAS_DESC_MEDICO    =   self.get_day_worked_days(pay,'LEAVE20')
                    DIAS_SUBS_INCAPAC   =  self.get_day_worked_days(pay,'LEAVE21')
                    DIAS_SUBS_MAT   =  self.get_day_worked_days(pay,'LEAVE22') +\
                                    self.get_day_worked_days(pay,'LEAVE09')
                    DIAS_SUSPENSION =    self.get_day_worked_days(pay,'LEAVE01')
                    vacation_purchased = self.env["hr.vacation.purchased"].search(
                        [
                            ("date_from",">=",pay.date_from),
                            ("date_to","<=",pay.date_to),
                            ("employee_id","=",pay.employee_id.id),
                            ])
                    DIAS_COMPRA_VAC = sum([i.number_real_days for i in vacation_purchased])
                    TOTAL_DIAS =   DIAS_TRABAJADOS + DIAS_VAC+ DIAS_LIC_SIN_GOCE+ DIAS_LIC_CON_GOCE+ INASIST+ DIAS_LIC_POR_PATERNIDAD+ DIAS_DESC_MEDICO+ DIAS_SUBS_INCAPAC+ DIAS_SUBS_MAT+ DIAS_SUSPENSION
                    val1 = {
                        "ID":contador,
                        "CODIGO":pay.employee_id.cod_ref or '',
                        "REGIMEN LABORAL":pay.employee_id.contract_id.peru_employee_regime.name or '',
                        "TIPO DOCUMENTO":pay.employee_id.l10n_latam_identification_type_id.name or '',
                        "NUM DOCUMENTO":pay.employee_id.identification_id or '',
                        "PRIMER APELLIDO":pay.employee_id.first_last_name or '',
                        "SEGUNDO APELLIDO":pay.employee_id.second_last_name or '',
                        "PRIMER NOMBRE":pay.employee_id.first_name or '',
                        "SEGUNDO NOMBRE":pay.employee_id.second_name or '',
                        "CENTRO DE COSTO":pay.employee_id.cod_coste_center.name or '',
                        "LOCALIDAD": pay.employee_id.location_id.name or '',
                        "AREA/DEPARTAMENTO":pay.employee_id.department_id.name or '',
                        "CARGO/PUESTO DE TRABAJO":pay.employee_id.job_id.name or '',
                        "AFP":pay.employee_id.pension_system_id.name if pay.employee_id.pension_system_id else '',
                        "TIPO COMISION AFP": str(pay.employee_id.pension_mode).upper() if pay.employee_id.pension_mode else '',
                        "CUSPP":pay.employee_id.cod_cuspp or '',
                        "BANCO HABERES":pay.employee_id.bank_account_id.bank_id.name or '',
                        "CUENTA HABERES":pay.employee_id.bank_account_id.acc_number or '',
                        "FECHA INGRESO":pay.employee_id.first_contract_date or '',
                        "FECHA CESE":pay.employee_id.last_contract_date or '',
                    }
                    if DIAS_TRABAJADOS > 0:
                        val1["Dias_DIAS TRABAJADOS"] = DIAS_TRABAJADOS
                    if DIAS_VAC > 0:
                        val1["Dias_DIAS_VAC"] = DIAS_VAC
                    if DIAS_LIC_SIN_GOCE > 0:
                        val1["Dias_DIAS LIC SIN GOCE"] = DIAS_LIC_SIN_GOCE
                    if DIAS_LIC_CON_GOCE > 0:
                        val1["Dias_DIAS LIC CON GOCE"] = DIAS_LIC_CON_GOCE
                    if INASIST > 0:
                        val1["Dias_INASIT"] = INASIST
                    if DIAS_LIC_POR_PATERNIDAD > 0:
                        val1["Dias_DIAS LIC POR PATERNIDAD"] = DIAS_LIC_POR_PATERNIDAD
                    if DIAS_DESC_MEDICO > 0:
                        val1["Dias_DIA DESC MEDICO"] = DIAS_DESC_MEDICO
                    if DIAS_SUBS_INCAPAC > 0:
                        val1["Dias_SUBS INCAPACIDAD"] = DIAS_SUBS_INCAPAC
                    if DIAS_SUBS_MAT > 0:
                        val1["Dias_SUBS MATERNIDAD"] = DIAS_SUBS_MAT
                    if DIAS_SUSPENSION > 0:
                        val1["Dias_SUSPENSION"] = DIAS_SUSPENSION
                    if DIAS_COMPRA_VAC > 0:
                        val1["Dias_COMPRA VAC"] = DIAS_COMPRA_VAC
                    if TOTAL_DIAS > 0:
                        val1["Dias_TOTAL DIAS"] = TOTAL_DIAS
                    
                    SISTEMA_DE_SALUD = pay.employee_id.health_regime_id.name if pay.employee_id.health_regime_id else ""
                    SALARIO_BASICO = pay.employee_id.contract_id.wage if pay.employee_id.contract_id else 0
                
                    val1["SISTEMA DE SALUD"] =  SISTEMA_DE_SALUD
                    val1["SALARIO BASICO"] = SALARIO_BASICO

                    if not pay.lbs_id:
                        """
                                TODA INFORMACION DE LAS REGLAS
                        """
                        val2 = {}
                        title = "TOTAL INGRESO"
                        total = 0
                        for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code in ["BASIC","BASIC_NA"] and x.appears_report_payroll).sorted(key=lambda r: r.sequence):
                        # for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code in ["BASIC","BASIC_NA"] and x.appears_lbs).sorted(key=lambda r: r.sequence):                        
                            amount = self.get_amount_line(pay,rule.code)
                            if amount > 0:
                                val2["Inc_"+rule.name.upper()] = amount
                                total += amount
                        val2[title] = total

                        title = "TOTAL DEDUCCION"
                        total = 0
                        for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code == "DED").sorted(key=lambda r: r.sequence):
                            amount = self.get_amount_line(pay,rule.code)
                            if amount > 0:
                                val2["Ded_"+rule.name.upper()] = amount
                                total += amount
                        val2[title] = total

                        val2["NETO"] = val2["TOTAL INGRESO"] - val2["TOTAL DEDUCCION"]

                        title = "TOTAL APORTACIONES"
                        total = 0
                        for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code == "COMP").sorted(key=lambda r: r.sequence):
                            amount = self.get_amount_line(pay,rule.code)
                            if amount > 0:
                                val2["Apo_"+rule.name.upper()] = amount
                                total += amount
                        val2[title] = total

                    else:
                        """
                                TODA INFORMACION DE LAS REGLAS
                        """
                        val2 = {}
                        title = "TOTAL INGRESO"
                        total = 0
                        for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code in ["BASIC","BASIC_NA"] and x.appears_report_payroll).sorted(key=lambda r: r.sequence):
                        # for rule in hr_salary_rule.filtered(lambda x:x.code in list_codes and x.category_id.code in ["BASIC","BASIC_NA"] and x.appears_nomina).sorted(key=lambda r: r.sequence):
                            amount = self.get_amount_line(pay,rule.code)
                            if amount > 0:
                                val2["Inc_"+rule.name.upper()] = amount
                                total += amount
                        val2[title] = total

                        title = "TOTAL DEDUCCION"
                        total = 0
                        for deduction in pay.lbs_id.deductions:
                            amount = deduction.amount_report
                            if amount > 0:
                                val2["Ded_"+deduction.name.upper()] = amount
                                total += amount
                        val2[title] = total

                        val2["NETO"] = val2["TOTAL INGRESO"] - val2["TOTAL DEDUCCION"]

                        title = "TOTAL APORTACIONES"
                        total = 0
                        for aportation in pay.lbs_id.aportations:
                            amount = aportation.amount_report
                            if amount > 0:
                                val2["Apo_"+aportation.name.upper()] = amount
                                total += amount
                        val2[title] = total


                    val = {**val1, **val2}

                    values.append(val)
                    contador += 1


            data["pay"] = values            
            """
                GET INFORMATION LBS    
            """

            contador = 1
            values = [] 
            for pay in payslip_lbs:
                val1 = {
                        "ID":contador,
                        "CODIGO":pay.employee_id.cod_ref or '',
                        "REGIMEN LABORAL":pay.employee_id.contract_id.peru_employee_regime.name or '',
                        "TIPO DOCUMENTO":pay.employee_id.l10n_latam_identification_type_id.name or '',
                        "NUM DOCUMENTO":pay.employee_id.identification_id or '',
                        "PRIMER APELLIDO":pay.employee_id.first_last_name or '',
                        "SEGUNDO APELLIDO":pay.employee_id.second_last_name or '',
                        "PRIMER NOMBRE":pay.employee_id.first_name or '',
                        "SEGUNDO NOMBRE":pay.employee_id.second_name or '',
                        "CENTRO DE COSTO":pay.employee_id.cod_coste_center.name or '',
                        "LOCALIDAD":  pay.employee_id.location_id.name or '',
                        "AREA/DEPARTAMENTO":pay.employee_id.department_id.name or '',
                        "CARGO/PUESTO DE TRABAJO":pay.employee_id.job_id.name or '',
                        "AFP":pay.employee_id.pension_system_id.name if pay.employee_id.pension_system_id else '',
                        "TIPO COMISION AFP": str(pay.employee_id.pension_mode).upper() or '',
                        "CUSPP":pay.employee_id.cod_cuspp or '',
                        "BANCO HABERES":pay.employee_id.bank_account_id.bank_id.name or '',
                        "CUENTA HABERES":pay.employee_id.bank_account_id.acc_number or '',
                        "FECHA INGRESO":pay.employee_id.first_contract_date or '',
                        "FECHA CESE":pay.employee_id.last_contract_date or '',
                    }
                
                SISTEMA_DE_SALUD = pay.employee_id.health_regime_id.name if pay.employee_id.health_regime_id else ""
                SALARIO_BASICO = pay.employee_id.contract_id.wage if pay.employee_id.contract_id else 0
                    
                val1["SISTEMA DE SALUD"] = SISTEMA_DE_SALUD
                val1["SALARIO BASICO"] = SALARIO_BASICO

                """
                        TODA INFORMACION DE LAS REGLAS
                """

                val2 = {}
                val2 = self.lbs_codes(pay)

                val = {**val1, **val2}

                values.append(val)
                contador += 1

            data["lbs"] = values            

            obj.generate_excel(data)

    def generate_excel(self, data):
        report_xls = PayslipExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE PLANILLA "+self.payslip_run_id.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)

    def lbs_codes(self,payslip):
        lbs = payslip.lbs_id
        codes = {}
        total_inc = 0
        total_ded = 0
        total_apo = 0
        if lbs.vaca_amount > 0:
            rule_cod = self.env['hr.salary.rule'].search([('code','=',"VACAC_TRUN")])
            total_inc += lbs.vaca_amount
            codes["Inc_"+rule_cod.name.upper()] = round(lbs.vaca_amount,2)
        if lbs.grati_amount > 0:
            rule_cod = self.env['hr.salary.rule'].search([('code','=',"GRAT_LEY_TRUNC")])
            total_inc += lbs.grati_amount
            codes["Inc_"+rule_cod.name.upper()] = round(lbs.grati_amount,2)
        if lbs.boni_extra_grati_amount > 0:
            rule_cod = self.env['hr.salary.rule'].search([('code','=',"BON_LEY_TRUNC")])
            total_inc += lbs.boni_extra_grati_amount
            codes["Inc_"+rule_cod.name.upper()] = round(lbs.boni_extra_grati_amount,2)
        if lbs.cts_amount > 0:
            rule_cod = self.env['hr.salary.rule'].search([('code','=',"CTS_TRUNC")])
            total_inc += lbs.cts_amount
            codes["Inc_"+rule_cod.name.upper()] = round(lbs.cts_amount,2)
        if lbs.quinta_devolucion > 0:
            rule_cod = self.env['hr.salary.rule'].search([('code','=',"DEV_IMP_5TA")])
            total_inc += lbs.quinta_devolucion
            codes["Inc_"+rule_cod.name.upper()] = round(lbs.quinta_devolucion,2)

        # if lbs.lbs_amount > 0:
        #     rule_cod = self.env['hr.salary.rule'].search([('code','=',"COMIS_LBS")])
        #     total_inc += lbs.lbs_amount
        #     codes["Inc_"+rule_cod.name.upper()] = round(lbs.lbs_amount,2)


        if len(lbs.incomes) > 0:
            for income in lbs.incomes:
                if income.total > 0:
                    total_inc += income.total
                    codes["Inc_"+income.name.upper()] = round(income.total,2)
        
        if len(lbs.bons) > 0:
            for bon in lbs.bons:
                if bon.amount > 0:
                    rule_cod = self.env['hr.salary.rule'].search([('code','=',bon.code[2:])])
                    if rule_cod:
                        total_inc += bon.amount
                        codes["Inc_"+rule_cod.name.upper()] = round(bon.amount,2)
        codes["TOTAL INGRESO"] = total_inc

        if len(lbs.deductions) > 0:
            for deduction in lbs.deductions:
                if deduction.amount_lbs > 0:
                    total_ded += deduction.amount_lbs
                    codes["Ded_"+deduction.name.upper()] = round(deduction.amount_lbs,2)

        # if len(lbs.ded) > 0:
        # 	for d in lbs.ded:
        # 		if d.amount > 0:
        # 			rule_cod = self.env['hr.salary.rule'].search([('code','=',d.code[2:])])
        # 			if rule_cod:
        # 				total_ded += d.amount
        # 				codes["Ded_"+rule_cod.name.upper()] = round(d.amount,2)
        codes["TOTAL DEDUCCION"] = total_ded

        if len(lbs.aportations) > 0:
            for aportation in lbs.aportations:
                if aportation.amount_lbs > 0:
                    total_apo += aportation.amount_lbs
                    codes["Apo_"+aportation.name.upper()] = round(aportation.amount_lbs,2)		
        codes["TOTAL APORTACIONES"] = total_apo

        codes["NETO"] = codes["TOTAL INGRESO"] - codes["TOTAL DEDUCCION"] 

        return codes
