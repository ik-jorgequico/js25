from odoo import api, fields, models, _

class EmployeePension(models.Model):
    _name = 'hr.employee.pension'
    _description = 'Employee Pension'
    
    parent_id = fields.Many2one("hr.employee",string="Empelados", ondelete='cascade')
    date_start = fields.Date(string = "F. inicio", store=True, required=True)
    date_end = fields.Date(string = "F. fin", store=True)
    pension_system_id = fields.Many2one("pension.system", string="S. de pen.", required=True)
    pension_system_name = fields.Char(related="pension_system_id.name", string="S. de pensión - String", store=True)
    pension_mode = fields.Selection([('flujo', 'Flujo'), ('mixto', 'Mixto')], string='T. de Pen.', store=True)
    cod_cuspp = fields.Char("CUSPP", store=True)
    is_onp = fields.Boolean("es onp",compute='compute_is_onp',store=True)
    
    @api.onchange('pension_system_id')
    def change_pension_system(self):
        if(self.pension_system_id.name == "ONP"):
            self.pension_mode = None
            self.cod_cuspp = None

    @api.depends('pension_system_id')
    def compute_is_onp(self):
        for r in self:
            if r.pension_system_id and r.pension_system_id.name == 'ONP':
                r.is_onp = True
            else:
                r.is_onp = False