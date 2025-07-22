from odoo import api, fields, models


class HrPayslipWorkedDays(models.Model):
    _name = 'hr.payslip.worked_days'
    _description = 'HrPayslipWorkedDays'
    _inherit = ['hr.payslip.worked_days','mail.thread']
    afectation_days = fields.Float(string='Number of Holidays', tracking=True)

    contract_id = fields.Many2one(
        string=u'Contrato',
        related='payslip_id.contract_id',
        store=True,tracking=True
    )

    employee_id = fields.Many2one(
        string=u'Empleado',
        related='payslip_id.employee_id',
        store=True, tracking=True
    )

    @api.depends('is_paid', 'number_of_hours', 'payslip_id', 'contract_id.wage', 'payslip_id.sum_worked_hours')
    def _compute_amount(self):
        for worked_days in self.filtered(lambda wd: not wd.payslip_id.edited):
            if not worked_days.contract_id or worked_days.code == 'OUT':
                worked_days.amount = 0
                continue
            if worked_days.payslip_id.wage_type == "hourly":
                worked_days.amount = worked_days.payslip_id.contract_id.hourly_wage * worked_days.number_of_hours if worked_days.is_paid else 0
            else:
                worked_days.amount = worked_days.payslip_id.contract_id.contract_wage * worked_days.number_of_days / (30) if worked_days.is_paid else 0
