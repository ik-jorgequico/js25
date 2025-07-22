# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.addons.account.models.account_account import AccountAccount
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta


class DataMovYear(models.Model):
    _name = "data.mov.year"
    _description = "Data for movimiento anual"
    
    # Utils
    months = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Setiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]
    list_months = [(str(i), month) for i, month in enumerate(months, start=1)]
    current_year = int(datetime.now().date().strftime("%Y"))
    list_year = [(str(year), year) for year in range(current_year, current_year - 8, -1)]
    
    # Fields
    name = fields.Char("Nombre")
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda x: x.env.company)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Realizado'),
        ('cancel', 'Cancelado'),
    ], "Estado", default='draft')
    
    year = fields.Selection(list_year, "Año", default=str(current_year), required=True, store=True)
    month_to = fields.Selection(list_months, "Hasta mes", default='12', required=True, store=True)
    
    balance_filename = fields.Char()
    balance_xlsx = fields.Binary('Reporte Balance')
    
    child_ids = fields.One2many("data.mov.year.line", "parent_id", "Líneas")
    
    @staticmethod
    def last_day_of_month(month: int, year: int):
        return datetime(year, month, 1) + relativedelta(months=1) - timedelta(days=1)
    
    @api.onchange("year")
    def _onchange_year(self):
        if self.year:
            self.name = f"Balance Anual - {self.year}"
    
    def _get_init_balance(self, d_to, cta):
        if not cta:
            return 0
        
        init_debit = 0
        init_credit = 0
        
        move_lines = self.env["account.move.line"].search([
            ("date", "<", d_to),
            ("company_id.id", "=", self.company_id.id),
            ("parent_state", "=", 'posted'),
            ("account_id", "=", cta),
            ("account_id.include_initial_balance", "=", True),
        ])
        
        init_debit = sum(move_lines.mapped('debit'))
        init_credit = sum(move_lines.mapped('credit'))
            
        return init_debit - init_credit
    
    def compute_sheet(self):
        self.ensure_one()
        self.child_ids.unlink()
        
        init_date_from = datetime(int(self.year), 1, 1).date()
        date_to = self.last_day_of_month(int(self.month_to), int(self.year))
        
        all_entrys = self.env["account.move.line"].search([
            "|",
            ("date", "<=", date_to),
            ("company_id.id", "=", self.company_id.id),
            ("parent_state", "=", 'posted'),
        ])
        
        entrys = all_entrys.filtered(lambda l: l.date >= init_date_from)
        entrys_init = all_entrys.filtered(lambda l: l.date < init_date_from and l.account_id.include_initial_balance)
        
        charts: AccountAccount = entrys.mapped("account_id") | entrys_init.mapped("account_id")
        
        lines = []
        for chart in charts:
            init_bal = self._get_init_balance(init_date_from, chart.id)
            
            val = {
                "parent_id": self.id,
                "chart_type": chart.group_id.parent_id.name,
                "chart_group": chart.group_id.code_prefix_start,
                "chart": chart.id,
                "chart_code": chart.code,
                "chart_name": chart.name,
                "init_balance": init_bal,
            }
            
            # Calcular saldos mensuales
            for n_month in range(1, int(self.month_to) + 1):
                date_from = datetime(int(self.year), n_month, 1).date()
                date_to = self.last_day_of_month(n_month, int(self.year)).date()
                
                month_lines = entrys.filtered(lambda l: l.date >= date_from and l.date <= date_to and l.account_id == chart)
                
                sum_debit = sum(d for d in month_lines.mapped("debit") if isinstance(d, (float, int)))
                sum_credit = sum(d for d in month_lines.mapped("credit") if isinstance(d, (float, int)))
                
                sum_saldos = sum_debit - sum_credit
                
                val.update({f"month_{n_month}": sum_saldos})
                
            lines.append(val)
            
        self.child_ids.create(lines)
    
    def action_confirm(self):
        for rec in self:
            rec.write({'state':'done'})
    
    def action_draft(self):
        for rec in self:
            rec.write({'state':'draft'})
    
    def generate_annual_balance(self):
        self.ensure_one()
        
        report = self.env.ref("account_reports_oa.report_annual_balance")
        filename, extension = report.get_filename()
        
        self.write({
            'balance_xlsx': report.render_xlsx(self.ids),
            'balance_filename': f"{filename} - {self.year}{extension}",
        })
    

class DataMovYearLine(models.Model):
    _name = "data.mov.year.line"
    _description = "Data for movimiento de cuentas anual"
    _order = 'chart_code asc'
    
    parent_id = fields.Many2one("data.mov.year", string="Parent", ondelete='cascade', store=True)
    company_id = fields.Many2one('res.company', 'Compañía', store=True)
    
    chart_type = fields.Char("Tipo Cuenta")
    chart_group = fields.Char("Grupo Cuenta")
    chart = fields.Many2one('account.account', "Cuenta", store=True)
    chart_code = fields.Char("Codigo Cuenta")
    chart_name = fields.Char("Nombre Cuenta")
    init_balance =  fields.Float("Saldos", digits=[20,2])
    month_1 = fields.Float("Enero", digits=[20,2])
    month_2 = fields.Float("Febrero", digits=[20,2])
    month_3 = fields.Float("Marzo", digits=[20,2])
    month_4 = fields.Float("Abril", digits=[20,2])
    month_5 = fields.Float("Mayo", digits=[20,2])
    month_6 = fields.Float("Junio", digits=[20,2])
    month_7 = fields.Float("Julio", digits=[20,2])
    month_8 = fields.Float("Agosto", digits=[20,2])
    month_9 = fields.Float("Septiembre", digits=[20,2])
    month_10 = fields.Float("Octubre", digits=[20,2])
    month_11 = fields.Float("Noviembre", digits=[20,2])
    month_12 = fields.Float("Diciembre", digits=[20,2])
    total_month = fields.Float("Total", compute='_compute_total_month', digits=[20,2])
    
    @api.depends('month_1', 'month_2', 'month_3', 'month_4', 'month_5', 'month_6', 'month_7', 'month_8', 'month_9', 'month_10', 'month_11', 'month_12')
    def _compute_total_month(self):
        for rec in self:
            rec.total_month = sum([
                rec.month_1,
                rec.month_2,
                rec.month_3,
                rec.month_4,
                rec.month_5,
                rec.month_6,
                rec.month_7,
                rec.month_8,
                rec.month_9,
                rec.month_10,
                rec.month_11,
                rec.month_12,
                rec.init_balance,
            ])