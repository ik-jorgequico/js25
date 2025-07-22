from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
from .hr_prov_vaca_rep import VacaExcelReport
import base64

class BonVaca(models.Model):
    _name = 'hr.prov.vaca'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Provision Vacaciones'
    _order = "date_from asc"

    employee_id = fields.Many2one("hr.employee",tracking=True, string="Empleado")
    name = fields.Char(string="Nombre")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aprobado'),
        ('cancel', 'Cancelado'),
    ], string="State", default='draft', tracking=True, copy=False, )
    
    #Para el form 
    current_year = int(datetime.now().date().strftime("%Y"))
    
    list_anios = [(str(i),str(i)) for i in range(current_year-5,current_year+1)]
    anio = fields.Selection(
        selection=list_anios, 
        store=True,tracking=True,
        string="Año"
    )
    
    selection_period = {
        "01":"ENERO",
        "02":"FEBRERO",
        "03":"MARZO",
        "04":"ABRIL",
        "05":"MAYO",
        "06":"JUNIO",
        "07":"JULIO",
        "08":"AGOSTO",
        "09":"SETIEMBRE",
        "10":"OCTUBRE",
        "11":"NOVIEMBRE",
        "12":"DICIEMBRE",
    }
    period = fields.Selection(
        selection=[(i,j) for i,j in selection_period.items()], store=True,tracking=True,string="Mes")
    
    period_vaca = fields.Char(string="Nombre Periodo")
    
    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True, )
    date_from = fields.Date(string="Dia Inicio", store=True,tracking=True)
    date_to = fields.Date(string="Dia Fin", store=True,tracking=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    child_ids = fields.One2many("hr.prov.vaca.line","parent_id",string="Provisiones Vacación",
                                states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')
    
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model', '=', 'hr.prov.vaca.line'), ('report_type', '=', 'qweb-pdf')]", default=lambda self: self.env.ref('hr_vaca.action_report_vaca', False))
    
    ##################################################################################################
    
    @api.onchange("date_from","date_to", )
    def _compute_name(self):
        if self.date_from and self.date_to :
            name_period = self.date_from.strftime("%m")
            year_period = self.date_from.strftime("%Y")
            self.name = "Provisión Vacaciones - " + name_period + " - " + year_period
   
    def _day_of_month(self, month, anio):		
        if month != "12":
            _smonth = int(month) + 1
            first_day_month = datetime.strptime("01/" + str(month) + "/" + str(anio), '%d/%m/%Y')			
            last_day_month = datetime.strptime("01/" + str(_smonth) + "/" + str(anio), '%d/%m/%Y')-timedelta(days=1)
        else:
            first_day_month = datetime.strptime("01/12/" + str(anio), '%d/%m/%Y')			
            last_day_month = datetime.strptime("31/12/" + str(anio), '%d/%m/%Y')
        return first_day_month, last_day_month
    
    def get_basic_salary_asig_family(self):
        basic_salary_obj = self.env['basic.salary'].search([
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_to),
        ], limit=1)
        return basic_salary_obj.value * 0.10 if basic_salary_obj else 0.0
    
    def _check_states_month(self, date_from, date_to): # se debe ejecutar en el boton de calcular
        slip_count = self.env['hr.payslip'].search_count([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("state","in",['draft','verify']),
        ])
        leave_count = self.env['hr.leave'].search_count([
            ("date_from",">=",date_from),
            ("date_to","<=",date_to),
            ("state","in",['draft','confirm','validate1']),
        ])
        lbs_count = self.env['hr.lbs.line'].search_count([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("state","in",['draft','verify']),
        ])
        if slip_count > 0:
            raise UserError(_('Se encontraron Boletas en estado Borrador o En Espera, termine todos los procesos para continuar.'))
        if leave_count > 0:
            raise UserError(_('Se encontraron Ausencias en estado Borrador o En Espera, termine todos los procesos para continuar.'))
        if lbs_count > 0:
            raise UserError(_('Se encontraron Liquidaciones en estado Borrador o En Espera, termine todos los procesos para continuar.'))
    
    def _check_get_active_account_analytic(self,employee):
        active_accounts = employee.cod_coste_center_account.filtered(lambda x: x.is_active)
        if len(active_accounts) == 0:
            raise UserError(_('No se encontró ninguna cuenta de centro de costos activa para el empleado %s') % employee.name)
        elif len(active_accounts) > 1:
            raise Warning(_('El empleado %s tiene más de una cuenta de centro de costos activa. Por favor, modifique las cuentas para que sólo haya una activa.') % employee.name)
        return active_accounts
    
    def _get_active_account_analytic(self,employee):
        active_accounts = employee.cod_coste_center_account.filtered(lambda x: x.is_active)
        return active_accounts.account_analytic_account_id.name if active_accounts else 'No tiene'
    
    @api.onchange('anio', 'period')
    def _compute_dates(self):
        if self.anio and self.period:
            self.date_from, self.date_to = self._day_of_month(self.period, self.anio)
            if self.period in ['01','02','03','04','05','06','07','08','09','10','11','12']:
                _sanio = int(self.anio)
                self.period_vaca = "ENERO " + str(_sanio) + " - DICIEMBRE " + str(self.anio)
    
    # Para filtrar empleados en función de sus fechas de contrato
    def _filter_employees(self, employe, date_from, date_to):
        employees = employe.filtered(lambda x: x.first_contract_date <= date_to and (not x.last_contract_date or (x.last_contract_date > date_from if x.last_contract_date != False else 0)))
        employees = [employee for employee in employees if (employee.last_contract_date and employee.first_contract_date and (employee.last_contract_date - employee.first_contract_date).days >= 30 or not employee.last_contract_date)]
        return employees
   
    #PARA OBTENER LOS DIAS NO COMPUTABLES  
    def _get_number_leave_days(self,employee,date_from,date_to):
        number_real_days = 0
        
        first_day = employee.first_contract_date
        if first_day:
            if first_day <= date_from:
                first_day = date_from
            Type_suspension = ['01','03','04','05','06','07','08','09','10','11','16','21','22','23','25','26','28','29','30','31','35'] #Codigo del tipo de ausencias
            afectation_days =  self.env["hr.leave"].search([
                ("employee_id","=",employee.id),
                ("date_from",">=",first_day),
                ("date_to","<=",date_to),
                ("state","=","validate"),
                ("subtype_id.type_id.have_holiday","=",False),
                ("code","in",Type_suspension),
            ])
            number_real_days = sum([i.number_real_days for i in afectation_days if isinstance(i.number_real_days, (float, int))])
        
        return number_real_days

    # DIAS COMPUTABLES         
    def _get_days_compute(self, employee):
        fcd = employee.first_contract_date
        lcd = employee.last_contract_date
        dfrom, dto = self._day_of_month(self.period, self.anio)
        df = dfrom.date()
        dt = dto.date()
        days_computables = 0

        if not lcd:
            
            if (fcd == df) :
                days_computables = 2.5
                
            elif fcd == dt:
                days_computables = 2.5/30
                
            elif fcd > df and fcd < dt:
                prop = 30 - int(fcd.strftime("%d")) + 1
                days_computables = 2.5/30 * prop
                
            elif fcd < df:
                days_computables = 2.5
                
        else:
            if lcd == df:
                days_computables = 2.5/30
                
            elif lcd == dt:
                
                if fcd <= df:
                    days_computables = 2.5
                    
                elif fcd > df and fcd < dt:
                    prop = 30 - int(fcd.strftime("%d")) + 1
                    days_computables = 2.5/30 * prop
                    
                elif fcd == dt:
                    days_computables = 2.5/30
                    
            elif lcd > df and lcd < dt:
                prop = int(lcd.strftime("%d")) - int(df.strftime("%d")) + 1
                days_computables = 2.5/30 * prop
                
            elif lcd > dt:
                
                if fcd <= df:
                    days_computables = 2.5
                    
                elif fcd > df and fcd < dt:
                    prop = 30 - int(fcd.strftime("%d")) + 1
                    days_computables = 2.5/30 * prop
                    
                elif fcd == dt:
                    days_computables = 2.5/30
                    
        return days_computables

    #Para realizar los calculos en el line
    def compute_sheet(self):
        self.ensure_one()
        self._check_states_month(self.date_from, self.date_to)
        self.child_ids.subline_ids.unlink()
        self.child_ids.unlink()
        
        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('struct_id.company_id.id', '=', self.company_id.id),
        ])
        
        basic_salary = self.env['basic.salary']._get_basic_salary_in_range(self.date_from,self.date_to)
        
        val_list = []
        if payslips:
            employees = payslips.mapped('employee_id')
            employees = self._filter_employees(employees, self.date_from, self.date_to)
        
            for employee in employees:
                number_aditional_days = 0
                self._check_get_active_account_analytic(employee)
                account_analytic_active = self._get_active_account_analytic(employee)
                vaca_prev = self._vaca_prev(employee,self.date_from)
                vaca_lbs_value, vaca_pagada_value = self._vaca_lbs(employee,self.date_from,self.date_to)
                
                # Asignacion familiar segun el régimen del empleado
                if employee.contract_id.peru_employee_regime.abbr == 'RG' and employee.children > 0:
                    family_asig = self.get_basic_salary_asig_family()
                    number_leave_days = self._get_number_leave_days(employee,self.date_from,self.date_to)
                    days_computables = self._get_days_compute(employee)
                else:
                    family_asig = 0
                    number_leave_days = (self._get_number_leave_days(employee,self.date_from,self.date_to))/2
                    days_computables = (self._get_days_compute(employee))/2
                
                
                val_list.append({
                    "date_from":self.date_from,
                    "date_to":self.date_to,
                    "name":" VACACIONES " + employee.name,
                    "employee_id":employee.id,
                    "salary":   employee.contract_id.wage,
                    "family_asig": family_asig,
                    "parent_id":self.id,
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(self.date_from,employee)],
                    "number_aditional_days": number_aditional_days ,
                    "cost_center": employee.cod_coste_center.name,
                    "location": employee.location_id.name,
                    "department": employee.department_id.name,
                    "job": employee.job_id.name,
                    "regime":employee.contract_id.structure_type_id.name,
                    "last_contract_date":employee.last_contract_date,
                    "total_prev":vaca_prev, #Prov. Acum
                    "vaca_lbs":vaca_lbs_value,
                    "vaca_pagada":vaca_pagada_value,
                    "days_no_computable":number_leave_days, #DIAS NO COMPUTABLES
                    "days_computable": days_computables, #DIAS COMPUTABLES
                    "analytic_ac": account_analytic_active
                })
                
            self.env["hr.prov.vaca.line"].create(val_list)       
            return  self.env.cr.commit()
        self.action_submit()
        
    def _vaca_lbs(self, employee, date_from, date_to):
        cont = 0
        vaca_pagada = 0
        lbs = self.env["hr.lbs.line"].search([
            ("date_from","=",date_from),
            ("date_to","=",date_to),
            ("employee_id","=",employee.id),
        ])
        
        if lbs.vaca_amount: # vaca_amount es el monto de vacacion
            cont = lbs.vaca_amount
            
        return cont, vaca_pagada

    def _last_day_of_month(self, any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)
    
    def _compute_sublines(self, date_from, employee):
        sublines = []
        
        ndt = date_from - relativedelta(days=1)
        ndf = date_from - relativedelta(months=6)
    
        payslip = self.env["hr.payslip"].search([
            ("date_from", ">=", ndf),
            ("date_to", "<=", ndt),
            ("struct_id.company_id.id", "=", self.company_id.id),
        ])
    
        line_ids = payslip.filtered(lambda x: x.employee_id == employee).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_holiday == True and x.amount > 0)
    
        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
    
        for code in codes:
            line_ids_code = line_ids.filtered(lambda x: x.code == code)
            
            if len(line_ids_code) >= 3: # solo se obtiene 3 bonos
                amount = sum([line_id.amount for line_id in line_ids_code])
                average = round(amount/6,2)

                sublines.append({
                    "name": line_ids_code[0].name,
                    "cont": len(line_ids_code),
                    "amount": amount,
                    "average": average,
                })
                
        return sublines

    def get_dicts_proms(self, child_id):
        return {"Prom_" + subline_id.name: subline_id.average for subline_id in child_id.subline_ids}

    def action_dowload_report_tabular(self):
        for obj in self:
            values = []
            contador = 1
                
            for child_id in obj.child_ids:
                val1 = {
                    "ID":contador,
                    "Cod.":child_id.employee_id.cod_ref or '',
                    "Tipo_doc":child_id.employee_id.l10n_latam_identification_type_id.name or '',
                    "documento":child_id.employee_id.identification_id or '',
                    "PRIMER APELLIDO":child_id.employee_id.first_last_name or '',
                    "SEGUNDO APELLIDO":child_id.employee_id.second_last_name or '',
                    "PRIMER NOMBRE":child_id.employee_id.first_name or '',
                    "SEGUNDO NOMBRE":child_id.employee_id.second_name or '',
                    "centro de costo":child_id.employee_id.cod_coste_center.name or '',
                    "cuenta analitica":child_id.analytic_ac or '',
                    "zonal": child_id.employee_id.location_id.name or '',
                    "area":child_id.employee_id.department_id.name or '',
                    "cargo": child_id.employee_id.job_id.name or '',
                    "regime": child_id.employee_id.contract_id.structure_type_id.name or '',
                    "fecha de ingreso": child_id.employee_id.first_contract_date or '',
                    "FECHA CESE":child_id.employee_id.last_contract_date or '',
                }
                
                val2 = self.get_dicts_proms(child_id)
                
                val3 = {
                    "Sumatorio Promedios":child_id.average_variables,
                    "Salario Basico":child_id.salary,
                    "Asig Familiar":child_id.family_asig,
                    "Total Base":child_id.total_amount,
                    "lbs":child_id.vaca_lbs,
                    "Dias computables":child_id.days_computable,
                    "Dias ganados":child_id.vaca_days,
                    "Provision Actual":child_id.prov_mes_adjust, #Provision Mes
                    "Provision Acum":child_id.total_prev, #Provision Acumulada
                }
                
                values.append({**val1, **val2, **val3})
                contador += 1
                
            obj.generate_excel(values)
        
    def generate_excel(self, data):
        report_xls = VacaExcelReport(data, self)
        self.write({
            'xls_filename': self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        })
    
    ################ state bar ########################
    
    def action_submit(self):
        self.mapped('child_ids').write({'state': 'verify'})
        return self.write({'state': 'done'})

    def action_cancel(self):
        self.mapped('child_ids').write({'state': 'cancel'})
        return self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.child_ids:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.mapped('child_ids').action_payslip_approve()
                self.write({'state': 'done'})

    def action_draft(self):
        self.mapped('child_ids').write({'state': 'draft'})
        return self.write({'state': 'draft'})
    
    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(vaca.state not in ('draft', 'cancel') for vaca in self):
            raise UserError(_('You cannot delete a vacaciones which is not draft or cancelled!'))
        
    #obtener las vacaciones acumulados al comienzo de mes
    def _vaca_prev(self, employee, date_from):
        vaca_prev = 0
        
        if date_from.strftime("%m") == '01':
            vaca_prev = 0
            
        else:
            m_pf = int(date_from.strftime("%m")) - 1
            # y_pf = date_from.strftime("%Y")
            new_date_from = datetime.strptime("01/" + str(m_pf) + "/"+ str(date_from.strftime("%Y")), '%d/%m/%Y')
            data = self.env["hr.prov.vaca.line"].search([
                ("date_from","=",new_date_from),
                ("employee_id","=",employee.id),
            ])
            vaca_prev = data.total_prev + data.prov_mes_adjust
            
        return vaca_prev

##########################################################################################################################################

class BonVacaLine(models.Model):
    _name = 'hr.prov.vaca.line'
    _description = 'Provision vacacion line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    structure_type = fields.Char(string="Tipo de Regimen", compute='_compute_structure_type')

    date_from = fields.Date(related = "parent_id.date_from", store=True,)
    date_to = fields.Date(related = "parent_id.date_to", store=True,)
    first_contract_date = fields.Date(store=True, string="Fecha Inicio", compute="compute_information")
    identification_id = fields.Char(store=True, string="Num. Doc.", compute="compute_information" )

    @api.depends('employee_id')
    def _compute_structure_type(self):
        for rec in self:
            rec.structure_type = rec.employee_id.contract_id.peru_employee_regime.abbr or ''
    
    @api.depends('employee_id')
    def compute_information(self):
        for record in self:
            if record.employee_id:
                record.first_contract_date = record.employee_id.first_contract_date
                record.identification_id = record.employee_id.identification_id
                                
    name = fields.Char(string="Nombre", store=True,)
    employee_id = fields.Many2one("hr.employee", store=True,string="Empleado")
    salary = fields.Float(string="Sueldo Contrato", default= 0)
    family_asig = fields.Float(string="A.F.", default= 0)
    average_variables = fields.Float(string="Prom. Variables", compute='_compute_average_variables', default= 0)
    total_amount = fields.Float(string="Monto",  compute='_compute_total_amount', default= 0, store=True,)
    
    total = fields.Float(string="Total Mes Sin LBS",  compute='_compute_total', default= 0, store=True,)
    parent_id = fields.Many2one("hr.prov.vaca",string="Vacación", ondelete='cascade', store=True,)
    subline_ids = fields.One2many("hr.prov.vaca.subline","vaca_line",string="Variables")
    number_aditional_days = fields.Integer(string="D. Adicionales",default=0, help= "Dias Adicionales de Trabajo cuando no has sido parte de la bonificación Vacación del periodo anterior.")
    cost_center = fields.Char('CC')
    location = fields.Char('Localidad')
    department = fields.Char('Area')
    job = fields.Char('Puesto')
    regime = fields.Char('Regimen L.')
    last_contract_date = fields.Date('Fecha de Cese')
    
    total_prev = fields.Float('Prov. Acum',store=True)
    vaca_lbs = fields.Float(string='LBS', default= 0, store=True,)
    prov_mes_adjust = fields.Float(string='Prov. Mes',compute='_compute_prov_mes_adjust', default= 0, store=True)
    vaca_pagada = fields.Float(string='vaca_pagada', default= 0, store=True,)
    
    days_computable = fields.Float(string='Dias computables', store=True) ########################################################
    analytic_ac=fields.Char(string='Cuenta Analitica',store=True)  
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('verify', 'Enviado'),
        ('approve', 'Aprobado'),
        ('refuse', 'Rechazado'),
        ('cancel', 'Cancelado'),
    ], string="State", default='draft', tracking=True, copy=False, )

    days_no_computable = fields.Float(string='Dias No computables', store=True)
    vaca_days = fields.Float(string='Dias Ganados',compute='_compute_vaca_days', store=True)
    
    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark vacaciones as approve if not confirmed.'))
        self.write({'state': 'approve'})

    @api.depends('days_no_computable','days_computable')
    def _compute_vaca_days(self):
        for record in self:
            if record.days_computable:
                record.vaca_days = record.days_computable - (record.days_no_computable * 2.5/30)
    
    #PROV ACTUAL
    @api.depends('vaca_lbs','total_prev', 'total')
    def _compute_prov_mes_adjust(self):
        for record in self:
            if record.vaca_lbs > 0:
                if (record.vaca_lbs - record.total_prev) <= 0:
                    record.prov_mes_adjust = record.total
                else:
                    record.prov_mes_adjust = record.vaca_lbs - record.total_prev
            else:
                record.prov_mes_adjust = record.total
                
    @api.depends('subline_ids')
    def _compute_average_variables(self):
        for record in self:
            amount = 0
            for subline_id in record.subline_ids:
                amount += subline_id.average
            record.average_variables = amount

    #BASE COMPUTABLE
    @api.depends('salary','family_asig','average_variables')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.salary + record.family_asig + record.average_variables
            
    @api.depends('total_amount')
    def _compute_total(self):
        for record in self:
            record.total = round(record.total_amount/30*(record.days_computable),2)

class BonVacaSubLine(models.Model):
    _name = 'hr.prov.vaca.subline'
    _description = 'Provision vacaciones subline'
    
    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")
    vaca_line = fields.Many2one("hr.prov.vaca.line", ondelete='cascade', store=True,)