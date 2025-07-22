from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import  timedelta, datetime
from dateutil.relativedelta import relativedelta
from .hr_cts_reports import CTSExcelReport
import base64


import logging
_logger = logging.getLogger(__name__)

STATE_SELECTION = [
    ('draft', 'Borrador'),
    ('verify', 'Calculado'),
    ('approve', 'Aprobado'),
    ('refuse', 'Rechazado'),
    ('cancel', 'Cancelado'),
]

class BonCts(models.Model):
    _name = 'hr.cts'
    _description = 'CTS'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nombre",tracking=True)
    state = fields.Selection(STATE_SELECTION, string="State", default='draft', tracking=True, copy=False)
    current_year = int(datetime.now().date().strftime("%Y"))
    list_anios = [(str(i),str(i)) for i in range(current_year-5,current_year+1)]
    anio = fields.Selection(selection=list_anios, store=True, string="Año",tracking=True)
    selection_period = {"0": "Noviembre-Abril", "1": "Mayo-Octubre"}
    period = fields.Selection([(i,j) for i,j in selection_period.items()], store=True,string="Periodo",tracking=True)
    period_name = fields.Char(string="Nombre Periodo",tracking=True)
    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True,tracking=True)
    date_from = fields.Date(string="Dia Inicio", store=True,tracking=True)
    date_to = fields.Date(string="Dia Fin", store=True,tracking=True)
    payday = fields.Date(string="Dia de Pago", store=True,tracking=True)

    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company.id, store=True)
    child_ids = fields.One2many("hr.cts.line","parent_id",string="Bonificaciones CTS", states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)
    
    def action_open_hr_cts(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.cts.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros CTS",
        }

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)

    def action_dowload_report_pdf(self):
        self.ensure_one()
        return {
            'name': 'CTS',
            'type': 'ir.actions.act_url',
            'url': '/print/cts?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        }

    @api.onchange('anio', 'period')
    def _compute_dates(self):
        if self.anio and self.period:
            if self.period == "0":
                _sanio = int(self.anio) - 1
                self.date_from = datetime.strptime("01/11/"+str(_sanio), '%d/%m/%Y')
                self.date_to = datetime.strptime("30/04/"+self.anio, '%d/%m/%Y')
                self.period_name = str(self.anio)+"-I"
                self.payday = datetime.strptime("15/05/"+self.anio,'%d/%m/%Y')

            if self.period == "1":
                self.date_from = datetime.strptime("01/05/"+self.anio,'%d/%m/%Y')
                self.date_to = datetime.strptime("31/10/"+self.anio,'%d/%m/%Y')
                self.period_name = str(self.anio)+"-II"
                self.payday = datetime.strptime("15/11/"+self.anio,'%d/%m/%Y')

    @api.onchange("anio", "period")
    def _compute_name(self):
        if self.anio and self.period :
            name_period = self.selection_period[self.period]
            self.name = "CTS-" + name_period + "-" + str(self.anio)  

    def _first_day_of_month(self,any_day):
        return any_day - timedelta(days=(any_day.day  - 1))
    
    def _filter_employees(self,employees,date_to):
        employees =  employees.filtered(lambda x: x.first_contract_date <= self._first_day_of_month(date_to) and not x.last_contract_date)
        return employees

    def compute_sheet(self):
        self.ensure_one()

        if any(cts.state in ('approve') for cts in self):
            raise UserError(_('You cannot compute a cts which is not draft or cancelled!'))

        payslip_pays = self._delete_data()

        payslips = self.env["hr.payslip"].search([
            ("date_from",">=",self.date_from),
            ("date_to","<=",self.date_to),
            ("company_id.id","=",self.company_id.id),
        ])
        
        basic_salary = self.env["basic.salary"]._get_basic_salary_in_range(self.date_from,self.date_to)

        val_list = []
        if payslips:
            employees = payslips.mapped("employee_id")
            employees = self._filter_employees(employees,self.date_to)
            for employee in employees:
                number_aditional_days = self._get_number_aditional_days(employee,self.date_from,self.date_to)
                number_days, date_real_evaluate = self._get_number_days(employee,payslips,self.date_from,self.date_to)
                number_leave_days, number_leave_days_no_counted = self._get_number_leave_days(employee,self.date_from,self.date_to)
                
                peru_employee_regime = employee.contract_id.peru_employee_regime
                if peru_employee_regime and peru_employee_regime.abbr == "RG" and employee.children > 0:
                    family_asig = basic_salary * 0.1
                else:
                    family_asig = 0
                
                val_list.append({
                    "date_from": self.date_from,
                    "date_to": self.date_to,
                    "name": "CTS " + employee.name,
                    "employee_id": employee.id,
                    "salary": employee.contract_id.wage,
                    "family_asig": family_asig,
                    "gratification": round(self._get_gratification(employee, payslips, self.date_from, self.date_to) / 6, 2),
                    "parent_id": self.id,
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(employee,payslips)],
                    "number_days": number_days,
                    "number_leave_days": number_leave_days,
                    "number_aditional_days": number_aditional_days,
                    "number_leave_days_no_counted": number_leave_days_no_counted,
                    "date_real_evaluate": date_real_evaluate,
                })
                
            self.env["hr.cts.line"].create(val_list)
            self.env.cr.commit()
            self.compute_sheet_import(payslip_pays)
            return
        
    def compute_sheet_import(self, payslip_pays):
        employees = self.child_ids.mapped('employee_id')
        payslip = payslip_pays
        
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id == employee).input_line_ids
            final_input = input.filtered(lambda x: x.input_type_id.code == 'I_CTS')
            total = self.child_ids.filtered(lambda x: x.employee_id == employee).total
            final_input.amount = float(total)            
        payslip.compute_sheet()

    def _delete_data(self):
        employees = self.child_ids.mapped('employee_id')
        payslip = self.env['hr.payslip'].search([('date_from', '<=', self.payday), ('date_to', '>=', self.payday)])
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id == employee).input_line_ids
            final_input = input.filtered(lambda x: x.input_type_id.code == 'I_CTS')
            # total = self.child_ids.filtered(lambda x: x.employee_id == employee).total
            final_input.amount = 0.00    
        payslip.compute_sheet()

        self.child_ids.subline_ids = [(5,0,0)]
        self.child_ids = [(5,0,0)]
        return payslip        
        
    def _get_number_aditional_days(self,employee,date_from,date_to):
        cont = 0
        specific_date = date_from  - relativedelta(months=1)
        if date_from > employee.first_contract_date > specific_date:
            r = 30 - int(employee.first_contract_date.strftime("%d")) + 1
            if r > 0:
                cont += r
        return cont

    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        # this will never fail 
        return next_month - timedelta(days=next_month.day)

    def _get_number_days(self,employee,payslips,date_from,date_to):        
        cont = 0
        first_contract_date =  employee.first_contract_date
        if not employee.last_contract_date:
            if first_contract_date <= date_from:
                return 180, date_from
            else:                
                r = 30 - int(first_contract_date.strftime("%d"))  + 1
                if r > 0:
                    cont += r
                else :
                    cont += 1
                new_date = self._first_day_of_month(first_contract_date)
                new_date = new_date + relativedelta(months=1)
                while new_date < date_to:
                    cont += 30
                    new_date = new_date + relativedelta(months=1)
                    
        return cont, first_contract_date

    def _get_number_leave_days(self,employee,date_from,date_to):
        number_real_days = 0
        first_day = employee.first_contract_date
        if first_day and not employee.last_contract_date:
            if first_day <= date_from:
                first_day = date_from
                
            afectation_days =  self.env["hr.leave"].search([
                ("employee_id","=",employee.id),
                ("date_from",">=",first_day),
                ("date_to","<=",date_to),
                ("state","=","validate"),
                ("subtype_id.type_id.have_cts","=",False),
            ])
            number_real_days = sum([i.number_real_days for i in afectation_days])

            leave_days_no_counted =  self.env["hr.leave"].search([
                ("employee_id","=",employee.id),
                ("date_from",">=",first_day),
                ("date_to","<=",date_to),
                ("state","=","validate"),
                ("code","in",['16','21']),
            ])
            number_leave_days_no_counted = sum([i.number_real_days for i in leave_days_no_counted])

        return number_real_days, number_leave_days_no_counted

    def _get_gratification(self, employee, payslips, date_from, date_to):
            if date_from.strftime("%m") == "11" and date_to.strftime("%m") == "04":
                date_from =  datetime.strptime("01/12/"+date_from.strftime("%Y"), '%d/%m/%Y')
                date_to = datetime.strptime("31/12/"+date_from.strftime("%Y"), '%d/%m/%Y')
                _logger.info(f"______xxxxxxxxxxxxxxxx_______ :{date_from},{date_to}")
            else:
                date_from = datetime.strptime("01/07/"+date_from.strftime("%Y"), '%d/%m/%Y')
                date_to = datetime.strptime("31/07/"+date_from.strftime("%Y"), '%d/%m/%Y')
                _logger.info(f"______xccccccccccccccccc_______ : date from {date_from} dato to{date_to}")
                
            _logger.info(f"mmmmmmmmmmmmmmmm_______ :{date_from},{date_to}")
            pay = payslips.search([
                ("date_from",">=",date_from),
                ("date_to","<=",date_to),
                ("employee_id","=",employee.id)], limit = 1)
            
            _logger.info(f"______111111111111_______ : {pay},{employee.id}")
            _logger.info(f"_____LINE_______ : {pay.line_ids}")
            for line in pay.line_ids.filtered(lambda input: input.code == "GRATI"):
                _logger.info(f"_________________ : {line.total}")
                return line.total if (line and line.total is not None) else 0
            return 0

    def _compute_sublines(self, employee, payslip):
        sublines = []
        line_ids = payslip.filtered(lambda x: x.employee_id == employee ).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_cts == True and x.amount > 0) 

        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
        for code in codes:
            line_ids_code = line_ids.filtered(lambda x: x.code == code)
            if len(line_ids_code) >= 3:
                amount = sum([line_id.amount for line_id in line_ids_code])
                average = round(amount/6,2)
                val = {
                    "name": line_ids_code[0].name,
                    "cont": len(line_ids_code),
                    "amount": amount,
                    "average": average
                }
                sublines.append(val)
        return sublines

    def action_dowload_report_tabular(self):
        for obj in self:
            values = []
            contador = 1
            for child_id in obj.child_ids:
                val1 = {
                    "id": contador,
                    "code": child_id.employee_id.cod_ref or '',
                    "regime": child_id.employee_id.contract_id.structure_type_id.name or '',
                    "doc_type": child_id.employee_id.l10n_latam_identification_type_id.name or '',
                    "doc_num": child_id.employee_id.identification_id or '',
                    "first_lastname": child_id.employee_id.first_last_name or '',
                    "second_lastname": child_id.employee_id.second_last_name or '',
                    "first_name": child_id.employee_id.first_name or '',
                    "second_name": child_id.employee_id.second_name or '',
                    "coste_center": child_id.employee_id.cod_coste_center.name or '',
                    "zonal": child_id.employee_id.location_id.name or '',
                    "area": child_id.employee_id.department_id.name or '',
                    "job": child_id.employee_id.job_id.name or '',
                    "bank": child_id.employee_id.bank_cts_id.bank_id.name or '',
                    "num_account": child_id.employee_id.bank_cts_id.acc_number or '',
                    "date_first_contract": child_id.employee_id.first_contract_date or '',
                    "date_last_contract": child_id.employee_id.last_contract_date or '',
                }

                val2 = self.get_dicts_proms(child_id)
                for subline_id in child_id.subline_ids:
                    val2[f"Prom_{subline_id.name}"] = subline_id.average

                val3 = {
                    "Sumatorio Promedios": child_id.average_variables,
                    "salary_basic": child_id.salary,
                    "family_asig": child_id.family_asig,
                    "grati": child_id.gratification,
                    "base_total": child_id.total_amount,
                    "number_leave_days": child_id.number_leave_days,
                    "working_days": child_id.number_total,
                    "cts": child_id.sub_total,
                    "total_ingreso": child_id.sub_total,
                    # "Adelanto": 0,
                    # "dscto_total": 0,
                    "desc_cts": child_id.desc_cts,
                    "total": child_id.total,
                    "number_total_working_days": child_id.number_total_working_days ,
                }

                val = {**val1, **val2, **val3}
                values.append(val)
                contador += 1
            obj.generate_excel(values)
    
    def get_dicts_proms(self, child_id):
        return {"Prom_" + subline_id.name: subline_id.average for subline_id in child_id.subline_ids}

    def generate_excel(self,data):
        report_xls = CTSExcelReport(data, self)
        values = {
            'xls_filename': f"REPORTE CTS TABULAR {self.name}.xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)

    @api.model
    def _get_default_report_id(self):
        return self.env.ref('hr_cts.action_report_cts', False)
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model','=','hr.cts.line'),('report_type','=','qweb-pdf')]", default=_get_default_report_id)

    ################ state bar ########################

    def action_refuse(self):
        self.mapped('child_ids').write({'state': 'refuse'})
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.mapped('child_ids').write({'state': 'verify'})
        return self.write({'state': 'verify'})

    def action_cancel(self):
        self.mapped('child_ids').write({'state': 'cancel'})
        return self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.child_ids:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.mapped('child_ids').action_payslip_approve()
                self.write({'state': 'approve'})

    def action_draft(self):
        self.mapped('child_ids').write({'state': 'draft'})
        return self.write({'state': 'draft'})

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(cts.state not in ('draft', 'cancel','refuse') for cts in self):
            raise UserError(_('You cannot delete a cts which is not draft or cancelled!'))
    ####################################################
    
    def unlink(self):
        employees = self.child_ids.mapped("employee_id")
        payslip = self.env['hr.payslip'].search([("date_from","<=",self.payday),("date_to",">=",self.payday)])
        
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id == employee).input_line_ids
            final_input = input.filtered(lambda x: x.input_type_id.code == "I_CTS")
            final_input.amount = 0
        payslip.compute_sheet()
        
        return super(BonCts,self).unlink()

class BonCtsLine(models.Model):
    _name = 'hr.cts.line'
    _description = 'CTS DETALLE'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nombre", store=True,)

    employee_id = fields.Many2one("hr.employee", store=True,string="Empleado")
    salary = fields.Float(string="Sueldo Contrato", default=0)
    family_asig = fields.Float(string="A.F.", default=0)
    gratification = fields.Float(string="1/6 Grati", default=0)
    average_variables = fields.Float(string="Prom. Variables", compute='_compute_average_variables', default= 0)
    total_amount = fields.Float(string="Monto", compute='_compute_total_amount', default=0, store=True)
    sub_total = fields.Float(string="SubTotal", compute='_compute_subtotal', default=0, store=True)

    total = fields.Float(string="Total", compute='_compute_total', default=0, store=True)
    parent_id = fields.Many2one("hr.cts", string="CTS", ondelete='cascade', store=True)
    subline_ids = fields.One2many("hr.cts.subline", "cts_line", string="Variables")
    number_days = fields.Integer(string="Dias Totales", default=180)
    number_leave_days = fields.Integer(string="Ausent.", default=0)
    number_leave_days_no_counted = fields.Integer(string="Ausent. No Contados (Desc Med + Subsidios)s",default=0)
    number_aditional_days = fields.Integer(string="D. Adicionales",default=0, help="Dias Adicionales de Trabajo cuando no has sido parte de la bonificación CTS del periodo anterior.")
    number_total_working_days = fields.Integer(string="D. Trabajados del Periodo", default=0,  compute='_compute_number_total_working_days', help="Dias Laborados + Dias Adicionales")
    number_total = fields.Integer(string="D. Laborados", default=0, compute='_compute_number_total', help="Dias Trabajados del Periodo - Dias Ausentismos")
    payday = fields.Date(related="parent_id.payday", store=True)
    text_notes_2 = fields.Text(string="Notas", store=True, default="")
    desc_cts =  fields.Float(string="Descuento", store=True) # manual 
    state = fields.Selection(STATE_SELECTION, string="State", default='draft', tracking=True, copy=False)
    
    date_real_evaluate = fields.Date(store=True,string="Primer Dia Real Evaluado")
    date_from = fields.Date(related = "parent_id.date_from", store=True)
    date_to = fields.Date(related = "parent_id.date_to", store=True)
    first_contract_date = fields.Date(store=True, string="Fecha Inicio", compute="compute_information")
    identification_id = fields.Char(store=True, string="Num. Doc.", compute="compute_information" )

    structure_type = fields.Char(string="Tipo de Regimen", compute='_compute_structure_type', store=True)
    
    @api.depends('employee_id')
    def compute_information(self):
        for record in self:
            if record.employee_id:
                record.first_contract_date = record.employee_id.first_contract_date
                record.identification_id = record.employee_id.identification_id

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)
    
    def action_dowload_report_pdf(self):
        return {
            'name': 'CTS',
            'type': 'ir.actions.act_url',
            'url': '/print/cts?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        }
    
    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark cts as approve if not confirmed.'))
        self.write({'state': 'approve'})

    @api.depends('subline_ids')
    def _compute_average_variables(self):
        for record in self:
            amount = 0
            for subline_id in record.subline_ids:
                amount += subline_id.average
            record.average_variables = amount

    @api.depends('salary','family_asig','gratification','average_variables')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.salary + record.family_asig + record.gratification + record.average_variables

    @api.depends('total','desc_cts')
    def _compute_subtotal(self):
        for record in self:
            record.sub_total = record.total + record.desc_cts

    @api.depends('total_amount', 'desc_cts')
    def _compute_total(self):
        for record in self:
            total = record.total
            peru_employee_regime = record.employee_id.contract_id.peru_employee_regime
            if peru_employee_regime:
                abbr = peru_employee_regime.abbr
                if abbr == "RG":
                    total = round(record.total_amount/360 * (record.number_days + record.number_aditional_days - record.number_leave_days), 2) - record.desc_cts
                elif abbr == "RP":
                    total = round((record.total_amount/360)/2 * (record.number_days + record.number_aditional_days - record.number_leave_days), 2) - record.desc_cts
                elif abbr == "RM":
                    total = round((record.total_amount/360)*0, 2) - record.desc_cts
            record.total = total
    
    @api.depends('number_days','number_aditional_days')
    def _compute_number_total_working_days(self):
        for record in self:
            record.number_total_working_days = record.number_days + record.number_aditional_days

    @api.depends('number_total_working_days','number_leave_days','number_leave_days_no_counted')
    def _compute_number_total(self):
        for record in self:
            record.number_total = record.number_total_working_days - record.number_leave_days
            if record.number_leave_days_no_counted >= 80:
                diff = record.number_leave_days_no_counted - 60
                record.number_total -= diff
                
                note = f"- El empleado a superado los 60 días por incapacidad temporal - son de {diff} días."
                if record.text_notes_2 == "" or not record.text_notes_2:
                    record.text_notes_2 = note
                else :
                    note = "\n" + note
                    record.text_notes_2 += note
                    
    @api.depends('employee_id')
    def _compute_structure_type(self):
        for rec in self:
            peru_employee_regime = rec.employee_id.contract_id.peru_employee_regime
            rec.structure_type = peru_employee_regime.abbr if peru_employee_regime else ''
            

class BonCtsSubLine(models.Model):
    _name = 'hr.cts.subline'
    _description = 'CTS DETALLE'

    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")

    cts_line = fields.Many2one("hr.cts.line", ondelete='cascade', store=True,)
