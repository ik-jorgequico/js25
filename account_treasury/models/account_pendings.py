# -*- coding: utf-8 -*-
from odoo import models, fields, api
# from odoo.osv.expression import OR
import hashlib

class AccountPendings(models.Model):
    _name = 'account.pendings'
    _description = 'Cuentas Pendientes'
    
    bank_line_id = fields.Many2one('account.bank.statement.line', string="Linea banco",store=True)
    name_statement = fields.Many2one('account.bank.statement', string="Estado de Cta",related='bank_line_id.statement_id',store=True)    
    journal_bank_id = fields.Many2one('account.journal', string='Banco', related='bank_line_id.journal_id',store=True)
    date = fields.Date('Fecha', related='bank_line_id.date', readonly=True,store=True)
    ref = fields.Char('N. Operacion', related='bank_line_id.ref',store=True)
    payment_ref = fields.Char('Etiqueta', related='bank_line_id.payment_ref',store=True)
    partner_id = fields.Many2one('res.partner', string='Socio', related='bank_line_id.partner_id',store=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', related='bank_line_id.currency_id',store=True)
    amount = fields.Monetary('Importe', currency_field='currency_id', related='bank_line_id.amount',store=True)
    
    expense_concept = fields.Many2one('expense.concept', string='Concepto de Gasto',store=True)
    account_zonal = fields.Many2one('account.zonal', string='Zonal',store=True)
    account_canal = fields.Many2one('account.canal', string='Canal',store=True)
    note = fields.Char('Nota')
    external_id = fields.Char('Identificación externa', compute='compute_external_id',store=True)
    
    #funciones para las cuentas pendientes de pagos de bancos
    def get_account_bank_statement(self):
        bank_lines = self.env['account.bank.statement.line'].search([('state','=','posted')])
        # Crear un conjunto de IDs de account.bank.statement.line actuales
        existing_bank_ids = set(bank_lines.ids)
        # Obtener solo los account.pendings que coinciden con los IDs de account.bank.statement.line
        existing_bank = self.search([('bank_line_id', 'in', list(existing_bank_ids))])
        existing_bank_dict = {rec.bank_line_id.id: rec for rec in existing_bank}
        
        records_to_create = []
        for bank in bank_lines:
            if bank.id in existing_bank_dict:
                # Si ya existe en account.pendings, actualizar
                record = existing_bank_dict[bank.id]
                if record:
                    record.write({
                        'bank_line_id': bank.id,
                    })
            else:
                records_to_create.append({
                    'bank_line_id': bank.id,
                })
        if records_to_create:
            self.create(records_to_create)
            
        # Eliminar los registros en account.pendings cuyo ID ya no está en account.bank.statement.line
        ids_to_remove = self.search([('bank_line_id', 'not in', list(existing_bank_ids))])
        if ids_to_remove:
            ids_to_remove.unlink()

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountPendings, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'tree':
            self.get_account_bank_statement()
        return res

    def _generate_external_id_odoo(self, record_id):
        model_name = self._name.replace('.', '_')
        hash_input = f"{record_id}".encode('utf-8')
        hash_suffix = hashlib.md5(hash_input).hexdigest()[:8]
        return f"{model_name}_{record_id}_{hash_suffix}"

    def _get_external_id_odoo(self):
        data_obj = self.env['ir.model.data']
        for record in self:
            if record:
                external_id = data_obj.search([('model', '=', self._name),
                                                ('res_id', '=', record.id)], limit=1)
                if not external_id:
                    new_name = self._generate_external_id_odoo(record.id)
                    external_id = data_obj.create({
                        'name': new_name,
                        'model': self._name,
                        'module': '__export__',
                        'res_id': record.id,
                        'noupdate': True,
                    })
                record.external_id = external_id.complete_name
            
    @api.depends('bank_line_id')
    def compute_external_id(self):
        for record in self:
            record._get_external_id_odoo()