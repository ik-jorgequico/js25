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

class HrHolidaysPeru(models.Model):
    _name = 'hr.holidays.peru'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Días feriados'
    
    # CONSTANTS
    label = "DÍAS FERIADOS"
    
    # MAIN
    name = fields.Char("Nombre", compute='_compute_name')
    state = fields.Selection(SELECTION_STATE, "Estado", default='draft', tracking=True, copy=False)
    
    current_year = datetime.today().year
    month = fields.Selection(MONTHS_SELECTION, required=True)
    year = fields.Selection([(str(y), str(y)) for y in range(current_year, current_year - 8, -1)], required=True)
    date_from = fields.Date("Día Inicio", compute='_compute_date_from', store=True)
    date_to = fields.Date("Día Fin", compute='_compute_date_to', store=True)
    period = fields.Char("Periodo", tracking=True)
    
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    
    attachment_ids = fields.Many2many('ir.attachment', string='Subir archivo', tracking=True)
    
    xlsx_filename = fields.Char()
    xlsx = fields.Binary('Reporte Excel', tracking=True)
    
    # RELATIONS
    child_ids = fields.One2many("hr.holidays.peru.line", "parent_id", "Bonificaciones Gratificación", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]}, tracking=True)
    
    ############################### STATIC METHODS ###############################

    @staticmethod
    def _first_day(any_date: datetime):
        return any_date.replace(day=1)
    
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
    
    ############################### PRIVATE METHODS #############################
    
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
                # "structure_type_abbr": line.structure_type_abbr,
                "amount": line.amount,
            })
        return lines
    
    def _update_input_type(self, payslip, input_type, amount):
        input_line = payslip.input_line_ids.filtered(lambda x: x.input_type_id.id == input_type)
        if input_line:
            input_line.amount = amount
        else:
            payslip.input_line_ids = [(0, 0, {
                'input_type_id': input_type,
                'amount': amount,
            })]
    
    def _fill_child_ids(self, payslips):
        def _filter_employees(employee_id):
            return (
                employee_id.first_contract_date <= self._first_day(self.date_to)
                and
                not employee_id.last_contract_date
                # and
                # employee_id.contract_id.peru_employee_regime.abbr == "RG"
            )
            
        # Busca sólo los empleados que están en payslips
        employee_ids = payslips.mapped("employee_id").filtered(_filter_employees)
        xlsx = BytesIO(base64.b64decode(self.attachment_ids[0].datas))
        df = pd.read_excel(xlsx, dtype={0: str}) # La columna de DNI será de tipo Texto
        df = df.fillna('')
        for _, row in df.iterrows():
            dni = str(row.iloc[0])
            qty_days = row.iloc[1]
            obs = row.iloc[2]
            
            employee_id = employee_ids.filtered(lambda x: x.identification_id == dni)
            line_id = self.child_ids.filtered(lambda x: x.employee_id.id == employee_id.id)
            
            if line_id:
                line_id.qty_days = qty_days
                line_id.obs = obs
            else:
                self.child_ids.create({
                "parent_id": self.id,
                "employee_id": employee_id.id,
                "qty_days": qty_days,
                "obs": obs,
            })
    
    def _import_to_payslip(self, payslips):
        hrPayslipInputType = self.env['hr.payslip.input.type']
        for line_id in self.child_ids:
            payslip = payslips.filtered(lambda x: x.employee_id.id == line_id.employee_id.id)
            
            input_holidays = hrPayslipInputType.search([('code', '=', 'I_HOLIDAYS')], limit=1).id
            self._update_input_type(payslip, input_holidays, line_id.amount)
            
            payslip.compute_sheet()
    
    ################################ MAIN METHODS #################################
    
    def compute_sheet(self):
        self.ensure_one()
        
        payslips = self.env.get('hr.payslip').search([
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('company_id.id', '=', self.company_id.id),
        ])
        
        if not payslips:
            raise ValidationError('No hay payslips para calcular.')
        
        self._fill_child_ids(payslips)
        
        self._import_to_payslip(payslips)
        
        self.state = 'calculated'
        
        return self.env.cr.commit()
    
    def action_generate_xlsx(self):
        if not self.any_child:
            raise ValidationError("No hay ningún registro para generar este reporte.")
            
        report_xlsx = ReportXlsx(self)
        self.write({
            'xlsx_filename': f"{self.name}.xlsx",
            'xlsx': report_xlsx.get_xlsx(self._get_data_lines()),
        })


class HrHolidaysPeruLine(models.Model):
    _name = 'hr.holidays.peru.line'
    _description = 'Holidays Peru Line'
    
    parent_id = fields.Many2one("hr.holidays.peru", ondelete='cascade')
    state = fields.Selection(SELECTION_STATE, string="State", default='draft')
    
    employee_id = fields.Many2one("hr.employee", string="Empleado", store=True)
    num_doc = fields.Char(string="Num. Doc.", related="employee_id.identification_id", store=True)
    qty_days = fields.Float("Cant. días")
    amount = fields.Float("Monto total", compute='_compute_amount')
    obs = fields.Char("Observaciones", store=True)
    
    # structure_type_abbr = fields.Char(string="Tipo de Regimen", related='employee_id.contract_id.peru_employee_regime.abbr', store=True)

    ################################### COMPUTES #################################
    
    @api.depends('qty_days')
    def _compute_amount(self):
        for rec in self:
            rec.amount = ( rec.employee_id.salary_amount / 30 ) * rec.qty_days