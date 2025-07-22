# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import ValidationError 
import calendar
import pandas as pd
from .report_xlsx import ReportXlsx
from io import BytesIO
import base64


SELECTION_STATE = [
    ('draft', 'Borrador'),
    ('calculated', 'Calculado'),
]

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

class HorasExtras(models.Model):
    _name = 'hr.he'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Horas Extras'
    
    # CONSTANTS
    label = "HORAS EXTRA"
    
    # MAIN
    name = fields.Char(string="Nombre",compute='_compute_name')
    state = fields.Selection(SELECTION_STATE, string="Estado", default='draft', tracking=True, copy=False)
    
    current_year = datetime.today().year
    month = fields.Selection(MONTHS_SELECTION,tracking=True, required=True)
    year = fields.Selection([(str(y), str(y)) for y in range(current_year, current_year - 8, -1)],tracking=True, required=True)
    date_from = fields.Date(string="Día Inicio", compute='_compute_date_from',tracking=True, store=True)
    date_to = fields.Date(string="Día Fin", compute='_compute_date_to',tracking=True, store=True)
    period = fields.Char("Periodo")
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    attachment_ids = fields.Many2many('ir.attachment', string='Subir archivo',tracking=True, required=True)
    
    xlsx_filename = fields.Char()
    xlsx = fields.Binary('Reporte Excel',tracking=True)
    
    any_child = fields.Boolean(compute='_compute_any_child', tracking=True,store=True)
    
    # RELATIONS
    child_ids = fields.One2many("hr.he.line", "parent_id", string="Bonificaciones Gratificación", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    observation_ids = fields.One2many('hr.he.obs', "parent_id", string="Observaciones",tracking=True, store=True)
    
    ############################### STATIC METHODS ###############################

    @staticmethod
    def _first_day(any_date: datetime): return any_date.replace(day=1)
    
    @staticmethod
    def _last_day(any_date=None, year=None, month=None):
        last_day = calendar.monthrange(int(year or any_date.year), int(month or any_date.month))[1]
        if any_date:
            return any_date.replace(day=last_day)
        return date(int(year), int(month), last_day)
    
    ################################# CONSTRAINS ################################
    
    @api.constrains('attachment_ids')
    def _check_single_attachment(self):
        for rec in self:
            if len(rec.attachment_ids) > 1:
                raise ValidationError('Solo se permite subir un archivo.')
            
            for attachment in rec.attachment_ids:
                if not any(attachment.name.endswith(ext) for ext in ['.xls', '.xlsx']):
                    raise ValidationError('Solo está permitida la carga de archivos Excel (.xls, .xlsx).')
    
    ################################### FILTERS #################################
    
    def _filter_employees(self, employee):
        return (
            employee.first_contract_date <= self._first_day(self.date_to)
            and
            not employee.last_contract_date
            # and
            # employee.contract_id.peru_employee_regime.abbr == "RG"
        )
    
    ################################### COMPUTES #################################
    
    @api.depends('year', 'month')
    def _compute_name(self):
        for rec in self:
            name = ""
            if rec.year and rec.month:
                rec.period = f"{dict(MONTHS_SELECTION).get(rec.month).upper()} {rec.year}"
                name = f"{self.label} - {rec.period}"
            rec.name = name
    
    @api.depends('year', 'month')
    def _compute_date_from(self):
        for rec in self.filtered(lambda x: x.year and x.month):
            rec.date_from = date(int(rec.year), int(rec.month), 1)
    
    @api.depends('year', 'month')
    def _compute_date_to(self):
        for rec in self.filtered(lambda x: x.year and x.month):
            rec.date_to = self._last_day(year=rec.year, month=rec.month)
    
    @api.depends('child_ids')
    def _compute_any_child(self):
        for rec in self:
            rec.any_child = len(rec.child_ids) > 0
    
    ############################### PRIVATE METHODS #############################
    
    def _update_input_type(self, payslip, input_type, amount):
        input_line = payslip.input_line_ids.filtered(lambda x: x.input_type_id.id == input_type)
        if input_line:
            input_line.amount = amount
        else:
            payslip.input_line_ids = [(0, 0, {
                'input_type_id': input_type,
                'amount': amount,
            })]
    
    def _get_data_lines(self):
        lines = []
        for line in self.child_ids:
            employee_id = line.employee_id
            lines.append({
                "id": line.id,
                "code": employee_id.cod_ref,
                "type_doc": employee_id.l10n_latam_identification_type_id.name,
                "num_doc": employee_id.identification_id,
                "first_last_name": employee_id.first_last_name,
                "second_last_name": employee_id.second_last_name,
                "first_name": employee_id.first_name,
                "second_name": employee_id.second_name,
                "structure_type_abbr": line.structure_type_abbr,
                "salary": line.salary,
                "family_asig": line.family_asig,
                "h_25": line.hours_25,
                "h_35": line.hours_35,
                "amount_25": line.amount_25,
                "amount_35": line.amount_35,
                "total_amount": line.total_amount,
            })
        return lines
    
    def _get_data_from_xlsx(self):
        data = {}
        xlsx = BytesIO(base64.b64decode(self.attachment_ids[0].datas))
        df = pd.read_excel(xlsx, dtype={0: str}) # La columna de DNI será de tipo Texto
        for _, row in df.iterrows():
            data.update({
                str(row.iloc[0]): {
                    'h_25': float(row.iloc[1]),
                    'h_35': float(row.iloc[2]),
                },
            })
        return data
    
    def _add_obs(self, dni, hours, obs):
        obs_id = self.observation_ids.filtered(lambda x: x.identification_id == dni)
        if obs_id:
            obs_id.obs += f"; {obs}"
        else:
            self.observation_ids = [(0, 0, {
                "parent_id": self.id,
                "identification_id": dni,
                "hours_25": hours.get('h_25'),
                "hours_35": hours.get('h_35'),
                "obs": obs,
            })]
    
    def _fill_child_ids(self, payslips):
        vals = []
        data = self._get_data_from_xlsx()
        employee_ids = payslips.mapped("employee_id").filtered(self._filter_employees)
        
        for dni, hours in data.items():
            employee = employee_ids.filtered(lambda x: x.identification_id == dni)
            h_25 = hours.get('h_25')
            h_35 = hours.get('h_35')
            
            if not employee:
                self._add_obs(dni, hours, "El empleado no existe en Payslips")
            
            if h_25 > 2:
                self._add_obs(dni, hours, "Horas 25% no debe exceder las 2 horas")
            
            vals.append({
                "parent_id": self.id,
                "employee_id": employee.id,
                "hours_25": h_25,
                "hours_35": h_35,
            })
            
        if not any(self.observation_ids):
            self.child_ids.create(vals)
            self._import_to_payslip(payslips)
            self.state = 'calculated'
            
    def _import_to_payslip(self, payslips):
        employee_ids = self.child_ids.mapped('employee_id')
        hrPayslipInputType = self.env['hr.payslip.input.type']
        
        for employee_id in employee_ids:
            payslip = payslips.filtered(lambda x: x.employee_id.id == employee_id.id)
            
            input_type_25 = hrPayslipInputType.search([('code', '=', 'I_HE_25')], limit=1).id
            amount_25 = self.child_ids.filtered(lambda x: x.employee_id == employee_id).amount_25
            self._update_input_type(payslip, input_type_25, amount_25)
            
            input_type_35 = hrPayslipInputType.search([('code', '=', 'I_HE_35')], limit=1).id
            amount_35 = self.child_ids.filtered(lambda x: x.employee_id == employee_id).amount_35
            self._update_input_type(payslip, input_type_35, amount_35)
            
            payslip.compute_sheet()
    
    ################################ MAIN METHODS #################################
    
    def compute_sheet(self):
        self.ensure_one()
        self.observation_ids = [(5, 0, 0)]
        self.child_ids = [(5, 0, 0)]
        
        payslips = self.env.get('hr.payslip').search([
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('company_id.id', '=', self.company_id.id),
        ])
        
        if not payslips:
            raise ValidationError('No hay payslips para calcular.')
        
        self._fill_child_ids(payslips)
        
        return self.env.cr.commit()
    
    def action_generate_xlsx(self):
        if not self.any_child:
            raise ValidationError("No hay ningún registro para generar este reporte.")
            
        report_xlsx = ReportXlsx(self)
        self.write({
            'xlsx_filename': f"{self.name}.xlsx",
            'xlsx': report_xlsx.get_xlsx(self._get_data_lines()),
        })


class HorasExtrasLine(models.Model):
    _name = 'hr.he.line'
    _description = 'Extras Hours Line'
    
    parent_id = fields.Many2one("hr.he", ondelete='cascade')
    state = fields.Selection(SELECTION_STATE, string="State", default='draft')
    
    employee_id = fields.Many2one("hr.employee", string="Empleado", store=True)
    contract_id = fields.Many2one("hr.contract", string="Contrato", related="employee_id.contract_id")
    
    identification_id = fields.Char(string="Num. Doc.", related="employee_id.identification_id", store=True)
    structure_type_abbr = fields.Char(string="Tipo de Regimen", related='employee_id.contract_id.peru_employee_regime.abbr', store=True)
    salary = fields.Float(string="Sueldo C.", compute='_compute_salary')
    family_asig = fields.Float(string="A. F.", compute='_compute_family_asig', store=True)
    hours_25 = fields.Float('Horas 25%', default=0, store=True)
    hours_35 = fields.Float('Horas 35%', default=0, store=True)
    amount_25 = fields.Float('Monto 25%', compute='_compute_amount_25', default=0, store=True)
    amount_35 = fields.Float('Monto 35%', compute='_compute_amount_35', default=0, store=True)
    total_amount = fields.Float(string="Total", compute='_compute_total_amount', default=0, store=True)

    ################################### COMPUTES #################################
    
    @api.depends('contract_id')
    def _compute_salary(self):
        for rec in self:
            rec.salary = rec.contract_id.wage or 0
    
    @api.depends('parent_id')    
    def _compute_family_asig(self):
        for rec in self:
            basic_salary_obj = self.env.get('basic.salary').search([
                ('date_from', '<=', rec.parent_id.date_to),
                ('date_to', '>=', rec.parent_id.date_to),
            ], limit=1)
            rec.family_asig = basic_salary_obj.value * 0.10 if basic_salary_obj else 0

    @api.depends('hours_25')
    def _compute_amount_25(self):
        for rec in self:
            min_cost = (rec.salary + rec.family_asig) / (30 * 8 * 60)
            rec.amount_25 = (rec.hours_25 * 60) * min_cost * 1.25
            
    @api.depends('hours_35')
    def _compute_amount_35(self):
        for rec in self:
            min_cost = (rec.salary + rec.family_asig) / (30 * 8 * 60)
            rec.amount_35 = (rec.hours_35 * 60) * min_cost * 1.35
            
    @api.depends('amount_25', 'amount_35')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.amount_25 + rec.amount_35


class HorasExtrasObs(models.Model):
    _name = 'hr.he.obs'
    _description = 'Observaciones de horas extra'

    parent_id = fields.Many2one('hr.he', ondelete='cascade')
    identification_id = fields.Char(string="Num. Doc.", store=True)
    hours_25 = fields.Float('Horas 25%', default=0, store=True)
    hours_35 = fields.Float('Horas 35%', default=0, store=True)

    obs = fields.Char("Observaciones", store=True)
