# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .hr_utilities_report import LiquidationsExcelReport
import base64


class HrUtilities(models.Model):
    _name = 'hr.utilities'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Utilities'

    name = fields.Char(string="Nombre",default="",  store=True,tracking=True)
    current_year = int(datetime.now().date().strftime("%Y"))
    anio = fields.Selection([(str(i),str(i)) for i in range(current_year-3,current_year+3)], "Año", store=True, tracking=True)
    date_from = fields.Date(string="Dia Inicio",required=True,  store=True,tracking=True)
    date_to = fields.Date(string="Dia Fin",required=True,  store=True,tracking=True)
    date_pay = fields.Date(string="Dia de Pago",required=True,tracking=True,  store=True, help="Se necesita para 5ta")
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    regimen_id = fields.Many2one('hr.payroll.structure.type',tracking=True,required=True,store=True,string='Régimen',default=lambda self: self.env['hr.payroll.structure.type'].search([], limit=1).id)

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    child_ids = fields.One2many('hr.utilities.incomes','parent_id', string="Utilidades Empleado",store=True,tracking=True)
    child_ids_count = fields.Integer(compute='_compute_total', store=True,)
    amount_client = fields.Float(string="Monto de Cliente",tracking=True,required=True, )
    percent_client = fields.Float(string="Porcentaje",tracking=True,required=True, )
    amount_100_utilities = fields.Float(string="100% Utilidades",store=True,tracking=True)
    amount_50_total = fields.Float(string="50% para Remuneraciones", store=True,tracking=True)
    amount_50_days_total = fields.Float(string="50% para Dias Trabajados", store=True,tracking=True)
    bimp_total = fields.Float(string="BImp Rem",compute='_compute_total', store=True,tracking=True)
    days_total = fields.Float(string="BImp Dias",compute='_compute_total', store=True,tracking=True)

    factor_total = fields.Float (string="Factor Tot", compute="_compute_factors",store=True,tracking=True,)
    factor_days_total = fields.Float (string="Factor Dias", compute="_compute_factors",store=True,tracking=True,)

    utilities_total = fields.Float(string="Total Utilidades", compute="_compute_utilities_total",tracking=True,store=True,)
    limit_uit = fields.Float(string="7UIT",tracking=True, store=True,compute='_get_7uit')

    # month = fields.Integer(string="Month", required=True)


    # @api.depends('date_pay')
    # def _get_7uit(self):
    #     for record in self:
    #         uit_5ta = self.env["uit.table"].search([("year","=",record.date_pay.year)], limit=1)  
    #         record.limit_uit=  uit_5ta.value * 7
    

    @api.depends('date_pay')
    def _get_7uit(self):
        for record in self:
            if record.date_pay:
                uit_5ta = self.env["uit.table"].search([("year", "=", record.date_pay.year)], limit=1)
                record.limit_uit = uit_5ta.value * 7 if uit_5ta else 0
            else:
                record.limit_uit = 0

    @api.model
    def _get_default_report_id(self):
        return self.env.ref('hr_utilities.action_report_utilities', False)
    
    report_id = fields.Many2one('ir.actions.report',
        string="Report", domain="[('model','=','hr.utilities.incomes'),('report_type','=','qweb-pdf')]", default=_get_default_report_id)

    

    def action_dowload_report_pdf_utilities(self):
        self.ensure_one()
        return {
            'name': 'CTS',
            'type': 'ir.actions.act_url',
            'url': '/print/utilities?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        }
    

    @api.depends('child_ids.utilities_total_amount')
    def _compute_utilities_total(self):
        for record in self:
            record.utilities_total = sum([i.utilities_total_amount for i in record.child_ids])

    @api.depends('bimp_total','amount_50_total','days_total','amount_50_days_total',)
    def _compute_factors(self):
        for record in self:
            if record.bimp_total and record.amount_50_total:
                record.factor_total = round(record.amount_50_total/record.bimp_total,8)

            if record.days_total and record.amount_50_days_total:
                record.factor_days_total = round(record.amount_50_days_total/record.days_total,8)

    @api.onchange('amount_client','percent_client')
    def _onchange_amounts(self):
        if self.amount_client and self.percent_client:
            self.amount_100_utilities = round(self.amount_client*self.percent_client/100,2)
            self.amount_50_total = round(self.amount_100_utilities/2,2)
            self.amount_50_days_total = round(self.amount_100_utilities/2)

    @api.onchange('company_id',"anio","regimen_id")
    def _onchange_name(self):
        if self.company_id and self.anio and self.regimen_id:
            self.name = "Utilidades " + self.company_id.name +" " + self.anio

    @api.depends('child_ids')
    def _compute_total(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)
            record.bimp_total = sum([i.bimp_total for i in record.child_ids ])
            record.days_total = sum([i.days_work for i in record.child_ids ])

    @api.onchange("anio")
    def _onechange_dates(self):
        if self.anio:
            self.date_from = datetime.strptime("01/01/"+str(self.anio), '%d/%m/%Y')
            self.date_to = datetime.strptime("31/12/"+str(self.anio), '%d/%m/%Y')

    def action_open_hr_utilities(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.utilities.incomes",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Utilidades",
            'flags':{'mode':'edit'} 
        }
        
    def compute_sheet(self):
        self.ensure_one()
        self.child_ids.income_lines.unlink()
        self.child_ids.unlink()

        employees = self.env["hr.payslip.line"].search(
                                    [
                                        ("date_from",">=",self.date_from),
                                        ("date_to","<=",self.date_to),
                                    ]).mapped("employee_id")

        
        if employees:
            if not self.date_pay:
                raise UserError(_("El campo 'Dia de Pago' (date_pay) es obligatorio. Por favor, establezca un valor antes de continuar."))

            val_list = [{"employee_id": emp.id, "parent_id": self.id, "date_pay": self.date_pay} for emp in employees]  # Asegúrate de incluir "date_pay"
            self.env['hr.utilities.incomes'].create(val_list)
            self.env.cr.commit()
        self.after_create_values()
        
        date_related = self.date_pay.replace(day=15)
        object_5ta = self.env["hr.5ta"].create({
            "date_5ta":date_related,
            "company_id":self.company_id.id,
            "regimen_id":self.regimen_id.id,
            "name":"5TA CATEGORIA - " + str(date_related.strftime("%b")).upper() + " " + str(date_related.year),
            "month": date_related.strftime("%m"),
            "year": str(date_related.year),
        })
        self.env.cr.commit()
        object_5ta.compute_sheet()
        #### SE LLEVAN LOS PORCENTAJES DE 5ta A CADA EMPLEADO
        employee_ids = self.child_ids.mapped("employee_id")
        for employee_id in employee_ids:
            object_5ta_line = object_5ta.child_ids.filtered(lambda x: x.employee_id.id == employee_id.id)
            utilitie = self.child_ids.filtered(lambda x:x.employee_id.id == employee_id.id)

            utilitie.person_percent_max = 0
            utilitie.rem_bruta_5ta_aux = 0

            if object_5ta_line:
                utilitie.person_percent_max = object_5ta_line.person_percent_max
                utilitie.rem_bruta_5ta_aux = object_5ta_line.grati_projection + object_5ta_line.salary_projection + object_5ta_line.salary_amount
                
        object_5ta.child_ids.subline_ids.unlink()
        object_5ta.child_ids.unlink()
        object_5ta.unlink()
        self.compute_sheet_import()
        
    def after_create_values(self):
        pass

    def compute_sheet_import(self):
        employees = self.child_ids.mapped("employee_id")
        payslip = self.env['hr.payslip'].search([("date_from","<=",self.date_pay),
                                                 ("date_to",">=",self.date_pay),])
        
        for employee in employees:
            pay = payslip.filtered(lambda x: x.employee_id == employee)
            input = pay.input_line_ids
            input_I_UTI = input.filtered(lambda x: x.input_type_id.code == "I_UTI")
            input_I_DEV_IMP_5TA = input.filtered(lambda x: x.input_type_id.code == "I_5TA_DIRECT")
            input_I_ADEL_UTIL = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_UTIL")
            
            child_id = self.child_ids.filtered(lambda x: x.employee_id == employee )

            utilities_total_amount = sum([i.utilities_total_amount for i in child_id ])
            ir_qdir = sum([i.ir_qdir for i in child_id ])
            utilities_total_amount_neta = sum([i.utilities_total_amount_neta for i in child_id ])

            if input_I_UTI:
                input_I_UTI.amount = float(utilities_total_amount)
            if input_I_DEV_IMP_5TA:
                input_I_DEV_IMP_5TA.amount = float(ir_qdir)
            if input_I_ADEL_UTIL:
                input_I_ADEL_UTIL.amount = float(utilities_total_amount_neta)

        payslip.compute_sheet()


    """
        REPORTES EXCEL
    """
    def action_dowload_report_tabular_utilities(self):
        for record in self:
            values = []

            for child_id in record.child_ids:
                values.append({
                    "Codidgo":child_id.employee_id.cod_ref or '',
                    "Doc.":child_id.employee_id.identification_id or '',
                    "Apellidos y Nombres":child_id.employee_id.name or '',
                    "Fecha Ingreso":child_id.first_contract_date or '',
                    "Fecha Cese":child_id.last_contract_date or '',
                    "BImp Dias":child_id.days_work or '',
                    "Factor Dia":record.factor_days_total or '',
                    "Utilidades Dias":child_id.utilities_days or '',
                    "BImp Rem":child_id.bimp_total or '',
                    "Factor Tot":record.factor_total or '',
                    "Utilidades Remu":child_id.utilities_total or '',
                    "Total Utilidades":child_id.utilities_total_amount or '',
                    "Porcentaje 5ta":child_id.person_percent_max/100 or 0,
                    "Rem. Bruta 5ta":child_id.rem_bruta_5ta_aux or '',
                    "Rem. Neta con Utilidades":child_id.rem_net_util or '',
                    "7UIT":child_id.limit_uit or '',
                    "IR QDIR":child_id.ir_qdir or '',
                    "Monto de Prestamos":child_id.loan or '',
                    "Total Descuentos":child_id.t_desc or '',
                    "T. Utilidades Netas":child_id.utilities_total_amount_neta or '',
                })
            record.generate_excel(values)



    def generate_excel(self,data):
        report_xls = LiquidationsExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE LIQUIDACIONES TABULAR "+self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)
 
 
    def _is_validated_in_sending(self, utility_income):
        for record in self:
            if not utility_income.employee_id.last_contract_date:
                return utility_income
            last_contract_date = utility_income.employee_id.last_contract_date
            # Si AÑO del CALCULO DE UTILIDAD es 2023. Tiene que haber cesado antes del 01/04/2024. En el envío masivo.
            bound = datetime.strptime("01/04/"+str(int(record.anio)+1), '%d/%m/%Y').date()
            if last_contract_date < bound :
                return utility_income
            
 
    # def send_utilities_email(self):
    #     ir_model_data = self.env['ir.model.data']
    #     template = ir_model_data.check_object_reference(
    #         'hr_utilities', 'email_template_edi_hr_utilities')[1]
    #     template_id = self.env['mail.template'].browse(template)
    #     if template_id:
    #         for utility_income in self.child_ids:
    #             if self._is_validated_in_sending(utility_income):
    #                 template_id.send_mail(utility_income.id, force_send=True)

