from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64


class LbsGrati(models.Model):
    _name = 'hr.lbs.grati'
    _description = 'Gratificación Información'

    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado")
    date_from = fields.Date(string = "Dia Inicio Evaluado",required=True, store=True,)
    date_to = fields.Date(string = "Dia Final Evaluado",required=True, store=True,)
    period = fields.Char(string="Periodo",)
    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one("hr.employee", store=True,)
    salary = fields.Float(string="Sueldo Contrato", default= 0, store=True,)
    family_asig = fields.Float(string="Asignación Familiar", default= 0, store=True,)
    average_variables = fields.Float(string="Promedio de Variables", compute='_compute_average_variables', default= 0, store=True,)
    base_amount = fields.Float(string="Base Imponible",compute='_compute_base_amount', store=True,)
    number_days = fields.Integer(string="Dias", compute="_compute_number_days", store=True,)
    amount = fields.Float(string="Total", compute="_compute_amount", store=True,)
    lbs_grati_variables = fields.One2many('hr.lbs.grati.variables',"lbs_grati_line",string="Conceptos para el Promedio de Variables")


    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)
    
    def _first_day_of_month(self,any_day):
        return any_day - timedelta(days=(any_day.day  - 1))

    @api.depends('employee_id','date_from','date_to')
    def _compute_number_days(self):
        for record in self:
            if record.date_from and record.date_to and record.employee_id:
                number_days = 0
                leave_days = 0
                initial = record.date_from
                if record.date_from.day != 1:
                    initial = self._last_day_of_month(initial) + relativedelta(days=1)

                final = record.date_to
                if self._last_day_of_month(record.date_to) != record.date_to:
                    final = self._first_day_of_month(final) - relativedelta(days=1)

                if initial < final:
                    number_days = (final.month - initial.month + 1 )*30 

                    afectation_days =  self.env["hr.leave"].search([("employee_id","=",record.employee_id.id),
                                                        ("date_from",">=",initial),
                                                        ("date_to","<=",final),
                                                        ("state","=","validate"),
                                                        ("subtype_id.type_id.have_gratification","=",False)])
                                                        
                    leave_days = sum([i.number_real_days for i in afectation_days])

                record.number_days = number_days - leave_days

    @api.depends('lbs_grati_variables')
    def _compute_average_variables(self):
        for record in self:
            record.average_variables = sum([i.average for i in record.lbs_grati_variables])
    
    @api.depends('average_variables','salary','family_asig')
    def _compute_base_amount(self):
        for record in self:
            record.base_amount = record.average_variables + record.salary + record.family_asig  

    @api.depends('base_amount','number_days')
    def _compute_amount(self):
        for record in self:
            if record.employee_id.contract_id.peru_employee_regime.abbr == "RG":
                record.amount = record.number_days*record.base_amount/180
            elif record.employee_id.contract_id.peru_employee_regime.abbr == "RP":
                record.amount = record.number_days*record.base_amount/360


class LbsGratiVariables(models.Model):
    _name = 'hr.lbs.grati.variables'
    _description = 'Variables en grati'

    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")
    lbs_grati_line = fields.Many2one("hr.lbs.grati", ondelete='cascade', store=True,)
