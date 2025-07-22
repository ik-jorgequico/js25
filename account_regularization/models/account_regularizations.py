# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import datetime

class AccountRegularizations(models.Model):
	_name = "account.regularizations"
	_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
	_description = "Regularizacion de Cuentas Contables"
 
	date = fields.Date("Fecha", tracking=True)
	name = fields.Char("Nombre", compute='_compute_name')
	journal_id = fields.Many2one(comodel_name='account.journal', required=True, string='Diario Contable', store=True, tracking=True)
	company_id = fields.Many2one(comodel_name='res.company', string='Compañia', store=True, default=lambda self: self.env.company, tracking=True)
	currency_id = fields.Many2one(comodel_name='res.currency', string='Moneda', default=lambda self :self.env.company.currency_id,store=True, tracking=True)
	glosa_sunat = fields.Char(string="Glosa", index=True, tracking=True)
	state = fields.Selection(
		[('draft', 'Borrador'),
		('import', 'Importado'),
		('done', 'Publicado')],
		'Estado', readonly=True, default='draft', tracking=True)
	sequence = fields.Integer('Secuencia',store=True,default=1)
	entry_id = fields.Many2one('account.move' ,string = "Asiento Contable", tracking=True)

	child_ids = fields.One2many("account.regularizations.line","parent_id", string="Move lines") #Para modificar
	account_move_line = fields.Many2many('account.move.line', string='Asientos Contables') #Seleccionados

	def set_to_draft(self):
		for rec in self:
			rec.write({'state':'draft'})
   
	def set_to_import(self):
		for rec in self:
			rec.write({'state':'import'})

	def done(self):
		for rec in self:
			rec.write({'state':'done'})

	@api.depends('journal_id','date',)
	def _compute_name(self):
		for rec in self:
			if not rec.name and rec.date and rec.journal_id:
				pag_prev = rec.search_count([('company_id', '=', rec.company_id.id)])
				rec.sequence += int(pag_prev)
				year_month = rec.date.strftime("%Y/%m")
				sequence_str = str(rec.sequence).zfill(6 if rec.sequence > 9999 else 4)
				rec.name = f"REG/{year_month}/{sequence_str}"

	def compute_sheet(self):
		# target_move_line = self.env['account.move.line'].search([])
		line_list = []
		for element in self.child_ids:
			line_data = {
				'reg_aml_id': element.id,
				'name': element.name,
				'partner_id': element.partner_id.id or False,
				'currency_id': element.currency_id.id or False,
				"analytic_distribution": element.analytic_distribution,
				'debit': element.debit,
				'credit': element.credit,
				'account_id': element.account_id.id ,
				'amount_currency': element.amount_currency,
				'company_id': element.company_id.id,
				}
			line_list.append(line_data)
		moves_data = {
			'reg_am_id': self.id,
			'ref': self.glosa_sunat,
			'date': self.date,
			'journal_id': self.journal_id.id,
			'move_type': 'entry',
		}
		target_move = self.env['account.move'].create(moves_data)
		target_move.write({
						'line_ids': [(0, 0, i) for i in line_list]
					})
		if target_move.state == 'draft':
			target_move.action_post()
			self.entry_id = target_move.id
			self.done()
		# reconciliacion por target line	
		for move_line in self.entry_id.line_ids:
			if not move_line.account_id.reconcile:
				continue
			to_reconcile = move_line + self.child_ids.filtered_domain([('id','=', move_line.reg_aml_id.id)]).aml_id
			to_reconcile.reconcile()

	def compute_sheet_select(self):
		for rec in self:
			values = []
			for element in self.account_move_line:
				amount = rec._get_amount(element,rec)
				val = {
					'parent_id': rec.id,
					'name': rec.glosa_sunat,
					'aml_id': element.id,
					'name': element.name,
					'partner_id': element.partner_id.id or False,
					'currency_id': rec.currency_id.id or False,
					'amount_currency': amount,
					'debit': amount if amount > 0 else 0,
					'credit': amount if amount < 0 else 0,
					'account_id': element.account_id.id ,
					'company_id': rec.company_id.id,
				}
				values.append(val)
			self.env["account.regularizations.line"].create(values)
			self.set_to_import()
		return
	
	def _get_amount(self,line,parent):
		amount = 0
		if line.currency_id.id != parent.currency_id.id:
			currency_rate = self.env['res.currency']._get_conversion_rate(
				from_currency=line.currency_id,
				to_currency=parent.currency_id,
				company=parent.company_id,
				date=parent.date,
			)
			amount += line.amount_residual * currency_rate *-1
		else:
			amount += line.amount_residual *-1
		return amount

class AccountRegularizationsLine(models.Model):
	_name = "account.regularizations.line"
	_inherit = "analytic.mixin"
	_description = "Lineas de Regularizacion de Cuentas Contables"

	parent_id = fields.Many2one("account.regularizations", string="Asiento contable", ondelete='cascade', store=True,)
	aml_id = fields.Many2one('account.move.line', string='Apunte Contable', store=True)
	account_id = fields.Many2one('account.account', string='Cuenta Contable', store=True)
	currency_id = fields.Many2one('res.currency', string='Moneda', store=True)
	name = fields.Char("Descripcion")
	amount_currency = fields.Float("Importe en Moneda")
	partner_id = fields.Many2one("res.partner", string="Socio",	store=True)
	move_id = fields.Many2one('account.move', string="Apunte contable", readonly=True, store=True)
	debit = fields.Float(string="Débito",compute='_compute_debit_credit')
	credit = fields.Float(string="Crédito",compute='_compute_debit_credit')
	company_id = fields.Many2one("res.company", string="Compañía",default=lambda self: self.env.company)
	amount_residual = fields.Float(string="Residual")
	analytic_distribution = fields.Json()

	def _validate_analytic_distribution(self):
		for line in self.filtered(lambda line: line.analytic_distribution):	
			line._validate_distribution(**{
						# 'product': line.product_id.id,
						'account': line.account_id.id,
						'business_domain': 'account_regularizations',
						'company_id': line.company_id.id,
			})
	
	@api.onchange('account_id')
	def _onchange_account_id(self):
		for rec in self:
			if rec.account_id:
				rec.currency_id = rec.parent_id.currency_id.id
				rec.name = rec.parent_id.glosa_sunat

	@api.depends('amount_currency')
	def _compute_debit_credit(self):
		for rec in self:
			currency_rate = 1
			if rec.currency_id.id != rec.parent_id.currency_id.id:
				currency_rate = self.env['res.currency']._get_conversion_rate(from_currency=rec.currency_id,to_currency=rec.parent_id.currency_id,company=rec.parent_id.company_id,
															date=rec.parent_id.date,)
			amount = abs(rec.amount_currency) * currency_rate
			if rec.amount_currency > 0:
				rec.debit = amount
				rec.credit = 0.00
			elif rec.amount_currency < 0:
				rec.debit = 0.00
				rec.credit = amount
			else:
				rec.debit = 0.00
				rec.credit = 0.00