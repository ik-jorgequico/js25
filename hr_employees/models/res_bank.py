# -*- coding: utf-8 -*-

import re

from collections.abc import Iterable

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResPartnerBank(models.Model):
    _name = 'res.partner.bank'
    _inherit = ['res.partner.bank','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'res.partner.bank'

    
    cci = fields.Char('Cuenta Interbancaria (CCI)', required=False)
    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', string="Tipo de Identificación")
    vat = fields.Char(string='Identification No', groups="hr.group_hr_user", tracking=True)
    acc_holder_name = fields.Char('Account Holder Name')


    # @api.onchange('l10n_latam_identification_type_id', 'vat')
    # def _get_name_vendor(self):
    #     vat = self.vat
    #     vat_type = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        
    #     if vat_type and vat:
    #         partner = self.env['res.partner']
    #         if vat_type == '1':
    #             if len(vat) != 8:
    #                 raise UserError(_('The DNI entered is incorrect'))
    #             dni_name = partner.consultar_dni(vat)
    #             if dni_name:
    #                 self.acc_holder_name = dni_name['name']

    #         elif vat_type == '6':
    #             partner.validate_ruc(vat)
    #             partner.consultar_ruc(vat)
    #             if partner.name:
    #                 self.acc_holder_name = partner.name

