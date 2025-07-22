
from odoo import api, Command, fields, models

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    lbs_ids = fields.One2many('hr.lbs.line', "payslip_id", store=True, string="LBSs")
    lbs_id = fields.Many2one('hr.lbs.line', compute = 'compute_lbs', store=True, string="LBS")

    @api.depends('lbs_ids')
    def compute_lbs(self):
        for record in self:
            if len(record.lbs_ids) == 1:
                record.lbs_id = record.lbs_ids[0].id
            else:
                record.lbs_id == False