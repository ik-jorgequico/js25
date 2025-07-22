# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCurrencyRate(models.Model):
	_inherit = "res.currency.rate"
	_description = "Res Curency Rate"

	# SOLO PARA AGREGARLE EL DEFAULT Y EL STORE TRUE
	inverse_company_rate = fields.Float('Tipo de Cambio Peruano', store=True, default=1.00)