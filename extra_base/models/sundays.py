from odoo import api, fields, models
from dateutil.relativedelta import relativedelta

from datetime import datetime, timedelta, time


class SundaysGenerator(models.Model):
    _name = 'sundays.generator'
    _description = 'Sundays'
    
    
    name = fields.Char(string="Nombre", compute="_compute_name", store=True,)

    current_year = int(datetime.now().date().strftime("%Y"))
    list_anios = [(str(i),str(i)) for i in range(current_year-3,current_year+3)]
    anio = fields.Selection(
        selection=list_anios, 
        store=True,
        string="Año"
    )
    date_from = fields.Date(string="Dia Inicio",required=True,  store=True,)
    date_to = fields.Date(string="Dia Fin",required=True,  store=True,)
    sundays_ids = fields.One2many('sundays','sunday_generator_id', string="Domingos",store=True,)
            
    @api.onchange("anio")
    def _onechange_dates(self):
        if self.anio:
            self.date_from = datetime.strptime("01/01/"+str(self.anio), '%d/%m/%Y')
            self.date_to = datetime.strptime("31/12/"+str(self.anio), '%d/%m/%Y')  

    @api.depends('anio')
    def _compute_name(self): 
        for record in self:
            record.name = "Periodo " + str(record.anio)
        
    def sundays_generator(self):
        val_list = []
        current_date = self.date_from
        while current_date <= self.date_to:
            if current_date.weekday() == 6:  # Sunday is represented by 6 in the weekday() function
                val_list.append(current_date)
            current_date += timedelta(days=1)
        self.sundays_ids.unlink()
        self.write({
            "sundays_ids":[(0, 0, {"date":i,"sunday_generator_id":self.id}) for i in val_list],
        })
            

class Sundays(models.Model):
    _name = 'sundays'
    _description = 'Sundays'
    
    name = fields.Char(string="Nombre",store=True, compute="_compute_name", )
    date = fields.Date(string="Fecha", store=True,)
    is_affected_utility = fields.Boolean(string="Es afecto a Utilidad?", store=True, default=True)
    sunday_generator_id = fields.Many2one('sundays.generator',string="Periodo",store=True,)

    @api.depends("date")
    def _compute_name(self):
        for record in self:
            record.name = "Domingo " + record.date.strftime("%Y-%m-%d")