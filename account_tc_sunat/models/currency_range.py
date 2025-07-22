# -*- coding: utf-8 -*-
from odoo import fields, models, _
from datetime import datetime
from .nazk import Nazk
from odoo.exceptions import UserError

class ResCurrency(models.Model):
	_inherit = "res.currency"
	_description = 'Tipo de Cambio Sunat actualizar en rango'

	date_to = fields.Date("Fecha de Final")
	date_from = fields.Date("Fecha de Inicio")
	
	def _get_range_rate(self, date_from: str, date_to: str, currency: str):
		nk = Nazk(date_format='%d/%m/%Y', currency=currency)
		sunat_rate = nk.get_exchange_rate(date_from, date_to)
		return sunat_rate 

	def update_currency_range(self):
		if int((self.date_to - self.date_from).days) > 95:
			raise UserError(_("¡Lo máximo que se puede actualizar en rango son 90 días!"))
		
		if not self.date_from or not self.date_to:
			raise UserError(_("¡Debe ingresar fechas para poder actualizar por rango!"))
		
		company_id = self.env.company.id
		date_from = datetime.strftime(self.date_from, '%d/%m/%Y')
		date_to = datetime.strftime(self.date_to, '%d/%m/%Y')
		data = self._get_range_rate(date_from, date_to, self.name)

		for key, value in data.items():
			date = datetime.strptime(key, '%d/%m/%Y')	
			currency_exist = self.env['res.currency.rate'].search_count([('company_id', '=', company_id), ('name', '=', date), ('currency_id', '=', self.id)])

			if currency_exist > 0:
				query = ''' DELETE FROM res_currency_rate WHERE name = %(date)s and company_id = %(company_id)s and currency_id = 2'''
				self.env.cr.execute(query, {'date': date, 'company_id': company_id})

				self.env['res.currency.rate'].create({
					'company_id': company_id,
					'name': date,
					'currency_id': 1,
					'inverse_company_rate': value["sell"],
				})
			else:	
				self.env['res.currency.rate'].create({
					'company_id': company_id,
					'name': date,
					'currency_id': 1,
					'inverse_company_rate': value["sell"],
				})
