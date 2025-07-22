# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError 
import calendar
import pandas as pd
from io import BytesIO
import base64
import logging

_logger = logging.getLogger(__name__)

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

class HrLeaveImport(models.Model):
    _name = "hr.leave.import"
    _description = "Import of Leaves"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    # CONSTANTS
    label = "AUSENCIAS"
    
    # MAIN
    name = fields.Char(string="Nombre", compute='_compute_name')
    state = fields.Selection(SELECTION_STATE, string="Estado", default='draft', tracking=True, copy=False)
    
    current_year = datetime.today().year
    month = fields.Selection(MONTHS_SELECTION, required=True)
    year = fields.Selection([(str(y), str(y)) for y in range(current_year, current_year - 8, -1)], required=True)
    date_from = fields.Date(string="Día Inicio", compute='_compute_date_from', store=True)
    date_to = fields.Date(string="Día Fin", compute='_compute_date_to', store=True)
    period = fields.Char("Periodo")
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company)
    
    attachment_ids = fields.Many2many('ir.attachment', string='Subir archivo', required=True)

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
                # "structure_type_abbr": line.structure_type_abbr,
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
        if not self.attachment_ids:
            raise ValidationError("Debe de subir un archivo, para cargar ausencias.")
        
        data = []
        xlsx = BytesIO(base64.b64decode(self.attachment_ids[0].datas))
        
        df = pd.read_excel(xlsx, dtype={0: str})
                
        for _, row in df.iterrows():
            dni = str(row.iloc[0])

            date_init = datetime.strptime(str(row.iloc[2]), "%Y-%m-%d %H:%M:%S").date()
            date_end = datetime.strptime(str(row.iloc[3]), "%Y-%m-%d %H:%M:%S").date()
            
            if date_init > date_end:
                raise ValidationError(f"La fecha de inicio ({date_init}) no puede ser mayor que la fecha de fin ({date_end}) para el DNI {dni}.")

            if row.iloc[1] == "SI Descanso Vacacional":
                selected_period = str(row.iloc[4])
                if not selected_period:
                    raise ValidationError(f"El periodo no está presente en la cuarta columna para el empleado con DNI: {dni}")
                
            dict_xls = {
                'dni' : dni,
                'subtype': row.iloc[1],
                'date_init': date_init,
                'date_end': date_end,
                'selected_period_for_holidays': selected_period or '',
                    }
            data.append(dict_xls)
               
        return data
        
    ################################ MAIN METHODS #################################
    
    def load_data(self):
        self.ensure_one()
        errores = []
        ausencias_creadas = 0  # Contador para las ausencias exitosamente creadas
        data_xls = self._get_data_from_xlsx()
        HrLeave = self.env['hr.leave']

        # _logger.warning(data_xls)

        for data in data_xls:
            try:
                # Buscar el subtipo de ausencia
                subtype_id = self.env['hr.leave.subtype'].search([
                    ('name', '=', data['subtype']),
                ], limit=1)

                if not subtype_id:
                    errores.append(f'No se encontró el subtipo: {data["subtype"]} para el empleado con DNI: {data["dni"]}')
                    continue

                # Buscar el empleado
                employee_id = self.env['hr.employee'].search([
                    ('identification_id', '=', data["dni"]),
                ], limit=1)

                if not employee_id:
                    errores.append(f'No se encontró el empleado con DNI: {data["dni"]}')
                    continue

                leave_data = {
                    'holiday_status_id': subtype_id.type_id.id,
                    'code': subtype_id.type_id.code,
                    'subtype_id': subtype_id.id,
                    'employee_id': employee_id.id,
                    'date_from': data['date_init'],
                    'request_date_from': data['date_init'],
                    'date_to': data['date_end'],
                    'request_date_to': data['date_end'],
                }

                if data['subtype'] == "SI Descanso Vacacional" and data['selected_period_for_holidays']:
                    leave_data['selected_period_for_holidays'] = data['selected_period_for_holidays']

                # Crear la ausencia
                new_entry = HrLeave.create(leave_data)

                # Confirmar la ausencia antes de aprobarla
                if new_entry.state == 'draft':
                    new_entry.action_confirm()  # Confirmar primero
                if new_entry.state == 'confirm':
                    new_entry.action_approve()  # Luego aprobar

                new_entry._onchange_number_real_days()

                if new_entry and data['subtype'] == "SI Descanso Vacacional":
                    new_entry._onchange_number_real_days()
                    new_entry._onchange_earned_holiday()

                ausencias_creadas += 1  # Incrementar el contador de ausencias creadas

            except Exception as e:
                errores.append(f'Error creando la ausencia para el empleado con DNI {data["dni"]}: {str(e)}')

        # Si hubo errores, lanzarlos
        if errores:
            raise UserError('\n'.join(errores))
        
        # Mostrar mensaje final con la cantidad de ausencias creadas
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Proceso Completado',
                'message': f'Se crearon {ausencias_creadas} ausencias exitosamente.',
            }
        }
