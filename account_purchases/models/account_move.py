# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime


class AccountMove(models.Model):
    _inherit = 'account.move'
    _description = 'Account Move Inherit'
    
    invoice_date = fields.Date(default=datetime.now())
    seriecomp_sunat = fields.Char('Serie CPE',store=True)
    numcomp_sunat = fields.Char('Numero CPE',store=True)
    glosa_sunat = fields.Char('Glosa', index=True,store=True)
    detraction_type_id = fields.Many2one('l10n_pe_edi.catalog.54', 'Tipo Detracción', copy=False,store=True)
    num_det = fields.Char('Constancia Detraccion',store=True)
    date_det = fields.Date('Fecha de Pago Detraccion',store=True)
    percent_det = fields.Integer('Porcentaje',store=True) 
    entry_id = fields.Many2one('account.move' ,'Asiento Detracción',store=True,copy=False)
    am_det_parent = fields.Many2one('account.move', 'Padre Detracción', store=True)
    total_det = fields.Float('Total Detracción', compute='_get_total', digits=(12, 0),store=True)
    state_ple = fields.Selection([
        ('0', 'Comprobante de Pago o documento no da derecho al crédito fiscal.'),
        ('1', 'Comprobante de Pago o documento en el periodo que se emitió o que se pagó el impuesto, según corresponda, y da derecho al crédito fiscal.'),
        ('6', 'Fecha de emisión del Comprobante de Pago o de pago del impuesto, por operaciones que dan derecho a crédito fiscal, es anterior al periodo de anotación y esta se produce dentro de los doce meses siguientes a la emisión o pago del impuesto, según corresponda.'),
        ('7', 'La fecha de emisión del Comprobante de Pago o pago del impuesto, por operaciones que no dan derecho a crédito fiscal, es anterior al periodo de anotación y esta se produce luego de los doce meses siguientes a la emisión o pago del impuesto, según corresponda.'),
        ('9', 'Ajuste o rectificación en la anotación de la información de una operación registrada en un periodo anterior.'),
    ], 'Estado PLE Compras', compute='_compute_state_ple', store=True)
    convenio_nodom = fields.Many2one('l10n_pe_edi.table.25', 'Convenio Evitar Doble Tributación', store=True)
    type_profit_nodom = fields.Many2one('l10n_pe_edi.table.31', 'Tipo de Renta No Dom', store=True)
    op_nodom = fields.Boolean('Operacion No Domiciliado',store=True)
    state_ple_sale = fields.Selection([
        ('0', 'Operación (anotación optativa sin efecto en el IGV) corresponde al periodo.'),
        ('1', 'Operación (ventas gravadas, exoneradas, inafectas y/o exportaciones) corresponde al periodo, así como a las Notas de Crédito y Débito emitidas en el periodo.'),
        ('2', 'Documento ha sido inutilizado durante el periodo previamente a ser entregado, emitido o durante su emisión.'),
        ('8', 'Operación (ventas gravadas, exoneradas, inafectas y/o exportaciones) corresponde a un periodo anterior y NO ha sido anotada en dicho periodo.'),
        ('9', 'Operación (ventas gravadas, exoneradas, inafectas y/o exportaciones) corresponde a un periodo anterior y SI ha sido anotada en dicho periodo.'),
    ], "Estado ple Ventas", compute='_compute_state_ple_sale', store=True)
    amount_others_purchase = fields.Float('Otros Cargos (Compras)', compute='_compute_l10n_pe_edi_tax_totals')
    amount_expo = fields.Float('Exportacion', compute='_compute_l10n_pe_edi_tax_totals')
    l10n_pe_edi_amount_base = fields.Monetary(string="Base Amount", compute='_compute_l10n_pe_edi_tax_totals')

    reversal_type = fields.Char('Tipo de Origen', store=True)
    l10n_pe_edi_reversal_serie = fields.Char('Serie Doc Origen', store=True)
    l10n_pe_edi_reversal_number = fields.Char('Numero Doc Origen', store=True)
    l10n_pe_edi_reversal_date = fields.Date('Fecha Doc Origen', store=True)
    
    l10n_pe_edi_operation_type = fields.Selection([
        ('1', 'INTERNAL SALE'),
        ('2', 'EXPORTATION'),
        ('4', 'INTERNAL SALE - ADVANCES'),
        ('29', 'VENTAS NO DOMICILIADOS QUE NO CALIFICAN COMO EXPORTACIÓN'),
        ('30', 'OPERACIÓN SUJETA A DETRACCIÓN'),
        ('33', 'DETRACCIÓN - SERVICIOS DE TRANSPORTE CARGA'),
        ('34', 'OPERACIÓN SUJETA A PERCEPCIÓN'),
        ('32', 'DETRACCIÓN - SERVICIOS DE TRANSPORTE DE PASAJEROS'),
        ('31', 'DETRACCIÓN - RECURSOS HIDROBIOLÓGICOS'),
    ], string='Transaction type', help='Default 1, the others are for very special types of operations, do not hesitate to consult with us for more information', 
                                                default='1',store=True)
    
    @api.depends(
        "line_ids",
        "line_ids.display_type",
        "line_ids.tax_ids",
        "line_ids.tax_group_id",
        "line_ids.l10n_pe_edi_amount_free",
        "line_ids.price_unit",
    )
    def _compute_l10n_pe_edi_tax_totals(self):
        for move in self:
            sign = move.direction_sign
            amount_free = 0.0
            amount_exonerated = 0.0
            amount_unaffected = 0.0
            amount_igv = 0.0
            amount_isc = 0.0
            amount_icbper = 0.0
            amount_expo = 0.0
            amount_others_purchase = 0.0
            amount_base = 0.0
            
            for line in move.line_ids.filtered(lambda x: x.display_type == "product"):
                if move.is_invoice(True):
                    if any(tax.l10n_pe_edi_tax_code in ["9996"] for tax in line.tax_ids):
                        amount_free += line.l10n_pe_edi_amount_free
                    elif any(tax.l10n_pe_edi_tax_code in ["9995"] for tax in line.tax_ids):
                        amount_expo += line.price_subtotal
                    elif any(tax.l10n_pe_edi_tax_code in ["1000"] for tax in line.tax_ids):
                        amount_base += line.price_subtotal
                    elif any(tax.l10n_pe_edi_tax_code in ["9997"] for tax in line.tax_ids):
                        amount_exonerated += line.price_subtotal
                    elif any(tax.l10n_pe_edi_tax_code in ["9998"] for tax in line.tax_ids):
                        amount_unaffected += line.price_subtotal
                    elif any(tax.l10n_pe_edi_tax_code in ["9999"] for tax in line.tax_ids):
                        amount_others_purchase += line.price_subtotal
            
            for line in move.line_ids.filtered(lambda x: x.display_type == "tax"):
                if move.is_invoice(True):
                    if line.tax_group_id.name == "IGV":
                        amount_igv += line.amount_currency
                    if line.tax_group_id.name == "ISC":
                        amount_isc += line.amount_currency
                    if line.tax_group_id.name == "ICBPER":
                        amount_icbper += line.amount_currency
                    if line.tax_group_id.name == "EXP":
                        amount_expo += line.amount_currency
            
            move.l10n_pe_edi_amount_base = amount_base
            move.l10n_pe_edi_amount_free = amount_free
            move.l10n_pe_edi_amount_exonerated = amount_exonerated
            move.l10n_pe_edi_amount_unaffected = amount_unaffected
            move.amount_expo = amount_expo
            move.amount_others_purchase = amount_others_purchase
            
            move.l10n_pe_edi_amount_igv = sign * amount_igv
            # move.l10n_pe_edi_amount_isc = sign * amount_isc
            move.l10n_pe_edi_amount_icbper = sign * amount_icbper
    
    @api.depends('invoice_line_ids','invoice_date','date','l10n_latam_document_type_id')
    def _compute_state_ple(self):
        # TODO: revisar esto
        for move in self:
            if move.date and move.invoice_date and move.move_type in ['in_invoice', 'in_refund', 'in_receipt']:
                if move.l10n_latam_document_type_id.code not in ['91','97','98']:
                    if move.l10n_pe_edi_amount_unaffected != 0 and move.l10n_pe_edi_amount_igv == 0:
                        new_date = move.invoice_date + relativedelta(months=12)
                        move.state_ple = '7' if move.date >= new_date else '0'
                    elif move.l10n_pe_edi_amount_unaffected == 0 and move.l10n_pe_edi_amount_igv != 0:
                        if move.date.strftime("%m%Y") == move.invoice_date.strftime("%m%Y"):
                            move.state_ple = '1'
                        else:
                            new_date = move.invoice_date + relativedelta(months=12)
                            if move.date < new_date:
                                move.state_ple = '6'
                    else:
                        move.state_ple = '0'
                else:
                    move.state_ple = '0'
            else:
                move.state_ple = '0'
    
    @api.depends('invoice_line_ids','invoice_date','date','l10n_latam_document_type_id')
    def _compute_state_ple_sale(self):
        for move in self:
            if move.move_type in ['out_invoice', 'out_refund', 'out_receipt']:
                move.state_ple_sale = '2' if move.state == 'cancel' else '1'
    
    @api.onchange('l10n_latam_document_type_id')
    def _get_op_nodom(self):
        self.op_nodom = self.l10n_latam_document_type_id.code in ['91','97','98']
    
    @api.depends('detraction_type_id','invoice_line_ids.account_id','invoice_line_ids.name','invoice_line_ids.price_unit','invoice_line_ids.tax_ids')
    def _get_total(self):
        for rec in self:
            if rec.move_type == 'in_invoice' and len(rec.invoice_line_ids) > 0 and rec.detraction_type_id:
                if rec.currency_id == rec.company_id.currency_id :        
                    rec.total_det = round(rec.amount_total * (rec.detraction_type_id.rate / 100), 0)
                    rec.percent_det = rec.detraction_type_id.rate
                else:
                    new_amount = rec.currency_id._convert(self.amount_total, self.company_id.currency_id, rec.company_id, rec.invoice_date or fields.Date.context_today(self))
                    rec.total_det = round(new_amount * (rec.detraction_type_id.rate / 100), 0) 
                    rec.percent_det = rec.detraction_type_id.rate 
    
    @api.onchange('numcomp_sunat')
    def _get_doc_cpe(self):
        for rec in self:
            if rec.numcomp_sunat and rec.l10n_latam_document_type_id.code != '50':
                rec.numcomp_sunat = rec.numcomp_sunat.zfill(8)
            serie = rec.seriecomp_sunat
            num = rec.numcomp_sunat
            rec.ref = f"{serie}-{num}" if serie and num else ""
    
    def _repeat(self, string_to_repeat, length):
        multiple = int(length / len(string_to_repeat) + 1)
        repeated_string = string_to_repeat * multiple
        return repeated_string[:length]
    
    def _get_sequence_ple(self):
        sequence = 0
        for line in self.line_ids:
            sequence += 1
            sec = 5 - len(str(sequence))
            zerosec = self._repeat("0",sec)
            line.sequence_ple = "M" + zerosec + str(sequence)
    
    def action_post(self):
        res = super(AccountMove, self).action_post()
        self._get_sequence_ple()
        if self.detraction_type_id:
            self.create_detraction()
        return res
    
    def create_detraction(self):
        entry_count = self.env['account.move'].search_count([("am_det_parent","=",self.id)])
        if entry_count == 0:
            if self.total_det <= 0:
                raise UserError("No se puede generar una detraccion por pagar con monto negativo %s !!"  % (self.total_det))
            
            ac_journal = self.env['account.journal'].search([("is_detraction","=",True)])

            det_data = { 
                'am_det_parent': self.id,
                'ref': str(self.ref) + " - " + str(self.glosa_sunat),
                'date': self.date,
                'journal_id': ac_journal.id,
                'move_type': 'entry',
            }
            det_move = self.env['account.move'].create(det_data)
            det_move = det_move
            line_credit = {
                        'move_id' : det_move.id,
                        'account_id': ac_journal.account_det.id,
                        'partner_id': self.partner_id.id or False,
                        'name': self.glosa_sunat, 
                        'currency_id': self.company_id.currency_id.id or False,
                        'amount_currency': - self.total_det,
                        'debit': 0.00,
                        'credit': self.total_det,
                        'company_id': self.company_id.id,
                    }			
            line_debit = {
                        'move_id' : det_move.id,
                        'account_id': self.partner_id.property_account_payable_id.id,
                        'partner_id': self.partner_id.id or False,
                        'name': self.glosa_sunat, 
                        'currency_id': self.company_id.currency_id.id or False,
                        'amount_currency': self.total_det,
                        'debit': self.total_det,
                        'credit': 0.00,
                        'company_id': self.company_id.id,
                    }			
            det_move.write({'line_ids': [(0, 0, line_debit),(0, 0, line_credit)]})

            if det_move.state == 'draft':
                det_move.action_post()			
            self.entry_id = det_move.id
            # reconciliacion por target line	
            for move_line in det_move.line_ids:
                if not move_line.account_id.reconcile:
                    continue
                to_reconcile = move_line + self.line_ids.filtered(
                    lambda x: x.account_id.id == move_line.account_id.id)
                to_reconcile.reconcile()
    

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _description = "Account Move Line Inherit"

    sequence_ple = fields.Char('Secuencia PLE')
