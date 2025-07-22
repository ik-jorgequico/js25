
from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from .hr_grati_reports import GratiExcelReport
import base64


SELECTION_STATE = [
    ('draft', 'Borrador'),
    ('verify', 'Entregado'),
    ('approve', 'Aprobado'),
    ('refuse', 'Rechazado'),
    ('cancel', 'Cancelado'),
]

SELECTION_PERIOD = [
    ('0', 'Enero - Junio'),
    ('1', 'Julio - Diciembre'),
]

class BonGrati(models.Model):
    _name = 'hr.grati'
    _description = 'Gratificación'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(SELECTION_STATE, string="State", default='draft', tracking=True, copy=False)

    is_superuser = fields.Boolean(compute="_compute_is_superuser", store=True)
    name = fields.Char(string="Nombre",tracking=True)
    current_year = datetime.now().year
    anio = fields.Selection([(str(i), str(i)) for i in range(current_year, current_year - 6, -1)], string="Año",tracking=True, store=True)
    period = fields.Selection(SELECTION_PERIOD, string="Periodo",tracking=True, store=True)
    period_name = fields.Char(string="Nombre Periodo",tracking=True,)
    date_from = fields.Date(string="Día Inicio", store=True,tracking=True,)
    date_to = fields.Date(string="Día Fin", store=True,tracking=True,)
    payday = fields.Date(string="Día de Pago", store=True, compute='_compute_payday',tracking=True, required=True)
    
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    
    #obtencion de la tabla
    regimen_id = fields.Many2one("hr.payroll.structure.type", store=True,tracking=True,)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)
    #obtencion de un parametro de una tabla
    child_ids = fields.One2many("hr.grati.line", "parent_id", string="Bonificaciones Gratificación",tracking=True, 
                                states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model', '=', 'hr.grati.line'), ('report_type', '=', 'qweb-pdf')]",tracking=True,
                                default=lambda self: self.env.ref('hr_grati.action_report_grati', False))
    
    def get_basic_salary_asig_family(self):
        basic_salary_obj = self.env['basic.salary'].search([
            ('date_from', '<=', self.date_to),
            ('date_to', '>=', self.date_to),
        ], limit=1)
        return basic_salary_obj.value * 0.10 if basic_salary_obj else 0.0
    
    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)
    
    def _first_day_of_month(self,any_day):
        return any_day - timedelta(days=(any_day.day  - 1))
    
    def _filter_employees(self,employees,date_to):
        employees = employees.filtered(lambda x: x.first_contract_date <= self._first_day_of_month(date_to) and not x.last_contract_date) # filtrado de los empleados segun condiciones
        return employees
    
    @api.depends('period', 'anio')
    def _compute_payday(self):
        for rec in self.filtered(lambda x: x.anio):
            rec.payday = date(int(rec.anio), 7 if rec.period == '0' else 12, 15)

    def compute_sheet(self):
        self.ensure_one() # pasar solo un registro

        if any(grati.state in ('approve') for grati in self):
            raise UserError(_('You cannot compute a gratification which is not draft or cancelled!'))

        # self.child_ids.subline_ids.unlink() # elimina los datos que estan likeados de sub hijos
        # self.child_ids.unlink() # elimina los datos linkeado de los padres
        
        payslip_pays = self._delete_data()

        payslips = self.env["hr.payslip"].search([
            ("date_from",">=",self.date_from),
            ("date_to","<=",self.date_to),
            ("company_id.id","=",self.company_id.id),
        ])  # busca por filtro los datos de payslips
        
        val_list = []
        if payslips:
            employees = payslips.mapped("employee_id") # obtencion del id del empleado de la tabla payslip
            employees = self._filter_employees(employees,self.date_to)
            
            for employee in employees:
                number_days, number_periods = self._get_number_days(employee,self.date_to, self.date_from)
                number_leave_days = self._get_number_leave_days(employee,self.date_from,self.date_to)
                peru_employee_regime = employee.contract_id.peru_employee_regime
                # if peru_employee_regime:
                #     if peru_employee_regime.abbr == 'RG' and employee.children > 0:
                #         family_asig = self.get_basic_salary_asig_family()
                # else:
                #     family_asig = 0
                family_asig = 0
                if peru_employee_regime:
                    if peru_employee_regime.abbr in ('RG', 'RP') and employee.children > 0:
                        family_asig = self.get_basic_salary_asig_family()
                
                val_list.append({
                    "date_from":self.date_from,
                    "date_to":self.date_to,
                    "name":"GRATIFICACION " + employee.name,
                    "employee_id":employee.id,
                    "salary":   employee.contract_id.wage,
                    "family_asig": family_asig,
                    "parent_id":self.id,
                    "subline_ids": [(0,0,subline) for subline in self._compute_sublines(employee,payslips)],
                    "number_days": number_days,
                    "number_leave_days": number_leave_days ,
                    "number_total": number_days - number_leave_days,
                    "number_periods": number_periods,
                })

            self.env["hr.grati.line"].create(val_list)            
            self.env.cr.commit()
            self.compute_sheet_import(payslip_pays)
            return
        
    def compute_sheet_import(self, payslip_pays):
        employees = self.child_ids.mapped("employee_id")
        # payslip = self.env['hr.payslip'].search([("date_from","<=",self.payday),("date_to",">=",self.payday),])
        payslip = payslip_pays
        
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id == employee).input_line_ids
            input_I_GRATI = input.filtered(lambda x: x.input_type_id.code == "I_GRATI")
            input_I_BON_EXT_TEMP_30334 = input.filtered(lambda x: x.input_type_id.code == "I_BON_EXT_TEMP_30334")
            input_I_ADEL_GRATI = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_GRATI")

            total = self.child_ids.filtered(lambda x: x.employee_id == employee).total
            health_regimen = self.child_ids.filtered(lambda x: x.employee_id == employee).health_regimen
            grati_bono = self.child_ids.filtered(lambda x: x.employee_id == employee).grati_bono
            desc_grati = self.child_ids.filtered(lambda x: x.employee_id == employee).desc_grati

            input_I_GRATI.amount = float(total)
            input_I_BON_EXT_TEMP_30334.amount = float(health_regimen)
            input_I_ADEL_GRATI.amount = float(grati_bono + desc_grati)
            
        payslip.compute_sheet()

    def _delete_data(self):
        employees = self.child_ids.mapped('employee_id')
        payslip = self.env['hr.payslip'].search([('date_from', '<=', self.payday), ('date_to', '>=', self.payday)])
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id == employee).input_line_ids
            input_I_GRATI = input.filtered(lambda x: x.input_type_id.code == 'I_GRATI')
            input_I_BON_EXT_TEMP_30334 = input.filtered(lambda x: x.input_type_id.code == "I_BON_EXT_TEMP_30334")
            input_I_ADEL_GRATI = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_GRATI")

            input_I_GRATI.amount = 0.00
            input_I_BON_EXT_TEMP_30334.amount = 0.00
            input_I_ADEL_GRATI.amount = 0.00
        payslip.compute_sheet()

        self.child_ids.subline_ids = [(5,0,0)]
        self.child_ids = [(5,0,0)]
        return payslip 

    def _get_number_days(self,employee,date_to,date_from):
        first_contract_date = employee.first_contract_date
        
        if first_contract_date <= date_from:
            return 180,6
        
        # se puede colocar la fecha para el primer dia de evaluacion
        month_contract = first_contract_date.month
        
        if first_contract_date.day == 1:
            month = month_contract - 1
        else:
            month = month_contract

        return (date_to.month - month)*30, date_to.month - month
        
    def _get_number_leave_days(self, employee, date_from, date_to):
        number_real_days = 0
        first_day = employee.first_contract_date
        
        if first_day and not employee.last_contract_date:
            if first_day <= date_from:
                first_day = date_from
            else:
                if first_day.day != 1:
                    first_day = first_day + relativedelta(months=1)
                    first_day = self._first_day_of_month(first_day)

            afectation_days = self.env["hr.leave"].search([
                ("employee_id", "=", employee.id),
                ("date_from", ">=", first_day),
                ("date_to", "<=", date_to),
                ("state", "=", "validate"),
                ("subtype_id.type_id.have_gratification", "=" ,False),
            ])
            
            number_real_days = sum([i.number_real_days for i in afectation_days])

        return number_real_days

    def _get_gratification(self, employee, payslips, date_from, date_to):
        if date_from.strftime("%m") == "11" and date_to.strftime("%m") == "04":
            date_from = datetime.strptime("01/12/"+date_from.strftime("%Y"), '%d/%m/%Y')
            date_to = datetime.strptime("31/12/"+date_from.strftime("%Y"), '%d/%m/%Y')
        else:
            date_from = datetime.strptime("01/07/"+date_from.strftime("%Y"), '%d/%m/%Y')
            date_to = datetime.strptime("31/07/"+date_from.strftime("%Y"), '%d/%m/%Y')
        
        pay = payslips.search([
            ("date_from",">=",date_from),
            ("date_to","<=",date_to),
            ("employee_id.id","=",employee.id),
        ], limit = 1)
        
        for line in pay.line_ids.filtered(lambda input: input.code == "GRATI"):
            return abs(line.total) if (line and line.total is not None) else 0
        
        return 0

    def _compute_sublines(self, employee, payslip):
        sublines = []
        line_ids = payslip.filtered(lambda x: x.employee_id == employee ).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_gratification == True and x.amount > 0) 

        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
        
        for code in codes:
            line_ids = line_ids.filtered(lambda x: x.code == code)
            
            if len(line_ids) >= 3:
                amount = sum([line_id.amount for line_id in line_ids])
                average = amount/6
                
                sublines.append({
                    "name": line_ids[0].name,
                    "cont": len(line_ids),
                    "amount": amount,
                    "average": average
                })
                
        return sublines

    def get_dicts_proms(self, child_id):
        return {"Prom_" + subline_id.name: subline_id.average for subline_id in child_id.subline_ids}

    def action_dowload_report_tabular_grati(self):
        contador = 1
        for obj in self:
            values = []
            
            for child_id in obj.child_ids:
                zona = ''
                
                if child_id.employee_id.location_id: 
                    zona = child_id.employee_id.location_id.name

                start_period = obj.date_from

                if obj.date_from <= child_id.employee_id.first_contract_date:
                    start_period = child_id.employee_id.first_contract_date

                val1 = {
                    "ID":contador,
                    "Cod.": child_id.employee_id.cod_ref or '',
                    "Tipo_doc": child_id.employee_id.l10n_latam_identification_type_id.name or '',
                    "documento": child_id.employee_id.identification_id or '',
                    "PRIMER APELLIDO": child_id.employee_id.first_last_name or '',
                    "SEGUNDO APELLIDO": child_id.employee_id.second_last_name or '',
                    "PRIMER NOMBRE": child_id.employee_id.first_name or '',
                    "SEGUNDO NOMBRE": child_id.employee_id.second_name or '',

                    "centro de costo": child_id.employee_id.cod_coste_center.name or '',
                    "zonal": zona or '',
                    "area": child_id.employee_id.department_id.name or '',
                    "cargo": child_id.employee_id.job_id.name or '',
                    "banco": child_id.employee_id.bank_account_id.bank_id.name or '',
                    "n cuenta": child_id.employee_id.bank_account_id.acc_number or '',
                    "fecha de ingreso": child_id.employee_id.first_contract_date or '',
                    "FECHA CESE":child_id.employee_id.last_contract_date or '',

                    "number_periods": child_id.number_periods,
                    "structure_type": child_id.structure_type,
                    "inicio de periodo": start_period or '',
                    "termino de periodo": obj.date_to or '',
                    "fecha de pago": self.payday or '',
                    "basico": child_id.salary or '',
                    "health bool": child_id.health_bool or '',
                    "identification": child_id.identification_id or '',
                    "periodo": self.period,
                }
                
                val2 = self.get_dicts_proms(child_id)
                
                val3 = {
                    "Sumatorio Promedios": child_id.average_variables,
                    "Salario Basico": child_id.salary,
                    "Asig Familiar": child_id.family_asig,
                    "Total Base": child_id.total_amount,
                    "Dias No Laborados": child_id.number_leave_days,
                    "Dias Laborados": child_id.number_days ,
                    "Dias Totales": child_id.number_total,                    
                    "Grati": child_id.total,
                    "Total de Ingreso": child_id.total,
                    "Adelanto": 0,
                    "Total Descuento": 0,
                    "Neto a Pagar": child_id.grati_bono,
                    "health regimen": child_id.health_regimen,
                    "Descuento": child_id.desc_grati,
                    "Grati + Bono": child_id.grati_bruto,

                    "suma basico": round(sum(obj.child_ids.mapped('salary')), 2),
                    "suma asig fam": round(sum(obj.child_ids.mapped('family_asig')), 2),

                    "suma dias laborados": round(sum(obj.child_ids.mapped('number_days')), 2),
                    "suma ausentismos": sum(obj.child_ids.mapped('number_leave_days')),
                    "suma dia lab total": sum(obj.child_ids.mapped('number_total')),
                    "suma gratificacion": round(sum(obj.child_ids.mapped('total')), 2),
                    "suma bon extra": round(sum(obj.child_ids.mapped('health_regimen')), 2),
                    "suma total grati": round(sum(obj.child_ids.mapped('grati_bono')), 2),
                    "suma descuento": round(sum(obj.child_ids.mapped('desc_grati')), 2),
                    "suma neto a pagar": round(sum(obj.child_ids.mapped('grati_bono')), 2),
                }
                
                contador += 1
                values.append({**val1, **val2, **val3})
                
            obj.generate_excel(values)

    def generate_excel(self, data):
        report_xls = GratiExcelReport(data, self)
        self.write({
            'xls_filename': f"REPORTE GRATIFICACION TABULAR {self.name}.xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        })

    ####################################### EVENTS ###########################################################

    @api.onchange("anio", "period")
    def _compute_dates(self):
        if self.anio and self.period:
            if self.period == "0":
                self.date_from = datetime.strptime("01/01/"+self.anio, '%d/%m/%Y')
                self.date_to = datetime.strptime("30/06/"+self.anio, '%d/%m/%Y')
                self.period_name = str(self.anio)+"-I"

            if self.period == "1":
                self.date_from = datetime.strptime("01/06/"+self.anio,'%d/%m/%Y')
                self.date_to = datetime.strptime("31/12/"+self.anio,'%d/%m/%Y')
                self.period_name = str(self.anio)+"-II"

    @api.onchange("anio", "period")
    def _compute_name(self):
        if self.anio and self.period:
            self.name = f"GRATIFICACION  {self.anio} ({dict(SELECTION_PERIOD).get(self.period)})"
    
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
        return self.write({'state': 'draft'})
    

    def _compute_is_superuser(self):
        self.update({'is_superuser': self.env.user._is_superuser() and self.user_has_groups("base.group_no_one")})

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancel(self):
        if any(grati.state not in ('draft', 'cancel', 'refuse') for grati in self):
            raise UserError(_('You cannot delete a gratification which is not draft or cancelled!'))
    
    def unlink(self):
        self.child_ids.unlink()
        return super(BonGrati,self).unlink()
    

class BonGratiLine(models.Model):
    _name = 'hr.grati.line'
    _description = 'GRATIFICACION DETALLE'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Nombre")
    state = fields.Selection(SELECTION_STATE, string="State", default='draft', tracking=True, copy=False)
    structure_type = fields.Char(string="Tipo de Regimen", compute='_compute_structure_type', store=True)

    date_from = fields.Date(related="parent_id.date_from", store=True)
    date_to = fields.Date(related="parent_id.date_to", store=True)
    payday = fields.Date(related="parent_id.payday", store=True,tracking=True,)

    desc_grati = fields.Float(string="Descuento", tracking=True,store=True)  # manual 
    first_day_contract = fields.Date(related="employee_id.first_contract_date", string="Fecha de ingreso")
    employee_id = fields.Many2one("hr.employee", string="Empleados", store=True)
    identification_id = fields.Char(string="Num. Doc.",store=True, related="employee_id.identification_id")
    salary = fields.Float(string="Sueldo C.",tracking=True, store=True)
    family_asig = fields.Float(string="A. F.",tracking=True, store=True)
    average_variables = fields.Float(string="P. Variables", compute='_compute_average_variables', default=0, store=True)
    total_amount = fields.Float(string="Monto", compute='_compute_total_amount', default=0, store=True)
    health_regimen = fields.Float(string="Bono Extr.", compute='_compute_health_regimen', default=0, store=True)
    grati_bono = fields.Float(string="Neto a Pagar", compute='_compute_grat_bono', default=0, store=True)
    grati_bruto = fields.Float(string="T. Grati.", compute='_compute_grat_bruto', default=0, store=True)
    total = fields.Float(string="Grati", compute='_compute_total', default= 0, store=True)
    parent_id = fields.Many2one("hr.grati", string="GRATIFICACION", ondelete='cascade')
    subline_ids = fields.One2many("hr.grati.subline","grati_line", string="Variables")
    number_periods = fields.Integer(string="Num Periodos", store=True)
    number_days = fields.Integer(string="Dias Laborados", default=180)
    number_leave_days = fields.Integer(string="Ausent.", default=0)
    number_total = fields.Integer(string="Tot. Dias", default=0, help="Dias Trabajados del Periodo - Dias Ausentismos")
    health_bool = fields.Char(string="EPS")

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark gratification as approve if not confirmed.'))
        self.write({'state': 'approve'})
        
    @api.depends('employee_id')
    def _compute_structure_type(self):
        for rec in self:
            peru_employee_regime = rec.employee_id.contract_id.peru_employee_regime
            if peru_employee_regime:
                rec.structure_type = peru_employee_regime.abbr or ''
                
    @api.depends('subline_ids')
    def _compute_average_variables(self):
        for record in self:
            amount = 0
            for subline_id in record.subline_ids:
                amount += subline_id.average
            record.average_variables = amount

    @api.depends('salary','family_asig','average_variables')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.salary + record.family_asig + record.average_variables

    @api.depends('total_amount', 'number_total')
    def _compute_total(self):
        for record in self:
            total = 0
            peru_employee_regime = record.employee_id.contract_id.peru_employee_regime
            if peru_employee_regime:
                if peru_employee_regime.abbr == 'RG':
                    total = record.total_amount/180*(record.number_total)
                    # record.structure_type = 'RG'
                    
                elif peru_employee_regime.abbr == 'RP':
                    total = ((record.total_amount/180)/2)*(record.number_total)
                    # record.structure_type = 'RP'
                    
                elif peru_employee_regime.abbr == 'RM':
                    total = ((record.total_amount/180)*0)*(record.number_total)
                    # record.structure_type = 'RM'
            record.total = total
    @api.depends('total')
    def _compute_health_regimen(self):
        for record in self:
            if record.employee_id.health_regime_id.code == '02':
                record.health_regimen = record.total * 6.75 / 100
                record.health_bool = 'Sí'
            else:
                record.health_regimen = record.total * 9 / 100
                record.health_bool = 'No'

    @api.depends('health_regimen', 'total', 'desc_grati')
    def _compute_grat_bono(self):
        for record in self:
            record.grati_bono = record.health_regimen + record.total - record.desc_grati
            
    @api.depends('health_regimen', 'total')
    def _compute_grat_bruto(self):
        for record in self:
            record.grati_bruto = record.health_regimen + record.total
            
    def unlink(self):
        pays = self.env["hr.payslip"].search([
            ("date_from","<=",self.parent_id.payday),
            ("date_to",">=",self.parent_id.payday),
            ("struct_id.type_id.id","=",self.parent_id.regimen_id.id),
        ])
        
        for element in self:
            pay = pays.filtered(lambda x: x.employee_id == element.employee_id)
            input = pay.input_line_ids
            input_I_GRATI = input.filtered(lambda x: x.input_type_id.code == "I_GRATI")
            input_I_BON_EXT_TEMP_30334 = input.filtered(lambda x: x.input_type_id.code == "I_BON_EXT_TEMP_30334")
            input_I_ADEL_GRATI = input.filtered(lambda x: x.input_type_id.code == "I_ADEL_GRATI")
            
            if input_I_GRATI:
                input_I_GRATI.amount = 0
            if input_I_BON_EXT_TEMP_30334:
                input_I_BON_EXT_TEMP_30334.amount = 0
            if input_I_ADEL_GRATI:
                input_I_ADEL_GRATI.amount = 0

        pays.compute_sheet()

        return super(BonGratiLine,self).unlink()

class BonGratiSubLine(models.Model):
    _name = 'hr.grati.subline'
    _description = 'GRATI DETALLE'

    name = fields.Char(string="Nombre Concepto")
    cont = fields.Float(string="Conteo Meses")
    amount = fields.Float(string="Monto")
    average = fields.Float(string="Promedio")

    grati_line = fields.Many2one("hr.grati.line", ondelete='cascade')
