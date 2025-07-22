from odoo import api, fields, models, _


INSURER_SELECTION = [
    ('01', 'RIMAC'),
    ('02', 'PACIFICO'),
    ('03', 'MAPFRE'),
    ('04', 'SANITAS'),
    ('05', 'POSITIVA'),
]

class HrSctr(models.Model):
    _name = "hr.sctr"
    _description = 'Ingreso de SCTR'
    
    name = fields.Char("Descripcion")
    insurer = fields.Selection(INSURER_SELECTION, string='Aseguradora')
    sctr_salud = fields.Float(string = "Porcentaje Salud", store=True)
    sctr_pension = fields.Float(string = "Porcentaje Pesion", store=True)

    @api.onchange('insurer')
    def _compute_name(self):
        for rec in self:
            if rec.insurer:
                field_info = dict(rec._fields['insurer'].get_description(rec.env))
                field_selection = dict(field_info.get('selection'))
                field_label = field_selection.get(rec.insurer)
                rec.name = field_label
            else:
                rec.name = ''