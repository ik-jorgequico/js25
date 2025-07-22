from odoo import fields, models

class AccountAnalyticApplicability(models.Model):
    _inherit = "account.analytic.applicability"

    business_domain = fields.Selection(
        selection_add=[("account_regularizations", "Regularizacion Contable")],
        ondelete={"account_regularizations": "cascade"},
    )