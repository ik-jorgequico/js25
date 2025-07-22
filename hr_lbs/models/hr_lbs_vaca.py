from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64


class LbsVacation(models.Model):
    _name = 'hr.lbs.vaca'
    _description = 'Vacación Información'

    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado", store=True,)
    date_from = fields.Date(string = "Dia Inicio Evaluado",  store=True,default=fields.Date.today())
    date_to = fields.Date(string = "Dia Final Evaluado", store=True,default=fields.Date.today())
    period_year = fields.Char(string="Periodo Anual", compute="_compute_period_year", )
    name = fields.Char(string="Nombre", compute="_compute_name",)
    type_vacation = fields.Char(string="Tipo de Vacación", store=True)
    employee_id = fields.Many2one("hr.employee", required=True, store=True)
    salary = fields.Float(string="Sueldo Contrato",required=True, default= 0, store=True)
    family_asig = fields.Float(string="Asignación Familiar",required=True, default= 0, store=True)
    average_variables = fields.Float(string="Promedio de Variables", compute='_compute_average_variables', default= 0, store=True)
    base_amount = fields.Float(string="Base Imponible",compute='_compute_base_amount',  default= 0,)
    number_days = fields.Float(string="Numero de Dias",default=30 )
    amount = fields.Float(string="Total", compute="_compute_amount", default=0)
    lbs_vaca_variables = fields.One2many('hr.lbs.vaca.variables', 'lbs_vaca', string="Conceptos para el Promedio de Variables")

    @api.depends('date_from','date_to')
    def _compute_period_year(self):
        for record in self:
            record.period_year = str(record.date_from.year)+ "-" +str(record.date_from.year + 1)
    
    @api.depends('employee_id','period_year','type_vacation')
    def _compute_name(self):
        for record in self:
            record.name = "Vacacion "+record.employee_id.name + " " + record.period_year
 
    @api.depends('lbs_vaca_variables')
    def _compute_average_variables(self):
        for record in self:
            record.average_variables = sum([i.average for i in record.lbs_vaca_variables])
    
    @api.depends('average_variables','salary','family_asig' )
    def _compute_base_amount(self):
        for record in self:
            record.base_amount = record.average_variables + record.salary + record.family_asig 

    @api.depends('number_days','base_amount')
    def _compute_amount(self):
        for record in self:
            record.amount = (record.base_amount*record.number_days)/30

class LbsVacationVariables(models.Model):
    _name = 'hr.lbs.vaca.variables'
    _description = 'Variables en Vacaciones'

    lbs_vaca = fields.Many2one("hr.lbs.vaca", ondelete='cascade', store=True,)
    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")


