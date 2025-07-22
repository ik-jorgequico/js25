# -*- coding: utf-8 -*-

from odoo import models, api


class BulkSendUtilities(models.TransientModel):
    _name = "bulk.send.utilities.incomes"
    _description = "Bulk Send Utility in Email"

    # def send_utilities_in_email(self):
    #     active_ids = self._context.get('active_ids')
    #     incomes_ids = self.env['hr.utilities.incomes'].browse(active_ids)
    #     ir_model_data = self.env['ir.model.data']
    #     template = ir_model_data.check_object_reference(
    #         'hr_utilities', 'email_template_edi_hr_utilities')[1]
    #     template_id = self.env['mail.template'].browse(template)
    #     if template_id:
    #         for utility in incomes_ids:
    #             template_id.send_mail(utility.id, force_send=True)

