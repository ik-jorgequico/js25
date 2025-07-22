from odoo import fields, models, api

import math


class HrJob(models.Model):
    _inherit = 'hr.job'
    _description = 'Hr Job'
    
    location_id = fields.Many2one("hr.table.location",string="Localidad",store=True)
    
    date_approbation = fields.Date("Fecha de aprobación", store=True)
    prepare_by = fields.Many2one("hr.job", string="Preparado por", store=True)
    approve_by = fields.Many2one("hr.job", string="Aprobado por", store=True)
    direct_boss = fields.Many2one("hr.job", string="Dependencia jerárquica (jefe directo)", store=True)
    
    mision = fields.Text(string="Misión del puesto", store=True)
    context = fields.Text("Contexto")
    
    jobs_aspect_ids = fields.One2many("hr.job.aspect", "parent_id", string="Cuadro de aspectos", store=True)
    jobs_benefit_ids = fields.One2many("hr.job.benefit", "parent_id", string="Cuadro de beneficios", store=True)
    jobs_skill_ids = fields.One2many("hr.job.skill", "parent_id", string="Cuadro de habilidades", store=True)
    jobs_experience_ids = fields.One2many("hr.job.experience", "parent_id", string="Cuadro de experiencias", store=True)
    jobs_technical_ids = fields.One2many("hr.job.technical", "parent_id", string="Cuadro de conocimientos técnicos", store=True)
    jobs_functional_ids = fields.One2many("hr.job.functional", "parent_id", string="Cuadro de conocimientos funcionales", store=True)
    parents_boss = fields.Char('Jefes directos', compute="get_parents_boss", store=True)
    
    age_min = fields.Integer('Mínima', store=True)
    
    age_max = fields.Integer('Máxima', store=True)
    
    age_indiferent = fields.Boolean('Indiferente', store=True)
    
    gender = fields.Selection(
        selection=[
            ('01', 'Masculino'),
            ('02', 'Femenino'),
            ('03', 'Indiferente'),
        ],
        string='Género', store=True)
    
    degree = fields.Selection(
        selection=[
            ('01', 'Universitario'),
            ('02', 'Técnico'),
            ('03', 'Otros'),
        ],
        string='Nivel de Educación', store=True)
    
    degree_other = fields.Char('Especificar', store=True)
    
    desirable_degree = fields.Char('Formación Académica deseada', store=True)
    
    travel = fields.Selection(
        selection=[
            ('01', 'No requerido'),
            ('02', 'Deseable'),
            ('03', 'Indispensable'),
        ],
        string='Disponibilidad para viajar', store=True)

    
    def recursive_boss(self, direct_boss):
        if(direct_boss):
            return direct_boss.name + '|||' +  self.recursive_boss(direct_boss.direct_boss)
        return ""
    
    
    @api.depends('direct_boss')
    def get_parents_boss(self):

        for element in self:
            element.parents_boss = element.name + '|||' + self.recursive_boss(element.direct_boss)
            
    @api.onchange('degree')
    def change_degree(self):
        if(self.degree != "03"):
            self.degree_other = None
    
    
    @api.onchange('age_indiferent')
    def change_age(self):
        if(self.age_indiferent):
            self.age_min = None
            self.age_max = None
        
    
class HrJobAspect(models.Model):
    _name = 'hr.job.aspect'
    _description = 'ASPECTOS BAJO SU RESPONSABILIDAD'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    aspect = fields.Char("ASPECTOS BAJO SU RESPONSABILIDAD")
    measure = fields.Selection(
        selection=[
            ('01', 'ALTA'),
            ('02', 'MEDIA'),
            ('03', 'BAJA'),
            ('04', 'N/A'),
        ],
        string='Medida', store=True)
    
class HrJobBenefit(models.Model):
    _name = 'hr.job.benefit'
    _description = 'BENEFICIOS'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    benefit = fields.Text("BENEFICIOS (a completarse por RRHH)")
    description = fields.Text("Descripción")
    

class HrJobSkill(models.Model):
    _name = 'hr.job.skill'
    _description = 'COMPETENCIAS Y HABILIDADES'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    skill = fields.Char("COMPETENCIAS Y HABILIDADES")
    measure = fields.Selection(
        selection=[
            ('01', 'ALTA'),
            ('02', 'MEDIA'),
            ('03', 'BAJA'),
        ],
        string='Medida', store=True)
    
class HrJobExperience(models.Model):
    _name = 'hr.job.experience'
    _description = 'EXPERIENCIA LABORAL PREVIA (posición /tiempo)'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    experience = fields.Char("EXPERIENCIA LABORAL PREVIA (posición /tiempo)")
    
class HrJobTechnical(models.Model):
    _name = 'hr.job.technical'
    _description = 'CONOCIMIENTOS TÉCNICOS'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    technical = fields.Char("CONOCIMIENTOS ESPECIFICOS: (Técnicos)")
    measure = fields.Selection(
        selection=[
            ('01', 'BÁSICO'),
            ('02', 'INTERMEDIO'),
            ('03', 'AVANZADO'),
        ],
        string='Medida', store=True)
    
class HrJobFunctional(models.Model):
    _name = 'hr.job.functional'
    _description = 'CONOCIMIENTOS FUNCIONAL'

    parent_id = fields.Many2one("hr.job", ondelete='cascade')
    
    functional = fields.Char("CONOCIMIENTOS ESPECIFICOS: (funcionales)")
    measure = fields.Selection(
        selection=[
            ('01', 'NO REQUERIDO'),
            ('02', 'DESEABLE'),
            ('03', 'INDISPENSABLE'),
        ],
        string='Medida', store=True)
 
