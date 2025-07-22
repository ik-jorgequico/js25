from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date


class VacLine(models.Model):
    _name = 'hr.vacation.line'
    _description = 'RECORD VACACIONAL POR PERIODO' 

    employee_id = fields.Many2one("hr.employee", string="Empleado")
    job = fields.Char(related="employee_id.job_id.name", string="Puesto", store=True,)
    first_contract_date =  fields.Date(related="employee_id.first_contract_date", string="Fecha Ingreso", store=True,)
    last_contract_date =  fields.Date(related="employee_id.last_contract_date", string="Fecha de Cese", store=True,)

    period_year_from = fields.Integer("Año Inicio", store=True,)
    period_year_to = fields.Integer("Año Fin", store=True,)
    period_date_from = fields.Date("Fecha Inicio", store=True,)
    period_date_to = fields.Date("Fecha Fin", store=True,)
    period_char_date = fields.Char(string="Periodo", compute='_compute_period_char_date' ,store=True,)

    number_periods = fields.Float(string="Cantidad de Periodos", compute='_compute_number_periods',store=True,)
    days_generated =  fields.Float(string="Dias Generados", compute='_compute_days_generated', store=True,)
    vacation_enjoyed =  fields.Float(string="Vac. Gozadas", compute='_compute_vacation_enjoyed', store=True,)
    days_earrings =  fields.Float(string="Pendientes", compute='_compute_days_earrings', store=True,)
    vacation_days_earrings =  fields.Float(string="Vac. Pendientes", compute='_compute_vacation_days_earrings', store=True,)

    vacation_trunced =  fields.Float(string="Vac. Truncas", compute='_compute_vacation_trunced', store=True,)
    vacation_compensable = fields.Float(string="Vac. Vencidas", store=True,)
    vacation_purchased = fields.Float(string="Vac. Compradas", compute='_compute_vacation_purchased',store=True,)

    parent_id = fields.Many2one("hr.vacation",string="VAC", ondelete='cascade', store=True,)
    accum_id = fields.Many2one("hr.vacation.acum.line",string="VAC ACUM", ondelete='cascade', store=True,)

    subline_ids = fields.One2many("hr.vacation.subline","vac_line",string="Variables")
    structure_type_abbr = fields.Char(string="Tipo de Régimen",related='employee_id.contract_id.peru_employee_regime.abbr',store=True)

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

    @api.depends('period_year_from','period_year_to')
    def _compute_period_char_date(self):
        for record in self:
            record.period_char_date = str(record.period_year_from) + "-" + str(record.period_year_to)    

    @api.depends('period_date_from','period_date_to')
    def _compute_number_periods(self):
        for record in self:
            record.number_periods = self._get_number_periods(record.period_date_from, record.period_date_to)

    # @api.depends('number_periods')
    # def _compute_days_generated(self):
    #     for record in self:
    #         record.days_generated = round(record.number_periods*30,2)

    @api.depends('number_periods', 'structure_type_abbr')
    def _compute_days_generated(self):
        for record in self:
            if record.structure_type_abbr == 'RG':
                record.days_generated = round(record.number_periods * 30, 2)
            else:
                record.days_generated = round(record.number_periods * 15, 2)


    @api.depends('subline_ids')
    def _compute_vacation_enjoyed(self):
        for record in self:
            record.vacation_enjoyed = sum([i.number_real_days for i in record.subline_ids])    

    @api.depends('days_generated','vacation_enjoyed')
    def _compute_days_earrings(self):
        for record in self:
            record.days_earrings = record.days_generated - record.vacation_enjoyed

    # @api.depends('days_earrings','vacation_compensable','vacation_trunced','first_contract_date')
    # def _compute_vacation_days_earrings(self):
    #     for record in self:
    #         b = record.period_date_from  + relativedelta(years=1) 
            
    #         if  b <  record.parent_id.date_to_cese:
    #             record.vacation_days_earrings = record.days_earrings - record.vacation_purchased - record.vacation_compensable
    #         else:
    #             record.vacation_days_earrings = 0

    @api.depends('days_earrings', 'vacation_purchased', 'vacation_compensable', 'structure_type_abbr')
    def _compute_vacation_days_earrings(self):
        for record in self:
            b = record.period_date_from + relativedelta(years=1)
            if b < record.parent_id.date_to_cese:
                max_vacation = 30 if record.structure_type_abbr == 'RG' else 15
                record.vacation_days_earrings = record.days_earrings - record.vacation_purchased - record.vacation_compensable
                # Asegurar que no exceda el máximo permitido
                if record.vacation_days_earrings > max_vacation:
                    record.vacation_days_earrings = max_vacation
            else:
                record.vacation_days_earrings = 0

                
    # @api.depends('days_earrings' ,'period_date_from', 'period_date_to', 'parent_id','vacation_purchased')
    # def _compute_vacation_trunced(self):
    #     for record in self:
    #         record.vacation_trunced = 0
    #         first_day = record.employee_id.first_contract_date
    #         evaluate_day = first_day + relativedelta(months=1)
    #         if evaluate_day < record.parent_id.date_to_cese and record.period_date_from <  record.parent_id.date_to_cese <= record.period_date_to :
    #             record.vacation_trunced = record.days_earrings - record.vacation_purchased
    
    @api.depends('days_earrings', 'vacation_purchased', 'structure_type_abbr')
    def _compute_vacation_trunced(self):
        for record in self:
            record.vacation_trunced = 0
            first_day = record.employee_id.first_contract_date
            evaluate_day = first_day + relativedelta(months=1)
            if evaluate_day < record.parent_id.date_to_cese and record.period_date_from < record.parent_id.date_to_cese <= record.period_date_to:
                record.vacation_trunced = record.days_earrings - record.vacation_purchased
                # Ajustar si excede el máximo
                max_vacation = 30 if record.structure_type_abbr == 'RG' else 15
                if record.vacation_trunced > max_vacation:
                    record.vacation_trunced = max_vacation


    @api.depends('employee_id','period_char_date',)
    def _compute_vacation_purchased(self):
        for record in self:
            vacation_purchaseds = self.env["hr.vacation.purchased"].search([
                ("employee_id","=",record.employee_id.id),
                ("selected_period_for_holidays","=",record.period_char_date),
            ])
            record.vacation_purchased = sum([i.number_real_days for i in vacation_purchaseds])

    def _get_number_periods(self, period_date_from, period_date_to):
        str_first_contract_date = period_date_from.strftime("%Y-%m-%d")
        str_date_to_cese = period_date_to.strftime("%Y-%m-%d")
        return self.days360(str_first_contract_date, str_date_to_cese, method=True )/360