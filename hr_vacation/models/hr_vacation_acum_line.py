from odoo import api, fields, models, _
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import ValidationError, UserError
import base64
from datetime import date


class VacAcumLine(models.Model):
    _name = 'hr.vacation.acum.line'
    _description = 'RECORD VACACIONAL POR EMPLEADO'

    name = fields.Char(string="Nombre", related="employee_id.name",
                       compute='_compute_general_info',)
    employee_id = fields.Many2one("hr.employee", string="Empleado")
    job = fields.Char(
        string="Puesto", related="employee_id.job_id.name", store=True,)
    location_id = fields.Many2one(related="employee_id.location_id", store=True,)
    
    department = fields.Char(
        related="employee_id.department_id.name", store=True, string="Area/Departamento")

    job = fields.Char(string="Puesto", store=True,
                      compute='_compute_general_info',)
    first_contract_date = fields.Date(
        string="Fecha Ingreso", store=True, compute='_compute_general_info',)
    last_contract_date = fields.Date(
        string="Fecha de Cese", store=True, compute='_compute_general_info',)

    number_periods = fields.Float(
        string="Cantidad de Periodos", compute='_compute_number_periods', store=True,)
    days_generated = fields.Float(
        string="Dias Generados", compute='_compute_days_generated',  store=True,)
    vacation_enjoyed = fields.Float(
        string="Vac. Gozadas", compute='_compute_vacation_enjoyed', store=True,)
    days_earrings = fields.Float(
        string="Vac. Pendientes", compute='_compute_days_earrings', store=True,)
    vacation_compensable = fields.Float(
        string="Vac. Vencidas", compute='_compute_vacation_compensable', store=True,)
    vacation_trunced = fields.Float(
        string="Vac. Truncas", compute='_compute_vacation_trunced', store=True,)
    vacation_purchased = fields.Float(
        string="Vac. Compradas", compute='_compute_vacation_purchased', store=True,)

    period_year_from = fields.Integer("Año Inicio", store=True,)
    period_year_to = fields.Integer("Año Fin", store=True,)
    period_date_from = fields.Date("Fecha Inicio", store=True,)
    period_date_to = fields.Date("Fecha Fin", store=True,)
    period_char_date = fields.Char(
        string="Periodo", compute='_compute_period_char_date', store=True,)

    parent_id = fields.Many2one(
        "hr.vacation", string="VAC", ondelete='cascade', store=True,)
    child_ids = fields.One2many(
        "hr.vacation.line", "accum_id", string="Vacaciones por Periodos",)
    
    structure_type_abbr = fields.Char(string="Tipo de Régimen",related='employee_id.contract_id.peru_employee_regime.abbr',store=True)

    @api.depends('employee_id')
    def _compute_general_info(self):
        for record in self:
            record.name = "Vac "+record.employee_id.name
            record.job = record.employee_id.job_id.name
            record.first_contract_date = record.employee_id.first_contract_date
            record.last_contract_date = record.employee_id.last_contract_date

    @api.depends('period_year_from', 'period_year_to')
    def _compute_period_char_date(self):
        for record in self:
            record.period_char_date = str(
                record.period_year_from) + "-" + str(record.period_year_to)

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_number_periods(self):
        for record in self:
            if len(record.child_ids) > 1:
                child_ids = record.child_ids
                record.number_periods = sum([i.number_periods for i in child_ids]) - child_ids.sorted(
                    key=lambda x: x.period_date_from, reverse=True)[0].number_periods
            else:
                record.number_periods = 0

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_days_generated(self):
        for record in self:
            if len(record.child_ids) > 1:
                child_ids = record.child_ids
                record.days_generated = sum([i.days_generated for i in child_ids]) - child_ids.sorted(
                    key=lambda x: x.period_date_from, reverse=True)[0].days_generated

            else:
                record.days_generated = 0

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_vacation_enjoyed(self):
        for record in self:
            record.vacation_enjoyed = sum(
                [i.vacation_enjoyed for i in record.child_ids])

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_vacation_compensable(self):
        for record in self:
            record.vacation_compensable = sum(
                [i.vacation_compensable for i in record.child_ids])

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_vacation_trunced(self):
        for record in self:
            record.vacation_trunced = sum(
                [i.vacation_trunced for i in record.child_ids])

    @api.depends('employee_id', 'period_date_from', 'period_date_to')
    def _compute_vacation_purchased(self):
        for record in self:
            record.vacation_purchased = sum(
                [i.vacation_purchased for i in record.child_ids])

    @api.depends('employee_id', 'period_date_from', 'period_date_to', 'vacation_trunced', 'vacation_compensable')
    def _compute_days_earrings(self):
        for record in self:
            record.days_earrings = sum(
                [i.vacation_days_earrings for i in record.child_ids])

    def action_excel_vac_earrings(self):
        pass

    '''
        REPORT DE VACACIONES PENDIENTES
    '''


    def action_pending_by_period(self):
        dataset = []
        for record in self:
            btn = False
            val1 = {
                'cod': record.employee_id.cod_ref or '',
                "type_doc":record.employee_id.l10n_latam_identification_type_id.name or '',
                'doc': record.employee_id.identification_id or '',
                'employee_id': record.employee_id.name,
                'first_contract_date': record.employee_id.first_contract_date.strftime("%d/%m/%Y"),
                'job': record.employee_id.job_id.name or '',
                'center_coste': record.employee_id.cod_coste_center.name or '',
                'area': record.employee_id.department_id.name or '',
                'localidad':  record.employee_id.location_id.name or '',
                'total_days_pending': record.vacation_compensable + record.days_earrings,

            }
            val2 = {}
            for child_id in record.child_ids:
                if child_id.vacation_compensable > 0 :
                    val2["_Period_"+child_id.period_char_date]= child_id.vacation_compensable
                    btn = True
                if child_id.vacation_days_earrings > 0 :
                    val2["_Period_"+child_id.period_char_date]= child_id.vacation_days_earrings
                    btn = True

            if btn:
                val = {**val1,**val2}
                dataset.append(val.copy())
            
        data = {
            'dataset': dataset,
            'form_data': self.read()[0],
            'information': {
                "company":self.env.company.name,
                "date":self.parent_id.date_to_cese.strftime("%d/%m/%Y")
            }
        }
        return self.env.ref('hr_vacation.detail_pending_by_period').report_action(self, data=data)

    '''
        REPORTE DE VACACIONES GOZADAS
    '''

    def action_excel_vac_enjoyed(self):
        dataset = []
        for record in self:
            val = {
                'cod': record.employee_id.cod_ref or '',
                "type_doc":record.employee_id.l10n_latam_identification_type_id.name or '',
                'doc': record.employee_id.identification_id or '',
                'employee_id': record.employee_id.name,
                'first_contract_date': record.employee_id.first_contract_date.strftime("%d/%m/%Y"),
                'job': record.employee_id.job_id.name or '',
                'center_coste': record.employee_id.cod_coste_center.name or '',
                'area': record.employee_id.department_id.name or '',
                'localidad':  record.employee_id.location_id.name or '',
                "period_char_date": '',
                "days_generated": '',
                "date_from": '',
                "date_to": '',
                "number_real_days": 0,
                "vacation_purchased": 0,
                "vacation_days_earrings": 0,
                "vacation_compensable": 0,
                "vacation_trunced": 0,

            }

            for i, child_id in enumerate(record.child_ids):
                val.update({
                    "period_char_date": child_id.period_char_date,
                })

                if child_id.subline_ids:
                    for j, subline_id in enumerate(child_id.subline_ids):
                        val.update(
                                {
                                    "vacation_purchased": 0,
                                    "vacation_compensable": 0,
                                    "days_generated": 0,
                                    "vacation_trunced": 0,
                                    "vacation_days_earrings": 0,
                                })
                        if (child_id.vacation_compensable > 0  or  child_id.days_generated > 0 or  child_id.vacation_days_earrings > 0) and j + 1 == len(child_id.subline_ids):
                            val.update(
                                {
                                    "vacation_compensable": child_id.vacation_compensable,
                                    "days_generated": child_id.days_generated,
                                    "vacation_days_earrings": child_id.vacation_days_earrings,
                                })
                        if (child_id.vacation_purchased > 0  ) and j == 0:
                            val.update(
                                {
                                    "vacation_purchased": child_id.vacation_purchased,
                                })

                        if j + 1 == len(child_id.subline_ids) and i + 1 == len(record.child_ids):
                            val.update(
                                {
                                    "vacation_trunced": child_id.vacation_trunced,
                                })

                        val.update({
                            "date_from": subline_id.date_from.strftime("%d/%m/%Y"),
                            "date_to": subline_id.date_to.strftime("%d/%m/%Y"),
                            "number_real_days": subline_id.number_real_days,
                        })
                        dataset.append(val.copy())
                else:
                    val.update({
                        "days_generated": child_id.days_generated,
                        "vacation_purchased": child_id.vacation_purchased,
                        "vacation_days_earrings": child_id.vacation_days_earrings,
                        "vacation_compensable": child_id.vacation_compensable,
                        "date_from": '',
                        "date_to":'',
                        "number_real_days": 0
                    })
                    if i + 1 == len(record.child_ids):
                        val.update(
                            {
                                "vacation_trunced": child_id.vacation_trunced,
                            })
                    dataset.append(val.copy())

        data = {
            'dataset': dataset,
            'form_data': self.read()[0],
            'information': {
                "company":self.env.company.name,
                "date":self.parent_id.date_to_cese.strftime("%d/%m/%Y")
            }
        }
        return self.env.ref('hr_vacation.detail_record_vacational').report_action(self, data=data)
