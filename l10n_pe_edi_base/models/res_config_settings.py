#######################################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
#######################################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_pe_edi_send_invoice = fields.Boolean(
        related="company_id.l10n_pe_edi_send_invoice", readonly=False
    )
    l10n_pe_edi_ose_id = fields.Many2one(
        related="company_id.l10n_pe_edi_ose_id", readonly=False
    )
    l10n_pe_edi_send_invoice_interval_unit = fields.Selection(
        related="company_id.l10n_pe_edi_send_invoice_interval_unit",
        readonly=False,
    )
    l10n_pe_edi_send_invoice_next_execution_date = fields.Datetime(
        related="company_id.l10n_pe_edi_send_invoice_next_execution_date",
        readonly=False,
    )
    l10n_pe_service_token = fields.Char(
        "RUC token", related="company_id.l10n_pe_service_token", readonly=False
    )
    l10n_pe_edi_send_picking = fields.Boolean(
        related="company_id.l10n_pe_edi_send_picking", readonly=False
    )
    l10n_pe_edi_picking_default_catalog_18_id = fields.Many2one(
        related="company_id.l10n_pe_edi_picking_default_catalog_18_id", readonly=False
    )
    l10n_pe_edi_picking_default_carrier_id = fields.Many2one(
        related="company_id.l10n_pe_edi_picking_default_carrier_id", readonly=False
    )
    l10n_pe_edi_picking_default_driver_id = fields.Many2one(
        related="company_id.l10n_pe_edi_picking_default_driver_id", readonly=False
    )
    l10n_pe_edi_picking_default_auto_field_arrival_point = fields.Boolean(
        related="company_id.l10n_pe_edi_picking_default_auto_field_arrival_point",
        readonly=False
    )
    module_l10n_pe_edi_odoofact = fields.Boolean(string="Electronic Inviocing")
    module_l10n_pe_edi_picking = fields.Boolean(string="Electronic Remission Guide")
    module_odoope_ruc_validation = fields.Boolean(string="Data Validator - (PE)")
    module_l10n_pe_currency = fields.Boolean(string="Exchange Rate of the Day - (PE)")
