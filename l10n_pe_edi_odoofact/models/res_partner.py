###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from odoo import fields, models, api, _

class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_pe_edi_retention_type_id = fields.Many2one(
        comodel_name="l10n_pe_edi.catalog.23", string="Retention Type", copy=False
    )
