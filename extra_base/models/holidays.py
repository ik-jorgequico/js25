from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class Holidays(models.Model):
    _name = 'holidays'
    _description = 'Holidays'

    name = fields.Char(string='Description',default="", store = True)
    date_publication = fields.Date(string="Fecha Publicacion", store=True,)
    date_celebrate = fields.Date(string="Primera Fecha de Celebracion", store=True,help="Se entiende que para los siguientes años se mantendrá la misma fecha.",)
    day = fields.Char(string="Dia del Feriado", help="Dia relacionado a la fecha de celebracion", store=True,compute="compute_date_celebrate")
    month = fields.Selection(selection=[
        ("01","Enero"),
        ("02","Febrero"),
        ("03","Marzo"),
        ("04","Abril"),
        ("05","Mayo"),
        ("06","Junio"),
        ("07","Julio"),
        ("08","Agosto"),
        ("09","Septiembre"),
        ("10","Octubre"),
        ("11","Noviembre"),
        ("12","Diciembre"),
    ], string="Mes del Feriado",help="Mes relacionado a la fecha de celebracion", store=True,compute="compute_date_celebrate")


    day_int = fields.Integer(string="Dia", help="Formato en numerico", store=True,compute="compute_date_celebrate")
    month_int = fields.Integer(string="Mes", help="Formato en numerico", store=True,compute="compute_date_celebrate")


    @api.depends('date_celebrate')
    def compute_date_celebrate(self):
        for record in self:
            if record.date_celebrate:
                record.month= record.date_celebrate.strftime("%m")
                record.day= record.date_celebrate.strftime("%d")
                record.month_int= int(record.date_celebrate.strftime("%m"))
                record.day_int= int(record.date_celebrate.strftime("%d"))