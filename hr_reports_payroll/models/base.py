from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    plame_id = fields.Many2one(
        comodel_name='plame.lines',
        string='Nombre Plame'
    )
    plame_code = fields.Char(related='plame_id.code',string="Código Plame")

    appears_report_payroll = fields.Boolean(string="¿Aparece estrictamente en el Reporte Tabular de Nomina?", store=True,default=True)
    appears_report_lbs = fields.Boolean(string="¿Aparece en el Reporte Tabular de Liquidaciones?", store=True,default=True)

    company_id = fields.Many2one('res.company', 'Compañia', readonly=True,default=lambda self: self.env.company , tracking=True)
    # for_reports = fields.Selection(
    #     selection=[
    #         ('', 'Estrictamente para Nominas'),
    #         ('02', 'Estrictamente para Liquidaciones [LBS]'),
    #     ],
    #     string='Aparece en Reportes', store=True,)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    code_file_plame = fields.Char(
        string='Código archivo Plame',
        config_parameter='process_plame.code_file_plame',
    )
