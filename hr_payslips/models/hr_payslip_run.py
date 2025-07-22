
from odoo import api, fields, models
from datetime import datetime
import calendar


MONTHS_SELECTION = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]

class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run','mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='_compute_name', tracking=True)
    dt_today = datetime.today()
    month = fields.Selection(MONTHS_SELECTION, required=True, tracking=True)
    year = fields.Selection([(str(y), y) for y in range(dt_today.year, dt_today.year - 8, -1)], required=True, tracking=True)
    rmv = fields.Float('Remuneracion minima vital',compute='_compute_rmv',store=True)

    @api.depends('month','year')
    def _compute_rmv(self):
        for r in self:
            if r.month and r.year:
                date_rmv = self._get_last_day(int(r.year), int(r.month))
                dates = self.env['basic.salary'].search([('date_from','<',date_rmv)])
                rmv = 0
                if dates:
                    dates.sorted(lambda o: o.date_from, reverse=True)
                    rmv = dates.value
                r.rmv = rmv

    @staticmethod
    def _get_last_day(year, month):
        _, ultimo_dia = calendar.monthrange(year, month)
        return datetime(year, month, ultimo_dia)
    
    @api.depends('month', 'year')
    def _compute_name(self):
        for rec in self:
            rec.name = f'{(dict(MONTHS_SELECTION).get(rec.month) or "").upper()} {rec.year or ""}'
            if rec.year and rec.month:
                rec.date_start = datetime(int(rec.year), int(rec.month), 1)
                rec.date_end = self._get_last_day(int(rec.year), int(rec.month))