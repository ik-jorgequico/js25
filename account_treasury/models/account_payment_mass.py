# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare
from datetime import datetime
import unicodedata
import os
import logging
from os import path

_logger = logging.getLogger(__name__)


RUTA_BASE = '/tmp/'

class PaymentMass(models.Model):
    _name = 'account.payment.mass'
    _description = "Payment Mass"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string='Nombre', store=True)
    sequence = fields.Integer("secuencia")
    date = fields.Datetime("Fecha", required=True, default=datetime.now())
    
    sequence_id = fields.Char('Sequence', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    
    journal_id = fields.Many2one('account.journal', string='Diario de Pago', required=True, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    journal_type = fields.Selection(related="journal_id.type", string='Tipo de Diario de Pago')
    
    memo = fields.Char(string='Referencia', store=True, required=True)
    check_amount = fields.Monetary(string='Monto de Confirmación', required=True, compute="_compute_check_amount", store=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Tipo de Pago')
    state = fields.Selection([
        ('draft','Borrador'),
        ('toaprob', 'Por Aprobar'),
        ('aprob', 'Aprobado'),
        ('paid', 'Pagado'),
        ('cancel', 'Cancelled'),
    ], string='Estado', index=True, default='draft', tracking=True, copy=False)
    payment_date = fields.Date('Fecha de Pagos', required=True, default=datetime.now(), store=True)
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method')
    total_pay_amount = fields.Monetary(compute='_compute_pay_total', )
    
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], default='outbound' ,string='Payment Type', required=True)
    invoice_payments = fields.One2many('account.payment.mass.line', 'acc_payment_mass_id',string='Pagos')
    invoice_payments_inicial_ids = fields.One2many('account.payment.mass.inicial', 'acc_payment_mass_op_id',string='Pagos de Operación Inicial',readonly=True)
    invoice_payments_final_ids = fields.One2many('account.payment.mass.final', 'acc_payment_mass_op_id',string='Pagos de Operación Final', readonly=True)
    payment_ids = fields.One2many('account.payment','mass_id', string="Ids Pagos")
    currency_id = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id')
    currency_id1 = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id')

    txt_type = fields.Selection([('1','Proveedor'),('2','Varios'),],string='Formato Txt',default='1',tracking=True,store=True)
    
    def _compute_name(self):
        pag_prev = self.env['account.payment.mass'].search([('company_id','=',self.company_id.id),('sequence','>',0)], limit=1 , order='name desc')
        if not self.name:
            if not pag_prev:
                self.sequence = 1
            else:
                self.sequence = int(pag_prev.sequence) + 1
            
            if len(str(self.sequence)) <= 4:
                self.name = "MASIVO/" + self.date.strftime("%Y") + "/" + self.date.strftime("%m") + "/" + str(self.sequence).zfill(4)
            elif  len(str(self.sequence)) > 4 and len(self.sequence) <= 6:
                self.name = "MASIVO/" + self.date.strftime("%Y") + "/" + self.date.strftime("%m") + "/" + str(self.sequence).zfill(6)

    @api.onchange('memo')
    def _onchange_memo(self):
        for line in self.invoice_payments:
            line.ref = self.memo

    @api.depends('invoice_payments.receiving_amt')
    def _compute_check_amount(self):
        if(self.invoice_payments):
            amount = 0
            for line in self.invoice_payments:
                amount += line.receiving_amt
            self.check_amount = amount

    def list_payments(self):
        self.ensure_one()
        domain = [('id', 'in', self.payment_ids.ids)]
        return {
            'name': 'Pagos',
            'domain': domain,
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': ""
        }

    @api.depends('journal_id')
    def _compute_currency_id(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id.id
                self.currency_id1 = self.journal_id.currency_id.id
            else:
                self.currency_id = self.journal_id.company_id.currency_id.id
                self.currency_id1 = False
        else:
            self.currency_id = False
            self.currency_id1 = False
    
    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        if not self.journal_id:
            self.hide_payment_method = True
            return
        if self.journal_id.type != 'bank':
            self.hide_payment_method = True
            self.payment_method_id = 1
        else:
            self.hide_payment_method = False
            self.payment_method_id = 1
    
    @api.depends('invoice_payments.receiving_amt')
    def _compute_pay_total(self):
        total_pay_amount = 0
        for line in self.invoice_payments:
            total_pay_amount += line.receiving_amt 
        self.total_pay_amount = total_pay_amount
    
    def ToAprob(self):
        if not self.invoice_payments:
            raise UserError(_("Por Favor, Crear algunas lineas de pagos"))
        if self.check_amount == 0.0:
            raise UserError(_("Error. El monto de Confirmación debe ser mayor a 0"))
        else:
            if float_compare(self.total_pay_amount, self.check_amount, precision_digits=2) != 0:
                raise UserError(_("Error. El monto a pagar debe ser igual al monto de confirmación"))
            else:
                for line in self.invoice_payments:
                    self.env['account.payment.mass.inicial'].create({
                        'invoice_id':line.invoice_id.id,
                        'currency_id':line.currency_id.id,
                        'partner_id':line.partner_id.id,
                        'monto_inicial':line.receiving_amt,
                        'monto_fact':line.balance_amt,
                        'acc_payment_mass_op_id':line.acc_payment_mass_id.id,
                        'account_bank':line.account_bank.id,
                        'account_id':line.account_id.id,
                        'tipo_abono_cuenta':line.tipo_abono_cuenta,
                        'bank_id':line.bank_id.id,
                        'currency_id':line.currency_id.id,
                        'move_line_id':line.move_line_id.id,
                        'ref':line.ref
                    })
                self.write({'state':'toaprob'})
    
    def backDraft(self):
        for line in self.invoice_payments:
            self.env['account.payment.mass.inicial'].search([('acc_payment_mass_op_id', '=', line.acc_payment_mass_id.id)]).unlink()

        for p in self.payment_ids:
            p.move_id.button_draft()
            _logger.warning(p.name)
            _logger.warning("borradoreando")
            p.unlink()
            _logger.warning("eliminado")

        self.write({'state':'draft'})
    
    def backMass(self):
        for line in self.invoice_payments:
            self.env['account.payment.mass.final'].search([('acc_payment_mass_op_id', '=', line.acc_payment_mass_id.id)]).unlink()
        self.write({'state':'toaprob'})

    
    def white_spaces(self, cad, cant, pos, char):
        space = ''
        for i in range(cant - len(str(cad))):
            space += char
        if pos == 'right':
            union = str(cad) + space 
            return union[0:cant]
        if pos == 'left':
            union = space + str(cad)
            return union[len(union) - cant: len(union)]
    
    def delete_tildes(self,cadena):
        s = ''.join((c for c in unicodedata.normalize('NFD',cadena) if unicodedata.category(c) != 'Mn'))
        return s
    
    def ExportTXT(self):
        res = []

        if len(self.invoice_payments_final_ids) <= 0:
            raise UserError("Por favor registre algun pago.")

        ''' AQUI SEPARAMOS PARA CADA FORMATO TXT POR BANCO'''
        '''SCOTIABANK'''
        if self.journal_id.bank_account_id.bank_id.code == 'scoti' and self.txt_type == '1': ##PARA FORMATO DE PROVEEDORES
            for invoice in self.invoice_payments_final_ids:
                ruc = self.white_spaces(str(invoice.partner_id.vat or ''),11, 'right', ' ')
                name_proveedor = self.white_spaces(str(invoice.partner_id.name or ''),60, 'right', ' ')
                ref_invoice = self.white_spaces(str(invoice.invoice_id.ref or ''),14, 'right', ' ')
                date_payment = self.white_spaces((self.payment_date.strftime("%Y%m%d") or ''),8, 'right', ' ')
                amount_to_pay = f"{int(round(invoice.monto_final * 100) or ''):011d}" ##11 ESPACIOS
                method = '4' if invoice.tipo_abono_cuenta == '99' else '2'
                payment_method = self.white_spaces((method or ''),1, 'right', ' ')
                account_bank_no_cci= self.white_spaces(str(invoice.account_bank.acc_number if invoice.tipo_abono_cuenta == '09' else '' or '') ,11, 'right', ' ') 
                email_proveedor = self.white_spaces(str(invoice.partner_id.email or '') ,30, 'right', ' ')
                account_bank = self.white_spaces(str(invoice.account_bank.cci if invoice.tipo_abono_cuenta == '99' else '' or '') ,30, 'right', ' ') 
                # Crear la línea sin limitar los caracteres de cada campo
                detail_line = ''.join([
                    ruc,
                    name_proveedor,
                    ref_invoice,
                    date_payment + amount_to_pay + payment_method +account_bank_no_cci,
                    email_proveedor,
                    account_bank,
                ])
                res.append(detail_line)
            # Nombre del archivo
            name = 'PROVEEDORES_' + self.journal_id.default_account_id.name + ' '+ self.payment_date.strftime("%Y%m%d")

        elif self.journal_id.bank_account_id.bank_id.code == 'scoti' and self.txt_type == '2': ##PARA FORMATO DE VARIOS
            for invoice in self.invoice_payments_final_ids:
                ruc = self.white_spaces(str(invoice.partner_id.vat or ''),8, 'right', ' ')
                name_proveedor = self.white_spaces(str(invoice.partner_id.name or ''),60, 'right', ' ')
                ref_invoice = self.white_spaces(str(invoice.ref or ''),20, 'right', ' ')
                date_payment = self.white_spaces((self.payment_date.strftime("%Y%m%d") or ''),8, 'right', ' ')
                amount_to_pay = f"{int(round(invoice.monto_final * 100) or ''):011d}" ##11 ESPACIOS
                method = '4' if invoice.tipo_abono_cuenta == '99' else '3'
                payment_method = self.white_spaces((method or ''),1, 'right', ' ')
                # email_proveedor = self.white_spaces(str(invoice.partner_id.email or '') ,30, 'right', ' ')
                account_bank = self.white_spaces(str(invoice.account_bank.acc_number if invoice.tipo_abono_cuenta == '09' else '' or '') ,26, 'right', ' ') 
                account_bank_cci = self.white_spaces(str(invoice.account_bank.cci if invoice.tipo_abono_cuenta == '99' else '' or '') ,20, 'right', ' ')
                # Crear la línea sin limitar los caracteres de cada campo
                detail_line = ''.join([
                    ruc,
                    name_proveedor,
                    ref_invoice,
                    date_payment + amount_to_pay + payment_method + account_bank + account_bank_cci,
                ])
                res.append(detail_line)

            # Nombre del archivo
            name = 'VARIOS_' + self.journal_id.default_account_id.name + ' '+ self.payment_date.strftime("%Y%m%d")

        else:
            name = ''
            res.append('NO HAY PLANTILLA PARA EL BANCO: ' + str(self.journal_id.bank_account_id.bank_id.name))

        # Guardar el archivo en el sistema
        file_path = f"{RUTA_BASE}{name}.txt"
        if path.exists(file_path):
            os.remove(file_path)

        with open(file_path, 'w') as f:
            for item in res:
                f.write("%s\n" % self.delete_tildes(item))

        # Devolver el archivo para su descarga
        return {
            'name': "Archivo banco",
            'type': 'ir.actions.act_url',
            'url': f'/download/txt?filename={name}.txt',
            'target': 'new',
        }
    
    def Aprob(self):
        if self.check_amount == 0.0:
            raise UserError(_("Error. El monto de Confirmación debe ser mayor a 0"))
        else:
            if float_compare(self.check_amount, self.total_pay_amount, precision_digits=2) != 0:
                raise UserError(_("Error. El monto a pagar debe ser igual al monto de Confirmación"))
        for line in self.invoice_payments:
            self.env['account.payment.mass.final'].create({
                'invoice_id':line.invoice_id.id,
                'currency_id':line.currency_id.id,
                'partner_id':line.partner_id.id,
                'monto_final':line.receiving_amt,
                'monto_fact':line.balance_amt,
                'acc_payment_mass_op_id':line.acc_payment_mass_id.id,
                'account_bank':line.account_bank.id,
                'account_id':line.account_id.id,
                'tipo_abono_cuenta':line.tipo_abono_cuenta,
                'bank_id':line.bank_id.id,
                'currency_id':line.currency_id.id,
                'move_line_id':line.move_line_id.id,
                'ref':line.ref
            })
        
        self._compute_name()
        self.state = 'aprob'
    
    def makePayments(self):
        move_line = self.env['account.move.line']
        precision = self.env['decimal.precision'].precision_get('Account')
        context = dict(self._context or {})
        context.update({'is_customer': False})
        if float_compare(self.total_pay_amount, self.check_amount, precision_digits=precision) != 0:
            raise ValidationError(_('Verification Failed! Total Invoices Amount and Check amount does not match!'))

        ##Eliminar los pagos realizados cuando se regrese
        # if len(self.payment_ids) :
        for p in self.payment_ids:
            p.move_id.button_draft()
            _logger.warning(p.name)
            _logger.warning("borradoreando")
            p.unlink()
            _logger.warning("eliminado")
        
        if self.invoice_payments:
            for line in self.invoice_payments:
                payment = self.env['account.payment'].create({
                    'partner_type': 'supplier',
                    'amount': self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt * self.currency_id._get_conversion_rate(self.currency_id, self.company_id.currency_id, self.company_id, self.payment_date) or line.receiving_amt,
                    'currency_id': self.currency_id.id,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'mass_id': self.id,
                    'partner_id': line.partner_id.id,
                    'payment_method_id': self.payment_method_id.id,
                    'payment_type':'outbound',
                    'ref':self.memo,
                })
                payment.action_post()
                for l in payment.move_id.line_ids:
                    l.name = str(line.invoice_id.name) + " - " +(str(line.invoice_id.ref) if line.invoice_id.ref else "")

                to_reconcile = payment.move_id.line_ids.filtered(lambda x:x.account_id.account_type == 'liability_payable')
                to_reconcile += line.invoice_id.line_ids.filtered(lambda x:x.account_id.account_type == 'liability_payable')
                to_reconcile.reconcile()

                # move_id = payment.move_id
                # move_id.button_draft()
                # move_id.write({
                #     'line_ids':[(5, _, _)],
                #     'ref':self.memo,
                #     'payment_id':False
                # })
                # credit_move_id = move_line.with_context(check_move_validity=False).create({
                #     'name': payment.name,
                #     'account_id': self.journal_id.suspense_account_id.id,
                #     'partner_id':line.partner_id.id,
                #     'currency_id':self.currency_id.id,
                #     'amount_currency':self.currency_id.id != self.company_id.currency_id.id and -self.check_amount or 0,
                #     'debit': 0.0,
                #     'move_id':move_id.id,
                #     'credit': self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt * self.currency_id._get_conversion_rate(self.currency_id,self.company_id.currency_id,self.company_id,self.payment_date) or line.receiving_amt,
                # })
                # move_line_ids =  []
                # move_line_ids.append(credit_move_id.id)
                # list_ids = []
                # list_invoice_payments=[]
                # if line.receiving_amt > 0 and line.invoice_id:
                #     list_invoice_payments.append(line.invoice_id.id)
                #     ids_to_reconcile = []
                #     debit_move_id = move_line.with_context(check_move_validity=False).create({
                #         'name': 'Pago a Proveedor '+line.invoice_id.name or '',
                #         'account_id': line.invoice_id.partner_id.property_account_payable_id.id,
                #         'partner_id':line.partner_id.id or False,
                #         'currency_id':self.currency_id.id,
                #         'amount_currency':self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt or 0,
                #         'credit': 0.0,
                #         'move_id':move_id.id,
                #         'debit': self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt * self.currency_id._get_conversion_rate(self.currency_id,self.company_id.currency_id,self.company_id,self.payment_date) or line.receiving_amt,
                #         'ref':line.ref,
                #     })
                #     ids_to_reconcile.append(debit_move_id.id)
                #     for x in line.invoice_id.line_ids:
                #         if x.account_id.id == line.invoice_id.partner_id.property_account_payable_id.id:
                #             ids_to_reconcile.append(x.id)
                    
                #     list_ids.append(ids_to_reconcile)
                
                # elif line.receiving_amt > 0 and line.account_id:
                #     ids_to_reconcile = []
                #     debit_move_id = move_line.with_context(check_move_validity=False).create({
                #         'name': 'Pago a Proveedor',
                #         'account_id': line.account_id.id,
                #         'partner_id':line.partner_id.id or False,
                #         'currency_id':self.currency_id.id,
                #         'amount_currency':self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt or 0,
                #         'credit': 0.0,
                #         'move_id':move_id.id,
                #         'debit': self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt * self.currency_id._get_conversion_rate(self.currency_id,self.company_id.currency_id,self.company_id,self.payment_date) or line.receiving_amt,
                #         'ref':line.ref,
                #     })
                
                # elif line.receiving_amt > 0 and line.move_line_id:
                #     ids_to_reconcile = []
                #     debit_move_id = move_line.with_context(check_move_validity=False).create({
                #         'name': 'Pago a Proveedor',
                #         'account_id': line.move_line_id.account_id.id,
                #         'partner_id':line.move_line_id.partner_id.id or False,
                #         'currency_id':self.currency_id.id,
                #         'amount_currency':self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt or 0,
                #         'credit': 0.0,
                #         'move_id':move_id.id,
                #         'debit': self.currency_id.id != self.company_id.currency_id.id and line.receiving_amt * self.currency_id._get_conversion_rate(self.currency_id,self.company_id.currency_id,self.company_id,self.payment_date) or line.receiving_amt,
                #         'ref':line.ref,
                #     })
                    
                #     ids_to_reconcile.append(debit_move_id.id)
                #     ids_to_reconcile.append(line.move_line_id.id)
                #     list_ids.append(ids_to_reconcile)
                
                # move_line_ids.append(debit_move_id.id)
                # move_id.write({'payment_id':payment.id})
                # move_id.action_post()
                
                # move_line.browse(list_ids).reconcile()
        
        self.write({'state':'paid'})

class PaymentMassInicial(models.Model):
    _name = 'account.payment.mass.inicial'
    _description = "Payment Mass Inicial"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'invoice_id'
    
    invoice_id = fields.Many2one('account.move', string="Factura", readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, readonly=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Proveedor", readonly=True)
    
    monto_fact = fields.Monetary(string="Monto de Factura",readonly=True)
    monto_inicial = fields.Monetary("Monto Inicial a Pagar", readonly=True)
    
    acc_payment_mass_op_id = fields.Many2one('account.payment.mass', string="Payment_ids")
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type')
    payment_difference = fields.Monetary(string='Monto Restante', compute='_compute_pay_total', readonly=True)
    account_bank = fields.Many2one('res.partner.bank', string='Cuentas Bancarias', readonly=True)
    
    state = fields.Selection(related='acc_payment_mass_op_id.state')
    
    bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True)
    tipo_abono_cuenta = fields.Selection([
        ('09', 'Abono en Cuenta'),
        # ('11', 'Cheque de Gerencia'),
        ('99', 'Interbancario')
    ], 'Tipo de Abono', required=True)
    account_id = fields.Many2one('account.account','Cuenta')
    account_dest_id = fields.Many2one('account.account', compute='_compute_destination_account_id')
    move_line_id = fields.Many2one('account.move.line', string='Apuntes', domain=[('credit', '>', 0), ('full_reconcile_id', '=', False), ('state', '=', 'posted'), ('journal_id.type', 'not in', ['bank','cash'])])
    ref = fields.Char('Referencia', related='invoice_id.ref')
    
    @api.depends('account_id','invoice_id')
    def _compute_destination_account_id(self):
        for line in self:
            if line.invoice_id:
                line.account_dest_id = line.invoice_id.line_ids[0].account_id.id
            elif line.account_id:
                line.account_dest_id = line.account_id.id
            else:
                line.account_dest_id = False
    
    @api.depends('monto_inicial','monto_fact')
    def _compute_pay_total(self):
        for line in self:
            if line.invoice_id:
                line.payment_difference = line.monto_fact - line.monto_inicial
            elif line.account_id:
                line.payment_difference = line.monto_inicial

class PaymentMassFinal(models.Model):
    _name = 'account.payment.mass.final'
    _description = 'Payment Mass Final'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'invoice_id'
    
    invoice_id = fields.Many2one('account.move', string="Factura", readonly=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, readonly=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Proveedor", readonly=True)
    
    monto_fact = fields.Monetary(string="Monto de Factura",readonly=True)
    monto_final = fields.Monetary("Monto Pagado", readonly=True)
    
    acc_payment_mass_op_id = fields.Many2one('account.payment.mass', string="Payment_ids")
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type')
    payment_difference = fields.Monetary(string='Monto Restante', compute='_compute_pay_total', readonly=True)
    account_bank = fields.Many2one('res.partner.bank',string='Cuentas Bancarias', readonly=True)
    
    state = fields.Selection(related='acc_payment_mass_op_id.state')
    
    bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True)
    tipo_abono_cuenta = fields.Selection([
        ("09","Abono en Cuenta"),
        # ("11","Cheque de Gerencia"),
        ("99","Interbancario")
    ], string="Tipo de Abono", required=True)
    account_id = fields.Many2one('account.account','Cuenta')
    account_dest_id = fields.Many2one('account.account',compute="_compute_destination_account_id")
    move_line_id = fields.Many2one('account.move.line', string="Apuntes", domain=[('credit', '>', 0), ('full_reconcile_id', '=', False), ('state', '=', 'posted'), ('journal_id.type', 'not in', ['bank','cash'])])
    ref = fields.Char('Referencia')
    
    @api.depends('account_id','invoice_id')
    def _compute_destination_account_id(self):
        for line in self:
            if line.invoice_id:
                line.account_dest_id = line.invoice_id.line_ids[0].account_id.id
            elif line.account_id:
                line.account_dest_id = line.account_id.id
            elif line.move_line_id:
                line.account_dest_id = line.move_line_id.account_id.id
    
    @api.depends('monto_final','monto_fact')
    def _compute_pay_total(self):
        for line in self:
            if line.invoice_id:
                line.payment_difference = line.monto_fact - line.monto_final
            elif line.account_id:
                line.payment_difference = line.monto_final

class PaymentMassLine(models.Model):
    _name = 'account.payment.mass.line'
    _description = 'Payment Mass Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'invoice_id'

    invoice_id = fields.Many2one('account.move', string="Factura")
    currency_id = fields.Many2one('res.currency', string='Moneda', required=True, tracking=True, default=lambda self: self.acc_payment_mass_id.journal_id.currency_id.id)
    partner_id = fields.Many2one('res.partner',string="Proveedor", required=True)
    balance_amt = fields.Monetary(related='invoice_id.amount_residual',string="Monto de Factura")
    receiving_amt = fields.Monetary("Monto a Pagar", required=True,  )
    acc_payment_mass_id = fields.Many2one('account.payment.mass', string="Payment_ids")
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type')
    payment_difference = fields.Float(string='Difference Amount', readonly=True)
    account_bank = fields.Many2one('res.partner.bank',string='Cuentas Bancarias')
    
    bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True)
    tipo_abono_cuenta = fields.Selection([
        ("09","Abono en Cuenta"),
        # ("11","Cheque de Gerencia"),
        ("99","Interbancario")
    ], string="Tipo de Abono", required=True)
    account_id = fields.Many2one('account.account','Cuenta')
    account_dest_id = fields.Many2one('account.account',compute="_compute_destination_account_id")
    
    move_line_id = fields.Many2one('account.move.line', string="Apuntes")
    ref = fields.Char('Referencia',store=True)
    pagare = fields.Char('Pagare')
    
    @api.onchange('balance_amt')
    def _onchange_balance_amt(self):
        if self.invoice_id:
            self.receiving_amt = self.balance_amt or 0
        else:
            self.receiving_amt = 0
    
    @api.depends('account_id','invoice_id')
    def _compute_destination_account_id(self):
        for line in self:
            if line.invoice_id:
                line.account_dest_id = line.invoice_id.account_id.id
            elif line.account_id:
                line.account_dest_id = line.account_id.id
            elif line.move_line_id:
                line.account_dest_id = line.move_line_id.account_id.id
    
    @api.onchange('receiving_amt')
    def _onchange_amount(self):
        if self.invoice_id:
            self.payment_difference = self.balance_amt - self.receiving_amt
        elif self.account_id:
            self.payment_difference = self.receiving_amt
    
    @api.onchange('invoice_id','account_id','move_line_id')
    def _onchange_type_line(self):
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id.id
            self.currency_id = self.invoice_id.currency_id.id
            self.pagare = self.invoice_id.move_type in ('in_invoice', 'in_refund') and self.invoice_id.name or (self.invoice_id.edocument_number or self.invoice_id.number)
        elif self.account_id:
            self.payment_difference = self.receiving_amt
            self.currency_id = self.acc_payment_mass_id.currency_id.id
            self.pagare = ''
        elif self.move_line_id:
            self.partner_id = self.move_line_id.partner_id.id
            self.receiving_amt = self.move_line_id.amount_residual < 0 and -self.move_line_id.amount_residual or self.move_line_id.amount_residual  
            self.payment_difference = self.receiving_amt
            self.currency_id = self.move_line_id.currency_id and self.move_line_id.currency_id.id or False
            self.pagare = self.move_line_id.pagare

# class AccountPaymentMass(models.Model):
#     _name = 'account.payment.mass'
#     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
#     _description = "Payment Mass"
    
#     name = fields.Char('Nombre', store=True, copy=False)
#     sequence = fields.Integer("secuencia")
#     date = fields.Datetime("Fecha", required=True, default=datetime.now(),store=True)
    
#     sequence_id = fields.Char('Sequence', readonly=True)
#     company_id = fields.Many2one('res.company', 'Compañía', required=True, default=lambda self: self.env.company,store=True)
    
#     journal_id = fields.Many2one('account.journal', 'Diario de Pago', required=True, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]",store=True)
#     journal_type = fields.Selection(related="journal_id.type", string='Tipo de Diario de Pago',store=True)
    
#     memo = fields.Char('Referencia', store=True, required=True)
#     check_amount = fields.Monetary('Monto de Confirmación', required=True, compute="_compute_check_amount", store=True)
#     payment_method_id = fields.Many2one('account.payment.method', 'Tipo de Pago')
#     state = fields.Selection([
#         ('draft','Borrador'),
#         ('toaprob', 'Por Aprobar'),
#         ('aprob', 'Aprobado'),
#         ('paid', 'Pagado'),
#         ('cancel', 'Cancelled'),
#     ], 'Estado', index=True, default='draft', tracking=True, copy=False,store=True)
#     payment_date = fields.Date('Fecha de Pagos', required=True, default=datetime.now(), store=True)
#     hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method')
#     total_pay_amount = fields.Monetary(compute='_compute_pay_total',store=True)
    
#     payment_type = fields.Selection([
#         ('outbound', 'Send Money'),
#         ('inbound', 'Receive Money'),
#     ], 'Payment Type', default='outbound', required=True,store=True)
    
#     invoice_payments = fields.One2many('account.payment.mass.line', 'acc_payment_mass_id', string='Pagos')
#     invoice_payments_inicial_ids = fields.One2many('account.payment.mass.inicial', 'acc_payment_mass_op_id', string='Pagos de Operación Inicial',readonly=True)
#     invoice_payments_final_ids = fields.One2many('account.payment.mass.final', 'acc_payment_mass_op_id', string='Pagos de Operación Final', readonly=True)
#     payment_ids = fields.One2many('account.payment','mass_id', string="Ids Pagos")
#     currency_id = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id',store=True)
#     currency_id1 = fields.Many2one(comodel_name='res.currency', compute='_compute_currency_id',store=True)
    
#     def _compute_name(self):
#         if not self.name:
#             pag_prev = self.search([
#                 ('company_id', '=', self.company_id.id),
#                 ('sequence', '>', 0),
#             ], limit=1, order='name desc')
        
#             self.sequence = int(pag_prev.sequence) + 1 if pag_prev else 1
            
#             year_month = self.date.strftime("%Y/%m")
#             sequence_str = str(self.sequence).zfill(6 if self.sequence > 9999 else 4)
#             self.name = f"MASIVO/{year_month}/{sequence_str}"
    
#     @api.onchange('memo')
#     def _onchange_memo(self):
#         for line in self.invoice_payments:
#             line.ref = self.memo
    
#     @api.depends('invoice_payments.receiving_amt')
#     def _compute_check_amount(self):
#         if(self.invoice_payments):
#             amount = 0
#             for line in self.invoice_payments:
#                 amount += line.receiving_amt
#             self.check_amount = amount
    
#     def list_payments(self):
#         self.ensure_one()
#         domain = [('id', 'in', self.payment_ids.ids)]
#         return {
#             'name': 'Pagos',
#             'domain': domain,
#             'res_model': 'account.payment',
#             'type': 'ir.actions.act_window',
#             'view_id': False,
#             'view_mode': 'tree,form',
#             'view_type': 'form',
#             'limit': 80,
#             'context': ""
#         }
    
#     @api.depends('journal_id')
#     def _compute_currency_id(self):
#         if self.journal_id:
#             if self.journal_id.currency_id:
#                 self.currency_id = self.journal_id.currency_id.id
#                 self.currency_id1 = self.journal_id.currency_id.id
#             else:
#                 self.currency_id = self.journal_id.company_id.currency_id.id
#                 self.currency_id1 = False
#         else:
#             self.currency_id = False
#             self.currency_id1 = False
    
#     @api.depends('journal_id')
#     def _compute_hide_payment_method(self):
#         if not self.journal_id:
#             self.hide_payment_method = True
#             return
#         if self.journal_id.type != 'bank':
#             self.hide_payment_method = True
#             self.payment_method_id = 1
#         else:
#             self.hide_payment_method = False
#             self.payment_method_id = 1
    
#     @api.depends('invoice_payments.receiving_amt')
#     def _compute_pay_total(self):
#         total_pay_amount = 0
#         for line in self.invoice_payments:
#             total_pay_amount += line.receiving_amt 
#         self.total_pay_amount = total_pay_amount
    
#     def to_aprob(self):
#         if not self.invoice_payments:
#             raise UserError("Por Favor, Crear algunas lineas de pagos")
#         if self.check_amount == 0.0:
#             raise UserError("Error. El monto de Confirmación debe ser mayor a 0")
#         else:
#             if float_compare(self.total_pay_amount, self.check_amount, precision_digits=2) != 0:
#                 raise UserError("Error. El monto a pagar debe ser igual al monto de confirmación")
#             else:
#                 for line in self.invoice_payments:
#                     self.env['account.payment.mass.inicial'].create({
#                         'invoice_id':line.invoice_id.id,
#                         'currency_id':line.currency_id.id,
#                         'partner_id':line.partner_id.id,
#                         'monto_inicial':line.receiving_amt,
#                         'monto_fact':line.balance_amt,
#                         'acc_payment_mass_op_id':line.acc_payment_mass_id.id,
#                         'account_bank':line.account_bank.id,
#                         'account_id':line.account_id.id,
#                         'tipo_abono_cuenta':line.tipo_abono_cuenta,
#                         'bank_id':line.bank_id.id,
#                         'currency_id':line.currency_id.id,
#                         'move_line_id':line.move_line_id.id,
#                         'ref':line.ref
#                     })
#                 self.write({'state':'toaprob'})
    
#     def back_draft(self):
#         for line in self.invoice_payments:
#             self.env['account.payment.mass.inicial'].search([('acc_payment_mass_op_id', '=', line.acc_payment_mass_id.id)]).unlink()
#         self.write({'state':'draft'})
    
#     def back_mass(self):
#         for line in self.invoice_payments:
#             self.env['account.payment.mass.final'].search([('acc_payment_mass_op_id', '=', line.acc_payment_mass_id.id)]).unlink()
#         self.write({'state':'toaprob'})
    
#     def convert_str(self, s):
#         return s and str(s) or ' '
    
#     def white_spaces(self, cad, cant, pos, char):
#         space = ''
#         for i in range(cant - len(str(cad))):
#             space += char
#         if pos == 'right':
#             union = str(cad) + space 
#             return union[0:cant]
#         if pos == 'left':
#             union = space + str(cad)
#             return union[len(union) - cant: len(union)]
    
#     def delete_tildes(self,cadena):
#         s = ''.join((c for c in unicodedata.normalize('NFD',cadena) if unicodedata.category(c) != 'Mn'))
#         return s
    
#     def name_export(self, cod, field):
#         list_names = [
#             ('PLANILLAS_Scotiabank_', 9),
#             ('PROVEEDORES', 2),
#             ('IBK', 3),
#         ]
#         for i in list_names:
#             if i[1] == cod:
#                 name = i[0] + field
#         return name
    
#     def export_txt(self):
#         res = []
#         lines_control_register = {}
#         lines_detail_register = {}
#         lines_final_register = {}
#         nap=0
#         total=0
#         sequence = 0
#         total_abonos = 0
#         total_cargo = 0
#         total_control = 0
#         if self.journal_id.bank_account_id.bank_id.code == '2':
#             count = 0
#             for invoice in self.invoice_payments_final_ids:
#                 count += 1
#                 nap += invoice.monto_final
#                 total += invoice.monto_final
#                 if invoice.bank_id != self.journal_id.bank_id:
#                     total_abonos += float(invoice.account_bank.cci_number[10:])
#                 else:
#                     total_abonos += float(invoice.account_bank.acc_number[3:])
            
#             header_register = '1'
#             fertilizers_quantity = self.white_spaces(count, 6, 'left', '0')
#             date_of_process = self.payment_date.strftime("%Y%m%d")
#             account_type_charge = self.white_spaces('C',1, 'right', ' ')
#             currency = '1001' if self.journal_id and self.journal_id.currency_id and self.journal_id.currency_id.name=='USD' else '0001'
#             account_number_charge = self.white_spaces(self.journal_id.bank_account_id.acc_number, 20, 'right', ' ')
#             total_amount_return = self.white_spaces("%.2f" % round(total, 2), 17, 'left', '0')
#             reference_sheet = self.white_spaces('PAGO PROVEEDOR', 40, 'right', ' ')
#             total_control = self.white_spaces(int(total_cargo+total_abonos), 15, 'left','0')
            
#             lines_control_register[1] = [
#                 self.convert_str(header_register),
#                 self.convert_str(fertilizers_quantity),
#                 self.convert_str(date_of_process),
#                 self.convert_str(account_type_charge),
#                 self.convert_str(currency),
#                 self.convert_str(account_number_charge),
#                 self.convert_str(total_amount_return),
#                 self.convert_str(reference_sheet),
#                 'N',
#                 self.convert_str(total_control),
#             ]

#             pos_i = 1
#             pos_f = 1
#             for i in lines_control_register[1]:
#                 pos_f = pos_i + len(i) - 1
#                 pos_i = pos_f + 1
            
#             for x in lines_control_register:
#                 elements = [
#                     lines_control_register[x][0],
#                     lines_control_register[x][1],
#                     lines_control_register[x][2],
#                     lines_control_register[x][3],
#                     lines_control_register[x][4],
#                     lines_control_register[x][5],
#                     lines_control_register[x][6],
#                     lines_control_register[x][7],
#                     lines_control_register[x][8],
#                     lines_control_register[x][9],
#                 ]
#                 res.append(''.join(elements))
            
#             for invoice in self.invoice_payments_final_ids:
#                 if invoice.account_bank.bank_id.code == '2':
#                     account_type = invoice.account_bank.account_type
#                     account_number_employee=invoice.account_bank.acc_number
#                 else:
#                     account_type = 'B'
#                     account_number_employee=invoice.account_bank.cci_number
#                 nap = 0
#                 nap += invoice.monto_final
#                 sequence += 1
#                 record_detail = '2'
#                 tipo_documento=invoice.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code
                
#                 if tipo_documento:
#                     if tipo_documento=='1':
#                         tipo_doc='1'
#                     elif tipo_documento=='4':
#                         tipo_doc='3'
#                     elif tipo_documento=='7':
#                         tipo_doc='4'
#                     elif tipo_documento=='6':
#                         tipo_doc='6'
#                     else:
#                         tipo_doc='7'
#                 else:
#                     tipo_doc='7'
                
#                 subscription_account_type = self.white_spaces(account_type, 1, 'right', ' ')
#                 subscription_account_number = self.white_spaces(account_number_employee, 20, 'right', ' ')
#                 type_document = self.white_spaces(tipo_doc, 1, 'right', ' ')
#                 number_document_employee = self.white_spaces(tipo_documento, 12, 'right', ' ')
#                 correlative_document = self.white_spaces('   ', 3, 'right', ' ')
#                 name_employee = self.white_spaces(str(invoice.partner_id.name), 75, 'right', ' ')
#                 beneficiary_reference = self.white_spaces('Referencia Beneficiario ' + str(tipo_documento), 40, 'right', ' ')
#                 company_reference = self.white_spaces('Ref Emp '+str(tipo_documento), 20, 'right', ' ')
#                 currency_detail = '1001' if invoice.currency_id and invoice.currency_id.name=='USD' else '0001'
#                 amount_to_pay = self.white_spaces("%.2f" % round(nap,3), 17, 'left', '0')
#                 flag_validate_idc = self.white_spaces('S', 1, 'right', ' ')
                
#                 code = self.convert_str(invoice.id) + self.convert_str(tipo_documento)
                
#                 lines_detail_register[code] = [
#                     self.convert_str(record_detail),
#                     self.convert_str(subscription_account_type),
#                     self.convert_str(subscription_account_number),
#                     '1',
#                     self.convert_str(type_document),
#                     self.convert_str(number_document_employee),
#                     self.convert_str(correlative_document),
#                     self.convert_str(name_employee),
#                     self.convert_str(beneficiary_reference),
#                     self.convert_str(company_reference),
#                     self.convert_str(currency_detail),
#                     self.convert_str(amount_to_pay),
#                     self.convert_str(flag_validate_idc),
#                     ]
#                 pos_i = 1
#                 pos_f = 1
#                 for i in lines_detail_register[code]:
#                     pos_f = pos_i + len(i) - 1
#                     pos_i = pos_f + 1
            
#             sequence = 0
#             for x in lines_detail_register:
#                 elements = [
#                     lines_detail_register[x][0],
#                     lines_detail_register[x][1],
#                     lines_detail_register[x][2],
#                     lines_detail_register[x][3],
#                     lines_detail_register[x][4],
#                     lines_detail_register[x][5],
#                     lines_detail_register[x][6],
#                     lines_detail_register[x][7],
#                     lines_detail_register[x][8],
#                     lines_detail_register[x][9],
#                     lines_detail_register[x][10],
#                     lines_detail_register[x][11],
#                     lines_detail_register[x][12],
#                 ]
#                 res.append(''.join(elements))
            
#             name = self.name_export(2, self.payment_date.strftime("%Y%m%d"))
        
#         else:
#             name = ''
#             res.append('NO HAY PLANTILLA PARA EL BANCO: ' + str(self.journal_id.bank_account_id.bank_id.name))
        
#         if os.path.exists(RUTA_BASE + name + ".txt"):
#             os.remove(RUTA_BASE + name + ".txt")
        
#         with open(RUTA_BASE + name + ".txt", 'w') as f:
#             for item in res:
#                 f.write("%s\n" % self.delete_tildes(item))
#             f.close()
        
#         return {
#             'name': "Archivo banco",
#             'type': 'ir.actions.act_url',
#             'url': '/download/txt?filename=%s' % (name + ".txt"),
#             'target': 'new',
#         }
    
#     def aprob(self):
#         if self.check_amount == 0.0:
#             raise UserError("Error. El monto de Confirmación debe ser mayor a 0")
        
#         if float_compare(self.check_amount, self.total_pay_amount, precision_digits=2) != 0:
#             raise UserError("Error. El monto a pagar debe ser igual al monto de Confirmación")
        
#         for line in self.invoice_payments:
#             self.env['account.payment.mass.final'].create({
#                 'invoice_id': line.invoice_id.id,
#                 'currency_id': line.currency_id.id,
#                 'partner_id': line.partner_id.id,
#                 'monto_final': line.receiving_amt,
#                 'monto_fact': line.balance_amt,
#                 'acc_payment_mass_op_id': line.acc_payment_mass_id.id,
#                 'account_bank': line.account_bank.id,
#                 'account_id': line.account_id.id,
#                 'tipo_abono_cuenta': line.tipo_abono_cuenta,
#                 'bank_id': line.bank_id.id,
#                 'currency_id': line.currency_id.id,
#                 'move_line_id': line.move_line_id.id,
#                 'ref': line.ref
#             })
        
#         self._compute_name()
#         self.state = 'aprob'
    
#     def make_payments(self):
#         move_line = self.env['account.move.line']
#         precision = self.env['decimal.precision'].precision_get('Account')
#         context = dict(self._context or {})
#         context.update({'is_customer': False})
        
#         if float_compare(self.total_pay_amount, self.check_amount, precision_digits=precision) != 0:
#             raise ValidationError(_('Verification Failed! Total Invoices Amount and Check amount does not match!'))
        
#         if self.invoice_payments:
#             for line in self.invoice_payments:
#                 amount = 0.00
#                 if line.currency_id.id != self.company_id.currency_id.id:
#                     currency_rate = self.env['res.currency']._get_conversion_rate(
#                                         from_currency=line.currency_id,
#                                         to_currency=self.company_id.currency_id,
#                                         company=self.company_id,
#                                         date=self.payment_date,
#                                     )
#                     amount += line.receiving_amt * currency_rate
#                 else:
#                     amount += line.receiving_amt
                
#                 payment = self.env['account.payment'].create({
#                     'partner_type': 'supplier',
#                     'amount': amount,
#                     'currency_id': self.currency_id.id,
#                     'journal_id': self.journal_id.id,
#                     'date': self.payment_date,
#                     'mass_id': self.id,
#                     'partner_id': line.partner_id.id,
#                     'payment_method_id': self.payment_method_id.id,
#                     'payment_type':'outbound',
#                 })
#                 payment.action_post()
#                 move_id = payment.move_id
#                 move_id.button_draft()
#                 move_id.write({
#                     'line_ids':[(5, _, _)],
#                     'ref':self.memo,
#                     'payment_id':False
#                 })
#                 credit_move_id = move_line.with_context(check_move_validity=False).create({
#                     'name': payment.name,
#                     'account_id': self.journal_id.suspense_account_id.id,
#                     'partner_id': line.partner_id.id,
#                     'currency_id':self.currency_id.id,
#                     'amount_currency':-amount,
#                     'debit': 0.0,
#                     'move_id': move_id.id,
#                     'credit': amount,
#                 })
#                 move_line_ids =  []
#                 move_line_ids.append(credit_move_id.id)
#                 list_ids = []
#                 list_invoice_payments=[]
#                 if line.receiving_amt > 0 and line.invoice_id:
#                     list_invoice_payments.append(line.invoice_id.id)
#                     ids_to_reconcile = []
#                     debit_move_id = move_line.with_context(check_move_validity=False).create({
#                         'name': 'Pago a Proveedor ' + line.invoice_id.name or '',
#                         'account_id': line.invoice_id.partner_id.property_account_payable_id.id,
#                         'partner_id': line.partner_id.id or False,
#                         'currency_id': self.currency_id.id,
#                         'amount_currency': amount, 
#                         'credit': 0.0,
#                         'move_id': move_id.id,
#                         'debit': amount,
#                         'ref': line.ref,
#                     })
#                     ids_to_reconcile.append(debit_move_id.id)
#                     for x in line.invoice_id.line_ids:
#                         if x.account_id.id == line.invoice_id.partner_id.property_account_payable_id.id:
#                             ids_to_reconcile.append(x.id)
                    
#                     list_ids.append(ids_to_reconcile)
                
#                 elif line.receiving_amt > 0 and line.account_id:
#                     ids_to_reconcile = []
#                     debit_move_id = move_line.with_context(check_move_validity=False).create({
#                         'name': 'Pago a Proveedor',
#                         'account_id': line.account_id.id,
#                         'partner_id': line.partner_id.id or False,
#                         'currency_id': self.currency_id.id,
#                         'amount_currency':amount, 
#                         'credit': 0.0,
#                         'move_id': move_id.id,
#                         'debit': amount, 
#                         'ref': line.ref,
#                     })
                
#                 elif line.receiving_amt > 0 and line.move_line_id:
#                     ids_to_reconcile = []
#                     debit_move_id = move_line.with_context(check_move_validity=False).create({
#                         'name': 'Pago a Proveedor',
#                         'account_id': line.move_line_id.account_id.id,
#                         'partner_id': line.move_line_id.partner_id.id or False,
#                         'currency_id': self.currency_id.id,
#                         'amount_currency': amount, 
#                         'credit': 0.0,
#                         'move_id': move_id.id,
#                         'debit': amount, 
#                         'ref': line.ref,
#                     })
                    
#                     ids_to_reconcile.append(debit_move_id.id)
#                     ids_to_reconcile.append(line.move_line_id.id)
#                     list_ids.append(ids_to_reconcile)
#                 move_line_ids.append(debit_move_id.id)
#                 move_id.write({'payment_id': payment.id})
#                 move_id.action_post()
#                 self.env['account.move.line'].browse(list_ids[0]).reconcile()
        
#         self.state ='paid'

#     def action_delete(self):
#         for rec in self:
#             rec.payment_ids.unlink()
    

# class PaymentMassInicial(models.Model):
#     _name = 'account.payment.mass.inicial'
#     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
#     _description = "Payment Mass Inicial"
#     _rec_name = 'invoice_id'
    
#     invoice_id = fields.Many2one('account.move', "Factura", readonly=True,store=True)
#     currency_id = fields.Many2one('res.currency', 'Moneda', required=True, store=True,readonly=True, tracking=True)
#     partner_id = fields.Many2one('res.partner', "Proveedor", readonly=True,store=True)
    
#     monto_fact = fields.Monetary("Monto de Factura",readonly=True,store=True)
#     monto_inicial = fields.Monetary("Monto Inicial a Pagar", readonly=True,store=True)
    
#     acc_payment_mass_op_id = fields.Many2one('account.payment.mass', "Payment_ids",store=True)
#     payment_method_id = fields.Many2one('account.payment.method', 'Payment Type',store=True)
#     payment_difference = fields.Monetary('Monto Restante', compute='_compute_pay_total', readonly=True,store=True)
#     account_bank = fields.Many2one('res.partner.bank', 'Cuentas Bancarias', readonly=True,store=True)
    
#     state = fields.Selection(related='acc_payment_mass_op_id.state',store=True)
    
#     bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True,store=True)
#     tipo_abono_cuenta = fields.Selection([
#         ('09', 'Abono en Cuenta'),
#         ('11', 'Cheque de Gerencia'),
#         ('99', 'Interbancario')
#     ], 'Tipo de Abono',store=True, required=True)
#     account_id = fields.Many2one('account.account','Cuenta',store=True)
#     account_dest_id = fields.Many2one('account.account', compute='_compute_destination_account_id',store=True)
#     move_line_id = fields.Many2one('account.move.line', 'Apuntes', 
#                                 domain=[('credit', '>', 0), ('full_reconcile_id', '=', False), ('state', '=', 'posted'), ('journal_id.type', 'not in', ['bank','cash'])],store=True)
#     ref = fields.Char(related='invoice_id.ref', string='Referencia',store=True)
    
#     @api.depends('account_id', 'invoice_id')
#     def _compute_destination_account_id(self):
#         for rec in self:
#             if rec.invoice_id:
#                 rec.account_dest_id = rec.invoice_id.line_ids.filtered(lambda x:x.account_type == 'liability_payable')[0].account_id.id
#             elif rec.account_id:
#                 rec.account_dest_id = rec.account_id.id
#             else:
#                 rec.account_dest_id = False
    
#     @api.depends('monto_inicial', 'monto_fact')
#     def _compute_pay_total(self):
#         for rec in self:
#             if rec.invoice_id:
#                 rec.payment_difference = rec.monto_fact - rec.monto_inicial
#             elif rec.account_id:
#                 rec.payment_difference = rec.monto_inicial
    

# class PaymentMassFinal(models.Model):
#     _name = 'account.payment.mass.final'
#     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
#     _description = 'Payment Mass Final'
#     _rec_name = 'invoice_id'
    
#     invoice_id = fields.Many2one('account.move', "Factura", readonly=True,store=True)
#     currency_id = fields.Many2one('res.currency', "Moneda", required=True,store=True, readonly=True, tracking=True)
#     partner_id = fields.Many2one('res.partner', "Proveedor",store=True, readonly=True)
    
#     monto_fact = fields.Monetary("Monto de Factura",readonly=True,store=True)
#     monto_final = fields.Monetary("Monto Pagado", readonly=True,store=True)
    
#     acc_payment_mass_op_id = fields.Many2one('account.payment.mass', "Payment_ids",store=True)
#     payment_method_id = fields.Many2one('account.payment.method', 'Payment Type',store=True)
#     payment_difference = fields.Monetary('Monto Restante', compute='_compute_pay_total', readonly=True,store=True)
#     account_bank = fields.Many2one('res.partner.bank', 'Cuentas Bancarias', readonly=True,store=True)
    
#     state = fields.Selection(related='acc_payment_mass_op_id.state',store=True)
    
#     bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True,store=True)
#     tipo_abono_cuenta = fields.Selection([
#         ("09","Abono en Cuenta"),
#         ("11","Cheque de Gerencia"),
#         ("99","Interbancario")
#     ], "Tipo de Abono", required=True,store=True)
#     account_id = fields.Many2one('account.account','Cuenta',store=True)
#     account_dest_id = fields.Many2one('account.account',compute="_compute_destination_account_id",store=True)
#     move_line_id = fields.Many2one('account.move.line', "Apuntes", 
#                                 domain=[('credit', '>', 0), ('full_reconcile_id', '=', False), ('state', '=', 'posted'), ('journal_id.type', 'not in', ['bank','cash'])],store=True)
#     ref = fields.Char('Referencia',store=True)
    
#     @api.depends('account_id','invoice_id')
#     def _compute_destination_account_id(self):
#         for rec in self:
#             if rec.invoice_id:
#                 rec.account_dest_id = rec.invoice_id.line_ids.filtered(lambda x:x.account_type == 'liability_payable')[0].account_id.id
#             elif rec.account_id:
#                 rec.account_dest_id = rec.account_id.id
#             elif rec.move_line_id:
#                 rec.account_dest_id = rec.move_line_id.account_id.id
    
#     @api.depends('monto_final','monto_fact')
#     def _compute_pay_total(self):
#         for rec in self:
#             if rec.invoice_id:
#                 rec.payment_difference = rec.monto_fact - rec.monto_final
#             elif rec.account_id:
#                 rec.payment_difference = rec.monto_final
    

# class PaymentMassLine(models.Model):
#     _name = 'account.payment.mass.line'
#     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
#     _description = 'Payment Mass Line'
#     _rec_name = 'invoice_id'

#     invoice_id = fields.Many2one('account.move', "Factura",store=True)
#     currency_id = fields.Many2one('res.currency', "Moneda", required=True, tracking=True, default=lambda self: self.acc_payment_mass_id.journal_id.currency_id.id,store=True)
#     partner_id = fields.Many2one('res.partner', "Proveedor", required=True,store=True)
#     balance_amt = fields.Monetary(related='invoice_id.amount_residual', string="Monto de Factura",store=True)
#     receiving_amt = fields.Monetary("Monto a Pagar", required=True,store=True)
#     acc_payment_mass_id = fields.Many2one('account.payment.mass', "Payment_ids",store=True)
#     payment_method_id = fields.Many2one('account.payment.method', "Payment Type",store=True)
#     payment_difference = fields.Float('Difference Amount', readonly=True,store=True)
#     account_bank = fields.Many2one('res.partner.bank', "Cuentas Bancarias",store=True)
    
#     bank_id = fields.Many2one(related='account_bank.bank_id', string="Banco", readonly=True,store=True)
#     tipo_abono_cuenta = fields.Selection([
#         ("09", "Abono en Cuenta"),
#         ("11", "Cheque de Gerencia"),
#         ("99", "Interbancario")
#     ], "Tipo de Abono", required=True,store=True)
#     account_id = fields.Many2one('account.account', 'Cuenta',store=True)
#     account_dest_id = fields.Many2one('account.account', compute="_compute_destination_account_id",store=True)
    
#     move_line_id = fields.Many2one('account.move.line', "Apuntes",store=True)
#     ref = fields.Char('Referencia', store=True)
#     pagare = fields.Char('Pagare',store=True)
    
#     @api.onchange('balance_amt')
#     def _onchange_balance_amt(self):
#         if self.invoice_id:
#             self.receiving_amt = self.balance_amt or 0
#         else:
#             self.receiving_amt = 0
    
#     @api.depends('account_id', 'invoice_id')
#     def _compute_destination_account_id(self):
#         for rec in self:
#             if rec.invoice_id:
#                 rec.account_dest_id = rec.invoice_id.line_ids.filtered(lambda x:x.account_type == 'liability_payable')[0].account_id.id
#             elif rec.account_id:
#                 rec.account_dest_id = rec.account_id.id
#             elif rec.move_line_id:
#                 rec.account_dest_id = rec.move_line_id.account_id.id
    
#     @api.onchange('receiving_amt')
#     def _onchange_amount(self):
#         if self.invoice_id:
#             self.payment_difference = self.balance_amt - self.receiving_amt
#         elif self.account_id:
#             self.payment_difference = self.receiving_amt
    
#     @api.onchange('invoice_id', 'account_id', 'move_line_id')
#     def _onchange_type_line(self):
#         if self.invoice_id:
#             self.partner_id = self.invoice_id.partner_id.id
#             self.currency_id = self.invoice_id.currency_id.id
#             self.pagare = self.invoice_id.move_type in ('in_invoice', 'in_refund') and self.invoice_id.name or (self.invoice_id.edocument_number or self.invoice_id.number)
#         elif self.account_id:
#             self.payment_difference = self.receiving_amt
#             self.currency_id = self.acc_payment_mass_id.currency_id.id
#             self.pagare = ''
#         elif self.move_line_id:
#             self.partner_id = self.move_line_id.partner_id.id
#             self.receiving_amt = self.move_line_id.amount_residual < 0 and -self.move_line_id.amount_residual or self.move_line_id.amount_residual  
#             self.payment_difference = self.receiving_amt
#             self.currency_id = self.move_line_id.currency_id and self.move_line_id.currency_id.id or False
#             self.pagare = self.move_line_id.pagare
