#-*- coding:utf-8 -*-
from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
from .hr_prov_grati_rep import GratiExcelReport
import base64


class BonGrati(models.Model):
    _name = 'hr.prov.grati'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Provision Gratificacion'
    _order = "date_from asc"
    
    name = fields.Char(string="Nombre")
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Aprobado'),
        ('cancel', 'Cancelado'),
    ], string="State", default='draft', tracking=True, copy=False, )
    
    current_year = int(datetime.now().date().strftime("%Y"))
    
    list_anios = [(str(i),str(i)) for i in range(current_year-5,current_year+1)]
    
    anio = fields.Selection(selection=list_anios, store=True,tracking=True, string="Año")
    
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
    period = fields.Selection(selection=[(i,j) for i,j in selection_period.items()], store=True,tracking=True, string="Mes")
    
    #Para el form 
    period_grati = fields.Char(string="Nombre Periodo")
    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True)
    date_from = fields.Date(string="Dia Inicio", store=True,tracking=True,)
    date_to = fields.Date(string="Dia Fin", store=True,tracking=True,)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    child_ids = fields.One2many("hr.prov.grati.line","parent_id",string="Provisiones Gratificacion", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    # child_ids_count = fields.Integer(compute='_compute_child_ids_count')
    
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model', '=', 'hr.prov.grati.line'), ('report_type', '=', 'qweb-pdf')]", default=lambda self: self.env.ref('hr_grati.action_report_grati', False))
    
    #########################################################################################################
    
    @api.onchange("date_from","date_to", )
    def _compute_name(self):
        if self.date_from and self.date_to :
            name_period = self.date_from.strftime("%m")
            year_period = self.date_from.strftime("%Y")
            self.name = "Provisión Gratificación - " + name_period + " - " + year_period

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
    
    def _check_states_month(self, date_from, date_to): 
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

    #Para filtar la cuenta analitica del empleado, si tiene activa o no
    def _check_get_active_account_analytic(self,employee):
        active_accounts = employee.cod_coste_center_account.filtered(lambda x: x.is_active)
        if len(active_accounts) == 0:
            raise UserError(_('No se encontró ninguna cuenta de centro de costos activa para el empleado %s') % employee.name)
        elif len(active_accounts) > 1:
            raise Warning(_('El empleado %s tiene más de una cuenta de centro de costos activa. Por favor, modifique las cuentas para que sólo haya una activa.') % employee.name)
        return active_accounts
    
    def _get_active_account_analytic(self,employee):
        active_accounts = employee.cod_coste_center_account.filtered(lambda x: x.is_active)
        if active_accounts:
            return active_accounts.account_analytic_account_id.name
        else:
            return 'No tiene'
    
    @api.onchange("anio","period")
    def _compute_dates(self):
        if self.anio and self.period:
            self.date_from, self.date_to = self._day_of_month(self.period, self.anio)
            if self.period in ['01','02','03','04','05','06']:
                _sanio = int(self.anio)
                self.period_grati = "ENERO " + str(_sanio) + " - JUNIO " + str(self.anio)
            else:
                _sanio = int(self.anio)
                self.period_grati = "JULIO " + str(self.anio) + " - DICIEMBRE " + str(_sanio)
            
    #Para filtrar empleados en función de sus fechas de contrato
    def _filter_employees(self,employe,date_from,date_to):	   
        employees = employe.filtered(lambda x: x.first_contract_date <= date_to and 
                    (not x.last_contract_date or (x.last_contract_date > date_from if x.last_contract_date != False else 0 )) )

        employees = [employee for employee in employees if (employee.last_contract_date and employee.first_contract_date and 
                    (employee.last_contract_date - employee.first_contract_date).days >= 30 or not employee.last_contract_date)]
        return employees

    def compute_sheet(self):
        self.ensure_one()
        # self._check_states_month(self.date_from, self.date_to)
        self.child_ids.subline_ids.unlink()
        self.child_ids.unlink()
        
        payslips = self.env["hr.payslip"].search([
            ("date_from", ">=", self.date_from),
            ("date_to", "<=", self.date_to),
            ("company_id.id", "=", self.company_id.id),
        ])
        
        val_list = []
        if payslips:
            employees = payslips.mapped("employee_id")
            employees = self._filter_employees(employees,self.date_from,self.date_to)
                
            for employee in employees:
                number_aditional_days = 0
                self._check_get_active_account_analytic(employee)
                number_days, date_real_evaluate = self._get_number_days(employee,payslips,self.date_from,self.date_to)
                number_leave_days, number_leave_days_no_counted = self._get_number_leave_days(employee,self.date_from,self.date_to)
                grati_prev , days_prev_ant, days_total_ant, bonf_prev = self._grati_prev(employee,self.date_from)
                grati_lbs_value, grati_pagada_value = self._grati_lbs(employee,self.date_from,self.date_to)
                bonf_lbs, bonf_pagada = self._bonf_lbs(employee,self.date_from,self.date_to)
                account_analytic_active = self._get_active_account_analytic(employee)

                peru_employee_regime = employee.contract_id.peru_employee_regime

                family_asig = 0
                if peru_employee_regime:
                    if peru_employee_regime.abbr == 'RG' and employee.children > 0:
                        family_asig = self.get_basic_salary_asig_family()


                
                # # Asignacion familiar segun el régimen del empleado
                # if employee.contract_id.peru_employee_regime.abbr == 'RG' and employee.children > 0:
                #     family_asig = self.get_basic_salary_asig_family()
                # else:
                #     family_asig = 0
                    
                val_list.append({
                    "date_from":self.date_from,
                    "date_to":self.date_to,
                    "name":"GRATIFICACIÓN " + employee.name,
                    "employee_id":employee.id,
                    "salary":   employee.contract_id.wage,
                    "family_asig": family_asig,
                    "parent_id":self.id,
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(self.date_from,employee)],
                    "number_days": number_days ,
                    "number_leave_days":  number_leave_days,
                    "number_aditional_days": number_aditional_days ,
                    "number_leave_days_no_counted": number_leave_days_no_counted,
                    "date_real_evaluate": date_real_evaluate ,
                    "cost_center": employee.cod_coste_center.name,
                    "location": employee.location_id.name,
                    "department": employee.department_id.name,
                    "job": employee.job_id.name,
                    "regime":employee.contract_id.peru_employee_regime.abbr,
                    "last_contract_date":employee.last_contract_date,
                    "total_prev":grati_prev, #total Acum
                    "days_prev":days_prev_ant + days_total_ant,
                    "grati_lbs":grati_lbs_value,
                    "grati_pagada":grati_pagada_value, #grati pagada    
                    "bonf_lbs":bonf_lbs,
                    "bonf_pagada":bonf_pagada,
                    "prov_bonf_prev": bonf_prev, #bonf Acum
                    "analytic_ac": account_analytic_active
                })
                
            self.env["hr.prov.grati.line"].create(val_list)            
            return self.env.cr.commit()
        self.action_submit()
        
    #Para obtener LBS (liquidacion)
    def _grati_lbs(self,employee,date_from,date_to):
        cont = 0
        grati_pagada = 0
        lbs = self.env["hr.lbs.line"].search([("date_from","=",date_from),
                                                ("date_to","=",date_to),
                                        ("employee_id","=",employee.id),])
        
        grati = self.env["hr.grati.line"].search([("date_to","=",date_to),
                                        ("employee_id","=",employee.id),])
        
        if lbs.grati_amount:
            cont = lbs.grati_amount
        elif grati.total:
            grati_pagada = grati.total #el total es la grati
        return cont, grati_pagada
    
    def _bonf_lbs(self,employee,date_from,date_to):
        bonf_lbs_cont = 0
        bonf_pagada = 0
        lbs = self.env["hr.lbs.line"].search([("date_from","=",date_from),
                                                ("date_to","=",date_to),
                                        ("employee_id","=",employee.id),])
        
        bonf = self.env["hr.grati.line"].search([("date_to","=",date_to),
                                        ("employee_id","=",employee.id),])
        
        if lbs.boni_extra_grati_amount:
            bonf_lbs_cont = lbs.boni_extra_grati_amount
        elif bonf.health_regimen:
            bonf_pagada = bonf.health_regimen
        return bonf_lbs_cont, bonf_pagada


    def _get_number_days(self,employee,payslips,date_from,date_to):       
        cont = 0
        fcd =  employee.first_contract_date
        m_fcd = fcd.strftime("%m")
        y_fcd = fcd.strftime("%Y")
        
        m_from = date_from.strftime("%m")
        y_from = date_from.strftime("%Y")
        
        if employee.last_contract_date == False: 
            
            if fcd <= date_from:
                cont = 30
            else:
                r = 30 - int(fcd.strftime("%d"))  + 1
                if r > 0:
                    cont += r
                else :
                    cont += 1
        elif employee.last_contract_date:
            lcdate =  employee.last_contract_date
            
            m_lcd = lcdate.strftime("%m")
            y_lcd = lcdate.strftime("%Y")
            
            if fcd < date_from and lcdate > date_to:
                cont = 30
            elif fcd >= date_from and lcdate > date_to:
                r = 30 - int(fcd.strftime("%d"))  + 1
                if r > 0:
                    cont += r
            elif m_fcd==m_from and m_lcd==m_from and y_fcd==y_from and y_lcd==y_from:
                r = int(lcdate.strftime("%d")) - int(fcd.strftime("%d"))  + 1
                if r > 30:
                    cont = 30
                else:
                    cont = r
            elif fcd < date_from and (m_lcd==m_from and y_lcd==y_from):
                r = int(lcdate.strftime("%d"))
                if r > 30:
                    cont = 30
                else:
                    cont = r
        return cont, fcd

    def _get_number_leave_days(self,employee,date_from,date_to):
        number_real_days = 0
        first_day = employee.first_contract_date
        last_day = employee.last_contract_date
        if first_day:
            if first_day <= date_from:
                first_day = date_from
                
            afectation_days =  self.env["hr.leave"].search([("employee_id","=",employee.id),
                                                            ("date_from",">=",first_day),
                                                            ("date_to","<=",date_to),
                                                            ("state","=","validate"),
                                                            ("subtype_id.type_id.have_gratification","=",False),
                                                            ])
            
            number_real_days = sum([i.number_real_days for i in afectation_days])
            
            leave_days_no_counted =  self.env["hr.leave"].search([("employee_id","=",employee.id),
                                                                ("date_from",">=",first_day),
                                                                ("date_to","<=",date_to),
                                                                ("state","=","validate"),
                                                                ("code","in",['16','21']),
                                                                ])
            
            number_leave_days_no_counted = sum([i.number_real_days for i in leave_days_no_counted])
            
        return number_real_days, number_leave_days_no_counted
    
    def _compute_sublines(self, date_from, employee):
        sublines = []
        
        per_1 = ['01','02','03','04','05','06']
        per_2 = ['07','08','09','10','11','12']
        
        m_f = date_from.strftime("%m") #Mes de date_from
        
        if m_f in per_1:
            year = int(date_from.strftime("%Y"))
            new_date =  datetime.strptime("01/01/"+str(year), '%d/%m/%Y') 
            
            payslip = self.env["hr.payslip"].search([("date_from","<=",date_from),
                                            ("date_from",">=",new_date),
                                            ("struct_id.company_id.id","=",self.company_id.id),])
            
        elif m_f in per_2:
            year = date_from.strftime("%Y")
            new_date =  datetime.strptime("01/07/"+ year, '%d/%m/%Y')
            
            payslip = self.env["hr.payslip"].search([("date_from","<=",date_from),
                                            ("date_from",">=",new_date),
                                            ("struct_id.company_id.id","=",self.company_id.id),])
            
        line_ids = payslip.filtered(lambda x: x.employee_id == employee).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_gratification == True and x.amount > 0)
        
        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
        
        for code in codes:

            line_ids_code = line_ids.filtered(lambda x: x.code == code)
            if len(line_ids_code) >= 3: #solo se obtiene 3 bonos
                amount = sum([line_id.amount for line_id in line_ids_code])
                average = round(amount/6,2)
                
                val = {
                    "name": line_ids_code[0].name,
                    "cont": len(line_ids_code),
                    "amount": amount,
                    "average": average
                }
                sublines.append(val)
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
                    "Dias No Laborados":child_id.number_leave_days,
                    "Dias Totales del Periodo":child_id.number_total_working_days ,
                    "Dias Acumulados Ant":child_id.days_prev,
                    "Provision Mes":child_id.prov_mes_adjust,
                    "Provision Ant":child_id.total_prev,
                    "Total Acum":child_id.total_prov_mes,
                    "lbs":child_id.grati_lbs,
                    "Dias Laborados":child_id.number_total,
                    "bonificacion mes":child_id.prov_bonf_adjust,
                    "bonificacion Ant":child_id.prov_bonf_prev,
                    "bonificacion Acum":child_id.bonf_prov_mes,
                    "bonificacion LBS":child_id.bonf_lbs
                }
                
                val = {**val1, **val2, **val3}
                values.append(val)
                contador += 1
            obj.generate_excel(values)
            
            
    def generate_excel(self,data):
        
        report_xls = GratiExcelReport(data, self)
        values = {
            'xls_filename': self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)
        
    ################################# state bar #########################################
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
        if any(grati.state not in ('draft', 'cancel') for grati in self):
            raise UserError(_('You cannot delete a grati which is not draft or cancelled!'))
        
    #obtener dias previos acumulados
    def _grati_prev(self, employee, date_from):
        grati_prev = 0
        days_prev_ant = 0
        days_total_ant = 0
        bonf_prev = 0
        
        if date_from.strftime("%m") == '01' or  date_from.strftime("%m") == '07':
            grati_prev = 0
            days_prev_ant = 0
            days_total_ant = 0
            bonf_prev = 0
    
        else:
            m_pf = int(date_from.strftime("%m")) - 1
            y_pf = date_from.strftime("%Y")
            new_date_from = datetime.strptime("01/" + str(m_pf) + "/"+ str(date_from.strftime("%Y")), '%d/%m/%Y')
            data = self.env["hr.prov.grati.line"].search([
                ("date_from", "=", new_date_from),
                ("employee_id", "=", employee.id),
            ])
            grati_prev = data.total_prov_mes
            days_prev_ant = data.days_prev
            days_total_ant = data.number_total
            bonf_prev = data.bonf_prov_mes
        return grati_prev , days_prev_ant, days_total_ant, bonf_prev

    ########################################################################################################

class BonGratiLine(models.Model):
    _name = 'hr.prov.grati.line'
    _description = 'Provision Gratificacion line'	
    # _order = "employee_id.name asc"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    date_real_evaluate = fields.Date(store=True,string="Primer Dia Real Evaluado")
    date_from = fields.Date(related = "parent_id.date_from", store=True)
    date_to = fields.Date(related = "parent_id.date_to", store=True)
    first_contract_date = fields.Date(store=True, string="Fecha Inicio", compute="compute_information")
    identification_id = fields.Char(store=True, string="Num. Doc.", compute="compute_information")
    
    structure_type = fields.Char(string="Tipo de Regimen", compute='_compute_structure_type')
    
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
    
    name = fields.Char(string="Nombre", store=True)
    
    employee_id = fields.Many2one("hr.employee", store=True,string="Empleado")
    salary = fields.Float(string="Sueldo Contrato", default= 0)
    family_asig = fields.Float(string="A.F.", default= 0)
    average_variables = fields.Float(string="Prom. Variables", compute='_compute_average_variables', default= 0)
    total_amount = fields.Float(string="Monto", compute='_compute_total_amount', default= 0, store=True,)
    
    total = fields.Float(string="Total Mes Sin LBS", compute='_compute_total', default= 0, store=True,)
    parent_id = fields.Many2one("hr.prov.grati",string="GRATIFICACIÓN", ondelete='cascade', store=True,)
    subline_ids = fields.One2many("hr.prov.grati.subline", "grati_line", string="Variables")
    number_days = fields.Integer(string="Dias Totales")
    number_leave_days = fields.Integer(string="Ausent.",default=0)
    number_leave_days_no_counted = fields.Integer(string="Ausent. No Contados (Desc Med + Subsidios)s", default=0)
    number_aditional_days = fields.Integer(string="D. Adicionales",default=0, help= "Dias Adicionales de Trabajo cuando no has sido parte de la bonificación grati del periodo anterior.")
    number_total_working_days = fields.Integer(string="D. Trabajados del Periodo",default=0, compute='_compute_number_total_working_days', help="Dias Laborados + Dias Adicionales")
    number_total = fields.Integer(string="D. Laborados", default=0, compute='_compute_number_total', help="Dias Trabajados del Periodo - Dias Ausentismos")
    
    text_notes_2 = fields.Text(string="Notas", store=True, default="")

    cost_center = fields.Char('CC')
    location = fields.Char('Localidad')
    department = fields.Char('Area')
    job = fields.Char('Puesto')
    regime = fields.Char('Regimen L.')
    last_contract_date = fields.Date('Fecha de Cese')
    
    total_prev = fields.Float('Total Acum.', store=True)
    total_prov_mes = fields.Float(string='Prov Act', compute='_compute_total_prov_mes', default= 0, store=True)
    days_prev = fields.Integer(string='Dias Ant', default= 0, store=True)
    grati_lbs = fields.Float(string='LBS', default= 0, store=True,)
    prov_mes_adjust = fields.Float(string='Total Mes',compute='_compute_prov_mes_adjust', default= 0, store=True)
    grati_pagada = fields.Float(string='grati_pagada', default= 0, store=True,)
    
    prov_bonf_prev=fields.Float(string='Bonf Acum', store=True)
    bonf_prov_mes = fields.Float(string='Bonf Act', compute='_compute_bonf_prov_mes', default= 0, store=True)
    bonf_lbs = fields.Float(string='Bonf LBS', default=0, store=True)
    prov_bonf_adjust=fields.Float(string='Bonf Mes', compute='_compute_prov_bonf_adjust', default= 0, store=True)
    bonf_pagada = fields.Float(string='Bonf Pagada', default= 0, store=True)
    bonf_total=fields.Float(string='Bonf Total', compute='_compute_bonf_total')
    analytic_ac=fields.Char(string='Cuenta Analitica', store=True)
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('verify', 'Enviado'),
        ('approve', 'Aprobado'),
        ('refuse', 'Rechazado'),
        ('cancel', 'Cancelado'),
    ], string="State", default='draft', tracking=True, copy=False)

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark gratificación as approve if not confirmed.'))
        self.write({'state': 'approve'})
    
    @api.depends('grati_lbs', 'total_prev', 'total')
    def _compute_prov_mes_adjust(self):
        for record in self:
            if record.grati_pagada > 0:
                record.prov_mes_adjust = record.grati_pagada - record.total_prev
            elif record.grati_lbs > 0:
                record.prov_mes_adjust = record.grati_lbs - record.total_prev
            else:
                record.prov_mes_adjust = record.total
    
    @api.depends('bonf_lbs', 'prov_bonf_prev', 'bonf_total', 'bonf_prov_mes')
    def _compute_prov_bonf_adjust(self):
        for record in self:
            if record.bonf_pagada > 0:
                    record.prov_bonf_adjust = record.bonf_pagada - record.prov_bonf_prev
            elif record.bonf_lbs > 0:
                    record.prov_bonf_adjust = record.bonf_lbs - record.prov_bonf_prev
            else:
                record.prov_bonf_adjust=record.bonf_total + (record.bonf_lbs - record.bonf_prov_mes)

    @api.depends('total', 'total_prev')
    def _compute_total_prov_mes(self):
        for record in self:           
            record.total_prov_mes = record.prov_mes_adjust + record.total_prev

    @api.depends('bonf_total','prov_bonf_prev')
    def _compute_bonf_prov_mes(self):
        for record in self:
            record.bonf_prov_mes = record.prov_bonf_adjust + record.prov_bonf_prev
    
    @api.depends('subline_ids')
    def _compute_average_variables(self):
        for record in self:
            amount = 0
            for subline_id in record.subline_ids:
                amount += subline_id.average
            record.average_variables = amount

    #base computable
    @api.depends('salary', 'family_asig', 'average_variables')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.salary + record.family_asig + record.average_variables
            
    #PROV ACTUAL
    @api.depends('total_amount')
    def _compute_total(self):
        for record in self:
            if record.employee_id.contract_id.peru_employee_regime.abbr == 'RG':
                record.total = round(record.total_amount/180*(record.number_total + record.days_prev) - record.total_prev,2)          
            elif record.employee_id.contract_id.peru_employee_regime.abbr == 'RP':
                record.total = round((record.total_amount/180*(record.number_total + record.days_prev) - record.total_prev)/2,2)
            elif record.employee_id.contract_id.peru_employee_regime.abbr == 'RM':
                record.total = round((record.total_amount/180*(record.number_total + record.days_prev) - record.total_prev)*0,2)
    
    #PROV. BEXT ACTUAL
    @api.depends('total_amount')
    def _compute_bonf_total(self):
        for record in self:
        
            if(record.employee_id.health_regime_id.code == '02'):
                bonf_percentage = 6.75/100 # 6.75% para seguro EPS
            else:
                bonf_percentage = 9/100  # 9% para otros seguros
            
            if record.employee_id.contract_id.peru_employee_regime.abbr == 'RG':
                record.bonf_total = round(record.total_amount * bonf_percentage / 180 * (record.number_total + record.days_prev) - record.prov_bonf_prev, 2)
            elif record.employee_id.contract_id.peru_employee_regime.abbr == 'RP':
                record.bonf_total = round((record.total_amount * bonf_percentage / 180 * (record.number_total + record.days_prev) - record.prov_bonf_prev)/2, 2)
            elif record.employee_id.contract_id.peru_employee_regime.abbr == 'RM':
                record.bonf_total = round((record.total_amount * bonf_percentage / 180 * (record.number_total + record.days_prev) - record.prov_bonf_prev)*0, 2)
            
    
    @api.depends('number_days', 'number_aditional_days')
    def _compute_number_total_working_days(self):
        for record in self:
            record.number_total_working_days =  (record.number_days + record.number_aditional_days)

    @api.depends('number_total_working_days', 'number_leave_days', 'number_leave_days_no_counted')
    def _compute_number_total(self):
        for record in self:
            record.number_total =  (record.number_total_working_days - record.number_leave_days)
            if record.number_leave_days_no_counted >= 80:
                diff = record.number_leave_days_no_counted - 60
                record.number_total -= diff
                
                note = "- El empleado a superado los 60 días por incapacidad temporal - son de {} días.".format(str(diff))
                if record.text_notes_2 == "" or not record.text_notes_2:
                    record.text_notes_2 = note
                else :
                    note = "\n" + note
                    record.text_notes_2 += note

class BonGratiSubLine(models.Model):
    _name = 'hr.prov.grati.subline'
    _description = 'Provision gratificacion subline'
    
    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")
    grati_line = fields.Many2one("hr.prov.grati.line", ondelete='cascade', store=True,)