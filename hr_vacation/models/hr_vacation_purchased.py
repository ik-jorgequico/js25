from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError

# import locale
import base64

class VacationPurchased(models.Model):
    _name = 'hr.vacation.purchased'
    _description = 'Compra de Vacaciones'

    # locale.setlocale(locale.LC_ALL, ("es_ES", "UTF-8"))

    name = fields.Char(string="Nombre", compute='_compute_name',default="", store=True,)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    employee_id = fields.Many2one("hr.employee", string="Empleado", store=True,required=True, )
    date_from = fields.Date(string="Dia de Inicio", store=True,help="Dia de Inicio para tomar en el lote")
    date_to = fields.Date(string = "Dia Fin", store=True,help="Dia Fin para tomar en el lote")
    current_year = int(datetime.now().date().strftime("%Y"))
    list_anios = [(str(i) + "-" + str(i+1), str(i) + "-" + str(i+1)) for i in range(current_year-10,current_year+2)]
    selected_period_for_holidays = fields.Selection(
        selection=list_anios, 
        store=True,
        string="Periodo Seleccionado para Vacaciones",
    )
    number_real_days = fields.Integer(string="Numero de Dias", store=True, required=True,)
    is_calculated = fields.Boolean(string="¿Se le utilizó en calculo vacacional?",store=True, default=False, readonly=True, )
    vacation_calculate_line = fields.Many2one("hr.vacation.calculate.line",store=True,)
    
    @api.constrains('number_real_days', 'employee_id')
    def _check_vacation_limits(self):
        for record in self:
            abbr = record.employee_id.contract_id.peru_employee_regime.abbr
            if abbr == 'RG' and record.number_real_days > 15:
                raise ValidationError("No se puede comprar más de 15 días.")
            elif abbr == 'RP' and record.number_real_days > 7:
                raise ValidationError("No se puede comprar más de 7 días.")
            elif abbr == 'RM' and record.number_real_days >  7:
                raise ValidationError("No se puede comprar más de 7 días.")

    @api.depends('employee_id','selected_period_for_holidays','number_real_days')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.selected_period_for_holidays and record.number_real_days:
                record.name = "{} ({} dia(s) {})".format(record.employee_id.name, record.number_real_days, record.selected_period_for_holidays )
    
    @api.onchange('date_from', 'date_to')
    def _onchange_dates(self):
        if self.date_from and self.date_to:
            delta = self.date_to - self.date_from 
            self.number_real_days = delta.days + 1 if delta.days >= 0 else 0

    def unlink(self):
        if self.is_calculated :
            raise UserError("El registro fue utilizado para el Cálculo Vacacional.")
        return super(VacationPurchased,self).unlink()
    
    def action_open_hr_vacation_acum(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.vacation.acum.line",
            "domain": [['id', '=', self.employee_id.vac_acum_ids.ids[0]]],
            "name": "Registros por Persona",
            'view_type': 'form',
            'view_mode': 'form',
            "res_id":  self.employee_id.vac_acum_ids.ids[0],
            'target':'new',
            'flags': {'action_buttons': True},
        }