#-*- coding:utf-8 -*-
from odoo import fields, models

class HrSctr(models.Model):
    _name = "hr.sctr.employee"
    _description = 'Ingreso de SCTR por empleado'
    
    parent_id = fields.Many2one("hr.employee",string="Empleados", store=True,ondelete='cascade')
    date_start = fields.Date(string = "F. Inicio", store=True, required=True)
    date_end = fields.Date(string = "F. Fin", store=True)
    employee_sctr_id = fields.Many2one('hr.sctr', string="Aseg.",store=True)
    sctr_salud = fields.Float(related="employee_sctr_id.sctr_salud",string = "% Salud", store=True)
    sctr_pension = fields.Float(related="employee_sctr_id.sctr_pension",string = "% Pension", store=True)
    cod_active = fields.Boolean(string="Activo", store=True, default=False)
