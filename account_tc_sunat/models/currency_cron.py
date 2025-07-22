# -*- coding: utf-8 -*-
from odoo import models, _
from datetime import datetime
from .nazk import Nazk

class CurrencyCron(models.Model):
	_name = 'currency.cron'
	_description = 'Tipo de Cambio Sunat Programado'

	def _get_exchange_rate_usd(self, date: str, currency: str):
		nk = Nazk(date_format='%d/%m/%Y', currency=currency)
		sunat_rate = nk.get_exchange_rate(date)
		return sunat_rate 
	
	def _get_currency_sunat(self, name):
		company_id = self.env['res.company'].search([])
		for company in company_id:
			date = datetime.strftime(name, '%d/%m/%Y')
			currency_exist = self.env['res.currency.rate'].search([('company_id', '=', company.id), ('name', '=', name), ('currency_id', '=', 2)])
			if not currency_exist:
				sunat_rate = self._get_exchange_rate_usd(date, "USD")
				self.env['res.currency.rate'].create({
					'company_id': company.id,
					'name': name,
					'currency_id': 2,
					'inverse_company_rate': sunat_rate["sell"],
				})
			
	def update_currency(self):
		name = datetime.now().date()
		self._get_currency_sunat(name)