from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import logging

_logger = logging.getLogger(__name__)


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

STATES_SELECTION = [
    ('draft', 'Borrador'),
    ('verify', 'Enviado'),
    ('approve', 'Aprobado'),
    ('refuse', 'Rechazado'),
    ('cancel', 'Cancelado'),
]

class Lbs(models.Model):
    _name = 'hr.lbs'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'LBS'

    current_year = datetime.today().year
    
    name = fields.Char(string="Nombre", default="", store=True,tracking=True)
    
    month = fields.Selection(MONTHS_SELECTION, required=True,tracking=True)
    year = fields.Selection([(str(y), y) for y in range(current_year, current_year - 8, -1)], required=True,tracking=True)

    date_from = fields.Date(string="Dia Inicio", compute='_compute_date_from', store=True,tracking=True)
    date_to = fields.Date(string="Dia Fin", compute='_compute_date_to', store=True,tracking=True)
    
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True,tracking=True)
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel',tracking=True)
    child_ids = fields.One2many('hr.lbs.line', 'parent_id', string="LBS Empleado", store=True,tracking=True)
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')
    payslip_id = fields.Many2one("hr.payslip", string="Lote", store=True)

    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model', '=', 'hr.lbs.line'), ('report_type', '=', 'qweb-pdf')]", default=lambda self: self.env.ref('hr_lbs.action_report_lbs', False))
    
    @staticmethod
    def _last_day(any_date=None, year=None, month=None):
        last_day = calendar.monthrange(int(year or any_date.year), int(month or any_date.month))[1]
        return any_date.replace(day=last_day) if any_date else date(int(year), int(month), last_day)
    
    @api.depends('month', 'year')
    def _compute_date_from(self):
        for rec in self:
            if rec.month and rec.year:
                rec.date_from = date(int(rec.year), int(rec.month), 1)
    
    @api.depends('month', 'year')
    def _compute_date_to(self):
        for rec in self:
            if rec.month and rec.year:
                rec.date_to = self._last_day(year=rec.year, month=rec.month)
    
    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for rec in self:
            rec.child_ids_count = len(rec.child_ids)
            
    def action_dowload_report_lbs_pdf(self):
        self.ensure_one()
        return {
            'name': 'LBS',
            'type': 'ir.actions.act_url',
            'url': '/print/lbs?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        }

    def action_open_hr_lbs(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.lbs.line",
            "views": [[False, 'tree'], [False, 'form']],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Ver Liquidaciones",
        }
    
    @api.onchange('company_id', 'date_from', 'date_to')
    def _onchange_name(self):
        if self.company_id and self.date_from and self.date_to:
            self.name = f'LBS {dict(MONTHS_SELECTION).get(self.month).upper()} {self.year} - {self.company_id.name} '

    def _compute_time_service(self, first_contract_date, last_contract_date) -> bool:
        diff = relativedelta(last_contract_date,first_contract_date)
        days = diff.days + 1
        months = diff.months or 0
        days = days or 0
        
        if self._last_day(last_contract_date) == last_contract_date and first_contract_date.day == 1:
            days = 0
            months += 1

        return months > 0
    
    def compute_sheet(self):
        self.ensure_one()
        
        hr_payslip_run = self.env['hr.payslip.run'].search([
            ('date_start','>=',self.date_from),
            ('date_end','<=',self.date_to),
        ])
        
        if not hr_payslip_run:
            return UserError("No se encuentra Lote respectivo en el rango de fechas")
        
        if len(hr_payslip_run) >= 2:
            return UserError("Se encuentra más de un lote en el rango de fechas")
        
        not_draft_employe_ids = self.child_ids.filtered(lambda x:x.state != 'draft').mapped("employee_id")
        self.child_ids.filtered(lambda x:x.state == 'draft').unlink()
        slip_ids = hr_payslip_run.slip_ids
        
        slip_ids = slip_ids.filtered(lambda x:x.employee_id.last_contract_date != False  )
        slip_ids = slip_ids.filtered(lambda x: self.date_from <= x.employee_id.last_contract_date <= self.date_to and x.employee_id not in not_draft_employe_ids)

        if slip_ids:
            #employees = [pay.employee_id.name for pay in slip_ids]
            #_logger.warning("----employees---%s"%employees)
            val_list = [{
                "employee_id": pay.employee_id.id,
                "payslip_id": pay.id,
                "parent_id": self.id
            } for pay in slip_ids]

            self.env["hr.lbs.line"].create(val_list)            
            self.env.cr.commit()

    def unlink(self):
        self.child_ids.unlink()
        return super(Lbs, self).unlink()

    def draft(self):
        self.child_ids.draft() 
