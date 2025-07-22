from odoo import api, fields, models, _
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import base64


class LbsCts(models.Model):
    _name = 'hr.lbs.cts'
    _description = 'CTS Información'

    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado")
    date_from = fields.Date(string="Dia Inicio Evaluado",required=True, store=True,)
    date_to = fields.Date(string="Dia Final Evaluado",required=True, store=True,)
    period_month = fields.Char(string="Periodo Nombre", compute="_compute_period_month")
    name = fields.Char(string="Nombre")
    employee_id = fields.Many2one("hr.employee")
    salary = fields.Float(string="Sueldo Contrato", default=0)
    family_asig = fields.Float(string="Asignación Familiar", default=0)
    gratification = fields.Float(string="1/6 Graficación", default=0)
    average_variables = fields.Float(string="Promedio de Variables", compute='_compute_average_variables', default=0)
    base_amount = fields.Float(string="Base Imponible", compute='_compute_base_amount',)
    number_days = fields.Integer(string="Dias Laborados", compute="_compute_number_days")
    amount = fields.Float(string="Total", compute="_compute_amount")
    lbs_cts_variables = fields.One2many('hr.lbs.cts.variables', "lbs_cts_line", string="Conceptos para el Promedio de Variables")

    def _last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def _first_day_of_month(self, any_day):
        return any_day - timedelta(days=(any_day.day - 1))

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_number_days(self):
        for record in self:
            if self._last_day_of_month(record.date_to) == record.date_to:
                working_days = 30 - record.date_from.day + 1
                if working_days < 0:
                    working_days = 1
            else :
                working_days = (record.date_to - record.date_from).days + 1

            leave = self.env["hr.leave"].search([("employee_id","=",record.employee_id.id),
                                                 ("date_from", ">=", record.date_from),
                                                ("date_to", "<=", record.date_to),
                                                ("state", "=", "validate"),
                                                ("subtype_id.type_id.have_cts", "=", False),])
            leave_days = sum([i.number_real_days for i in leave])
            record.number_days = working_days - leave_days

    @api.depends('date_from', 'date_to')
    def _compute_period_month(self):
        for record in self:
            record.period_month = record.date_from.strftime("%b %Y")

    @api.depends('lbs_cts_variables')
    def _compute_average_variables(self):
        for record in self:
            record.average_variables = sum(
                [i.average for i in record.lbs_cts_variables])

    @api.depends('average_variables', 'salary', 'family_asig', 'gratification')
    def _compute_base_amount(self):
        for record in self:
            record.base_amount = record.average_variables + \
                record.salary + record.family_asig + record.gratification

    @api.depends('base_amount', 'number_days')
    def _compute_amount(self):
        for record in self:
            regimes = record.employee_id.contract_id.peru_employee_regime
            if len(regimes) > 1:
                raise UserError(_("Se encontraron múltiples regímenes para el empleado %s. Por favor, revise los datos." % record.employee_id.name))
            elif regimes.abbr == "RG":
                record.amount = record.number_days * record.base_amount / 360
            elif regimes.abbr == "RP":
                record.amount = (record.number_days * record.base_amount / 360) / 2
            elif regimes.abbr == "RM":
                record.amount = 0
            else:
                record.amount = 0

class LbsCtsVariables(models.Model):
    _name = 'hr.lbs.cts.variables'
    _description = 'Variables en CTS'

    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")

    lbs_cts_line = fields.Many2one(
        "hr.lbs.cts", ondelete='cascade', store=True,)
