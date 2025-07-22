
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    rmv = fields.Float('Remuneracion minima vital',compute='_compute_rmv_payslip',store=True)

    @api.depends('date_to')
    def _compute_rmv_payslip(self):
        for r in self:
            if r.date_to:
                if r.payslip_run_id:
                    r.rmv = r.payslip_run_id.rmv
                else:
                    dates = self.env['basic.salary'].search([('date_from','<',r.date_to)])
                    rmv = 0
                    if dates:
                        dates.sorted(lambda o: o.date_from, reverse=True)
                        rmv = dates.value
                    r.rmv = rmv

    def _get_payslip_input_lines(self):
        result = {}
        for input_line_type in self.struct_id.input_line_type_ids:
            ### VALIDA SI EL CODIGO DEL TIPO DE ENTRADA ES PRESTAMO
            amount = 0
            if input_line_type.code == 'I_PREST':
                loans = self.env['hr.loan'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('state', '=', 'approve')
                ])

                if loans:
                    for loan in loans:
                        for line in loan.loan_lines:
                            if self.date_from <= line.date <= self.date_to and not line.paid:
                                amount += line.amount
                                    
            # COPIAR PARA GRATIFICACION
            elif input_line_type.code == 'I_GRATI':
                grati_line = self.env['hr.grati.line'].search([
                    ('employee_id','=',self.employee_id.id),
                    ('parent_id.payday','>=',self.date_from),
                    ('parent_id.payday','<=',self.date_to),
                ], limit=1)
                amount = grati_line.total

            elif input_line_type.code == 'I_CTS':
                cts_line = self.env['hr.cts.line'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('parent_id.payday', '>=', self.date_from),
                    ('parent_id.payday', '<=', self.date_to),
                ], limit=1)
                amount = cts_line.total

            elif input_line_type.code == 'I_AMOUNT_VAC':
                vac_cal_line = self.env['hr.vacation.calculate.line'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('parent_id.date_from_eval', '>=', self.date_from),
                    ('parent_id.date_from_eval', '<=', self.date_to),
                ], limit=1)
                if vac_cal_line:
                    amount = vac_cal_line.bruto_amount
                    if vac_cal_line.new_bruto_amount >0:
                        amount = vac_cal_line.new_bruto_amount

            elif input_line_type.code == 'I_ADEL_VACACIONES':
                vac_adel_line = self.env['hr.vacation.calculate.line'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('parent_id.date_from_eval', '>=', self.date_from),
                    ('parent_id.date_from_eval', '<=', self.date_to),
                ], limit=1)
                if vac_adel_line:
                    amount = vac_adel_line.net_amount

            result[input_line_type.code] = {
                'name': '',
                'sequence': 10,
                'input_type_id': input_line_type.id,
                'amount': amount,
                'payslip_id': self.id,
            }
        return result.values()

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        self._get_loans(payslips)
        # delete old payslip lines
        payslips.line_ids.unlink()

        for payslip in payslips:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True
    
    def _get_loans(self,payslip):
        for pay in payslip:
            final_input = pay.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_PREST")
            line_loans = self.env['hr.loan.line'].search([
                ('employee_id', '=', pay.employee_id.id),
                ('loan_id.state', '=', 'approve'),
                ('date', '<=', pay.date_to),
                ('date', '>=', pay.date_from),
                ('paid', '=', False),
            ])
            amount_loans_month = sum(line_loans.mapped('amount'))
            final_input.amount = amount_loans_month

    def _get_worked_day_lines_values(self, domain=None):
        res = super(HrPayslip, self)._get_worked_day_lines_values(domain=None)
        #### FALTA EDITAR EL CODIGO PARA LAS REMUNERACIONE

        

        employee_id = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        afectation_days = self.env["hr.leave"].search([
            ("employee_id","=",employee_id.id),
            ("date_from",">=",date_from),
            ("date_to","<=",date_to),
            ("state","=","validate"),
        ], order="date_from asc")
        number_real_days= sum([i.number_real_days for i in afectation_days])
        efirst_contract_date = self.employee_id.first_contract_date 
        elast_contract_date  = self.employee_id.last_contract_date

        KWORKLIMIT = 30
        if number_real_days > 30:
            number_real_days = 30

        if len(afectation_days) == 1 :
            if afectation_days.date_from.date() == date_from and afectation_days.date_to.date() == date_to and afectation_days.code in  ["21","09"]:
                KWORKLIMIT = number_real_days

        ## EL DIA DE LA PRIMERA FECHA DE CONTRATO o DEL INICIO DEL MES EVALUADO
        day_efirst = int(date_from.strftime("%d"))
        if date_from < efirst_contract_date:
            day_efirst = int(efirst_contract_date.strftime("%d"))

        working_days = (KWORKLIMIT - day_efirst) + 1
        if day_efirst > KWORKLIMIT:
                working_days = 1
        
        if elast_contract_date:
            day_elast = int(elast_contract_date.strftime("%d"))
            if elast_contract_date < date_to :
                working_days = day_elast - day_efirst + 1
        res.append({
            "number_of_days" : working_days - number_real_days,
            "number_of_hours" : 8*(working_days-number_real_days),
            "afectation_days" : number_real_days,
            'sequence': 25,
            'work_entry_type_id': 1, ## ID DE INASISTENCIA
        })

        for r in res:
            if r["work_entry_type_id"] != 1: ## ID DE ASISTENCIAS
                afectation_holidays_days = self.env["hr.leave"].search([
                    ("employee_id","=",employee_id.id),
                    ("date_from",">=",date_from),
                    ("date_to","<=",date_to),
                    ("holiday_status_id.work_entry_type_id","=",r["work_entry_type_id"]),
                ])
                
                number_holidays_real_days = sum([i.number_real_days for i in afectation_holidays_days])
                if len(afectation_holidays_days) == 1 :
                    if afectation_holidays_days.date_from == date_from and afectation_holidays_days.date_to == date_to :
                        if (afectation_holidays_days.code in ["21","09"]) or (afectation_holidays_days.code == "23" and afectation_holidays_days.date_from.strftime("%m") == "02") :
                            number_holidays_real_days = (date_to - date_from).days + 1
                else:
                    if number_holidays_real_days > 30:
                        number_holidays_real_days = 30

                r.update({
                    "number_of_days":number_holidays_real_days,
                    "number_of_hours":8*number_holidays_real_days,
                    "afectation_days":number_holidays_real_days,
                })
        return res

    def action_payslip_done(self):
        invalid_payslips = self.filtered(lambda p: p.contract_id and (p.contract_id.date_start > p.date_to or (p.contract_id.date_end and p.contract_id.date_end < p.date_from)))
        if invalid_payslips:
            raise ValidationError(_('The following employees have a contract outside of the payslip period:\n%s', '\n'.join(invalid_payslips.mapped('employee_id.name'))))
        if any(slip.contract_id.state == 'cancel' for slip in self):
            raise ValidationError(_('You cannot valide a payslip on which the contract is cancelled'))
        if any(slip.state == 'cancel' for slip in self):
            raise ValidationError(_("You can't validate a cancelled payslip."))
        self.write({'state' : 'done'})

        line_values = self._get_line_values(['NET'])

        # self.filtered(lambda p: not p.credit_note and line_values['NET'][p.id]['total'] < 0).write({'has_negative_net_to_report': True})
        self.mapped('payslip_run_id').action_close()
        # Validate work entries for regular payslips (exclude end of year bonus, ...)
        regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
        work_entries = self.env['hr.work.entry']
        for regular_payslip in regular_payslips:
            work_entries |= self.env['hr.work.entry'].search([
                ('date_start', '<=', regular_payslip.date_to),
                ('date_stop', '>=', regular_payslip.date_from),
                ('employee_id', '=', regular_payslip.employee_id.id),
            ])
        if work_entries:
            work_entries.action_validate()


    def action_print_payslip(self):
        self.ensure_one()  # Asegura que solo haya un registro
        report = self.env['ir.actions.report'].search([('report_name', '=', 'hr_payroll.report_payslip_lang')], limit=1)
        if not report:
            raise ValidationError(_('El informe para imprimir la nómina no existe. Por favor, verifique la configuración.'))
        return report.report_action(self)