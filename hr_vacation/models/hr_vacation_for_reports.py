from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date
from .hr_vacation_report import VacationExcelReport

class Vacation(models.Model):
    _name = 'hr.vacation.report'
    _description = 'REPORTES PARA VACACIONES'


    name = fields.Char(string="Nombre", compute='_compute_name', default="" )
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)

    child_ids = fields.One2many("hr.vacation.report.line","parent_id",string="Vacaciones por Periodos",)
    
    date_to_cese = fields.Date(string="Fecha de Cierre",required=True, store=True,default=fields.Date.today())

    child_acum_ids = fields.One2many("hr.vacation.report.acum.line","parent_id",string="Vacaciones Acumuladas")
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    child_acum_ids_count = fields.Integer(compute='_compute_child_acum_ids_count')
    


    def generate_excel(self,data):
        report_xls = VacationExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE EXCEL TABULAR "+self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)


    def action_open_hr_vacation_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.report.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros por Periodo",
        }

    def action_open_hr_vacation_report_acum(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.report.acum.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_acum_ids.ids]],
            "name": "Registros por Persona",
        }

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)

    @api.depends('child_acum_ids')
    def _compute_child_acum_ids_count(self):
        for record in self:
            record.child_acum_ids_count = len(record.child_acum_ids)

    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            record.name = "Reporte Record Vacacional - " + self.company_id.name

    def _first_day_of_month(self,any_day):
        if any_day.day != 1:
            return any_day - timedelta(days=(any_day.day  - 1))
        return any_day
    
    def _filter_employees(self,employees,date_to):
        employees =  employees.filtered(lambda x: x.first_contract_date <= self._first_day_of_month(date_to) and 
                                        not x.last_contract_date) # filtrado de los empleados segun condiciones
        return employees


    def is_last_day_of_feb(self,date):
        return date.month == 2 and date.day == 28 and not self.is_leap_year(date.year)

    def is_leap_year(self,year):
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


    #### CANTIDAD PERIODOS
    def _get_number_periods(self,employee,date_to_cese, period_date_from,period_date_to):
        # first_day = employee.first_contract_date
        str_first_contract_date = period_date_from.strftime("%Y-%m-%d")
        str_date_to_cese = period_date_to.strftime("%Y-%m-%d")
        result = self.days360(str_first_contract_date, str_date_to_cese, method=True )/360

        return result
    
    #### VACACIONES GOZADAS
    def _get_vacation_enjoyed(self,employee,date_to_cese, period_date_from,period_date_to):
        period_date_from_year = period_date_from.year
        period_date_to_year  = period_date_from.year + 1
        period = str(period_date_from_year)+"-"+str(period_date_to_year)
        afectation_days = self.env["hr.leave"].search([("employee_id","=",employee.id),
                                    ("selected_period_for_holidays","=",period),
                                    ("state","=","validate"),
                                    ("code","=",'23')])
        if len(afectation_days) != 0:
            return sum([i.number_real_days for i in afectation_days])
        return 0
    
    def _get_date_aniversary_past_year(self,first_day,anio) :
        anio = int(anio)
        if anio > first_day.year:
            past_date = first_day.replace(year=anio-1)
            present_date = first_day.replace(year=anio)
            return past_date, present_date
        elif anio == first_day.year:
            return False,first_day
        else :
            return False, False


    def _get_vacation_compensable(self,days_earrings, vacation_pending, vacation_trunced, ):
        r = days_earrings - (vacation_pending + vacation_trunced) 
        if r >= 0:
            return r
        return 0
    
    def _get_vacation_pending(self,days_earrings,vacation_trunced):
        if days_earrings - vacation_trunced < 0:
            return 0
        elif days_earrings - vacation_trunced > 30:
            return 30
        return days_earrings - vacation_trunced



    def _get_vacation_trunced(self, employee, date_to_cese, period_date_from, period_date_to, days_earrings):
        
        first_day = employee.first_contract_date
        evaluate_day = first_day + relativedelta(months=1)
        aux_date = period_date_from + relativedelta(years=1)
        if evaluate_day < date_to_cese and date_to_cese == period_date_to :
            return days_earrings
        return 0

        # past_anio, current_anio  = self._get_date_aniversary_past_year(first_day, date_to_cese.year)

        # if not current_anio and date_to_cese.month >= current_anio.month:
        #     return self.days360(current_anio, date_to_cese, True )/360*30
        # elif current_anio and date_to_cese.month < current_anio.month:
        #     return self.days360(past_anio, date_to_cese, True)/360*30
        # elif current_anio and date_to_cese.month >= current_anio.month:
        #     return self.days360(current_anio, date_to_cese, True)/360*30
        # else :
        #     return 0    

    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        # this will never fail 
        return next_month - timedelta(days=next_month.day)

 

    def _generate_periods(self,
                          employee,
                          date_to_cese,
                          period_date_from,
                          period_date_to):
        
        first_day = employee.first_contract_date
        list_periods = []
        if first_day < period_date_from:
            first_day = period_date_from

        if employee.last_contract_date :
            if employee.last_contract_date <  date_to_cese:
                date_to_cese = employee.last_contract_date

        if period_date_to < date_to_cese:
            date_to_cese = period_date_to

        i_period = first_day
        f_period = first_day + relativedelta(months=1)
        f_period = self._first_day_of_month(f_period)

        if  date_to_cese < f_period:
            f_period = date_to_cese

        list_periods.append([i_period,f_period])
        
        while f_period < date_to_cese:
            i_period = f_period
            f_period = f_period + relativedelta(months=1)
            
            if  date_to_cese < f_period:
                f_period = date_to_cese
                list_periods.append([i_period,f_period])

                break
            list_periods.append([i_period,f_period])

        return list_periods

    def _compute_sublines(self,
                          employee,
                          date_to_cese,
                          period_date_from,
                          period_date_to):
        
        list_periods = self._generate_periods(employee,
                                              date_to_cese,
                                              period_date_from,
                                              period_date_to)
        val_list = [] 

        for period in list_periods:
            period_date_from = period[0]
            period_date_to = period[1]
            # CANTIDAD DE PERIODOS
            number_periods = self._get_number_periods(employee,self.date_to_cese, period_date_from,period_date_to )
            # DIAS GENERADOS

            days_generated = number_periods* 30

            
            # VACACIONES GOZADAS
            vacation_enjoyed = self._get_vacation_enjoyed(employee,self.date_to_cese, period_date_from,period_date_to)
            # PENDIENTES
            days_earrings = days_generated - vacation_enjoyed
            # VACACIONES TRUNCAS
            # vacation_trunced = self._get_vacation_trunced(employee,self.date_to_cese, period_date_from,period_date_to)
            vacation_trunced = self._get_vacation_trunced(employee,self.date_to_cese, period_date_from,period_date_to,days_earrings)

            # VACACIONES PENDIENTES
            #vacation_pending = self._get_vacation_pending(days_earrings,vacation_trunced, )
            # VACACIONES INDEMNIZABLES
            #vacation_compensable = self._get_vacation_compensable(days_earrings, vacation_pending, vacation_trunced, )
            val = {
                "period_date_from":period_date_from,
                "period_date_to":period_date_to,
                "employee_id":employee.id,
                "number_periods":number_periods,# CANTIDAD DE PERIODOS
                "days_generated":days_generated ,# DIAS GENERADOS
                "vacation_enjoyed":vacation_enjoyed, # VACACIONES GOZADAS
                "days_earrings": days_earrings, # PENDIENTES
                #"vacation_compensable": vacation_compensable, # VACACIONES INDEMNIZABLES
                #"vacation_pending":vacation_pending, # VACACIONES PENDIENTES
                "vacation_trunced":vacation_trunced , # VACACIONES TRUNCAS
            }
            val_list.append(val)
        return val_list

    def _compute_period_employee_date_to(self,employee,date_to_cese):
        first_day = employee.first_contract_date
        list_periods = []
        
        if employee.last_contract_date:
            if  employee.last_contract_date <  date_to_cese :
                date_to_cese = employee.last_contract_date

        i_period = first_day
        f_period = first_day + relativedelta(years=1)
        
        list_periods.append([i_period,f_period,i_period.year,f_period.year])

        while f_period < date_to_cese :

            i_period = f_period
            f_period = f_period + relativedelta(years=1)
            list_periods.append([i_period,f_period,i_period.year,f_period.year])

        return list_periods


    def compute_sheet(self):
        self.ensure_one() # pasar solo un registro

        self.child_ids.subline_ids.unlink() # elimina los datos que estan likeados de sub hijos
        self.child_ids.unlink() # elimina los datos linkeado de los padres 
        self.child_acum_ids.unlink()
        val_list = [] 

        employees = self.env["hr.employee"].search([
            ("first_contract_date","<",self.date_to_cese),
        ])        
        for employee in employees:
            list_periods = self._compute_period_employee_date_to(employee,self.date_to_cese)

            for period in list_periods:
                period_date_from = period[0]
                period_date_to = period[1]
                period_year_from = period[2]
                period_year_to = period[3]
                val = {
                    "period_year_from":period_year_from,
                    "period_year_to":period_year_to,
                    "period_date_from":period_date_from,
                    "period_date_to":period_date_to,
                    "employee_id":employee.id,
                    "parent_id":self.id,
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(employee,
                                                                                         self.date_to_cese,
                                                                                         period_date_from,
                                                                                         period_date_to)],
                }

                val_list.append(val)

        self.env["hr.vacation.report.line"].create(val_list)            
        self.env.cr.commit()

        self._update_vacation_compensable()
        self._create_child_acum_ids()
        return  None


    def action_dowload_report_tabular_vacation_report(self):

        for obj in self:
            values = []

            for child_id in obj.child_ids:
                val = {
                    #### EMPLEADOS
                    "Cod.":child_id.employee_id.cod_ref or '',
                    "Doc.":child_id.employee_id.identification_id or '',
                    "Apellidos y Nombres":child_id.employee_id.name or '',
                    "Fecha Ingreso":child_id.employee_id.first_contract_date or '',
                    "Fecha Cese":child_id.employee_id.last_contract_date or '',
                    "Puesto":child_id.employee_id.job_id.name or '',
                    #### DIAS 
                    "Periodo":child_id.period_char_date,

                    "Cantidad de Periodos":child_id.number_periods,
                    "Dias Generados":child_id.days_generated,
                    "Vacaciones Gozadas":child_id.vacation_enjoyed,
                    "Pendientes":child_id.days_earrings,
                    "Vacaciones Vencidas":child_id.vacation_compensable,
                    "Vacaciones Truncas":child_id.vacation_trunced ,
                }
 
                values.append(val)
            obj.generate_excel(values)




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
                            child.vacation_compensable = child.days_earrings 


    def _create_child_acum_ids(self):
        employee_ids = self.child_ids.mapped("employee_id")
        if employee_ids:
            val_list = []
            for emp in employee_ids:
                child_ids = self.child_ids.filtered(lambda x: x.employee_id.id == emp.id)
                number_periods = sum([i.number_periods for i in child_ids])
                days_generated = sum([i.days_generated for i in child_ids])    
                vacation_enjoyed = sum([i.vacation_enjoyed for i in child_ids])    
                days_earrings = sum([i.days_earrings for i in child_ids])    
                vacation_compensable = sum([i.vacation_compensable for i in child_ids])    
                vacation_trunced = sum([i.vacation_trunced for i in child_ids])
                period_date_from = child_ids[0].period_date_from
                period_date_to = child_ids[-1].period_date_to
                period_year_from = child_ids[0].period_year_from
                period_year_to = child_ids[-1].period_year_to

                val = {
                    "employee_id":emp.id,
                    "structure_type_abbr": emp.contract_id.peru_employee_regime.abbr,
                    "number_periods":number_periods,
                    "days_generated":days_generated,
                    "vacation_enjoyed":vacation_enjoyed,
                    "days_earrings":days_earrings,
                    "vacation_compensable":vacation_compensable,
                    "vacation_trunced":vacation_trunced,
                    "period_year_from":period_year_from,
                    "period_year_to":period_year_to,
                    "period_date_from":period_date_from,
                    "period_date_to":period_date_to,
                    "parent_id":self.id,
                    "child_ids": [(4, i.id ) for i in child_ids],
                    
                }
                val_list.append(val)
            self.env["hr.vacation.report.acum.line"].create(val_list)
            #id_accum_created = self.env.cr.commit()
            return self.env.cr.commit()
            
########################################################################################################
########################################################################################################
########################################################################################################
########################################################################################################



class VacAcumLine(models.Model):
    _name = 'hr.vacation.report.acum.line'
    _description = 'VACACION ACUM EMPLEADO' 


    employee_id = fields.Many2one("hr.employee", string="Empleado")
    job = fields.Char(related="employee_id.job_id.name", string="Puesto", store=True,)
    first_contract_date =  fields.Date(related="employee_id.first_contract_date", string="Fecha Ingreso", store=True,)
    # number_periods = fields.Float(string="Cantidad de Periodos", compute='_compute_number_periods',store=True,)
    # days_generated =  fields.Float(string="Dias Generados", compute='_compute_days_generated', store=True,)
    # vacation_enjoyed =  fields.Float(string="Vacaciones Gozadas", compute='_compute_vacation_enjoyed', store=True,)
    # days_earrings =  fields.Float(string="Pendientes", compute='_compute_days_earrings', store=True,)
    # vacation_compensable = fields.Float(string="Vacaciones Vencidas", store=True,)
    # vacation_pending =  fields.Float(string="Vacaciones Pendientes", compute='_compute_vacation_pending', store=True,)
    # vacation_trunced =  fields.Float(string="Vacaciones Truncas", compute='_compute_vacation_trunced', store=True,)


    number_periods = fields.Float(string="Cantidad de Periodos", store=True,)
    days_generated =  fields.Float(string="Dias Generados",  store=True,)
    vacation_enjoyed =  fields.Float(string="Vacaciones Gozadas",  store=True,)
    days_earrings =  fields.Float(string="Pendientes", store=True,)
    vacation_compensable = fields.Float(string="Vacaciones Vencidas", store=True,)
    vacation_pending =  fields.Float(string="Vacaciones Pendientes",   store=True,)
    vacation_trunced =  fields.Float(string="Vacaciones Truncas", store=True,)


    period_year_from = fields.Integer("Año Inicio", store=True,)
    period_year_to = fields.Integer("Año Fin", store=True,)
    period_date_from = fields.Date("Fecha Inicio", store=True,)
    period_date_to = fields.Date("Fecha Fin", store=True,)
    period_char_date = fields.Char(string="Periodo", compute='_compute_period_char_date' ,store=True,)

    parent_id = fields.Many2one("hr.vacation.report",string="VAC", ondelete='cascade', store=True,)
    child_ids = fields.One2many("hr.vacation.report.line","accum_id",string="Vacaciones por Periodos",)

    structure_type_abbr = fields.Char(string="Tipo de Regimen", related='employee_id.contract_id.peru_employee_regime.abbr', store=True)


    @api.depends('period_year_from','period_year_to')
    def _compute_period_char_date(self):
        for record in self:
            record.period_char_date = str(record.period_year_from) + "-" + str(record.period_year_to)    



########################################################################################################
########################################################################################################
########################################################################################################
########################################################################################################

class VacLine(models.Model):
    _name = 'hr.vacation.report.line'
    _description = 'VACACION EMPLEADO' 


    employee_id = fields.Many2one("hr.employee", string="Empleado")
    job = fields.Char(related="employee_id.job_id.name", string="Puesto", store=True,)
    first_contract_date =  fields.Date(related="employee_id.first_contract_date", string="Fecha Ingreso", store=True,)
    number_periods = fields.Float(string="Cantidad de Periodos", compute='_compute_number_periods',store=True,)
    days_generated =  fields.Float(string="Dias Generados", compute='_compute_days_generated', store=True,)
    vacation_enjoyed =  fields.Float(string="Vacaciones Gozadas", compute='_compute_vacation_enjoyed', store=True,)
    days_earrings =  fields.Float(string="Pendientes", compute='_compute_days_earrings', store=True,)
    vacation_compensable = fields.Float(string="Vacaciones Vencidas", store=True,)
    vacation_pending =  fields.Float(string="Vacaciones Pendientes", compute='_compute_vacation_pending', store=True,)
    vacation_trunced =  fields.Float(string="Vacaciones Truncas", compute='_compute_vacation_trunced', store=True,)

    period_year_from = fields.Integer("Año Inicio", store=True,)
    period_year_to = fields.Integer("Año Fin", store=True,)
    period_date_from = fields.Date("Fecha Inicio", store=True,)
    period_date_to = fields.Date("Fecha Fin", store=True,)
    period_char_date = fields.Char(string="Periodo", compute='_compute_period_char_date' ,store=True,)

    parent_id = fields.Many2one("hr.vacation.report",string="VAC", ondelete='cascade', store=True,)
    accum_id = fields.Many2one("hr.vacation.report.acum.line",string="VAC ACUM", ondelete='cascade', store=True,)

    subline_ids = fields.One2many("hr.vacation.report.subline","vac_line",string="Variables")

    structure_type_abbr = fields.Char(string="Tipo de Regimen", related='employee_id.contract_id.peru_employee_regime.abbr', store=True)

    @api.depends('period_year_from','period_year_to')
    def _compute_period_char_date(self):
        for record in self:
            record.period_char_date = str(record.period_year_from) + "-" + str(record.period_year_to)    

    @api.depends('subline_ids')
    def _compute_number_periods(self):
        for record in self:
            record.number_periods = sum([i.number_periods for i in record.subline_ids])    

    @api.depends('subline_ids')
    def _compute_days_generated(self):
        for record in self:
            # record.days_generated = sum([i.days_generated for i in record.subline_ids])
            if record.structure_type_abbr == 'RG':
                record.days_generated = sum([i.days_generated for i in record.subline_ids])
            else:
                record.days_generated = sum([i.days_generated for i in record.subline_ids])/2


    @api.depends('subline_ids')
    def _compute_vacation_enjoyed(self):
        for record in self:
            record.vacation_enjoyed = sum([i.vacation_enjoyed for i in record.subline_ids])    

    @api.depends('subline_ids')
    def _compute_days_earrings(self):
        for record in self:
            # record.days_earrings = sum([i.days_earrings for i in record.subline_ids])
            if record.structure_type_abbr == 'RG':
                record.days_earrings = sum([i.days_earrings for i in record.subline_ids])
            else:
                record.days_earrings = sum([i.days_earrings for i in record.subline_ids])/2

    @api.depends('subline_ids')
    def _compute_vacation_pending(self):
        for record in self:
            record.vacation_pending = sum([i.vacation_compensable for i in record.subline_ids])

    @api.depends('subline_ids')
    def _compute_vacation_trunced(self):
        for record in self:
            # for rcd in record.subline_ids:
            #     fsc = rcd.employee_id.first_contract_date

            first_day = record.employee_id.first_contract_date
            evaluate_day = first_day + relativedelta(months=1)
            aux_date = record.period_date_from + relativedelta(years=1)
            if evaluate_day < record.parent_id.date_to_cese and record.period_date_from <=  record.parent_id.date_to_cese <= record.period_date_to :
                record.vacation_trunced = record.days_earrings
                # return days_earrings
        # return 0

        #     record.vacation_trunced = sum([i.vacation_trunced for i in record.subline_ids])    

########################################################################################################
########################################################################################################
########################################################################################################
########################################################################################################

class VacSubLine(models.Model):
    _name = 'hr.vacation.report.subline'
    _description = 'VAC DETALLE'


    employee_id = fields.Many2one("hr.employee", string="Empleado")
    number_periods = fields.Float(string="Cantidad de Periodos", store=True,)
    days_generated =  fields.Float(string="Dias Generados", store=True,)
    vacation_enjoyed =  fields.Float(string="Vacaciones Gozadas", store=True,)
    days_earrings =  fields.Float(string="Pendientes", store=True,)
    ### ELMINAR
    vacation_compensable = fields.Float(string="Vacaciones Vencidas", store=True,)
    vacation_pending =  fields.Float(string="Vacaciones Pendientes", store=True,)
    vacation_trunced =  fields.Float(string="Vacaciones Truncas", store=True,)

    period_date_from = fields.Date("Fecha Fin", store=True,)
    period_date_to = fields.Date("Fecha Inicio", store=True,)
    period_char_date = fields.Char(string="Periodo", compute='_compute_period_char_date', store=True,)

    vac_line = fields.Many2one("hr.vacation.report.line", ondelete='cascade', string="", store=True,)

    

    @api.depends('period_date_from','period_date_to')
    def _compute_period_char_date(self):
        for record in self:
            record.period_char_date = record.period_date_from.strftime("%d/%m/%Y") + "-" + record.period_date_to.strftime("%d/%m/%Y")

