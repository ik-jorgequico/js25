#######################################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
#######################################################################################

from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_pe_edi_min_amount_retention = fields.Float(string="Min Amount for Retention")
    l10n_pe_edi_min_amount_detraction = fields.Float(string="Min Amount for Detraction", default=700)
    l10n_pe_edi_detraction_payment_type_id = fields.Many2one(
        comodel_name="l10n_pe_edi.catalog.59",
        string="Detraction Payment Type",
        copy=False,
    )
    l10n_pe_edi_detraction_bank_account_id = fields.Many2one(
        comodel_name="res.partner.bank", string="National bank Account"
    )
    activate_einvoice_ticket = fields.Boolean(string="Print Electronic Ticket", default=False)

    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        for company in companies:
            if company.country_id and company.country_id.code == "PE":
                self.generate_shop(company)
        return companies
    
    @api.model
    def generate_shop(self, company):
        """
        This method is used for creating shop.
        :param company_id: company to generate shop for.
        :returns: True
        """
        self.env['l10n_pe_edi.shop'].create({
            'name': '%s (%s)' % (company.name, _('Shop')),
            'code': '0000',
            'company_id': company.id,
            'partner_id': company.partner_id.id,
        })
        return True
