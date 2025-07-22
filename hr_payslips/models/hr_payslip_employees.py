# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict
from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import format_date

MONTHS = {
    "01":'ENERO',
    "02":'FEBRERO',
    "03":'MARZO',
    "04":'ABRIL',
    "05":'MAYO',
    "06":'JUNIO',
    "07":'JULIO',
    "08":'AGOSTO',
    "09":'SEPTIEMBRE',
    "10":'OCTUBRE',
    "11":'NOVIEMBRE',
    "12":'DICIEMBRE'
}

class HrPayslipEmployees(models.TransientModel):
    _name = 'hr.payslip.employees'
    _description = 'HrPayslipEmployees'
    _inherit = ['hr.payslip.employees','portal.mixin', 'mail.thread', 'mail.activity.mixin']
    structure_type_id = fields.Many2one('hr.payroll.structure.type', tracking=True)
    
    @api.onchange('structure_type_id')
    def _cancel_selection(self):
        if self.structure_type_id:
            self.structure_id = None
    
    def _get_available_contracts_domain(self):
        res = super(HrPayslipEmployees, self)._get_available_contracts_domain()
        res.extend([
            ('contract_ids.structure_type_id', '!=', False),
            ('contract_ids.peru_employee_regime', '!=', False),
        ])
        return res
    
    @api.depends('department_id', 'structure_id')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.structure_id:
                domain_ext = []
                if wizard.department_id:
                    domain_ext = [('contract_id.structure_type_id', '=', self.structure_id.type_id.id),]
                domain = expression.AND([
                    domain,
                    [('contract_id.structure_type_id', '=', self.structure_id.type_id.id),] + domain_ext
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)
    
    def _check_undefined_slots(self, work_entries, payslip_run):
        """ Check if a time slot in the contract's calendar is not covered by a work entry
        """
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            work_entries_by_contract[work_entry.contract_id] |= work_entry

        for contract, work_entries in work_entries_by_contract.items():
            calendar_start = pytz.utc.localize(datetime.combine(max(contract.date_start, payslip_run.date_start), time.min))
            calendar_end = pytz.utc.localize(datetime.combine(min(contract.date_end or date.max, payslip_run.date_end), time.max))

    def compute_sheet(self):
        self.ensure_one()
        
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            today = fields.date.today()
            first_day = today + relativedelta(day=1)
            last_day = today + relativedelta(day=31)
            
            if from_date == first_day and end_date == last_day:
                batch_name = from_date.strftime('%B %Y')
            else:
                batch_name = _('From %s to %s', format_date(self.env, from_date), format_date(self.env, end_date))
            
            payslip_run = self.env['hr.payslip.run'].create({
                'name': batch_name,
                'date_start': from_date,
                'date_end': end_date,
            })
            
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        
        employees = self.with_context(active_test=False).employee_ids
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))
        
        # Prevent a payslip_run from having multiple payslips for the same employee
        employees -= payslip_run.slip_ids.employee_id
        success_result = {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        
        if not employees:
            return success_result
        
        Payslip = self.env['hr.payslip']
        
        contracts = employees._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close']).filtered(lambda c: c.active)
        
        default_values = Payslip.default_get(Payslip.fields_get())
        payslips_vals = []
        for contract in self._filter_contracts(contracts):
            values = dict(default_values, **{
                'name': _('New Payslip'),
                'employee_id': contract.employee_id.id,
                # 'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslips_vals.append(values)
        payslips = Payslip.with_context(tracking_disable=True).create(payslips_vals)
        payslips._compute_name()
        
        # INICIA LOS INPUTS NECESARIOS DE PAYSLIP
        hrPayslipInputType = self.env['hr.payslip.input.type']
        for payslip in payslips:
            input_line_ids = [] 
            
            input_type_id = hrPayslipInputType.search([('code', '=', 'I_PREST')], limit=1).id
            input_line_ids.append((0, 0, {'input_type_id': input_type_id}))
            
            payslip.write({'input_line_ids': input_line_ids})
        
        payslips.compute_sheet()
        
        payslip_run.state = 'verify'
        
        return success_result
