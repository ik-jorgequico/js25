from odoo import api, fields, models
from datetime import datetime, timedelta, time
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
#from oa_development.hr_analysis.models.hr_analysis_holidays import HrAnalysisHolidays

class Job(models.BaseModel):
    _inherit = "hr.job"

    
    cod = fields.Char(string="Codigo", store=True,)
    state = fields.Selection([('recruit', 'Recruitment in Progress'),('open', 'Not Recruiting')])
    parent_id = fields.Many2one('hr.job', string='Parent Job', index=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    child_ids = fields.One2many('hr.job', 'parent_id', string='Child Job')