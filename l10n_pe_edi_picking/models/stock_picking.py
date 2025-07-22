#######################################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
#######################################################################################

import json
import re

import pytz
from bs4 import BeautifulSoup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

CARRIER_DOCUMENT_TYPE = [("6", "RUC")]
DRIVER_DOCUMENT_TYPE = [
    ("1", "DNI"),
    ("4", "CARNET DE EXTRANJERIA"),
    ("7", "PASAPORTE"),
    ("A", "CEDULA DIPLOMATICA DE IDENTIDAD"),
    ("0", "NO DOMICILIADO, SIN RUC (EXPORTACION)"),
]
PARTNER_DOCUMENT_TYPE = CARRIER_DOCUMENT_TYPE + DRIVER_DOCUMENT_TYPE


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    def _default_l10n_pe_edi_shop_id(self):
        return (
            self.env["l10n_pe_edi.shop"]
            .search([("company_id", "=", self.env.company.id)], limit=1)
            .id
        )

    l10n_pe_edi_enable_epicking = fields.Boolean(
        string="Enable E-picking", default=False, copy=False
    )
    l10n_pe_edi_picking_sequence_id = fields.Many2one(
        "ir.sequence", string="E-Picking Sequence", copy=False
    )
    l10n_pe_edi_shop_id = fields.Many2one(
        comodel_name="l10n_pe_edi.shop",
        string="Shop",
        default=_default_l10n_pe_edi_shop_id,
    )
    l10n_pe_edi_request_document_type_id = fields.Many2one(
        comodel_name="l10n_pe_edi.request.document.type",
        string="Request Document Type",
    )
    # these field will be deprecated --------------------------------------------------
    l10n_pe_edi_is_epicking = fields.Boolean(
        string="Is E-picking", default=False, copy=False
    )
    # ---------------------------------------------------------------------------------


class StockPicking(models.Model):
    _inherit = "stock.picking"

    l10n_pe_edi_picking_company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Company Partner",
        related="company_id.partner_id",
    )
    l10n_pe_edi_picking_enable_epicking = fields.Boolean(
        related="picking_type_id.l10n_pe_edi_enable_epicking"
    )
    l10n_pe_edi_is_electronic = fields.Boolean(
        string="Is Electronic", compute="_compute_is_electronic", copy=False
    )
    l10n_pe_edi_request_id = fields.Many2one(
        comodel_name="l10n_pe_edi.request", string="PSE/OSE request", copy=False
    )
    l10n_pe_edi_ose_accepted = fields.Boolean(
        string="Sent to PSE/OSE",
        related="l10n_pe_edi_request_id.ose_accepted",
        store=True,
    )
    l10n_pe_edi_sunat_accepted = fields.Boolean(
        string="Accepted by SUNAT",
        related="l10n_pe_edi_request_id.sunat_accepted",
        store=True,
    )
    l10n_pe_edi_response = fields.Text(
        string="Response", related="l10n_pe_edi_request_id.response", store=True
    )
    l10n_pe_edi_shop_id = fields.Many2one(
        comodel_name="l10n_pe_edi.shop",
        string="Shop",
        related="picking_type_id.l10n_pe_edi_shop_id",
        store=True,
    )
    l10n_pe_edi_picking_name = fields.Char(
        string="E-Picking Name", readonly=True, copy=False
    )
    l10n_pe_edi_picking_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        compute="_compute_picking_partner",
        store=True,
    )
    l10n_pe_edi_picking_commercial_partner_id = fields.Many2one(
        related="l10n_pe_edi_picking_partner_id.commercial_partner_id"
    )
    l10n_pe_edi_picking_commercial_document_type = fields.Selection(
        selection=PARTNER_DOCUMENT_TYPE,
        string="Commercial Document Type",
        compute="_compute_partner_document",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_commercial_document_number = fields.Char(
        related="l10n_pe_edi_picking_commercial_partner_id.vat",
    )
    l10n_pe_edi_picking_catalog_20_id = fields.Many2one(
        comodel_name="l10n_pe_edi.catalog.20",
        string="Reason for transfer",
        compute="_compute_catalog_20",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_catalog_20_code = fields.Char(
        related="l10n_pe_edi_picking_catalog_20_id.code", string="Code 20",store=True
    )
    l10n_pe_edi_picking_catalog_20_others = fields.Char(
        string="Reason for transfer - others",store=True
    )
    l10n_pe_edi_picking_total_gross_weight = fields.Float(
        string="Total Gross Weight",help="Weight in Kg.",store=True
    )
    l10n_pe_edi_picking_gross_weight_uom = fields.Selection(
        selection=[("KGM", _("Kilograms")), ("TNE", _("Tons"))],
        string="UoM Gross Weight",
        default="KGM",
        store=True
    )
    l10n_pe_edi_picking_number_packages = fields.Integer(
        string="Number Of Packages", default=0
    )
    l10n_pe_edi_picking_catalog_18_id = fields.Many2one(
        comodel_name="l10n_pe_edi.catalog.18",
        string="Transport Type",
        compute="_compute_catalog_18",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_catalog_18_code = fields.Char(
        related="l10n_pe_edi_picking_catalog_18_id.code", string="Code 18"
    )
    l10n_pe_edi_picking_start_transport_date = fields.Date(
        string="Start Transport Date",
        copy=False,
        compute="_compute_start_transport_date",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_carrier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Carrier",
        compute="_compute_carrier",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_invoice_number_ids = fields.One2many(
        comodel_name='l10n_pe_edi.invoice.number',
        inverse_name="picking_id",
        string='Picking numbers'
        )
    # these field will be deprecated -------------------------------------------------
    l10n_pe_edi_picking_carrier_doc_type = fields.Many2one(
        comodel_name="l10n_latam.identification.type",
        compute="_compute_carrier_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_doc_type = fields.Many2one(
        comodel_name="l10n_latam.identification.type",
        compute="_compute_driver_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_type_is_epicking = fields.Boolean(
        related="picking_type_id.l10n_pe_edi_is_epicking"
    )
    l10n_pe_edi_picking_partner_for_carrier_driver = fields.Boolean(
        related="company_id.l10n_pe_edi_picking_partner_for_carrier_driver"
    )
    l10n_pe_edi_picking_partner_for_starting_arrival_point = fields.Boolean(
        related="company_id.l10n_pe_edi_picking_partner_for_starting_arrival_point"
    )
    l10n_pe_edi_picking_company_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="company partner id",
        related="company_id.partner_id",
    )
    l10n_pe_edi_is_epicking = fields.Boolean(readonly=True, copy=False)
    l10n_pe_edi_picking_serie = fields.Char(store=True, readonly=True, copy=False)
    l10n_pe_edi_picking_number = fields.Integer(store=True, readonly=True, copy=False)
    # ---------------------------------------------------------------------------------
    l10n_pe_edi_picking_carrier_document_type = fields.Selection(
        selection=CARRIER_DOCUMENT_TYPE,
        string="Carrier Document Type",
        compute="_compute_carrier_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_carrier_doc_number = fields.Char(
        string="Carrier Document Number",
        compute="_compute_carrier_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_carrier_name = fields.Char(
        string="Carrier Name",
        compute="_compute_carrier_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_carrier_license_plate = fields.Char(
        string="License Plate",
        compute="_compute_carrier_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_id = fields.Many2one(
        comodel_name="res.partner",
        string="Driver",
        compute="_compute_driver",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_document_type = fields.Selection(
        selection=DRIVER_DOCUMENT_TYPE,
        string="Driver Document Type",
        compute="_compute_driver_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_doc_number = fields.Char(
        string="Driver Document Number",
        compute="_compute_driver_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_complete_name = fields.Char(
        string="Driver Complete Name",
        compute="_compute_driver_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_driver_name = fields.Char(string="Driver Name")
    l10n_pe_edi_picking_driver_last_name = fields.Char(string="Driver Last Name")
    l10n_pe_edi_picking_driver_license_number = fields.Char(
        string="Driver License Number",
        compute="_compute_driver_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_id = fields.Many2one(
        comodel_name="res.partner",
        string="Starting Point",
        compute="_compute_starting_point",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Starting Point Country",
        compute="_compute_starting_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Starting Point State",
        compute="_compute_starting_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_province_id = fields.Many2one(
        comodel_name="res.city",
        string="Starting Point Province",
        compute="_compute_starting_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_district_id = fields.Many2one(
        comodel_name="l10n_pe.res.city.district",
        string="Starting Point District",
        compute="_compute_starting_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_ubigeo = fields.Char(
        string="Starting Point Ubigeo",
        compute="_compute_starting_point_ubigeo",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_starting_point_street = fields.Char(
        string="Starting Point Street",
        compute="_compute_starting_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_id = fields.Many2one(
        comodel_name="res.partner",
        string="Arrival Point",
        compute="_compute_arrival_point",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Arrival Point Country",
        compute="_compute_arrival_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Arrival Point State",
        compute="_compute_arrival_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_province_id = fields.Many2one(
        comodel_name="res.city",
        string="Arrival Point Province",
        compute="_compute_arrival_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_district_id = fields.Many2one(
        comodel_name="l10n_pe.res.city.district",
        string="Arrival Point District",
        compute="_compute_arrival_point_data",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_ubigeo = fields.Char(
        string="Arrival Point Ubigeo",
        compute="_compute_arrival_point_ubigeo",
        readonly=False,
        store=True,
    )
    l10n_pe_edi_picking_arrival_point_street = fields.Char(
        string="Arrival Point Street",
        compute="_compute_arrival_point_data",
        readonly=False,
        store=True,
    )
    canceled_edi_picking_in_sunat = fields.Boolean(
        string="Canceled edi picking in SUNAT",
        copy=False,
        store=True,
    )

    l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type',string="Tipo de documento",compute="_default_l10n_latam_document_type", store=True)#agregado

    @api.depends('partner_id','state')
    def _default_l10n_latam_document_type(self):
        for record in self:
            document_type = self.env['l10n_latam.document.type'].search([('code', '=', '09')], limit=1)
            if document_type:
                record.l10n_latam_document_type_id = document_type.id

    @api.depends("l10n_pe_edi_request_id")
    def _compute_is_electronic(self):
        for rec in self:
            rec.l10n_pe_edi_is_electronic = rec.l10n_pe_edi_request_id and True or False

    @api.depends("move_ids", "move_line_ids", "partner_id")
    def _compute_picking_partner(self):
        for rec in self:
            partner = False
            if rec.move_ids or rec.move_line_ids:
                partner = (
                    rec.move_ids
                    and rec.move_ids.mapped("partner_id")
                    or rec.move_line_ids
                    and rec.move_line_ids.mapped("picking_partner_id")
                )
            if not partner:
                partner = rec.partner_id
            rec.l10n_pe_edi_picking_partner_id = partner and partner.id or False

    @api.depends("l10n_pe_edi_picking_commercial_partner_id")
    def _compute_partner_document(self):
        for rec in self:
            partner = rec.l10n_pe_edi_picking_commercial_partner_id
            rec.l10n_pe_edi_picking_commercial_document_type = (
                partner
                and partner.l10n_latam_identification_type_id
                and (
                    partner.l10n_latam_identification_type_id.l10n_pe_vat_code
                    in [x[0] for x in PARTNER_DOCUMENT_TYPE]
                )
                and partner.l10n_latam_identification_type_id.l10n_pe_vat_code
                or False
            )

    @api.depends("picking_type_id")
    def _compute_catalog_20(self):
        Catalog20 = self.env["l10n_pe_edi.catalog.20"]
        for rec in self:
            catalog_20 = False
            if rec.picking_type_id and rec.picking_type_id.code == "outgoing":
                catalog_20 = Catalog20.search([("code", "=", "01")], limit=1)
            elif rec.picking_type_id and rec.picking_type_id.code == "incoming":
                catalog_20 = Catalog20.search([("code", "=", "02")], limit=1)
            elif rec.picking_type_id and rec.picking_type_id.code == "internal":
                catalog_20 = Catalog20.search([("code", "=", "04")], limit=1)
            rec.l10n_pe_edi_picking_catalog_20_id = (
                catalog_20 and catalog_20.id or False
            )

    @api.depends("company_id")
    def _compute_catalog_18(self):
        for rec in self:
            if not rec.l10n_pe_edi_picking_catalog_18_id:
                caatalog_18 = rec.company_id.l10n_pe_edi_picking_default_catalog_18_id
                if not caatalog_18:
                    caatalog_18 = self.env["l10n_pe_edi.catalog.18"].search([], limit=1)
                rec.l10n_pe_edi_picking_catalog_18_id = (
                    caatalog_18 and caatalog_18.id or False
                )

    @api.depends("date_done")
    def _compute_start_transport_date(self):
        for rec in self:
            rec.l10n_pe_edi_picking_start_transport_date = (
                rec.date_done and self.convert_date_to_timezone(rec.date_done) or False
            )

    @api.depends("company_id")
    def _compute_carrier(self):
        for rec in self:
            if not rec.l10n_pe_edi_picking_carrier_id:
                carrier = rec.company_id.l10n_pe_edi_picking_default_carrier_id
                if not carrier:
                    carrier = self.env["res.partner"].search(
                        [("l10n_pe_edi_picking_is_carrier", "=", True)], limit=1
                    )
                rec.l10n_pe_edi_picking_carrier_id = carrier and carrier.id or False

    @api.depends("l10n_pe_edi_picking_carrier_id")
    def _compute_carrier_data(self):
        for rec in self:
            rec.l10n_pe_edi_picking_carrier_doc_type = (
                rec.l10n_pe_edi_picking_carrier_id
                and rec.l10n_pe_edi_picking_carrier_id.l10n_latam_identification_type_id
                and rec.l10n_pe_edi_picking_carrier_id.l10n_latam_identification_type_id.id
                or False
            )
            rec.l10n_pe_edi_picking_carrier_document_type = (
                rec.l10n_pe_edi_picking_carrier_doc_type
                and rec.l10n_pe_edi_picking_carrier_doc_type.l10n_pe_vat_code == "6"
                and rec.l10n_pe_edi_picking_carrier_doc_type.l10n_pe_vat_code
                or ""
            )
            rec.l10n_pe_edi_picking_carrier_doc_number = (
                rec.l10n_pe_edi_picking_carrier_id
                and rec.l10n_pe_edi_picking_carrier_id.vat
                or False
            )
            rec.l10n_pe_edi_picking_carrier_name = (
                rec.l10n_pe_edi_picking_carrier_id
                and rec.l10n_pe_edi_picking_carrier_id.name
                or False
            )
            rec.l10n_pe_edi_picking_carrier_license_plate = (
                rec.l10n_pe_edi_picking_carrier_id
                and rec.l10n_pe_edi_picking_carrier_id.l10n_pe_edi_picking_license_plate
                or False
            )

    @api.depends("company_id")
    def _compute_driver(self):
        for rec in self:
            if not rec.l10n_pe_edi_picking_driver_id:
                driver = rec.company_id.l10n_pe_edi_picking_default_driver_id
                if not driver:
                    driver = self.env["res.partner"].search(
                        [("l10n_pe_edi_picking_is_driver", "=", True)], limit=1
                    )
                rec.l10n_pe_edi_picking_driver_id = driver and driver.id or False

    @api.depends("l10n_pe_edi_picking_driver_id")
    def _compute_driver_data(self):
        for rec in self:
            rec.l10n_pe_edi_picking_driver_doc_type = (
                rec.l10n_pe_edi_picking_driver_id
                and rec.l10n_pe_edi_picking_driver_id.l10n_latam_identification_type_id
                and rec.l10n_pe_edi_picking_driver_id.l10n_latam_identification_type_id.id
                or False
            )
            rec.l10n_pe_edi_picking_driver_document_type = (
                rec.l10n_pe_edi_picking_driver_doc_type
                and (
                    rec.l10n_pe_edi_picking_driver_doc_type.l10n_pe_vat_code
                    in [x[0] for x in DRIVER_DOCUMENT_TYPE]
                )
                and rec.l10n_pe_edi_picking_driver_doc_type.l10n_pe_vat_code
                or ""
            )
            rec.l10n_pe_edi_picking_driver_doc_number = (
                rec.l10n_pe_edi_picking_driver_id
                and rec.l10n_pe_edi_picking_driver_id.vat
                or False
            )
            rec.l10n_pe_edi_picking_driver_complete_name = (
                rec.l10n_pe_edi_picking_driver_id
                and rec.l10n_pe_edi_picking_driver_id.name
                or False
            )
            rec.l10n_pe_edi_picking_driver_license_number = (
                rec.l10n_pe_edi_picking_driver_id
                and rec.l10n_pe_edi_picking_driver_id.l10n_pe_edi_picking_license_number
                or False
            )

    @api.depends("picking_type_id")
    def _compute_starting_point(self):
        for rec in self:
            rec.l10n_pe_edi_picking_starting_point_id = (
                rec.picking_type_id
                and rec.picking_type_id.warehouse_id
                and rec.picking_type_id.warehouse_id.partner_id
                and rec.picking_type_id.warehouse_id.partner_id.id
                or False
            )

    @api.depends("l10n_pe_edi_picking_starting_point_id")
    def _compute_starting_point_data(self):
        for rec in self:
            rec.l10n_pe_edi_picking_starting_point_country_id = (
                rec.l10n_pe_edi_picking_starting_point_id
                and rec.l10n_pe_edi_picking_starting_point_id.country_id
                and rec.l10n_pe_edi_picking_starting_point_id.country_id.id
                or False
            )
            rec.l10n_pe_edi_picking_starting_point_state_id = (
                rec.l10n_pe_edi_picking_starting_point_id
                and rec.l10n_pe_edi_picking_starting_point_id.state_id
                and rec.l10n_pe_edi_picking_starting_point_id.state_id.id
                or False
            )
            rec.l10n_pe_edi_picking_starting_point_province_id = (
                rec.l10n_pe_edi_picking_starting_point_id
                and rec.l10n_pe_edi_picking_starting_point_id.city_id
                and rec.l10n_pe_edi_picking_starting_point_id.city_id.id
                or False
            )
            rec.l10n_pe_edi_picking_starting_point_district_id = (
                rec.l10n_pe_edi_picking_starting_point_id
                and rec.l10n_pe_edi_picking_starting_point_id.l10n_pe_district
                and rec.l10n_pe_edi_picking_starting_point_id.l10n_pe_district.id
                or False
            )
            rec.l10n_pe_edi_picking_starting_point_street = (
                rec.l10n_pe_edi_picking_starting_point_id
                and rec.l10n_pe_edi_picking_starting_point_id.street
                and rec.l10n_pe_edi_picking_starting_point_id.street
                or False
            )

    @api.onchange("l10n_pe_edi_picking_starting_point_district_id")
    def _onchange_l10n_pe_edi_picking_starting_point_district_id(self):
        if self.l10n_pe_edi_picking_starting_point_district_id and self.l10n_pe_edi_picking_starting_point_district_id.city_id:
            self.l10n_pe_edi_picking_starting_point_province_id = self.l10n_pe_edi_picking_starting_point_district_id.city_id

    @api.onchange("l10n_pe_edi_picking_starting_point_province_id")
    def _onchange_l10n_pe_edi_picking_starting_point_province_id(self):
        if self.l10n_pe_edi_picking_starting_point_province_id and self.l10n_pe_edi_picking_starting_point_province_id.state_id:
            self.l10n_pe_edi_picking_starting_point_state_id = self.l10n_pe_edi_picking_starting_point_province_id.state_id
        res = {}
        res["domain"] = {}
        res["domain"]["l10n_pe_edi_picking_starting_point_district_id"] = []
        if self.l10n_pe_edi_picking_starting_point_province_id:
            res["domain"]["l10n_pe_edi_picking_starting_point_district_id"] += [("city_id", "=", self.l10n_pe_edi_picking_starting_point_province_id.id)]
        return res

    @api.onchange("l10n_pe_edi_picking_starting_point_state_id")
    def _onchange_l10n_pe_edi_picking_starting_point_state_id(self):
        if self.l10n_pe_edi_picking_starting_point_state_id and self.l10n_pe_edi_picking_starting_point_state_id.country_id:
            self.l10n_pe_edi_picking_starting_point_country_id = self.l10n_pe_edi_picking_starting_point_state_id.country_id
        res = {}
        res["domain"] = {}
        res["domain"]["l10n_pe_edi_picking_starting_point_province_id"] = []
        if self.l10n_pe_edi_picking_starting_point_state_id:
            res["domain"]["l10n_pe_edi_picking_starting_point_province_id"] += [("state_id", "=", self.l10n_pe_edi_picking_starting_point_state_id.id)]
        return res
    
    @api.onchange("l10n_pe_edi_picking_arrival_point_district_id")
    def _onchange_l10n_pe_edi_picking_arrival_point_district_id(self):
        if self.l10n_pe_edi_picking_arrival_point_district_id and self.l10n_pe_edi_picking_arrival_point_district_id.city_id:
            self.l10n_pe_edi_picking_arrival_point_province_id = self.l10n_pe_edi_picking_arrival_point_district_id.city_id

    @api.onchange("l10n_pe_edi_picking_arrival_point_province_id")
    def _onchange_l10n_pe_edi_picking_arrival_point_province_id(self):
        if self.l10n_pe_edi_picking_arrival_point_province_id and self.l10n_pe_edi_picking_arrival_point_province_id.state_id:
            self.l10n_pe_edi_picking_arrival_point_state_id = self.l10n_pe_edi_picking_arrival_point_province_id.state_id
        res = {}
        res["domain"] = {}
        res["domain"]["l10n_pe_edi_picking_arrival_point_district_id"] = []
        if self.l10n_pe_edi_picking_arrival_point_province_id:
            res["domain"]["l10n_pe_edi_picking_arrival_point_district_id"] += [("city_id", "=", self.l10n_pe_edi_picking_arrival_point_province_id.id)]
        return res

    @api.onchange("l10n_pe_edi_picking_arrival_point_state_id")
    def _onchange_l10n_pe_edi_picking_arrival_point_state_id(self):
        if self.l10n_pe_edi_picking_arrival_point_state_id and self.l10n_pe_edi_picking_arrival_point_state_id.country_id:
            self.l10n_pe_edi_picking_arrival_point_country_id = self.l10n_pe_edi_picking_arrival_point_state_id.country_id
        res = {}
        res["domain"] = {}
        res["domain"]["l10n_pe_edi_picking_arrival_point_province_id"] = []
        if self.l10n_pe_edi_picking_arrival_point_state_id:
            res["domain"]["l10n_pe_edi_picking_arrival_point_province_id"] += [("state_id", "=", self.l10n_pe_edi_picking_arrival_point_state_id.id)]
        return res

    @api.depends("l10n_pe_edi_picking_starting_point_district_id")
    def _compute_starting_point_ubigeo(self):
        for rec in self:
            rec.l10n_pe_edi_picking_starting_point_ubigeo = (
                rec.l10n_pe_edi_picking_starting_point_district_id
                and rec.l10n_pe_edi_picking_starting_point_district_id.code
                or False
            )

    @api.depends("partner_id")
    def _compute_arrival_point(self):
        for rec in self:
            if rec.company_id.l10n_pe_edi_picking_default_auto_field_arrival_point:
                rec.l10n_pe_edi_picking_arrival_point_id = (
                    rec.partner_id and rec.partner_id or False
                )

    @api.depends("l10n_pe_edi_picking_arrival_point_id")
    def _compute_arrival_point_data(self):
        for rec in self:
            rec.l10n_pe_edi_picking_arrival_point_country_id = (
                rec.l10n_pe_edi_picking_arrival_point_id
                and rec.l10n_pe_edi_picking_arrival_point_id.country_id
                and rec.l10n_pe_edi_picking_arrival_point_id.country_id.id
                or False
            )
            rec.l10n_pe_edi_picking_arrival_point_state_id = (
                rec.l10n_pe_edi_picking_arrival_point_id
                and rec.l10n_pe_edi_picking_arrival_point_id.state_id
                and rec.l10n_pe_edi_picking_arrival_point_id.state_id.id
                or False
            )
            rec.l10n_pe_edi_picking_arrival_point_province_id = (
                rec.l10n_pe_edi_picking_arrival_point_id
                and rec.l10n_pe_edi_picking_arrival_point_id.city_id
                and rec.l10n_pe_edi_picking_arrival_point_id.city_id.id
                or False
            )
            rec.l10n_pe_edi_picking_arrival_point_district_id = (
                rec.l10n_pe_edi_picking_arrival_point_id
                and rec.l10n_pe_edi_picking_arrival_point_id.l10n_pe_district
                and rec.l10n_pe_edi_picking_arrival_point_id.l10n_pe_district.id
                or False
            )
            rec.l10n_pe_edi_picking_arrival_point_street = (
                rec.l10n_pe_edi_picking_arrival_point_id
                and rec.l10n_pe_edi_picking_arrival_point_id.street
                and rec.l10n_pe_edi_picking_arrival_point_id.street
                or False
            )

    @api.depends("l10n_pe_edi_picking_arrival_point_district_id")
    def _compute_arrival_point_ubigeo(self):
        for rec in self:
            rec.l10n_pe_edi_picking_arrival_point_ubigeo = (
                rec.l10n_pe_edi_picking_arrival_point_district_id
                and rec.l10n_pe_edi_picking_arrival_point_district_id.code
                or False
            )

    @api.onchange(
        "l10n_pe_edi_picking_carrier_document_type",
        "l10n_pe_edi_picking_carrier_doc_number",
    )
    def _onchange_carrier(self):
        res_partner = self.env["res.partner"]
        company = self.env.company
        self.l10n_pe_edi_picking_carrier_name = (
            self.l10n_pe_edi_picking_carrier_id
            and self.l10n_pe_edi_picking_carrier_id.name
            or ""
        )
        if (
            self.l10n_pe_edi_picking_carrier_document_type
            and self.l10n_pe_edi_picking_carrier_doc_number
        ):
            if (
                getattr(company, "l10n_pe_dni_validation", False)
                and self.l10n_pe_edi_picking_carrier_document_type == "1"
            ):
                result = getattr(res_partner, "l10n_pe_dni_connection", False)(
                    self.l10n_pe_edi_picking_carrier_doc_number
                )
                self.l10n_pe_edi_picking_carrier_name = (
                    result and str(result.get("nombre", False) or "").strip() or ""
                )
            if (
                getattr(company, "l10n_pe_ruc_validation", False)
                and self.l10n_pe_edi_picking_carrier_document_type == "6"
            ):
                result = getattr(res_partner, "l10n_pe_ruc_connection", False)(
                    self.l10n_pe_edi_picking_carrier_doc_number
                )
                self.l10n_pe_edi_picking_carrier_name = (
                    result and str(result.get("business_name", '')).strip() or ""
                )

    @api.onchange(
        "l10n_pe_edi_picking_driver_document_type",
        "l10n_pe_edi_picking_driver_doc_number",
    )
    def _onchange_driver(self):
        res_partner = self.env["res.partner"]
        company = self.env.company
        driver_name = (
            self.l10n_pe_edi_picking_driver_id
            and self.l10n_pe_edi_picking_driver_id.name
            or ""
        )
        self.l10n_pe_edi_picking_driver_name = " ".join(driver_name.split(" ")[2:])
        self.l10n_pe_edi_picking_driver_last_name = " ".join(driver_name.split(" ")[:2])
        if (
            self.l10n_pe_edi_picking_driver_document_type
            and self.l10n_pe_edi_picking_driver_doc_number
        ):
            if (
                getattr(company, "l10n_pe_dni_validation", False)
                and self.l10n_pe_edi_picking_driver_document_type == "1"
            ):
                result = getattr(res_partner, "l10n_pe_dni_connection", False)(
                    self.l10n_pe_edi_picking_driver_doc_number
                )
                driver_name = (
                    result and str(result.get("nombre", False) or "").strip() or ""
                )
                self.l10n_pe_edi_picking_driver_complete_name = driver_name
                self.l10n_pe_edi_picking_driver_name = " ".join(
                    driver_name.split(" ")[2:]
                )
                self.l10n_pe_edi_picking_driver_last_name = " ".join(
                    driver_name.split(" ")[:2]
                )
            if (
                getattr(company, "l10n_pe_ruc_validation", False)
                and self.l10n_pe_edi_picking_driver_document_type == "6"
            ):
                result = getattr(res_partner, "l10n_pe_ruc_connection", False)(
                    self.l10n_pe_edi_picking_driver_doc_number
                )
                driver_name = (
                    result
                    and str(result.get("business_name", False) or "").strip()
                    or ""
                )
                self.l10n_pe_edi_picking_driver_name = " ".join(
                    driver_name.split(" ")[2:]
                )
                self.l10n_pe_edi_picking_driver_last_name = " ".join(
                    driver_name.split(" ")[:2]
                )

    def _get_description_without_product_code(self, product, description, lot_id=False):
        if product and product.default_code:
            description = (
                str(description).replace("[" + product.default_code + "]", "").strip()
            )
        if lot_id:
            description = " ".join(
                [description, (lot_id and _("LOT: ") + lot_id.name or "")]
            )
        return description

    def _get_document_type_description(self, doc_type):
        for (x, y) in PARTNER_DOCUMENT_TYPE:
            if doc_type == x:
                return y
        return ""

    def _get_l10n_pe_edi_picking_name_split(self):
        serie = ""
        number = 0
        if self.l10n_pe_edi_picking_name:
            picking_name = self.l10n_pe_edi_picking_name.split("-")
            if len(picking_name) == 2:
                serie = picking_name[0]
                number = int(picking_name[1])
        return serie, number

    def _get_partner_address_odoofact(self, partner):
        if not partner:
            return ""
        return (
            (partner.street or "")
            + (partner.l10n_pe_district and ", " + partner.l10n_pe_district.name or "")
            + (partner.city_id and ", " + partner.city_id.name or "")
            + (partner.state_id and ", " + partner.state_id.name or "")
            + (partner.country_id and ", " + partner.country_id.name or "")
        )

    def convert_date_to_timezone(self, date_time):
        if self.env.user.tz:
            tz = pytz.timezone(self.env.user.tz)
            return pytz.utc.localize(date_time).astimezone(tz)
        else:
            return date_time

    def _get_document_values_generar_odoofact(self, ose_supplier):
        commercial_partner = self.l10n_pe_edi_picking_commercial_partner_id
        serie, number = self._get_l10n_pe_edi_picking_name_split()
        return {
            "operacion": "generar_guia",
            "tipo_de_comprobante": self.picking_type_id.l10n_pe_edi_request_document_type_id
            and self.picking_type_id.l10n_pe_edi_request_document_type_id.code_of
            or 0,
            "serie": serie,
            "numero": number,
            "cliente_tipo_de_documento": self.l10n_pe_edi_picking_commercial_document_type
            or "",
            "cliente_numero_de_documento": commercial_partner.vat or "",
            "cliente_denominacion": commercial_partner.name or "",
            "cliente_direccion": self._get_partner_address_odoofact(commercial_partner),
            "cliente_email": commercial_partner.email or "",
            "fecha_de_emision": self.date_done
            and self.convert_date_to_timezone(self.date_done).strftime("%d-%m-%Y")
            or "",
            "observaciones": self.note
            and " ".join(BeautifulSoup(self.note, "html.parser").stripped_strings)
            or "",
            "motivo_de_traslado": self.l10n_pe_edi_picking_catalog_20_id
            and self.l10n_pe_edi_picking_catalog_20_id.code
            or "",
            "motivo_de_traslado_otros_descripcion": self.l10n_pe_edi_picking_catalog_20_others
            or "",
            "peso_bruto_total": self.l10n_pe_edi_picking_total_gross_weight,
            "peso_bruto_unidad_de_medida": self.l10n_pe_edi_picking_gross_weight_uom
            or "",
            "numero_de_bultos": self.l10n_pe_edi_picking_number_packages,
            "tipo_de_transporte": self.l10n_pe_edi_picking_catalog_18_code or "",
            "fecha_de_inicio_de_traslado": self.l10n_pe_edi_picking_start_transport_date
            and self.l10n_pe_edi_picking_start_transport_date.strftime("%d-%m-%Y")
            or "",
            "transportista_documento_tipo": self.l10n_pe_edi_picking_carrier_document_type
            or "",
            "transportista_documento_numero": self.l10n_pe_edi_picking_carrier_doc_number
            or "",
            "transportista_denominacion": self.l10n_pe_edi_picking_carrier_name or "",
            "transportista_placa_numero": self.l10n_pe_edi_picking_carrier_license_plate
            or "",
            "conductor_documento_tipo": self.l10n_pe_edi_picking_driver_document_type
            or "",
            "conductor_documento_numero": self.l10n_pe_edi_picking_driver_doc_number
            or "",
            "conductor_denominacion": self.l10n_pe_edi_picking_driver_complete_name
            or "",
            "conductor_nombre": self.l10n_pe_edi_picking_driver_name or "",
            "conductor_apellidos": self.l10n_pe_edi_picking_driver_last_name or "",
            "conductor_numero_licencia": self.l10n_pe_edi_picking_driver_license_number
            or "",
            "punto_de_partida_ubigeo": self.l10n_pe_edi_picking_starting_point_ubigeo
            or "",
            "punto_de_partida_direccion": self.l10n_pe_edi_picking_starting_point_street
            or "",
            "punto_de_partida_codigo_establecimiento_sunat": "",
            "punto_de_llegada_ubigeo": self.l10n_pe_edi_picking_arrival_point_ubigeo
            or "",
            "punto_de_llegada_direccion": self.l10n_pe_edi_picking_arrival_point_street
            or "",
            "punto_de_llegada_codigo_establecimiento_sunat": "",
            "enviar_automaticamente_al_cliente": self.l10n_pe_edi_shop_id
            and self.l10n_pe_edi_shop_id.send_email
            and "true"
            or "false",
            "codigo_unico": "%s|%s|%s-%s"
            % (
                "odoo",
                self.company_id
                and self.company_id.partner_id
                and self.company_id.partner_id.vat
                or "",
                serie,
                str(number),
            ),
            "items": getattr(self, "_get_lines_values_generar_%s" % (ose_supplier))(),
            'documento_relacionado': getattr(self, "_get_picking_invoice_values_%s" % (ose_supplier))(),
        }

    def _get_lines_values_generar_odoofact(self):
        return [
            {
                "unidad_de_medida": line.product_uom_id
                and (
                    line.product_uom_id.l10n_pe_edi_uom_code_id
                    and line.product_uom_id.l10n_pe_edi_uom_code_id.code
                    or False
                )
                or "NIU",
                "codigo": line.product_id.default_code or "",
                "descripcion": self._get_description_without_product_code(
                    line.product_id, line.product_id.display_name, line.lot_id
                ),
                "cantidad": line.quantity,
            }
            for line in self.move_line_ids.filtered(lambda x: x.quantity > 0)
        ]
    
    def _get_picking_invoice_values_odoofact(self):
        return [
            {
                "tipo": invoice.type,
                "serie": invoice.series,
                "numero": invoice.number,
            }
            for invoice in self.l10n_pe_edi_invoice_number_ids
        ]

    def _get_document_values_consultar_odoofact(self, ose_supplier):
        """
        Prepare the dict of values to create the request for checking
        the document status. Valid for Nubefact.
        """
        serie, number = self._get_l10n_pe_edi_picking_name_split()
        return {
            "operacion": "consultar_guia",
            "tipo_de_comprobante": self.picking_type_id.l10n_pe_edi_request_document_type_id
            and self.picking_type_id.l10n_pe_edi_request_document_type_id.code_of
            or 0,
            "serie": serie,
            "numero": str(number),
        }

    def convert_to_electronic(self):
        if self.state != "done":
            raise UserError(
                _("The document must be in a 'done' state to convert it to electronic.")
            )
        if not self.l10n_pe_edi_picking_enable_epicking:
            raise UserError(_("The picking type must have electronic guides enabled."))
        if (
            not self.l10n_pe_edi_picking_commercial_document_type
            or not self.l10n_pe_edi_picking_commercial_document_number
        ):
            raise UserError(
                _(
                    "The type of document or customer document number has not been registered."
                )
            )
        if not self.picking_type_id.l10n_pe_edi_picking_sequence_id:
            raise UserError(_("Electronic Guide sequence not registered."))
        if not self.l10n_pe_edi_picking_name:
            self.l10n_pe_edi_picking_name = (
                self.picking_type_id.l10n_pe_edi_picking_sequence_id.next_by_id()
            )
        self._create_edi_request()

    def _create_edi_request(self):
        if (
            self.l10n_pe_edi_picking_enable_epicking
            and self.l10n_pe_edi_shop_id
            and not self.l10n_pe_edi_request_id
        ):
            request_id = self.env["l10n_pe_edi.request"].create(
                {
                    "company_id": self.company_id.id,
                    "l10n_pe_edi_shop_id": self.l10n_pe_edi_shop_id.id,
                    "l10n_pe_edi_document_type": "09",
                    "document_number": self.l10n_pe_edi_picking_name,
                    "document_date": self.date_done,
                    "model": self._name,
                    "res_id": self.id,
                }
            )
            self.l10n_pe_edi_request_id = request_id.id

    def check_data_to_send(self):
        if not self.l10n_pe_edi_is_electronic:
            raise UserError(_("The Picking is not a Electronic Document"))
        if (
            not self.l10n_pe_edi_picking_carrier_document_type
            and not self.l10n_pe_edi_picking_carrier_doc_number
            and self.l10n_pe_edi_picking_catalog_18_code == "01"
        ):
            raise UserError(
                _("Carrier doesn't have document number or document type assigned")
            )
        if (
            not self.l10n_pe_edi_picking_driver_document_type
            and not self.l10n_pe_edi_picking_driver_doc_number
            and self.l10n_pe_edi_picking_catalog_18_code == "02"
        ):
            raise UserError(
                _("Driver doesn't  have document number or document type assigned")
            )
        if (
            self.l10n_pe_edi_picking_carrier_license_plate
            and not self.check_l10n_pe_edi_picking_carrier_license_plate(
                self.l10n_pe_edi_picking_carrier_license_plate
            )
        ):
            raise UserError(_("License Plate is not valid."))

    def check_l10n_pe_edi_picking_carrier_license_plate(
        self, l10n_pe_edi_picking_carrier_license_plate
    ):
        regex = r"^[0-9A-Za-z]+$"
        isValid = re.match(regex, l10n_pe_edi_picking_carrier_license_plate)
        return isValid

    def action_document_send(self):
        """
        This method creates the request to PSE/OSE provider
        """
        for rec in self.filtered(
            lambda x: x.state == "done"
            and x.l10n_pe_edi_is_electronic
            and not x.l10n_pe_edi_ose_accepted
        ):
            rec.l10n_pe_edi_request_id.action_api_connect("generar")
            if (
                rec.l10n_pe_edi_request_id.log_id
                and rec.l10n_pe_edi_request_id.log_id.json_response
            ):
                json_response = json.loads(
                    rec.l10n_pe_edi_request_id.log_id.json_response
                )
                if json_response.get("codigo", 0) == 23:
                    rec.l10n_pe_edi_request_id.action_api_connect("consultar")

    def action_document_check(self):
        """
        Send the request for Checking document status for electronic invoices
        """
        for rec in self.filtered(
            lambda x: x.state == "done"
            and x.l10n_pe_edi_is_electronic
            and x.l10n_pe_edi_ose_accepted
            and not x.l10n_pe_edi_sunat_accepted
        ):
            rec.l10n_pe_edi_request_id.action_api_connect("consultar")

    def action_open_edi_request(self):
        """
        This method opens the EDI request
        """
        self.ensure_one()
        if self.l10n_pe_edi_request_id:
            return {
                "name": _("EDI Request"),
                "view_mode": "form",
                "res_model": "l10n_pe_edi.request",
                "res_id": self.l10n_pe_edi_request_id.id,
                "type": "ir.actions.act_window",
            }
        return True
    
    def _get_qr_code_picking(self):
        log_id = False
        for rec in self.l10n_pe_edi_request_id:
            if rec.sunat_accepted == True:
                log_id = json.loads(rec.log_id.json_response)
                cadena_qr = log_id.get('cadena_para_codigo_qr', False)
                if cadena_qr:
                    return cadena_qr
                
    def action_mark_canceled_edi_picking(self):
        for picking in self:
            picking.write({'canceled_edi_picking_in_sunat': True})
                
    def action_canceled_edi_picking(self):
        action = {
            'name': _('Mark as Canceled in SUNAT'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.canceled.edi.picking',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }
        return action
