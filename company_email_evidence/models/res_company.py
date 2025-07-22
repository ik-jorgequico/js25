from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

    
class Company(models.Model):
    _inherit = 'res.company'
    
    partner_ids = fields.Many2many(
        'res.partner', 'mail_compose_message_additional_res_partner_rel',
        'wizard_id', 'partner_id', 'Contactos Adicionales',)
    
    template_ids = fields.Many2many(
        'mail.template', 'mail_specific_templates_for_partner_ids',
        'wizard_id', 'template_id', 'Templates Afectados',)
    
    is_all_template = fields.Boolean(string = "Es para todos los templates?", store=True)
    
    def apply_changes_for_templates(self):
        emails = self.partner_ids.mapped('email')
        list_emails = ", ".join(list(emails))
        if list_emails:
            if not self.is_all_template:
                self.env["mail.template"].search([]).write({ "email_cc" : '' })
                self.template_ids.write({ "email_cc" : list_emails })
            else:
                self.env["mail.template"].search([]).write({ "email_cc" : list_emails})
            
            