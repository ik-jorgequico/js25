from .afp_reports import AfpExcelReport
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import base64

from datetime import timedelta, datetime, date


class AfpInterface(models.Model):
    _name = 'afp.interface'
    _description = 'Reporte AFP'


    name = fields.Char("Reporte AFP")

    payslip_run_id = fields.Many2one('hr.payslip.run',
                                     string="Lote",
                                     store=True,
                                     )
    

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte EXCEL')
    
    pdf_filename = fields.Char()
    pdf_binary = fields.Binary('Reporte PDF')
    
    ########################################################
    
    periodo = fields.Char("Periodo")
    company_id = fields.Many2one('res.company', string='Compañia', required=True, default=lambda self: self.env.company)
    
    fondo_habitat = fields.Float(store=True, default = 0)
    fondo_integra = fields.Float(store=True, default = 0)
    fondo_prima = fields.Float(store=True, default = 0)
    fondo_profuturo = fields.Float(store=True, default = 0)
    
    comision_habitat = fields.Float(store=True, default = 0)
    comision_integra = fields.Float(store=True, default = 0)
    comision_prima = fields.Float(store=True, default = 0)
    comision_profuturo = fields.Float(store=True, default = 0)
    
    prima_habitat = fields.Float(store=True, default = 0)
    prima_integra = fields.Float(store=True, default = 0)
    prima_prima = fields.Float(store=True, default = 0)
    prima_profuturo = fields.Float(store=True, default = 0)
    
    comision_saldo_habitat = fields.Float(store=True, default = 0)
    comision_saldo_integra = fields.Float(store=True, default = 0)
    comision_saldo_prima = fields.Float(store=True, default = 0)
    comision_saldo_profuturo = fields.Float(store=True, default = 0)
    
    employee_habitat = fields.Integer(store=True, default = 0)
    employee_integra = fields.Integer(store=True, default = 0)
    employee_prima = fields.Integer(store=True, default = 0)
    employee_profuturo = fields.Integer(store=True, default = 0)
    
    total_habitat = fields.Float(store=True, default = 0)
    total_integra = fields.Float(store=True, default = 0)
    total_prima = fields.Float(store=True, default = 0)
    total_profuturo = fields.Float(store=True, default = 0)
    
    sum_fondo = fields.Float(store=True, default = 0)
    sum_comision = fields.Float(store=True, default = 0)
    sum_comision_saldo = fields.Float(store=True, default = 0)
    sum_prima = fields.Float(store=True, default = 0)
    sum_total = fields.Float(store=True, default = 0)
    sum_employee = fields.Integer(store=True, default = 0)
    
    fondo_inactive = fields.Float(store=True, default = 0)
    comision_inactive = fields.Float(store=True, default = 0)
    prima_inactive = fields.Float(store=True, default = 0)
    comision_saldo_inactive = fields.Float(store=True, default = 0)
    employee_inactive = fields.Integer(store=True, default = 0)
    total_inactive = fields.Float(store=True, default = 0)
    
    def _last_day_of_month(self, any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)
    
    def process_data_pdf(self, payslip_run_id):
        
        payslip = self.env['hr.payslip'].search([('date_from', '=', payslip_run_id.date_start), ('date_to', '=', payslip_run_id.date_end)])
        pension_system = self.env['pension.system'].search([('name','not in',('onp','ONP'))], order = "name asc")
        list_fondo, list_seguro, list_comision_flujo, list_comision_mixto = [], [], [], []
        list_fondo_inactive, list_seguro_inactive, list_comision_flujo_inactive, list_comision_mixto_inactive = [], [], [], []
                
        cont, cont_2 = [], []

        for pen in pension_system:
            
            aux, aux1, aux2, aux3 = [], [], [], []
            aux_inactive, aux1_inactive, aux2_inactive, aux3_inactive = [], [], [], []
            
            for pay in payslip:
                if(pay.employee_id.pension_system_id.name == pen.name):

                    if(pay.lbs_id):                        
                        
                        if(pay.employee_id.last_contract_date.day == self._last_day_of_month(pay.date_from).day):
                            amount = pay.lbs_id.deductions.filtered(lambda x: x.name == "Afp - Fondo").amount_report
                            aux_inactive.append(pay.lbs_id.deductions.filtered(lambda x: x.name == "Afp - Fondo").amount_lbs)
                            aux1_inactive.append(pay.lbs_id.deductions.filtered(lambda x: x.name == "Afp - Seguro").amount_lbs)
                            if(pay.employee_id.pension_mode == "mixto"):
                                aux2_inactive.append(pay.lbs_id.deductions.filtered(lambda x: x.name == "Afp - Comisión").amount_lbs)
                            if(pay.employee_id.pension_mode == "flujo"):
                                aux3_inactive.append(pay.lbs_id.deductions.filtered(lambda x: x.name == "Afp - Comisión").amount_lbs)
                        else:
                            aux_inactive.append(pay.line_ids.filtered(lambda x: x.code == "AFP_FONDO").amount * -1)
                            aux1_inactive.append(pay.line_ids.filtered(lambda x: x.code == "AFP_SEG").amount * -1)
                            
                            if(pay.employee_id.pension_mode == "mixto"):
                                aux2_inactive.append(pay.line_ids.filtered(lambda x: x.code == "AFP_COMIS").amount * -1)
                            if(pay.employee_id.pension_mode == "flujo"):
                                aux3_inactive.append(pay.line_ids.filtered(lambda x: x.code == "AFP_COMIS").amount * -1)
                            

                    aux.append(pay.line_ids.filtered(lambda x: x.code == "AFP_FONDO").amount * -1)
                    aux1.append(pay.line_ids.filtered(lambda x: x.code == "AFP_SEG").amount * -1)
                    
                    if(pay.employee_id.pension_mode == "mixto"):
                        aux2.append(pay.line_ids.filtered(lambda x: x.code == "AFP_COMIS").amount * -1)
                    if(pay.employee_id.pension_mode == "flujo"):
                        aux3.append(pay.line_ids.filtered(lambda x: x.code == "AFP_COMIS").amount * -1)
                    
            
            list_fondo.append(aux)
            list_seguro.append(aux1)
            list_comision_mixto.append(aux2)
            list_comision_flujo.append(aux3)
            
            list_fondo_inactive.append(sum(aux_inactive))
            list_seguro_inactive.append(sum(aux1_inactive))
            list_comision_mixto_inactive.append(sum(aux2_inactive))
            list_comision_flujo_inactive.append(sum(aux3_inactive))
            
            cont.append(len(aux))
            cont_2.append(len(aux_inactive))
        
        comision_habitat_aux, comision_integra_aux, comision_prima_aux, comision_profuturo_aux = list_comision_flujo #habitat - integra - prima - profuturo
        comision_saldo_habitat_aux, comision_saldo_integra_aux, comision_saldo_prima_aux, comision_saldo_profuturo_aux = list_comision_mixto # #habitat - integra - prima - profuturo
        fondo_habitat_aux, fondo_integra_aux, fondo_prima_aux, fondo_profuturo_aux = list_fondo # #habitat - integra - prima - profuturo
        prima_habitat_aux, prima_integra_aux, prima_prima_aux, prima_profuturo_aux = list_seguro # #habitat - integra - prima - profuturo
        
        
        self.fondo_inactive = round(sum(list_fondo_inactive),2)
        self.comision_inactive = round(sum(list_comision_flujo_inactive),2)
        self.prima_inactive = round(sum(list_seguro_inactive),2)
        self.comision_saldo_inactive = round(sum(list_comision_mixto_inactive),2)
        self.employee_inactive = sum(cont_2)
        
        self.total_inactive = self.comision_inactive + self.prima_inactive + self.comision_saldo_inactive
        
        
        # poner las variables en orden asc
        self.comision_habitat, self.comision_integra, self.comision_prima, self.comision_profuturo = round(sum(comision_habitat_aux),2), round(sum(comision_integra_aux),2), round(sum(comision_prima_aux),2), round(sum(comision_profuturo_aux),2)
        self.comision_saldo_habitat, self.comision_saldo_integra, self.comision_saldo_prima, self.comision_saldo_profuturo = round(sum(comision_saldo_habitat_aux),2), round(sum(comision_saldo_integra_aux),2), round(sum(comision_saldo_prima_aux),2), round(sum(comision_saldo_profuturo_aux),2)
        self.fondo_habitat, self.fondo_integra, self.fondo_prima, self.fondo_profuturo = round(sum(fondo_habitat_aux),2), round(sum(fondo_integra_aux),2), round(sum(fondo_prima_aux),2), round(sum(fondo_profuturo_aux),2)
        self.prima_habitat, self.prima_integra, self.prima_prima, self.prima_profuturo = round(sum(prima_habitat_aux),2), round(sum(prima_integra_aux),2), round(sum(prima_prima_aux),2), round(sum(prima_profuturo_aux),2)
        
        self.total_habitat = self.comision_habitat + self.prima_habitat
        self.total_integra = self.comision_integra + self.prima_integra
        self.total_prima = self.comision_prima + self.prima_prima
        self.total_profuturo = self.comision_profuturo + self.prima_profuturo
        
        self.employee_habitat, self.employee_integra, self.employee_prima, self.employee_profuturo = cont  
        
        self.sum_fondo = self.fondo_habitat + self.fondo_integra + self.fondo_prima + self.fondo_profuturo
        self.sum_comision = self.comision_habitat + self.comision_integra + self.comision_prima + self.comision_profuturo 
        self.sum_comision_saldo = self.comision_saldo_habitat + self.comision_saldo_integra + self.comision_saldo_prima + self.comision_saldo_profuturo
        self.sum_prima = self.prima_habitat + self.prima_integra + self.prima_prima + self.prima_profuturo
        self.sum_total = self.total_habitat + self.total_integra + self.total_prima + self.total_profuturo
        self.sum_employee = self.employee_habitat + self.employee_integra + self.employee_prima + self.employee_profuturo
              
    def print_pdf(self):    
        self.process_data_pdf(self.payslip_run_id)
        
        report_template_id = self.env['ir.actions.report']._render_qweb_pdf(f"hr_reports_payroll.report_afp_interface", self.id)
        # report_template_id = self.env.ref('hr_reports_payroll.report_afp_interface' ).with_context(force_report_rendering=True)._render_qweb_pdf(self.id)
        self.pdf_binary = base64.b64encode(report_template_id[0])
        self.pdf_filename = self.name + ".pdf"
        
        
    ##########################################################
    

    @api.onchange('payslip_run_id')
    def _payslip_run_id_name(self):
        if self.payslip_run_id:
            self.name = "REPORTE AFP " + self.payslip_run_id.name
            aux = self.payslip_run_id.name.split("-") #agregado
            self.periodo = aux[0]#agregado
            
    @staticmethod
    def _get_periods(start_m, start_y, end_m, end_y):
        start = '{}/{}'.format("{:02d}".format(start_m), start_y)
        end = '{}/{}'.format("{:02d}".format(end_m), end_y)
        periods = [start]
        value = False
        if start == end:
            return periods
        while value != end:
            if start_y == end_y:
                start_m += 1
            else:
                start_m += 1
                if start_m == 13:
                    start_y += 1
                    start_m = 1
            value = '{}/{}'.format("{:02d}".format(start_m), start_y)
            periods.append(value)
        return periods

    def action_generate_report(self):
        for obj in self:
            
            if obj.payslip_run_id is False:
                raise ValidationError('Se tiene que escoger un Lote')

            payslip = self.env['hr.payslip'].search([
                ('payslip_run_id', '=', obj.payslip_run_id.id),
                ('employee_id.cod_cuspp', '!=', False)
            ])
            
            values = []
            start_m = int(self.payslip_run_id.date_start.strftime('%m'))
            start_y = int(self.payslip_run_id.date_start.strftime('%Y'))

            employees = payslip.mapped('employee_id')

            for employee in employees:
                employee_payslip = payslip.filtered(lambda x: x.employee_id == employee)
                rem = 0
                except_amount = ''
                work_type = 'N'
                for slip in employee_payslip:
                    line_ids = slip.line_ids.filtered(lambda x: x.code == 'GROSS')
                    rem += sum(line.amount for line in line_ids)
                if rem == 0:
                    except_amount = 'L'
                begin_business_relation = 'N'
                end_business_relation = 'N'
                
                if employee.first_contract_date and int(employee.first_contract_date.strftime('%m')) == start_m and int(
                        employee.first_contract_date.strftime('%Y')) == start_y:
                    begin_business_relation = 'S'

                if employee.last_contract_date and int(employee.last_contract_date.strftime('%m')) == start_m and \
                        int(employee.last_contract_date.strftime('%Y')) == start_y:
                    end_business_relation = 'S'

                if employee.pension_system_id  :
                    if employee.l10n_latam_identification_type_id and employee.l10n_latam_identification_type_id.l10n_pe_vat_code in ['1', '4', '7']:
                        if employee.l10n_latam_identification_type_id.l10n_pe_vat_code == '1':
                            document_type_id = '0'
                        elif employee.l10n_latam_identification_type_id.l10n_pe_vat_code == '4':
                            document_type_id = '1'
                        else:
                            document_type_id = '4'
                    else:
                        document_type_id = '5'
                    if  employee.second_name:
                        second_name = " " + employee.second_name
                    else :
                        second_name = ""
                    values.append({
                        'cuspp': employee.cod_cuspp or '0',
                        'document_type_id': document_type_id,
                        'document_number': employee.identification_id or '',
                        'lastname': employee.first_last_name or '',
                        'secondname': employee.second_last_name or '',
                        'firstname': (employee.first_name or '') + second_name,
                        'business_relation': 'S',
                        'begin_business_relation': begin_business_relation,
                        'end_business_relation': end_business_relation,
                        'except_amount': except_amount,
                        'rem': rem,
                        'amount_vol_fin': 0,
                        'amount_vol_nfin': 0,
                        'amount_vol': 0,
                        'work_type': work_type,
                        'afp': ''
                    })
            obj.generate_excel(values)

    def generate_excel(self, data):
        report_xls = AfpExcelReport(data, self)
        values = {
            'xls_filename': "AFP_" + self.payslip_run_id.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)
