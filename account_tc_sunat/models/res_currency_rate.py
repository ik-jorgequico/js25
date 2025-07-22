# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime
from .nazk import Nazk

def exchange_rate(date: str, currency: str):
	nk = Nazk(date_format='%d/%m/%Y', currency=currency)
	sunat_rate = nk.get_exchange_rate(date)
	return sunat_rate

class ResCurrencyRate(models.Model):
    _inherit = "res.currency.rate"
    
    @api.onchange("name")
    def _onchange_name(self):
        currency_exist = self.env['res.currency.rate'].search([('company_id', '=', self.company_id.id), ('name', '=', self.name), ('currency_id', '=', 1)])
        if not currency_exist and self.name:
            date = datetime.strftime(self.name, '%d/%m/%Y')
            sunat_rate = exchange_rate(date, self.currency_id.name)
            self.inverse_company_rate = sunat_rate["sell"]
            self.company_rate = 1.0 / self.inverse_company_rate

class ResCurrency(models.Model):
	_inherit = "res.currency"

	def _get_currency_sunat(self, name):
		company_id = self.env.company.id
		date = datetime.strftime(name, '%d/%m/%Y')
		currency_exist = self.env['res.currency.rate'].search([('company_id', '=', company_id), ('name', '=', name), ('currency_id', '=', self.id)])
		if not currency_exist:
			sunat_rate = exchange_rate(date, self.name)
			self.env['res.currency.rate'].create({
				'name': name,
				'company_id': company_id,
				'currency_id': 1,
				'inverse_company_rate': sunat_rate["sell"],
			})
			
	def update_currency(self):
		name = datetime.now().date()
		self._get_currency_sunat(name)

