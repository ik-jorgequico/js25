from odoo import api, fields, models, _

INSURERS_SELECTION = [
    ('01', 'RIMAC'),
    ('02', 'PACIFICO'),
    ('03', 'MAPFRE'),
    ('04', 'SANITAS'),
    ('05', 'POSITIVA'),
]

class EmployeeHealth(models.Model):
    _name = 'hr.employee.health'
    _description = 'Employee Health'
    
    parent_id = fields.Many2one("hr.employee",string="Empelados", ondelete='cascade')
    date_start = fields.Date(string = "F. inicio", store=True, required=True)
    date_end = fields.Date(string = "F. fin", store=True)
    regimen_id = fields.Many2one("health.regime", string="Rég. de salud", required=True)
    regimen_name = fields.Char(related="regimen_id.name", string="Reg. de Salud - String")
    insurers = fields.Selection(INSURERS_SELECTION, string='Aseg.', store=True)

    @api.onchange('regimen_id')
    def change_pension_system(self):
        if(self.regimen_id.name == "EPS"):
            self.insurers = None
    