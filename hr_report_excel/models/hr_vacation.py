from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date
import pytz


class HrEmployee(models.BaseModel):
    _inherit = 'hr.vacation'
    _description = 'Provision vacaciones'

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)


    def compute_to_provision(self,date_to_cese):
        self.ensure_one() # pasar solo un registro

        self.child_ids.subline_ids.unlink() # elimina los datos que estan likeados de sub hijos
        self.child_ids.unlink() # elimina los datos linkeado de los padres 
        self.child_acum_ids.unlink()

        val_list = [] 

        employees = self.env["hr.employee"].search([
            ("first_contract_date","<=",date_to_cese),
        ])
        
        for employee in employees:
            list_periods = self._generate_periods(employee,date_to_cese)
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
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(employee, period_date_from, period_date_to)],
                }

                val_list.append(val)

        self.env["hr.vacation.line"].create(val_list)            
        self.env.cr.commit()

        self._update_vacation_compensable()
        self._create_child_acum_ids()