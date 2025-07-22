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

from odoo import models, fields, api, _

class EdiInvoiceNumber(models.Model):
    _name = 'l10n_pe_edi.invoice.number'
    _description = 'Invoice numbers'

    picking_id = fields.Many2one('stock.picking', string="Picking")
    series = fields.Char(string="Invoice Serial", help="Sintaxt serial FXXX or BXXX")
    number = fields.Char(string="Invoice Number", help="Sintaxt number 1, 10, 100")
    partner_id = fields.Many2one('res.partner', string="Client")
    invoice_id = fields.Many2one('account.move', string="Invoice", domain="[('state', '=', 'posted')]")
    type = fields.Selection([
        ('01','INVOICE'),
        ('03','BILL OF SALE'),
        ('09','SENDER REFERRAL GUIDE'),
        ('31','CARRIER REFERRAL GUIDE')],
        string="Type", default='01')
    sale_order_name = fields.Char(
        string="Sale Order Name", 
        related='picking_id.sale_id.name',
        store=True, 
        readonly=True
    )

    @api.onchange('picking_id')
    def _onchange_picking_id(self):
        if self.picking_id:
            self.partner_id = self.picking_id.partner_id.commercial_partner_id.id
    
    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        if self.invoice_id:
            if self.invoice_id.name:
                ref = self.invoice_id.name.split('-')
                if len(ref) == 2:
                    self.series = ref[0].strip()
                    self.number = ref[1].strip()
                else:
                    self.series = ''
                    self.number = ''
