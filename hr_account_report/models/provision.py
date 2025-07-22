from odoo import api, fields, models, _

class BonCts(models.Model):
    _inherit = 'hr.prov.cts'
    _description = 'agregar cuentas Provision CTS'

    account_debit = fields.Many2one('account.account',"Cuenta Debito",store=True,tracking=True)
    account_credit = fields.Many2one('account.account',"Cuenta Credito",store=True,tracking=True)
    xls_filename_entry = fields.Char()
    xls_binary_entry = fields.Binary('Asiento Contable XLSX')

    def compute_data(self):
        self.env['hr.account.xlsx'].compute_entry_cts(self.date_from, self.date_to)

class BonVaca(models.Model):
    _inherit = 'hr.prov.vaca'
    _description = 'agregar cuentas Provision Vacaciones'

    account_debit = fields.Many2one('account.account',"Cuenta Debito",store=True,tracking=True)
    account_credit = fields.Many2one('account.account',"Cuenta Credito",store=True,tracking=True)
    xls_filename_entry = fields.Char()
    xls_binary_entry = fields.Binary('Asiento Contable XLSX')

    def compute_data(self):
        self.env['hr.account.xlsx'].compute_entry_vaca(self.date_from, self.date_to)

class BonGrati(models.Model):
    _inherit = 'hr.prov.grati'
    _description = 'agregar cuentas Provision Gratificaciones'

    account_debit = fields.Many2one('account.account',"Cuenta Debito",store=True,tracking=True)
    account_credit = fields.Many2one('account.account',"Cuenta Credito",store=True,tracking=True)
    xls_filename_entry = fields.Char()
    xls_binary_entry = fields.Binary('Asiento Contable XLSX')

    def compute_data(self):
        self.env['hr.account.xlsx'].compute_entry_grati(self.date_from, self.date_to)