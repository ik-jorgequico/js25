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


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_pe_edi_picking_is_carrier = fields.Boolean(string="Is Carrier?")
    l10n_pe_edi_picking_license_plate = fields.Char(string="License Plate")
    l10n_pe_edi_picking_is_driver = fields.Boolean(string="Is Driver?")
    l10n_pe_edi_picking_license_number = fields.Char(string="License Number")
