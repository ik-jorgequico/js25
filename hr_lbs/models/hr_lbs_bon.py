from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from datetime import datetime 
from odoo.exceptions import ValidationError, UserError
import base64

class LBSBonification(models.Model):
    _name = "hr.lbs.bon"
    _description = "Otros Ingresos"

    parent_id = fields.Many2one("hr.lbs.line", string="LBS Empleado",  )
    name = fields.Char(string="Descripción",store=True,)
    sequence = fields.Integer( index=True, default=10,store=True,)
    input_type_id = fields.Many2one('hr.payslip.input.type', string='Tipo',  )
    code = fields.Char(related='input_type_id.code',store=True,)
    amount = fields.Float( string="Monto",store=True,)
    
    def unlink(self):
        input = self.parent_id.payslip_id.input_line_ids.filtered(lambda x: x.input_type_id == self.input_type_id)
        if input:
            if len(input)==1:
                input.amount = 0
            else :
                for i in input:
                    i.amount = 0
            self.parent_id.payslip_id.compute_sheet()
        return super(LBSBonification,self).unlink()