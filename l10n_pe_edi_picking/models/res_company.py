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


class ResCompany(models.Model):
    _inherit = "res.company"
    
    # these fields will be deprecated -------------------------------------------------
    l10n_pe_edi_picking_partner_for_carrier_driver = fields.Boolean(
        string="Use partners for Carrier and Driver"
    )
    l10n_pe_edi_picking_partner_for_starting_arrival_point = fields.Boolean(
        string="Use partners for Starting and Arrival Point"
    )
    # ---------------------------------------------------------------------------------
