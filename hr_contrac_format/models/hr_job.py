from odoo import fields, models


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'Hr Job'

    jobs_ids = fields.One2many("hr.job.functions", "parent_id", string="Cuadro de Funciones")
    
class HrJobFunction(models.Model):
    _name = 'hr.job.functions'
    _description = 'Funciones de cargo'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    function = fields.Char("Funciones")
