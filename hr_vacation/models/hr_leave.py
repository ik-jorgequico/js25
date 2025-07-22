# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models
from datetime import datetime, timedelta, time
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
#from oa_development.hr_analysis.models.hr_analysis_holidays import HrAnalysisHolidays

class HrLeave(models.BaseModel):
    _inherit = "hr.leave"
    
    # CAMPOS DE AFECTACIONES PARA EL USO DE VACACIONES
    earned_holiday = fields.Float(string="Vacaciones Ganadas",store=True,)
    spent_holiday = fields.Float(string="Vacaciones Gozadas",store=True,)
    balance_holiday = fields.Float(string="Saldo de Vacaciones",store=True,)

    

    current_year = int(datetime.now().date().strftime("%Y"))
    list_anios = [(str(i) + "-" + str(i+1), str(i) + "-" + str(i+1)) for i in range(current_year-10,current_year+2)]
    selected_period_for_holidays = fields.Selection(
        selection=list_anios, 
        store=True,
        string="Periodo Seleccionado para Vacaciones"
    )

    @api.onchange('selected_period_for_holidays', 'employee_id')
    def _onchange_earned_holiday(self):
        if self.selected_period_for_holidays and self.employee_id:
            vac_line = self.env["hr.vacation.line"].search([
                ("employee_id", "=", self.employee_id.id),
                ("period_char_date", "=", self.selected_period_for_holidays)
            ])
            
            vac_purchased = self.env["hr.vacation.purchased"].search([
                ("employee_id", "=", self.employee_id.id),
                ("selected_period_for_holidays", "=", self.selected_period_for_holidays)
            ])

            vac_purchased_sum = sum(i.number_real_days for i in vac_purchased)
            self.balance_holiday = sum(vac_line.mapped('days_earrings')) - vac_purchased_sum
            
            peru_employee_regime = self.employee_id.contract_id.peru_employee_regime
            if peru_employee_regime.abbr != "RG":
                self.balance_holiday = self.balance_holiday / 2


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
    