from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class Lbs(models.Model):
    _inherit = 'hr.lbs'
    _description = 'LBS'

    @api.model
    def _get_default_report_work_id(self):
        return self.env.ref('hr_lbs.action_report_work_lbs', False)
    
    report_work_id = fields.Many2one('ir.actions.report',
        string="Report Work", domain="[('model','=','hr.lbs.line'),('report_type','=','qweb-pdf')]", default=_get_default_report_work_id)

    def action_dowload_report_lbs_work_pdf(self):
        self.ensure_one()
        return self.env.ref('hr_lbs_reports.action_report_work_lbs').report_action(self)
        # return {
        #     'name': 'LBS WORK',
        #     'type': 'ir.actions.act_url',
        #     'url': '/print/lbs_work?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        # }
        
    @api.model
    def _get_default_report_cts_id(self):
        return self.env.ref('hr_lbs.action_report_cts_lbs', False)
    
    report_cts_id = fields.Many2one('ir.actions.report',
        string="Report CTS", domain="[('model','=','hr.lbs.line'),('report_type','=','qweb-pdf')]", default=_get_default_report_cts_id)

    def action_dowload_report_lbs_cts_pdf(self):
        self.ensure_one()
        return self.env.ref('hr_lbs_reports.action_report_cts_lbs').report_action(self)
        # return {
        #     'name': 'LBS cts',
        #     'type': 'ir.actions.act_url',
        #     'url': '/print/lbs_cts?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        # }

class LbsLine(models.Model):
    _inherit = 'hr.lbs.line'
    _description = 'LBS de Empleado'

    first_contract_date_words = fields.Char(string="Primer dia de ingreso", compute='_first_contract_date', store=True,)

    def action_dowload_report_lbs_work_pdf(self):
        return self.env.ref('hr_lbs_reports.action_report_work_lbs').report_action(self)
        # return {
        #     'name': 'LBS WORK',
        #     'type': 'ir.actions.act_url',
        #     'url': '/print/lbs_work?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        # }
        
    def action_dowload_report_lbs_cts_pdf(self):
        return self.env.ref('hr_lbs_reports.action_report_cts_lbs').report_action(self)
        # return {
        #     'name': 'LBS cts',
        #     'type': 'ir.actions.act_url',
        #     'url': '/print/lbs_cts?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        # }

    def _compute_first_contract_date(self, first_contract_date):
        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        dias = {
            0: "Domingo",
            1: "Lunes",
            2: "Martes",
            3: "Miércoles",
            4: "Jueves",
            5: "Viernes",
            6: "Sábado",
        }

        numero_mes = first_contract_date.month
        # A entero para quitar los ceros a la izquierda en caso de que existan
        numero_dia = int(first_contract_date.strftime("%w"))
        # Leer diccionario
        dia = dias.get(numero_dia)
        mes = meses.get(numero_mes)
        # Formatear
        return "{}, {} de {} del {}".format(dia, first_contract_date.day, mes, first_contract_date.year)
    
    @api.depends('last_contract_date')
    def _first_contract_date(self):
        for element in self:
            element.first_contract_date_words = element._compute_first_contract_date(element.first_contract_date)