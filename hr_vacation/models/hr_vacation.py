from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date
import pytz

class Vacation(models.Model):
    _name = 'hr.vacation'
    _description = 'RECORD VACACIONAL'

    name = fields.Char(string="Nombre", compute='_compute_name', default="" )
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    child_ids = fields.One2many("hr.vacation.line","parent_id",string="Vacaciones por Periodos",)
    date_to_cese = fields.Date(string="Fecha de Cierre",required=True, store=True,default=fields.Date.today())
    child_acum_ids = fields.One2many("hr.vacation.acum.line","parent_id",string="Vacaciones Acumuladas")
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')
    child_acum_ids_count = fields.Integer(compute='_compute_child_acum_ids_count')

    def action_open_hr_vacation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros por Periodo",
        }

    def action_open_hr_vacation_acum(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.acum.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_acum_ids.ids]],
            "name": "Registros por Persona",
        }

    @api.depends('child_acum_ids')
    def _compute_child_acum_ids_count(self):
        for record in self:
            record.child_acum_ids_count = len(record.child_acum_ids)

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)

    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            record.name = f"Record Vacacional - {self.company_id.name}"

    def _first_day(self, date:datetime):
        return date.replace(day=1)
    
    def _filter_employees(self, employees, date_to):
        employees = employees.filtered(lambda x: x.first_contract_date <= self._first_day(date_to) and not x.last_contract_date) # filtrado de los empleados segun condiciones
        return employees


    def is_last_day_of_feb(self, date):
        return date.month == 2 and date.day == 28 and not self.is_leap_year(date.year)

    def is_leap_year(self, year):
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def days360(self,start_date, end_date, method=True):
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if method:
            start_day = start_date.day
            end_day = end_date.day

            if start_day == 31:
                start_day = 30

            if method and end_day == 31 and start_day < 30:
                end_day = 1

        else:
            start_day = start_date.day
            end_day = end_date.day

            if start_day == 31 or (method and start_date.month == 2 and self.is_last_day_of_feb(start_date)):
                start_day = 30

            if end_day == 31:
                
                if start_day < 30:
                    end_day = 1
                    
                elif start_date.month == 12:
                    end_day = 30
                    
                else:
                    end_day = 30

        return (end_date.year - start_date.year) * 360 + (end_date.month - start_date.month) * 30 + (end_day - start_day)
    
    #### VACACIONES GOZADAS
    def _get_vacation_enjoyed(self, employee, date_to_cese, period_date_from, period_date_to):
        period_date_from_year = period_date_from.year
        period_date_to_year  = period_date_from_year+1
        period = str(period_date_from_year)+"-"+str(period_date_to_year)
        afectation_days = self.env["hr.leave"].search([
            ("employee_id","=",employee.id),
            ("selected_period_for_holidays","=",period),
            ("state","=","validate"),
            ("code","=",'23'),
        ])
        
        if len(afectation_days) != 0:
            return sum([i.number_real_days for i in afectation_days])
        
        return 0
    
    def _get_date_aniversary_past_year(self, first_day, anio) :
        anio = int(anio)
        
        if anio > first_day.year:
            past_date = first_day.replace(year=anio-1)
            present_date = first_day.replace(year=anio)
            return past_date, present_date
        
        if anio == first_day.year:
            return False, first_day
        
        return False, False

    def _get_vacation_compensable(self,days_earrings, vacation_pending, vacation_trunced):
        r = days_earrings - (vacation_pending + vacation_trunced) 
        if r >= 0:
            return r
        return 0
    
    def _get_vacation_pending(self,days_earrings,vacation_trunced):
        if days_earrings - vacation_trunced < 0:
            return 0
        
        if days_earrings - vacation_trunced > 30:
            return 30
        
        return days_earrings - vacation_trunced

    def _get_vacation_trunced(self, employee, date_to_cese, period_date_from, period_date_to, days_earrings):
        first_day = employee.first_contract_date
        evaluate_day = first_day + relativedelta(months=1)
        aux_date = period_date_from + relativedelta(years=1)
        
        if evaluate_day < date_to_cese and date_to_cese == period_date_to :
            return days_earrings
        
        return 0

    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)
    
    def _compute_sublines(self, employee, period_date_from, period_date_to):
        period_date_from_year = period_date_from.year
        period_date_to_year  = period_date_from_year+1
        period = f"{str(period_date_from_year)}-{str(period_date_to_year)}"
        leaves = self.env['hr.leave'].search([
            ('selected_period_for_holidays', '=', period),
            ('code', '=', '23'),
            ('state', '=', 'validate'),
            ('employee_id', '=', employee.id)
        ])
        if leaves:
            return [{"leave_id":leave.id} for leave in leaves]
        return []

    def _generate_periods(self, employee, date_to_cese):
        first_day = employee.first_contract_date
        list_periods = []
        
        if employee.last_contract_date:
            if  employee.last_contract_date <  date_to_cese :
                date_to_cese = employee.last_contract_date

        i_period = first_day
        while i_period <= date_to_cese :
            f_period = i_period + relativedelta(years=1)
            if i_period <= date_to_cese <= f_period:
                list_periods.append([i_period,date_to_cese,i_period.year,f_period.year])
                break
            list_periods.append([i_period,f_period,i_period.year,f_period.year])
            i_period = f_period

        return list_periods


    def compute_sheet(self):
        self.ensure_one() # pasar solo un registro
        self.child_ids.subline_ids.unlink() # elimina los datos que estan likeados de sub hijos
        self.child_ids.unlink() # elimina los datos linkeado de los padres 
        self.child_acum_ids.unlink()
        peru_timezone  = pytz.timezone("America/Lima")
        current_time = datetime.now(peru_timezone)
        self.date_to_cese = current_time.date() + relativedelta(days=1)
        val_list = [] 

        employees = self.env["hr.employee"].search([("first_contract_date","<=",self.date_to_cese)])
        
        for employee in employees:
            list_periods = self._generate_periods(employee,self.date_to_cese)
            
            for period in list_periods:
                period_date_from = period[0]
                period_date_to = period[1]
                period_year_from = period[2]
                period_year_to = period[3]
                val_list.append({
                    "period_year_from":period_year_from,
                    "period_year_to":period_year_to,
                    "period_date_from":period_date_from,
                    "period_date_to":period_date_to,
                    "employee_id":employee.id,
                    "parent_id":self.id,
                    "subline_ids": [(0, 0, subline) for subline in self._compute_sublines(employee, period_date_from, period_date_to)],
                })

        self.env["hr.vacation.line"].create(val_list)            
        self.env.cr.commit()

        self._update_vacation_compensable()
        self._create_child_acum_ids()

    def _update_vacation_compensable(self):
        employee_ids = self.child_ids.mapped("employee_id")
        
        if employee_ids:
            for emp in employee_ids:
                child_ids = self.child_ids.filtered(lambda x: x.employee_id.id == emp.id).sorted(key=lambda r: r.period_char_date, reverse=True)
                tamanio_child_ids = len(child_ids) 
                if tamanio_child_ids >= 3:
                    date_to_evaluate = self.date_to_cese - relativedelta(years=2)
                    for child in child_ids.filtered(lambda x: x.period_date_from < date_to_evaluate ):
                        if child.days_earrings > 0:
                            child.vacation_compensable = child.vacation_days_earrings 


    def _create_child_acum_ids(self):
        employee_ids = self.child_ids.mapped("employee_id")
        
        if employee_ids:
            val_list = []
            
            for emp in employee_ids:
                child_ids = self.child_ids.filtered(lambda x: x.employee_id.id == emp.id)
                period_date_from = child_ids[0].period_date_from
                period_date_to = child_ids[-1].period_date_to
                period_year_from = child_ids[0].period_year_from
                period_year_to = child_ids[-1].period_year_to
                
                val_list.append({
                    "employee_id": emp.id,
                    "structure_type_abbr": emp.contract_id.peru_employee_regime.abbr,
                    "period_year_from": period_year_from,
                    "period_year_to": period_year_to,
                    "period_date_from": period_date_from,
                    "period_date_to": period_date_to,
                    "parent_id": self.id,
                    "child_ids": [(4, i.id) for i in child_ids],
                })
                
            self.env["hr.vacation.acum.line"].create(val_list)
            return self.env.cr.commit()