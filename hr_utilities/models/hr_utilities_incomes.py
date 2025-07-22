# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta


class HrUtilitiesIncomes(models.Model):
    _name = 'hr.utilities.incomes'
    _description = 'Utility Incomes'

    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Nombre",default="", compute="_compute_name", store=True,)
    date_from = fields.Date(related="parent_id.date_from", store=True,)
    date_to = fields.Date(related="parent_id.date_to", store=True,)
    employee_id = fields.Many2one("hr.employee" ,string="Empleado",store=True,tracking=True)
    date_pay = fields.Date(related = "parent_id.date_pay",required=True,  store=True, help="Se necesita para 5ta")
    structure_type = fields.Char(string="Tipo de Regimen", compute='_compute_structure_type', store=True)
    
    first_contract_date = fields.Date(related = "employee_id.first_contract_date", string="Fecha de Ingreso" , store=True,)
    last_contract_date = fields.Date(related = "employee_id.last_contract_date", string="Fecha de Cese",store=True,)
    parent_id = fields.Many2one("hr.utilities",string="Utilidad",store=True,)
    income_lines = fields.One2many('hr.utilities.incomes.lines','income_id',string="Conceptos de Ingresos",compute='_compute_income_lines',store=True, )
    bimp_total = fields.Float(string="BImp Rem",compute='_compute_total',store=True,)
    days_leave = fields.Integer("Días Ausencias", compute='_compute_days_leave', store=True, help="Se descuentan Tipos de Ausencias sin el Check en Utilidades. Nota: Para descontar Domingos y Feriados, se tiene que modificar en backend.")
    days_work = fields.Integer("BImp Dias", compute='_compute_days_worked', store=True,)
    # aditional_wd = fields.Integer("Adicional BImp Dias", store=True, default=0)
    
    utilities_days=fields.Float(string="Utilidades Dias", compute="_compute_utilities", store=True,)
    utilities_total=fields.Float(string="Utilidades Remu", compute="_compute_utilities", store=True,)

    utilities_total_amount = fields.Float(string="Total Utilidades", compute='_compute_utilities_total_amount', store=True,)

    person_percent_max = fields.Float(string="Porcentaje 5ta", store=True,)
    rem_bruta_5ta_aux = fields.Float(string="Rem. Bruta 5ta", store=True,)
    rem_net_util = fields.Float(string="Rem. Neta con Utilidades", compute="_compute_ir_qdir",store=True,)
    limit_uit = fields.Float(related = "parent_id.limit_uit", store=True,)
    ir_qdir = fields.Float(string="IR QDIR", compute="_compute_ir_qdir", store=True,)
    loan = fields.Float(string="Monto de Prestamos", default=0, store=True,readonly=False, tracking=True )
    t_desc = fields.Float(string="Total Descuentos", compute="_compute_t_desc", store=True,)
    utilities_total_amount_neta = fields.Float(string="T. Utilidades Netas",compute="_compute_utilities_total_amount_neta", store=True,)

    ## Information for Template
    company_id = fields.Many2one(related="parent_id.company_id")
    # street_number = fields.Char(related="parent_id.company_id.street_number")
    # street_number2 = fields.Char(related="parent_id.company_id.street_number2")

    @api.depends('employee_id')
    def _compute_structure_type(self):
        for rec in self:
            rec.structure_type = rec.employee_id.contract_id.peru_employee_regime.abbr or ''
    
    @api.depends('ir_qdir', 'loan')
    def _compute_t_desc(self):
        for record in self:
            record.t_desc = record.ir_qdir + record.loan


    @api.depends('utilities_total_amount','t_desc')
    def _compute_utilities_total_amount_neta(self):
        for record in self:
            record.utilities_total_amount_neta = record.utilities_total_amount - record.t_desc


    @api.depends('utilities_total_amount','person_percent_max','rem_bruta_5ta_aux','limit_uit')
    def _compute_ir_qdir(self):
        for record in self:
            # if record.utilities_total_amount > record.limit_uit:
            # 	record.rem_net_util = record.utilities_total_amount - record.limit_uit
            # 	record.ir_qdir = round(record.person_percent_max*record.utilities_total_amount/100,2)
            if record.employee_id.id == 1037: #ELIMINAR LUEGO
                record.rem_net_util = record.utilities_total_amount
                record.person_percent_max == 14
                record.ir_qdir = round(14*record.utilities_total_amount/100,2)

            elif record.rem_bruta_5ta_aux > record.limit_uit:
                record.rem_net_util = record.rem_bruta_5ta_aux - record.limit_uit
                record.ir_qdir = round(record.person_percent_max*record.utilities_total_amount/100,2)
            else :
                record.rem_net_util = 0
                record.ir_qdir = 0

            #record.ir_qdir = round(record.person_percent_max*record.rem_net_util/100,2)
            # if record.rem_net_util > 0:
            # 	record.ir_qdir = round(record.person_percent_max*record.utilities_total_amount/100,2)
            # else:
            # 	record.ir_qdir = 0


    def action_dowload_report_pdf_utilities(self):
        return {
            'name': 'UTILIDADES',
            'type': 'ir.actions.act_url',
            'url': '/print/utilities?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        }
    
    @api.depends('employee_id','parent_id.anio')
    def _compute_name(self):
        for record in self:
            if record.employee_id:
                record.name = "UTILIDAD " + record.employee_id.name + " " + str(record.parent_id.anio)


    @api.depends('utilities_days','utilities_total')
    def _compute_utilities_total_amount(self):
        for record in self:
            record.utilities_total_amount = record.utilities_days + record.utilities_total


    @api.depends('parent_id.factor_total','parent_id.factor_days_total',)
    def _compute_utilities(self):
        for record in self:
            if record.parent_id.factor_days_total and record.days_work:
                record.utilities_days = round(record.parent_id.factor_days_total*record.days_work,2)
            if record.parent_id.factor_total and record.bimp_total:
                record.utilities_total = round(record.parent_id.factor_total*record.bimp_total,2)


    @api.depends('employee_id','date_from','date_to','first_contract_date','last_contract_date',)
    def _compute_days_leave(self):
        def find_list_sundays(start_date, end_date):
            sundays = self.env['sundays'].search([
                    ("date",">=",start_date),
                    ("date","<=",end_date),
                    ("is_affected_utility","=",True),
                ]
               )
            val_list = [i.date.strftime("%Y-%m-%d") for i in sundays]
            return val_list
        
        
        def list_days(start_date, end_date):
            current_date = start_date
            val_list = []
            
            while current_date <= end_date:
                if current_date.weekday() != 6:
                    val_list.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
            return val_list
        

        for record in self:

            if record.date_from and record.date_to and record.employee_id:
                date_evaluate_from = record.date_from
                date_evaluate_to = record.date_to
                if date_evaluate_from < record.first_contract_date:
                    date_evaluate_from = record.first_contract_date
                if record.last_contract_date:
                    if date_evaluate_to > record.last_contract_date:
                        date_evaluate_to = record.last_contract_date
                
                dates_table_holidays = []
                table_holidays = self.env["holidays"].search([("date_celebrate","<=",date_evaluate_from)])
                for th in table_holidays:
                    date_celebrate = th.date_celebrate
                    date_celebrate = date_celebrate.replace(year =int(date_evaluate_from.strftime("%Y")))
                    if date_evaluate_from  <= date_celebrate <= date_evaluate_to :
                        if date_celebrate.weekday() != 6:
                            dates_table_holidays.append(date_celebrate.strftime("%Y-%m-%d"))
                    
                leave_days = self.env["hr.leave"].search([
                    ("employee_id","=",record.employee_id.id),
                    ("date_from",">=",date_evaluate_from),
                    ("date_to","<=",date_evaluate_to),
                    ("subtype_id.type_id.have_utilities","!=",True),
                    ("state","=",'validate')

                ])

                days_list = []
                '''
                    Recopilacion de Dias de Ausencia
                '''
                for ld in leave_days:
                    days_list += list_days(ld.date_from, ld.date_to)
                    
                '''
                    Recopilacion de Feriados
                '''
                days_list += dates_table_holidays
                
                '''
                    Recopilación de Domingos
                '''
                days_list += find_list_sundays(date_evaluate_from,date_evaluate_to)

                '''ELIMINA DIAS REPETIDOS, SE QUEDA CON DIAS UNICOS'''
                record.days_leave = len(list(set(days_list)))
                

    @api.depends('employee_id','days_leave')
    def _compute_days_worked(self):
        for record in self:
            
            if record.date_from and record.date_to and record.employee_id:
                date_evaluate_from = record.date_from
                date_evaluate_to = record.date_to
                if date_evaluate_from < record.first_contract_date:
                    date_evaluate_from = record.first_contract_date
                if record.last_contract_date:
                    if date_evaluate_to > record.last_contract_date:
                        date_evaluate_to = record.last_contract_date
            
                record.days_work = (date_evaluate_to-date_evaluate_from).days + 1 - record.days_leave
                
                # FIXME: SOLICITADO POR EL CLIENTE, cambiar luego
                if record.employee_id.id == 1730:
                    record.days_work += 77

    @api.depends('income_lines')
    def _compute_total(self):
        for record in self:
            record.bimp_total = sum([i.amount for i in record.income_lines ])

    @api.depends('employee_id')
    def _compute_income_lines(self):
        for record in self:
            record.income_lines.unlink()
            payslip_lines = self.env["hr.payslip.line"].search(
                [
                    ("employee_id","=",record.employee_id.id),
                    ("date_from",">=",record.date_from),
                    ("date_to","<=",record.date_to)
                ]
            )
            
            val_list = []
            salary_rule_ids = payslip_lines.filtered(lambda x: x.salary_rule_id.appears_on_utilities == True).mapped("salary_rule_id")
            for salary_rule in salary_rule_ids:
                payslip_line = payslip_lines.filtered(lambda x: x.salary_rule_id.id == salary_rule.id )
                amount = sum([i.total for i in payslip_line])
                if amount > 0:

                    val_list.append({
                        "amount":amount,
                        "type":salary_rule.id,
                        "name":salary_rule.name,
                        "income_id":record.id,
                    })

            record.write({
                'income_lines' :[(0,0,val) for val in val_list],
            })


    # def send_utilities_email(self):
    #     self.ensure_one()
    #     ir_model_data = self.env['ir.model.data']
    #     try:
           
    #         template_id = ir_model_data._xmlid_lookup('hr_utilities.email_template_edi_hr_utilities')[2]
    #     except ValueError:
    #         template_id = False
    #     try:
    #         compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[2]
    #     except ValueError:
    #         compose_form_id = False
    #     ctx = {
    #         'default_model': 'hr.utilities.incomes',
    #         'default_res_id': self.ids[0],
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode': 'comment',
    #         'mark_so_as_sent': True,
    #         'force_email': True
    #     }
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(compose_form_id, 'form')],
    #         'view_id': compose_form_id,
    #         'target': 'new',
    #         'context': ctx,
    #     }


class HrUtilitiesIncomesLines(models.Model):
    _name = 'hr.utilities.incomes.lines'
    _description = 'Utility Incomes Concepts'

    income_id = fields.Many2one('hr.utilities.incomes',string="Empleado Utilidad", store=True,)
    name = fields.Char(string="Nombre Concepto",default="", store=True,)
    amount = fields.Float('Monto',store=True,)
    type = fields.Many2one('hr.salary.rule', string="Regla",store=True,)

    