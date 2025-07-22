from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
from .hr_vacation_calculate_report import VacationCalculateExcelReport
import calendar
import base64


MONTHS_SELECTION = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]

STATES_SELECTION = [
    ('draft', 'Borrador'),
    ('verify', 'Enviado'),
    ('approve', 'Aprobado'),
    ('refuse', 'Rechazado'),
    ('cancel', 'Cancelado'),
]

class VacationCalculate(models.Model):
    _name = 'hr.vacation.calculate'
    _description = 'Calculo de Vacaciones'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Nombre", compute='_compute_name', default="", store=True,tracking=True)
    
    state = fields.Selection(STATES_SELECTION, string="State", default='draft', tracking=True, copy=False)
    
    current_year = datetime.today().year
    month = fields.Selection(MONTHS_SELECTION, tracking=True,required=True)
    year = fields.Selection([(str(y), y) for y in range(current_year, current_year - 8, -1)],tracking=True, required=True)

    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True)
    date_from = fields.Date(string="Fecha de Inicio para el Promedio", store=True,tracking=True)
    date_to = fields.Date(string="Fecha de Fin para el Promedio", store=True,tracking=True)
    date_from_eval = fields.Date(string="Fecha Inicio", compute='_compute_date_from_eval', store=True)
    date_to_eval = fields.Date(string="Fecha Fin", compute='_compute_date_to_eval', store=True)
    
    is_w_current_month = fields.Boolean(string="Evalua el mes presente?", default=False)

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    child_ids = fields.One2many("hr.vacation.calculate.line","parent_id",tracking=True,string="Calculo Empleados", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel',tracking=True)
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model','=','hr.vacation.calculate.line'), ('report_type','=','qweb-pdf')]", default=lambda self: self.env.ref('hr_vacation.action_report_vacation', False))
    
    @staticmethod
    def _first_day(year, month):
        return datetime(int(year), int(month), 1)
    
    @staticmethod
    def _last_day(any_date=None, year=None, month=None):
        last_day = calendar.monthrange(int(year or any_date.year), int(month or any_date.month))[1]
        return any_date.replace(day=last_day) if any_date else date(int(year), int(month), last_day)
    
    @api.depends('month', 'year')
    def _compute_date_from_eval(self):
        for rec in self:
            rec.date_from_eval = self._first_day(rec.year, rec.month)
            
    @api.depends('month', 'year')
    def _compute_date_to_eval(self):
        for rec in self:
            rec.date_to_eval = self._last_day(year=rec.year, month=rec.month)
    
    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def compute_sheet_import(self):
        employees = self.child_ids.mapped("employee_id")
        payslip = self.env['hr.payslip'].search([
            ("date_from","<=",self.date_from_eval),
            ("date_to",">=",self.date_to_eval),
        ])
        
        for employee in employees:
            pay = payslip.filtered(lambda x: x.employee_id == employee)
            input = pay.input_line_ids
            final_input_I_AMOUNT_VAC = input.filtered(lambda x: x.input_type_id.code == "I_AMOUNT_VAC")
            final_input_I_ADEL_VACACIONES = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_VACACIONES")
            
            child_id = self.child_ids.filtered(lambda x: x.employee_id == employee)

            bruto_amount = sum([i.bruto_amount for i in child_id if i.is_purchased==False])
            new_bruto_amount =sum([i.new_bruto_amount for i in child_id if i.is_purchased==False])
            net_amount = sum([i.net_amount for i in child_id if i.is_purchased==False])
            if final_input_I_AMOUNT_VAC:
                final_input_I_AMOUNT_VAC.amount = float(bruto_amount)
                if new_bruto_amount > 0:
                    final_input_I_AMOUNT_VAC.amount = float(new_bruto_amount)
            if final_input_I_ADEL_VACACIONES:
                final_input_I_ADEL_VACACIONES.amount = float(net_amount)
            
            final_input_I_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_COMVAC")
            final_input_I_ADEL_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_COMVAC")
            
            bruto_amount = sum([i.bruto_amount for i in child_id if i.is_purchased==True])
            new_bruto_amount =sum([i.new_bruto_amount for i in child_id if i.is_purchased==True])
            net_amount = sum([i.net_amount for i in child_id if i.is_purchased==True])
            if final_input_I_COMVAC:
                final_input_I_COMVAC.amount = float(bruto_amount)
                if new_bruto_amount > 0:
                    final_input_I_COMVAC.amount = float(new_bruto_amount)
            if final_input_I_ADEL_COMVAC:
                final_input_I_ADEL_COMVAC.amount = float(net_amount)

        payslip.compute_sheet()

    def unlink(self):
        employees = self.child_ids.mapped("employee_id")
        payslip = self.env['hr.payslip'].search([
            ("date_from","<=",self.date_from_eval),
            ("date_to",">=",self.date_to_eval),
            ("company_id.id","=",self.company_id.id),
        ])
        
        for employee in employees:
            pay = payslip.filtered(lambda x: x.employee_id == employee)
            input = pay.input_line_ids
            final_input_I_AMOUNT_VAC = input.filtered(lambda x: x.input_type_id.code == "I_AMOUNT_VAC")
            final_input_I_ADEL_VACACIONES = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_VACACIONES")
            final_input_I_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_COMVAC")
            final_input_I_ADEL_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_COMVAC")

            if final_input_I_AMOUNT_VAC:
                final_input_I_AMOUNT_VAC.amount = 0
            if final_input_I_ADEL_VACACIONES:
                final_input_I_ADEL_VACACIONES.amount = 0
            if final_input_I_COMVAC:
                final_input_I_COMVAC.amount = 0
            if final_input_I_ADEL_COMVAC:
                final_input_I_ADEL_COMVAC.amount = 0

        payslip.compute_sheet()
        return super().unlink()

    def action_open_hr_vacation_calculate(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.calculate.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros Vacacion",
        }

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)

    def action_dowload_report_pdf_vacation_calculate(self):
        self.ensure_one()
        return {
            'name': 'VACACION',
            'type': 'ir.actions.act_url',
            'url': '/print/vacation?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        }

    @api.onchange("month", "year", "is_w_current_month")
    def _onchange_period(self):
        if self.year and self.month:
            date = datetime(int(self.year), int(self.month), 1)
            self.date_from = date - relativedelta(months=6)
            self.date_to = self._last_day(date) - relativedelta(months=1)
            if self.is_w_current_month:
                self.date_from = date - relativedelta(months=5)
                self.date_to = self._last_day(date)

    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.name = f'CALCULO VAC {dict(MONTHS_SELECTION).get(rec.month).upper()} {rec.year}'
        
    def _filter_employees(self, employees, date_to):
        valid_employees = employees.filtered(lambda x: isinstance(x.first_contract_date, date) and x.first_contract_date and not isinstance(x.first_contract_date, bool))
        return valid_employees.filtered(lambda x: x.first_contract_date <= (date_to.replace(day=1)) and not x.last_contract_date)
    
    def get_basic_salary_asig_family(self):
        basic_salary_obj = self.env['basic.salary'].search([
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_to),
        ], limit=1)
        return basic_salary_obj.value * 0.10 if basic_salary_obj else 0.0
    
    def compute_sheet(self):
        self.ensure_one()
        average_variables = 0 
        salary = 0
        family_asig = 0 
        
        if any(vacation.state in ('approve') for vacation in self):
            raise UserError(_('You cannot compute a vacation which is not draft or cancelled!'))

        payslips = self.env["hr.payslip"].search([
            ("date_from",">=",self.date_from),
            ("date_to","<=",self.date_to),
            ("company_id.id","=",self.company_id.id)
        ,])
        
        leave = self.env["hr.leave"].search([
            ("date_from",">=",self.date_from_eval),
            ("date_to","<=",self.date_to_eval),
            ("state","=","validate"),
            ("code","=",'23'),
        ])
        
        val_list = []

        purchased_vacation = self.env['hr.vacation.purchased'].search([
            ("date_from",">=",self.date_from_eval),
            ("date_to","<=",self.date_to_eval),
        ])
        
        if purchased_vacation:
            purchased_vacation_employees = purchased_vacation.mapped("employee_id")
            new_employees = self._filter_employees(purchased_vacation_employees,self.date_to)

            for employee in new_employees:
                child_ids = self.child_ids.filtered(lambda x: x.employee_id == employee and x.is_purchased == True)
                days_saved = sum([i.number_days for i in child_ids])
                purchased_vacation_filtered = purchased_vacation.filtered(lambda self: self.employee_id.id == employee.id)
                purchased_vacation_sum_days  = sum([i.number_real_days for i in purchased_vacation_filtered])
                
                if purchased_vacation_sum_days - days_saved > 0:
                    number_days = purchased_vacation_sum_days - days_saved
                    sublines = self._compute_sublines(employee,payslips)
                    salary = employee.contract_id.wage
                    average_variables = sum([i["average"] for i in sublines])
                    
                    peru_employee_regime = employee.contract_id.peru_employee_regime

                    family_asig = 0
                    if peru_employee_regime:
                        if peru_employee_regime.abbr == 'RG' and employee.children > 0 and number_days == 30:
                            family_asig = self.get_basic_salary_asig_family()

                    # if employee.contract_id.peru_employee_regime.abbr == "RG" and employee.children > 0 and number_days == 30:
                    #     family_asig = self.get_basic_salary_asig_family()
                    # else:
                    #     family_asig = 0
                    
                    total_amount = salary + family_asig + average_variables
                    bruto_amount = round(total_amount * number_days / 30, 2)

                    val_list.append({
                        "date_from": self.date_from,
                        "date_to": self.date_to,
                        "name":"VACACION " + employee.name,
                        "employee_id": employee.id,
                        "salary": salary,
                        "family_asig": family_asig,
                        "average_variables": average_variables,
                        "total_amount": total_amount,
                        "number_days": number_days,
                        "bruto_amount":bruto_amount,
                        "parent_id": self.id,
                        "subline_ids": [(0,0,subline) for subline in sublines],
                        "is_purchased": True,
                        "vacation_purchased": [(4, i.id) for i in purchased_vacation]
                    })
                    
                    purchased_vacation_filtered.write({"is_calculated": True})

            self.env["hr.vacation.calculate.line"].create(val_list)
            self.env.cr.commit()

        val_list = []
        if leave:   
            employees = leave.mapped("employee_id")
            new_employees = self._filter_employees(employees,self.date_to)

            for employee in new_employees:
                child_ids = self.child_ids.filtered(lambda x: x.employee_id == employee and x.is_purchased != True)
                days_saved = sum([i.number_days for i in child_ids])
                leave_number_real_days  = self._get_number_days(employee,self.date_from_eval,self.date_to_eval)

                if leave_number_real_days - days_saved > 0:
                    number_days = leave_number_real_days - days_saved
                    sublines = self._compute_sublines(employee,payslips)
                    salary = employee.contract_id.wage
                    # family_asig = 102.50 if (employee.children > 0 and number_days == 30 ) else 0
                    # average_variables = sum([i["average"] for i in sublines])
                    # total_amount = salary + family_asig + average_variables
                    # bruto_amount = round(total_amount*number_days/30,2)
                    abbr = employee.contract_id.peru_employee_regime.abbr
                    if abbr == "RG" :
                        family_asig = self.get_basic_salary_asig_family() if (employee.children > 0 and number_days == 30) else 0
                        total_amount = salary + family_asig + average_variables
                        bruto_amount = round(total_amount * number_days / 30, 2)
                    elif abbr == "RP" or abbr == "RM" :
                        family_asig = 0
                        total_amount = salary + family_asig + average_variables
                        bruto_amount = round(total_amount * number_days/30, 2)
                    
                    val_list.append({
                        "date_from":self.date_from,
                        "date_to":self.date_to,
                        "name":"VACACION " + employee.name,
                        "employee_id":employee.id,
                        "salary": salary,
                        "family_asig": family_asig,
                        "average_variables": average_variables,
                        "total_amount":total_amount,
                        "number_days": number_days,
                        "bruto_amount":bruto_amount,
                        "parent_id":self.id,
                        "subline_ids": [(0,0,subline) for subline in sublines],
                    })
                    
            self.env["hr.vacation.calculate.line"].create(val_list)
            self.env.cr.commit()

        if self.is_w_current_month:
            for child_id in self.child_ids:
                sublines = self._compute_sublines(child_id.employee_id,payslips)
                child_id.salary_aux =  child_id.salary
                child_id.family_asig_aux = child_id.family_asig 
                child_id.average_variables_aux =  child_id.average_variables
                child_id.total_amount_aux =  child_id.total_amount
                child_id.salary = child_id.employee_id.contract_id.wage
                child_id.family_asig =  102.50 if (employee.children > 0 and child_id.number_days == 30 ) else 0
                child_id.average_variables = sum([i["average"] for i in sublines])
                child_id.total_amount = child_id.salary + child_id.family_asig + child_id.average_variables
                child_id.new_bruto_amount = round( child_id.total_amount*child_id.number_days/30,2)
                child_id.subline_ids.unlink()
                child_id.write({
                            'subline_ids':[(0,0,subline) for subline in sublines]
                        })

        self.compute_sheet_import()

    def _get_number_days(self, employee, date_from_eval, date_to_eval):        
        resut = 0
        afectation_days =  self.env["hr.leave"].search([
            ("employee_id","=",employee.id),
            ("date_from",">=",date_from_eval),
            ("date_to","<=",date_to_eval),
            ("state","=","validate"),
            ("code","=",'23'),
        ])
        
        if len(afectation_days) != 0:
            resut = sum([i.number_real_days for i in afectation_days])
            if resut > 30:
                resut = 30
        
        return resut

    def _compute_sublines(self, employee, payslip):
        sublines = []
        line_ids = payslip.filtered(lambda x: x.employee_id == employee ).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_holiday == True and x.amount > 0) 

        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
        
        for code in codes:
            line_ids_code = line_ids.filtered(lambda x: x.code == code)
            
            if len(line_ids_code) >= 3:
                amount = sum([line_id.amount for line_id in line_ids_code])
                average = round(amount/6,2)
                
                sublines.append({
                    "name": line_ids_code[0].name,
                    "cont": len(line_ids_code),
                    "amount": amount,
                    "average": average
                })
                
        return sublines

    def get_dicts_proms(self, child_id):
        return {"Prom_" + subline_id.name: subline_id.average for subline_id in child_id.subline_ids}
    
    def get_dicts_deductions(self,child_id):
        r = {}
        for subline_id in child_id.deduction_payments_ids:
            r["Ded_" + subline_id.description] = subline_id.amount
        return r
        
    def action_dowload_report_tabular_vacation_calculate(self):

        for obj in self:
            values = []
            contador = 1
            for child_id in obj.child_ids:
                val1 = {
                        "ID":contador,
                        "CODIGO":child_id.employee_id.cod_ref or '',
                        "TIPO DOCUMENTO":child_id.employee_id.l10n_latam_identification_type_id.name or '',
                        "NUM DOCUMENTO":child_id.employee_id.identification_id or '',
                        "PRIMER APELLIDO":child_id.employee_id.first_last_name or '',
                        "SEGUNDO APELLIDO":child_id.employee_id.second_last_name or '',
                        "PRIMER NOMBRE":child_id.employee_id.first_name or '',
                        "SEGUNDO NOMBRE":child_id.employee_id.second_name or '',
                        "CENTRO DE COSTO":child_id.employee_id.cod_coste_center.name or '',
                        "LOCALIDAD": child_id.employee_id.location_id.name or '',
                        "AREA/DEPARTAMENTO":child_id.employee_id.department_id.name or '',
                        "CARGO/PUESTO DE TRABAJO":child_id.employee_id.job_id.name or '',
                        "BANCO HABERES":child_id.employee_id.bank_account_id.bank_id.name or '',
                        "CUENTA HABERES":child_id.employee_id.bank_account_id.acc_number or '',
                        "FECHA INGRESO":child_id.employee_id.first_contract_date or '',
                        "FECHA CESE":child_id.employee_id.last_contract_date or '',
                        "ES COMPRA VAC?":"SI" if child_id.is_purchased else 'NO',
                }

                val2 = {
                    "DIAS VACACIONES":child_id.number_days,
                    "SUELDO":child_id.salary,
                }
                if child_id.family_asig > 0:
                    val2["ASIG. FAM."] =  child_id.family_asig
                val3 = self.get_dicts_proms(child_id)
                bruto = child_id.new_bruto_amount if child_id.new_bruto_amount > 0 else child_id.bruto_amount
                val4 = {
                    "BASE IMPONIBLE":child_id.total_amount,
                    "BRUTO":bruto,
                    "TOTAL INGRESO AFECTO":bruto,
                }
                val = {**val1, **val2, **val3, **val4,}
                contador += 1
                values.append(val)
 
            
            # REVISION DE COLUMNAS
            obj.generate_excel(values)

    def generate_excel(self,data):
        report_xls = VacationCalculateExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE VACACION TABULAR "+self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)
    
    ################ state bar ########################

    def action_refuse(self):
        self.mapped('child_ids').write({'state': 'refuse'})
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.mapped('child_ids').write({'state': 'verify'})
        return self.write({'state': 'verify'})

    def action_cancel(self):
        self.mapped('child_ids').write({'state': 'cancel'})
        return self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.child_ids:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.mapped('child_ids').action_payslip_approve()
                self.write({'state': 'approve'})

    def action_draft(self):
        self.mapped('child_ids').write({'state': 'draft'})
        return self.write({'state': 'draft'})

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(vacation.state not in ('draft', 'cancel','refuse') for vacation in self):
            raise UserError(_('You cannot delete a vacation which is not draft or cancelled!'))
    ####################################################


class VacationLine(models.Model):
    _name = 'hr.vacation.calculate.line'
    _description = 'VACACION DETALLE'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    structure_type = fields.Char(string = "Tipo de Regimen", compute = '_compute_structure_type')

    date_real_evaluate = fields.Date(store=True,string="Primer Dia Real Evaluado")
    date_from = fields.Date(related="parent_id.date_from", store=True,)
    date_to = fields.Date(related="parent_id.date_to", store=True,)
    first_day_contract = fields.Date(related = "employee_id.first_contract_date", string="Dia de Inicio" )

    date_from_eval = fields.Date(related = "parent_id.date_from_eval", store=True,)
    date_to_eval = fields.Date(related = "parent_id.date_to_eval", store=True,)
    
    name = fields.Char(string="Nombre")

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    company_id = fields.Many2one(related='parent_id.company_id',string='Compañia')

    salary = fields.Float(string="Sueldo Contrato", default= 0)
    family_asig = fields.Float(string="Asignación Familiar", default= 0)
    average_variables = fields.Float(string="Promedio de Variables",  default= 0)
    total_amount = fields.Float(string="Base Imponible", default= 0, store=True,)
    number_days = fields.Integer(string="Dias Totales",default= 30)

    state_payment = fields.Selection(string="Estado de Pago",selection=[('1',"Pagado"),('0',"Sin pagar")],default='0')
    bruto_amount = fields.Float(string="Bruto", default= 0, store=True,)
    desc_amount = fields.Float(string="Descuento", default= 0, compute='_compute_desc', store=True,)
    net_amount = fields.Float(string="Neto", default= 0, compute='_compute_net',store=True,)
    
    salary_aux = fields.Float(string="Sueldo Contrato Historico", default= 0)
    family_asig_aux = fields.Float(string="Asignación Familiar Historico", default= 0)
    average_variables_aux = fields.Float(string="Promedio de Variables Historico", default= 0)
    total_amount_aux = fields.Float(string="Base Imponible Historico", default= 0, store=True,)
    new_bruto_amount = fields.Float(string="Nuevo Bruto",   default= 0, store=True,)

    parent_id = fields.Many2one("hr.vacation.calculate",string="VACACION", ondelete='cascade', store=True,)
    subline_ids = fields.One2many("hr.vacation.calculate.subline","vacation_line",string="Variables")

    deduction_payments_ids = fields.One2many("hr.vacation.deduction.line","parent_id",string="Deducciones Empleados", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    
    is_purchased = fields.Boolean(string="¿Compra de Vac?",default=False,)
    vacation_purchased = fields.One2many("hr.vacation.purchased","vacation_calculate_line", string="Vacaciones Compradas")

    @api.depends('employee_id')
    def _compute_structure_type(self):
        for rec in self:
            rec.structure_type = rec.employee_id.contract_id.peru_employee_regime.abbr or ''
    
    @api.depends('deduction_payments_ids')
    def _compute_desc(self):
        for record in self:
            record.desc_amount = sum([i.amount for i in record.deduction_payments_ids])

    @api.depends('desc_amount')
    def _compute_net(self):
        for record in self:
            if record.desc_amount > 0:
                record.net_amount = record.bruto_amount - record.desc_amount

    def _get_afp_fondo(self,employee,date_from_eval,date_to_eval,bruto_amount):
        comis = employee.pension_system_id.comis_pension_ids.filtered(lambda res : res.date_from == date_from_eval and res.date_to == date_to_eval)
        return comis.fund/100*bruto_amount
    
    def _get_afp_seguro(self,employee,date_from_eval,date_to_eval,bruto_amount):
        comis = employee.pension_system_id.comis_pension_ids.filtered(lambda res : res.date_from == date_from_eval and res.date_to == date_to_eval)
        
        if comis.rem_max < bruto_amount:
            return comis.bonus/100*comis.rem_max
        
        return comis.bonus/100*bruto_amount
    
    def _get_afp_comision(self,employee,date_from_eval,date_to_eval,bruto_amount):
        comis = employee.pension_system_id.comis_pension_ids.filtered(lambda res : res.date_from == date_from_eval and res.date_to == date_to_eval)

        if employee.pension_mode == "flujo":
            return comis.flow/100*bruto_amount
        
        if employee.pension_mode in ["saldo","mixto"]:
            return comis.balance/100*bruto_amount
        
        return 0
    
    def _compute_deduction_payments(self, employee, date_from_eval, date_to_eval, bruto_amount):
        """
            I.R. 5ta
            result = 0
            if inputs.I_5TA:
                result = inputs.I_5TA.amount*-1
        """
        """
            Prestamo
            result = inputs.I_PREST and - (inputs.I_PREST.amount)
        """
        
        var_list = [
            {
                "description": "AFP FONDO",
                "amount": self._get_afp_fondo(employee,date_from_eval,date_to_eval,bruto_amount),
            },
            {
                "description": "AFP SEGURO",
                "amount":self._get_afp_seguro(employee,date_from_eval,date_to_eval,bruto_amount),
            },
            {
                "description": "AFP COMISION",
                "amount":self._get_afp_comision(employee,date_from_eval,date_to_eval,bruto_amount),
            },
            {
                "description": "ONP",
                "amount": 13/100*bruto_amount if employee.pension_system_id.name == 'ONP' else 0,
            },
            {
                "description": "IR 5TA",
                "amount":0,
            },
            {
                "description": "PRESTAMO",
                "amount":0,
            },
        ]
        
        return var_list

    def compute_sheet_import(self):
        employees = self.mapped("employee_id")
        payslip = self.env['hr.payslip'].search([
            ("date_from","<=",self.date_from_eval),
            ("date_to",">=",self.date_to_eval),
        ])
        
        for employee in employees:
            pay = payslip.filtered(lambda x: x.employee_id == employee)
            input = pay.input_line_ids
            final_input_I_AMOUNT_VAC = input.filtered(lambda x: x.input_type_id.code == "I_AMOUNT_VAC")
            final_input_I_ADEL_VACACIONES = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_VACACIONES")
            child_id = self.filtered(lambda x: x.employee_id == employee)

            if final_input_I_AMOUNT_VAC:
                final_input_I_AMOUNT_VAC.amount = float(child_id.bruto_amount)
                if child_id.new_bruto_amount > 0:
                    final_input_I_AMOUNT_VAC.amount = float(child_id.new_bruto_amount)
        
            if final_input_I_ADEL_VACACIONES:
                final_input_I_ADEL_VACACIONES.amount = float(child_id.net_amount)
            
            final_input_I_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_COMVAC")
            final_input_I_ADEL_COMVAC = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_COMVAC")
            
            bruto_amount = sum([i.bruto_amount for i in child_id if i.is_purchased == True])
            new_bruto_amount =sum([i.new_bruto_amount for i in child_id if i.is_purchased == True])
            net_amount = sum([i.net_amount for i in child_id if i.is_purchased == True])
            
            if final_input_I_COMVAC:
                final_input_I_COMVAC.amount = float(bruto_amount)
                
                if new_bruto_amount > 0:
                    final_input_I_COMVAC.amount = float(new_bruto_amount)
                    
            if final_input_I_ADEL_COMVAC:
                final_input_I_ADEL_COMVAC.amount = float(net_amount)

            pay.compute_sheet()
    
    def action_compute_payment(self):
        """ Computa los adelantos de records 
        """
        for record in self:
            record.deduction_payments_ids.unlink()
            deduction_payments = self._compute_deduction_payments(record.employee_id, record.date_from_eval, record.date_to_eval, record.bruto_amount)
            record.write({
                "deduction_payments_ids": [(0, 0, adv_payment) for adv_payment in deduction_payments],
                "state_payment": '1',
            })

            record.compute_sheet_import()

    def delete_compute_payment(self):
        """ Elimina los adelantos de records 
        """
        for record in self:
            record.deduction_payments_ids.unlink()
            record.write({
                'state_payment': '0',
                'desc_amount': 0,
                'net_amount': 0,
            })
            payslip = self.env['hr.payslip'].search([
                ('date_from', '<=', record.date_from_eval),
                ('date_to', '>=', record.date_to_eval),
                ('employee_id', '=', record.employee_id.id),
            ], limit=1)
        
            final_input_I_ADEL_VACACIONES = payslip.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_ADEL_VACACIONES")
            final_input_I_ADEL_VACACIONES.amount = 0
            payslip.compute_sheet()

    state = fields.Selection(STATES_SELECTION, string="State", default='draft', tracking=True, copy=False)

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def action_dowload_report_pdf_vacation_calculate(self):
        return {
            'name': 'VACACION',
            'type': 'ir.actions.act_url',
            'url': '/print/vacation?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        }
    
    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark vacation as approve if not confirmed.'))
        self.write({'state': 'approve'})

    def unlink(self):
        for rec in self:
            payslip = self.env['hr.payslip'].search([
                ("date_from","<=",rec.date_from_eval),
                ("date_to",">=",rec.date_to_eval),
            ])
            
            pay = payslip.filtered(lambda x: x.employee_id == rec.employee_id)
            input = pay.input_line_ids
            final_input_I_AMOUNT_VAC = input.filtered(lambda x: x.input_type_id.code == "I_AMOUNT_VAC")
            final_input_I_ADEL_VACACIONES = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_VACACIONES")
            final_input_I_AMOUNT_VAC.amount = 0
            final_input_I_ADEL_VACACIONES.amount = 0
            pay.compute_sheet()
            
        return super().unlink()


class VacationSubLine(models.Model):
    _name = 'hr.vacation.calculate.subline'
    _description = 'VACACIONES DETALLE'

    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")

    vacation_line = fields.Many2one("hr.vacation.calculate.line", ondelete='cascade', store=True)


class DeductionPaymentsVacationLine(models.Model):
    _name = "hr.vacation.deduction.line"
    _description = "Descuentos para Adelanto de Vacaciones"

    parent_id = fields.Many2one("hr.vacation.calculate.line", string="VACACION", ondelete='cascade', store=True)
    description = fields.Char(string="Descripción")
    amount = fields.Float(string="Monto", default=0)