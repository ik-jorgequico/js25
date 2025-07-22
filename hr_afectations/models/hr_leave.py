# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta

class HrLeave(models.BaseModel):

    _inherit = "hr.leave"
    subtype_id = fields.Many2one("hr.leave.subtype", string="Tipo de Falta", store=True,  )
    code = fields.Char(string='Código Principal', store=True,)
    number_real_days= fields.Float('Duración Real Dias',  store=True, readonly=False, copy=False, tracking=True, help='Número de días real de ausencia.') 

    import_id = fields.Many2one('hr.leave.import', string="Importación de Ausencias")
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company) 
    ############################################################################################################
    def _first_day_of_month(self,any_day):
        if any_day.day != 1:
            return any_day - timedelta(days=(any_day.day  - 1))
        return any_day
    
    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)

    @api.onchange('date_from', 'date_to', 'subtype_id')
    def _onchange_number_real_days(self):
        if self.date_from and self.date_to and self.subtype_id:
            self.number_real_days = (self.date_to - self.date_from).days + 1

            if self.code and self._first_day_of_month(self.date_from) == self.date_from and self._last_day_of_month(self.date_to) == self.date_to: 
                if self.code not in  ["21", "09"] :
                    self.number_real_days = 30
                if self.code == "23" and self.date_from.strftime("%m") == "02":
                    self.number_real_days = (self.date_to - self.date_from).days + 1

    @api.onchange('subtype_id','employee_id')
    def _onchange_subtype_id(self):
        if self.subtype_id:
            self.holiday_status_id = self.subtype_id.type_id
            self.code = self.subtype_id.type_id.code
    