# coding: utf-8
# import itertools
# from collections import defaultdict
# from datetime import datetime, date, time
# import pytz

# from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
# from odoo.addons.resource.models.utils import string_to_datetime, Intervals
# from odoo.osv import expression
# from odoo.tools import ormcache
# from odoo.exceptions import UserError

# from odoo.addons.hr_work_entry_contract.models.hr_work_intervals import WorkIntervals

class HrContract(models.Model):
    _inherit = 'hr.contract'

    reason_low_id = fields.Many2one('hr.departure.reason',string='Motivo de baja', store=True)
    last_contract_date = fields.Date(string="Fecha de Cese",store=True,)
    
    move_sa = fields.Float(string="Movilidad Supeditada Asistencia", store=True )

    # work_entry_source = fields.Selection(compute='_compute_work_entry_source')

    # @api.depends('name','peru_employee_regime','structure_type_id','resource_calendar_id')
    # def _compute_work_entry_source(self):
    #     for r in self:
    #         if r.name != False and r.peru_employee_regime != False and r.structure_type_id != False and r.resource_calendar_id != False:
    #             r.work_entry_source = 'attendance'

    @api.onchange('peru_employee_regime')
    def _onchange_peru_employee_regime(self):
        if self.peru_employee_regime:
            self.work_entry_source = 'attendance'

    @api.onchange('reason_low_id')
    def _onchange_reason_low_id(self):
        if self.reason_low_id:
            self.last_contract_date = fields.Date.context_today(self)
        else:
            self.last_contract_date = False
        self._update_state()

    @api.onchange('last_contract_date')
    def _onchange_last_contract_date(self):
        if self.last_contract_date:
            self.employee_id.last_contract_date = self.last_contract_date
        else:
            self.employee_id.last_contract_date = None
        self._update_state()

    def _update_state(self):
        today = fields.Date.context_today(self)
        if (self.reason_low_id and self.last_contract_date and self.last_contract_date < today):
            self.state = 'close'
        elif self.state == 'close' and (not self.reason_low_id or not self.last_contract_date):
            self.state = 'open'

class LowReason(models.Model):
    _inherit = 'hr.departure.reason'

    code = fields.Char(string='Código')