# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2019-TODAY OPeru.
#    Author      :  Grupo Odoo S.A.C. (<http://www.operu.pe>)
#
#    This program is copyright property of the author mentioned above.
#    You can`t redistribute it and/or modify it.
#
###############################################################################

from odoo import api, fields, models, _

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'
    
    def _prepare_invoice_values(self, order, so_line):
        res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, so_line)
        res.update({
            'l10n_pe_edi_odoofact_operation_type': '4',
        })
        return res
