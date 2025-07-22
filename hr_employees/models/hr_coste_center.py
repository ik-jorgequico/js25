
from odoo import api, fields, models
from datetime import datetime, timedelta, time
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
#from oa_development.hr_analysis.models.hr_analysis_holidays import HrAnalysisHolidays

class HrCosteCenter(models.Model):
    _name = "hr.cod.coste.employees"
    _description = "Coste Centers for Employees"
    _order = 'date_from desc'

    name = fields.Char(compute="_compute_name")
    date_from = fields.Date(string="Fecha Inicio",store=True,)
    date_to = fields.Date(string="Fecha Fin")
    account_analytic_account_id = fields.Many2one('account.analytic.account', string='Centro Costo Contable', store=True,  )
    percent = fields.Float(string="Porcentaje", store=True,)
    employee_id = fields.Many2one("hr.employee", string="Empleado", store=True,)
    is_active = fields.Boolean(string="¿Es un periodo activo?",store=True,help="Se activa o desactiva de acuerdo a su Fecha de Fin" )
    cod_coste_center = fields.Many2one('account.analytic.plan', string='Etiqueta Contable', related='employee_id.cod_coste_center')

    @api.depends("employee_id","account_analytic_account_id")
    def _compute_name(self):
        for record in self:
            record.name =  record.account_analytic_account_id.name +\
                        " " +\
                        record.date_from.strftime("%d-%m-&Y") +\
                        " " +\
                        record.date_to.strftime("%d-%m-&Y")
    
    # @api.depends('date_to')
    @api.onchange('date_to')
    def compute_is_active(self):
        for record in self:
            if not record.date_to:
                record.is_active = True
            else:
                record.is_active = False