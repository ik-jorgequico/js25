# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models,_
from datetime import datetime, timedelta, time
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
#from oa_development.hr_analysis.models.hr_analysis_holidays import HrAnalysisHolidays
from odoo.exceptions import UserError
    
class HrTableLocation(models.Model):
    _name = "hr.table.location"
    _description = "Tabla de Localidades"
    
    name = fields.Char("Nombre",store=True)
    code = fields.Char("Codigo",store=True)
    
    
    
    
