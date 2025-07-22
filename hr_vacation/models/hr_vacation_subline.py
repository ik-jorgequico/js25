from odoo import fields, models, _


class VacSubLine(models.Model):
    _name = 'hr.vacation.subline'
    _description = 'VACACIONES GOZADAS'

    date_from = fields.Date( string="Fecha Inicio", related = "leave_id.request_date_from", store=True,)
    date_to = fields.Date(string="Fecha Fin", related = "leave_id.request_date_to", store=True,)
    leave_id = fields.Many2one("hr.leave",string="Ausencia",store=True,)
    employee_id = fields.Many2one(related = "leave_id.employee_id", string="Empleado", store=True,)
    number_real_days = fields.Float(string="Dias", related = "leave_id.number_real_days",store=True,)
    vac_line = fields.Many2one("hr.vacation.line",  ondelete='cascade', string="", store=True,)

