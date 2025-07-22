from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError
from .hr_5ta_reports import Excel5taReport
import base64
import calendar
import logging
_logger = logging.getLogger(__name__)


MONTH_ABBR = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]

STATES_SELECTION = [
    ('draft', 'Borrador'),
    ('verify', 'Entregado'),
    ('approve', 'Aprobado'),
    ('refuse', 'Rechazado'),
    ('cancel', 'Cancelado'),
]

MONTHS_SELECTION = [
    ('01', 'Enero'),
    ('02', 'Febrero'),
    ('03', 'Marzo'),
    ('04', 'Abril'),
    ('05', 'Mayo'),
    ('06', 'Junio'),
    ('07', 'Julio'),
    ('08', 'Agosto'),
    ('09', 'Septiembre'),
    ('10', 'Octubre'),
    ('11', 'Noviembre'),
    ('12', 'Diciembre'),
]

class imp5ta(models.Model):
    _name = 'hr.5ta'
    _description = '5TA CATEGORIA'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nombre: ", store=True) 
    state = fields.Selection(STATES_SELECTION, string="State", default='draft', tracking=True, copy=False)

    current_year = datetime.today().year
    month = fields.Selection(MONTHS_SELECTION, tracking=True,required=True)
    year = fields.Selection([(str(y), y) for y in range(current_year, current_year - 8, -1)],tracking=True, required=True)
    
    date_5ta = fields.Date(string="Fecha", compute='_compute_date_5ta',tracking=True, store=True)

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel',tracking=True)

    regimen_id = fields.Many2one("hr.payroll.structure.type",tracking=True, required=True, store=True)
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)

    child_ids = fields.One2many("hr.5ta.line", "parent_id", string="Impuesto 5ta Categoria",tracking=True, states={'refuse': [('readonly', True)], 'cancel': [('readonly', True)], 'approve': [('readonly', True)]})
    child_ids_count = fields.Integer(compute='_compute_child_ids_count') 
    
    report_id = fields.Many2one('ir.actions.report', string="Report", domain="[('model','=','hr.5ta.line'),('report_type','=','qweb-pdf')]", default=lambda self: self.env.ref('hr_5ta.action_report_5ta', False))
    
    dic = {
        1: 0, 
        2: 0, 
        3: 0, 
        4: 3, 
        5: 4,
        6: 4,
        7: 4, 
        8: 7,
        9: 8,
        10: 8,
        11: 8,
        12: 11,
    }
    
    ################################### STATIC METHODS ##################################################
    
    @staticmethod
    def _last_day(any_date=None, year=None, month=None):
        last_day = calendar.monthrange(int(year or any_date.year), int(month or any_date.month))[1]
        return any_date.replace(day=last_day) if any_date else date(int(year), int(month), last_day)

    ################################### COMPUTES ##################################################

    @api.depends('year', 'month')
    def _compute_date_5ta(self):
        for rec in self:
            if rec.year and rec.month:
                rec.date_5ta = self._last_day(year=rec.year, month=rec.month)

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for rec in self:
            rec.child_ids_count = len(rec.child_ids)

    ################################### FUNCTION ##################################################

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

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

    def _filter_employees(self,employees,date):
        # date_from = datetime.strptime(str(date.year)+'-'+str(date.month)+'-01',"%Y-%m-%d").date()
        # date_to = date_from + relativedelta(months=1)         
        employees =  employees.filtered(lambda x: x.first_contract_date and x.first_contract_date <= date) # filtramonth_5ta_employeedo de los empleados segun condiciones
        return employees

    ###########################################################################################################################

    def rem_variable(self, employee, payslip):
        line_ids = payslip.filtered(lambda x: x.employee_id.id == employee ).line_ids
        line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_5ta_grati == True and x.amount > 0) 

        average = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))

        for code in codes:
            line_ids_2 = line_ids.filtered(lambda x: x.code == code)

            if len(line_ids_2) >= 3:
                amount = sum([line_id.amount for line_id in line_ids_2])
                average += amount/6
        return average

    #############################################################################################################################

    # def step_uit(self, value, date, tramo_5ta, uit_5ta_list):
    #     # tramo_5ta = self.env["tramo.5ta"].search([], order = 'id asc')
    #     # uit_5ta = self.env["uit.table"].search([("year","=", date.year)], limit=1) 
    #     uit_5ta = uit_5ta_list.filtered(lambda x: x.year == date.year)
        
    #     list_tramo, list_value = [], []

    #     if(uit_5ta):
    #         if(value < 0):
    #             return [0,0,0,0,0,0]
    #         list_tramo = [((tramo.uit_from * uit_5ta.value, tramo.uit_to * uit_5ta.value, tramo.percentage)) if tramo.uit_from * uit_5ta.value <= value else (0, 0, 0) for tramo in tramo_5ta ]

    #     if(list_tramo):
    #         list_value = [((step[1] - step[0])*step[2]/100) if (value > step[1]) else ((value - step[0])*step[2]/100) for step in list_tramo]

    #     porcent = max([i[2] for i in list_tramo]) 

    #     return [sum(list_value), list_value[0], list_value[1], list_value[2], list_value[3], list_value[4], porcent]

    def step_uit(self, value, date, tramo_5ta, uit_5ta_list):
        # _logger.info("--------------1--------------")
        # _logger.info(value)
        # _logger.info(date)
        # _logger.info(tramo_5ta)
        # _logger.info(uit_5ta_list)
        # _logger.info("--------------22222--------------")
        uit_5ta = uit_5ta_list.filtered(lambda x: x.year == date.year)
        list_value = [0, 0, 0, 0, 0, 0]  # Inicializar con ceros
        # _logger.info(uit_5ta)
        if uit_5ta:
            # _logger.info(tramo_5ta)
            for tramo in tramo_5ta:
                index = int(tramo.code) - 1
                tramo_from = tramo.uit_from * uit_5ta.value
                tramo_to = tramo.uit_to * uit_5ta.value
                percentage = tramo.percentage
                if value > tramo_to:
                    contribution = (tramo_to - tramo_from) * percentage / 100
                elif value > tramo_from:
                    contribution = (value - tramo_from) * percentage / 100
                else:
                    contribution = 0
                list_value[index] = contribution
                # list_value.append(contribution)
                # _logger.info("list_value")
                # _logger.info(list_value)

        if tramo_5ta:
            porcent = max([tramo.percentage for tramo in tramo_5ta] + [0])
        else:
            porcent = 0
        # _logger.info("porcent")
        # _logger.info(porcent)
        
        # _logger.info([sum(list_value[:6])] + list_value[:6] + [porcent])
        return [sum(list_value[:6])] + list_value[:6] + [porcent]  # Limita los resultados a los primeros 6




    def grati_projection(self, date_5ta, salary, family, employee_id, bono_input, health_regime, employee, grati_line, payslips):
        date_from = datetime.strptime(str(date_5ta.year)+'-01-01',"%Y-%m-%d").date()
        date_to = datetime.strptime(str(date_5ta.year)+'-06-30',"%Y-%m-%d").date()

        date_from_2 = datetime.strptime(str(date_5ta.year)+'-07-01',"%Y-%m-%d").date()
        date_to_2 = datetime.strptime(str(date_5ta.year)+'-12-31',"%Y-%m-%d").date()

        # payslips = self.env["hr.payslip"].search([("struct_id.type_id.id","=",self.regimen_id.id), ("struct_id.company_id.id","=",self.company_id.id),], order = 'id desc',)
        
        ######################################
        if(employee.last_contract_date and employee.last_contract_date.month == date_5ta.month and employee.last_contract_date.year == date_5ta.year):
            return [0, 0, 0, 0, 0]
        ######################################

        if(date_from <= date_5ta <= date_to):
            payslips = payslips.filtered(lambda x: x.date_from >= date_from and x.date_to <= date_to)
            if payslips:
                avarage_varible = self.rem_variable(employee_id, payslips)
                
                first_date = employee.first_contract_date 
                
                if(first_date.year == date_5ta.year):
                    
                    if(first_date.day == 1):
                        proportion = (6 - first_date.month + 1) / 6
                    else:
                        proportion = (6 - first_date.month) / 6
                else:
                    proportion = 1
                
                regimen_peru = employee.contract_id.peru_employee_regime.abbr
                if regimen_peru == "RG":
                    base_grati = (avarage_varible + salary + family)
                elif regimen_peru == "RM":
                    base_grati = 0
                elif regimen_peru == "RP":
                    base_grati = (avarage_varible + salary + family)/2

                _logger.info("---------------grati_projection---------------")
                _logger.info(employee.name)
                _logger.info(regimen_peru)
                _logger.info(base_grati)
                _logger.info([base_grati*proportion + base_grati, 0, 0, 0, 0])
                    
                return [base_grati*proportion + base_grati, 0, 0, 0, 0]
        
        
        elif(date_from_2 <= date_5ta <= date_to_2 and date_5ta.month != 12):
            payslips = payslips.filtered(lambda x: x.date_from >= date_from_2 and x.date_to <= date_to_2 and x.employee_id.id == employee_id)
            if payslips:

                avarage_varible = self.rem_variable(employee_id, payslips)

                # grati_real = self.env["hr.grati.line"].search([("employee_id", "=", employee_id), ("date_from","=",date_from), ("date_to","=",date_to)], order = 'id desc', limit=1)
                grati_real = grati_line.filtered(lambda x: x.employee_id.id == employee_id and x.date_from == date_from and x.date_to == date_to)

                first_date = payslips.employee_id.first_contract_date 
                
                if(first_date.year == date_5ta.year and first_date.month >=7):
                    if(first_date.day == 1):
                        proportion = (12 - first_date.month + 1) / 6
                    else:
                        proportion = (12 - first_date.month) / 6
                else:
                    proportion = 1

                regimen_peru = employee.contract_id.peru_employee_regime.abbr
                if regimen_peru == "RG":
                    base_grati = (avarage_varible + salary + family)
                elif regimen_peru == "RM":
                    base_grati = 0
                elif regimen_peru == "RP":
                    base_grati = (avarage_varible + salary + family)/2
                
                _logger.info("---------------222---------------")
                _logger.info(employee.name)
                
                return [base_grati * proportion, grati_real.total, 0, grati_real.health_regimen, 0]
        
        elif(date_from_2 <= date_5ta <= date_to_2 and date_5ta.month == 12):
            payslips = payslips.filtered(lambda x: x.date_from >= date_from_2 and x.date_to <= date_to_2)
            if payslips:
                avarage_varible = self.rem_variable(employee_id, payslips)

                # grati_real = self.env["hr.grati.line"].search([("employee_id", "=", employee_id), ("date_from","=",date_from), ("date_to","=",date_to)], order = 'id desc', limit=1)
                grati_real = grati_line.filtered(lambda x: x.employee_id.id == employee_id and x.date_from == date_from and x.date_to == date_to)
                # grati_real_2 = self.env["hr.grati.line"].search([("employee_id", "=", employee_id), ("date_from","=",date_from_2), ("date_to","=",date_to_2)], order = 'id desc', limit=1)    
                grati_real_2 = grati_line.filtered(lambda x: x.employee_id.id == employee_id and x.date_from == date_from_2 and x.date_to == date_to_2)  

                _logger.info("---------------333---------------")
                _logger.info(employee.name)
                
                return [0, grati_real.total, grati_real_2.total, grati_real.health_regimen, grati_real_2.health_regimen]

        return [0, 0, 0, 0, 0]

    def filter_payslip(self, date, payslip_line):
        payslip_line = payslip_line.filtered(lambda x: x.date_from <= date and x.date_to >= date )

        #payslip_line = payslip_line.filtered(lambda x: x.salary_rule_id.have_5ta == True)
        
        average = 0
        codes = payslip_line.mapped("code")
        codes = list(set(codes))        
        
        for code in codes:
            payslip_line_2 = payslip_line.filtered(lambda x: x.code == code)
            
            amount = sum([line_id.amount for line_id in payslip_line_2])
            average += amount
            
        # _logger.debug('AVERAGE: ' + str(average)) #imprime en el log de odoo sh

        return average

    def condition_contract(self, employee_id, date_5ta, salary, movil, family_asig, meses, from_range, to_range, extra, tax, payslip_line_line):
        # payslip_line = self.env["hr.payslip.line"].search([("employee_id", "=", employee_id.id), ("salary_rule_id.have_5ta","=",True)], order = 'id desc')
        payslip_line = payslip_line_line.filtered(lambda x: x.employee_id.id == employee_id.id and x.salary_rule_id.have_5ta == True)
        
        list_total = []
        # x.salary_rule_id.have_5ta == True
        for i in range(from_range-1, to_range):
            date = date_5ta - relativedelta(months=(date_5ta.month-i))
            list_total.append(self.filter_payslip(date, payslip_line))

        
        if(employee_id.last_contract_date and employee_id.last_contract_date.month == date_5ta.month and employee_id.last_contract_date.year == date_5ta.year):
            return [0, sum(list_total) , sum(list_total) + extra, extra, tax, list_total[-1]]

        return [salary*meses + family_asig*meses + movil * meses, sum(list_total) , sum(list_total) + extra, extra, tax, list_total[-1]]

    def salary_projection(self, employee_id, date_5ta, salary, family_asig, movil, payslip_line):
        meses = 12 - date_5ta.month 
        if(employee_id.first_contract_date < datetime.strptime(str(date_5ta.year)+'-01-01',"%Y-%m-%d").date()):
            return self.condition_contract(employee_id, date_5ta, salary, movil, family_asig, meses, 2, date_5ta.month+1, 0, 0, payslip_line)

        elif(1 <= employee_id.first_contract_date.month <= date_5ta.month and employee_id.first_contract_date.year == date_5ta.year):
            return self.condition_contract(employee_id, date_5ta, salary, movil, family_asig, meses, employee_id.first_contract_date.month+1, date_5ta.month+1, employee_id.salary_amount, employee_id.amount_5ta, payslip_line)
        
        else: 
            return [0,0,0,0,0,0]

    def rap_5ta(self, grati_project, salary_project, salary_amount, last_month_salary, salary_amount_5ta, bon_gen, utility, lbs):
        return grati_project + salary_project + salary_amount + salary_amount_5ta + bon_gen + utility + lbs

    def base_5ta_employee(self, date_5ta, rap, uit_5ta_list):  
        #uit_5ta = self.env["uit.table"].search([("year","=",date_5ta.year)], limit=1)
        uit_5ta = uit_5ta_list.filtered(lambda x: x.year == date_5ta.year)
        uit = uit_5ta.value
        deduction = uit_5ta.value * 7
        base_5ta = rap - deduction
        if(base_5ta < 0):
            base_5ta = 0

        return [base_5ta, uit, deduction]

    def data_5ta_employee(self, base_5ta, date_5ta, tramo_5ta, uit_5ta_list):
        result = self.step_uit(base_5ta, date_5ta, tramo_5ta, uit_5ta_list)
        return result[:7]
        # return self.step_uit(base_5ta, date_5ta, tramo_5ta, uit_5ta_list)

    def month_5ta_employee(self, data_5ta,  date_5ta, payslip_line, amount_5ta, employee):
        if(employee.last_contract_date):
            if(employee.last_contract_date.month == date_5ta.month and employee.last_contract_date.year == date_5ta.year):
                list_5ta = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA').total for i in range(1, date_5ta.month + 1 )]
                list_5ta_direct = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA_DIRECT').total for i in range(1, date_5ta.month + 1)]
            else:
                if(date_5ta.month > 3):
                    list_5ta = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA').total for i in range(1, self.dic[date_5ta.month] + 1 )]
                    list_5ta_direct = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA_DIRECT').total for i in range(1, self.dic[date_5ta.month] + 1)]

                else:
                    list_5ta = []
                    list_5ta_direct = []
        
        else:
            if(date_5ta.month > 3):
                list_5ta = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA').total for i in range(1, self.dic[date_5ta.month] + 1 )]
                list_5ta_direct = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == '5TA_DIRECT').total for i in range(1, self.dic[date_5ta.month] + 1)]

            else:
                list_5ta = []
                list_5ta_direct = []
            
            
        amount_retention = sum(list_5ta)*-1 + sum(list_5ta_direct)*-1
        
        balance = data_5ta - amount_retention - amount_5ta

        if(1 <= date_5ta.month <= 3):
            total = balance / 12
        elif(date_5ta.month == 4):
            total = balance / 9
        elif(5 <= date_5ta.month <= 7):
            total = balance / 8
        elif(date_5ta.month == 8):
            total = balance / 5
        elif(9 <= date_5ta.month <= 11):
            total = balance / 4
        else:
            total = balance / 1

        return [balance, total, amount_retention]

    def utility(self, date_5ta, payslip_line):
        list_utility = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == 'UTI').total for i in range(1, date_5ta.month + 1)]
        return sum(list_utility)

    def LBS(self, date_5ta, payslip_line,):
        list_lbs = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == 'LBS').total for i in range(1, date_5ta.month + 1)]
        return sum(list_lbs)

    def return_5ta(self, sum_retention, data_5ta):
        return data_5ta - sum_retention

    def compute_sheet(self):
        # with Cprofile.Profile() as profile:
        ###################################################################################################
        self.ensure_one()

        if any(data.state in ('approve') for data in self):
            raise UserError(_('You cannot compute a category 5ta which is not draft or cancelled!'))

        payslip_pays = self._delete_data()

        # self.child_ids.subline_ids.unlink()
        # self.child_ids.unlink()

        payslips = self.env["hr.payslip"].search([
            ("struct_id.type_id.id","=",self.regimen_id.id),
            ("struct_id.company_id.id","=",self.company_id.id),], order = 'id desc')
        
        grati_line = self.env["hr.grati.line"].search([], order = 'id desc') 
        uit_5ta_list = self.env["uit.table"].search([])
        tramo_5ta = self.env["tramo.5ta"].search([], order = 'id asc')

        val_list = []
        if payslips:
            
            employees = payslips.mapped("employee_id")
            employees = self._filter_employees(employees,self.date_5ta)
            

            for employee in employees:
                
                if(employee.last_contract_date and ((employee.last_contract_date.month < self.date_5ta.month and employee.last_contract_date.year <= self.date_5ta.year) or (employee.last_contract_date.month >= self.date_5ta.month and employee.last_contract_date.year < self.date_5ta.year))):
                    continue
                else:
                    
                    grati_project, grati, grati_2, grati_9por, grati_9por_2 = self.grati_projection(self.date_5ta, employee.contract_id.wage, 102.50 if employee.children > 0 else 0, employee.id, 0, employee.health_regime_id.code, employee, grati_line, payslips)

                    if(employee.health_regime_id.code == "02"):
                        bon_gen = grati_project * 0.0675
                    else:
                        bon_gen = grati_project * 0.09
                    
                    payslip_line = payslips.filtered(lambda x: x.employee_id.id == employee.id).line_ids.sorted(lambda x:x.id, reverse=True)
                    # _logger.warning("-------------------------%s-------%s" % (payslip_line,employee.name))
                    utility = 0
                    lbs = 0
                    
                    salary_project, salary_amount, remuneration_afected, salary_amount_5ta, amount_5ta, last_month_salary = self.salary_projection(employee, self.date_5ta, employee.contract_id.wage, employee.contract_id.move_sa, 102.50 if employee.children > 0 else 0, payslip_line)
                    rap = self.rap_5ta(grati_project, salary_project, salary_amount, last_month_salary, salary_amount_5ta, bon_gen, utility, lbs)
                    base_5ta, uit, deduction = self.base_5ta_employee(self.date_5ta, rap, uit_5ta_list)
                    data_5ta, step_1, step_2, step_3, step_4, step_5, porcent = self.data_5ta_employee(base_5ta, self.date_5ta, tramo_5ta, uit_5ta_list)

                    balance, mounth_5ta, amount_retention = self.month_5ta_employee(data_5ta, self.date_5ta, payslip_line, amount_5ta, employee)
                    
                    tax_total = amount_5ta + data_5ta

                    afected = rap - salary_amount_5ta
                    
                    return_5ta = 0
                    if(self.date_5ta.month == 12):
                        return_5ta = self.return_5ta(amount_retention, data_5ta)
                    structure_type_abbr = self.child_ids.filtered(lambda line: line.employee_id.id == employee.id).mapped('structure_type_abbr')
                    structure_type_abbr = structure_type_abbr[0] if structure_type_abbr else None


                    val = {
                        "date_5ta":self.date_5ta,
                        "name":"5TA CATEGORIA " + employee.name,
                        "employee_id":employee.id,
                        "structure_type_abbr": structure_type_abbr,
                        "salary":   employee.contract_id.wage,
                        "family_asig": 102.50 if employee.children > 0 else 0,
                        "grati": grati,
                        "grati_2": grati_2,
                        "grati_9por": grati_9por,
                        "grati_9por_2": grati_9por_2,
                        "grati_projection": grati_project,
                        "salary_projection": salary_project,
                        "rap": rap,
                        "base_5ta": base_5ta,
                        "data_5ta": data_5ta,
                        "parent_id":self.id,
                        # "subline_ids": [(0,0,subline) for subline in self._compute_sublines(employee, payslips, self.date_5ta, data_5ta)],
                        "salary_amount": salary_amount,
                        "salary_amount_5ta": salary_amount_5ta,
                        "amount_5ta": amount_5ta,
                        "deduction": deduction,
                        "uit": uit,
                        "remuneration_afected": remuneration_afected,
                        "step_1": step_1,
                        "step_2": step_2,
                        "step_3": step_3,
                        "step_4": step_4,
                        "step_5": step_5,
                        "tax_total": tax_total,
                        "afected": afected,
                        "movilidad": employee.contract_id.move_sa,
                        "data_5ta_mensual": mounth_5ta,
                        "last_month_salary": last_month_salary,
                        "bon_gen": bon_gen,
                        "amount_retention": amount_retention,
                        "balance": balance,
                        "person_percent_max": porcent,
                        "lbs": lbs,
                        "return_5ta": return_5ta,
                    }
                    
                    val_list.append(val)
            self.env["hr.5ta.line"].create(val_list)    
            self.env.cr.commit()
            self.compute_sheet_import(payslip_pays)     
            return  
        # results = pstats.Stats(profile)

    def compute_sheet_import(self,payslip_pays):
        employees = self.child_ids.mapped("employee_id")
        # payslip = self.env['hr.payslip'].search([("date_from","<=",self.date_5ta),("date_to",">=",self.date_5ta)])
        payslip = payslip_pays

        # FUNCION PARA CREAR LOS INPUTS NECESARIOS EN EL PAYSLIP
        codes_to_create = ["I_5TA","I_DEV_IMP_5TA"]

        inputs_to_create = self.env['hr.payslip.input.type'].search([('code','in',codes_to_create)])
        inputs_to_create = inputs_to_create.filtered(lambda x:x.company_id.id == self.env.company.id).ids

        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id.id == employee.id).input_line_ids

            for new in inputs_to_create:
                if new not in input.mapped('input_type_id').ids:
                    payslip.write({'input_line_ids': [(0,0,{'input_type_id':new,'amount':0})]})

            final_input = input.filtered(lambda x: x.input_type_id.code == "I_5TA")
            final_input_2 = input.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
            filter = self.child_ids.filtered(lambda x: x.employee_id.id == employee.id and x.date_5ta == self.date_5ta)
            total = filter.data_5ta_mensual
            
            return_5ta = filter.return_5ta

            if(self.date_5ta != 12):
                if total > 0:
                    final_input.amount = abs(float(total))
                else:
                    final_input.amount = 0
                
            else:
                if(return_5ta >= 0):
                    final_input.amount = float(return_5ta)
                else:
                    final_input_2.amount = abs(float(return_5ta))
                    
        payslip.compute_sheet()
    # @@@
    def _delete_data(self):
        employees = self.child_ids.mapped('employee_id')
        payslip = self.env['hr.payslip'].search([
            ('date_from', '<=', self.date_5ta),
            ('date_to', '>=', self.date_5ta),
        ])
        for employee in employees:
            input = payslip.filtered(lambda x: x.employee_id.id == employee.id).input_line_ids
            final_input = input.filtered(lambda x: x.input_type_id.code == "I_5TA")
            final_input_2 = input.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
            
            final_input.amount = 0.00
            final_input_2.amount = 0.00

        payslip.compute_sheet()

        self.child_ids.subline_ids = [(5,0,0)]
        self.child_ids = [(5,0,0)]
        return payslip 
    
    def _compute_sublines(self, employee, payslip, date_5ta, data_5ta):
        sublines = [] 

        list_retention = []
        for month in range(1,13):
            if 1 <= month <= 3:
                list_retention.append(data_5ta / 12)
            elif month == 4:
                list_retention.append((data_5ta - sum(list_retention[0:3])) / 9)
            elif 5 <= month <= 7:
                list_retention.append((data_5ta - sum(list_retention[0:4])) / 8)
            elif month == 8:
                list_retention.append((data_5ta - sum(list_retention[0:7])) / 5)
            elif 9 <= month <= 11:
                list_retention.append((data_5ta - sum(list_retention[0:8])) / 4)
            else:
                list_retention.append(data_5ta - sum(list_retention))

            sublines.append({
            "mes": MONTH_ABBR[int(month)-1],
                "sequence": month,
                "anio": date_5ta.year,
                "retention": list_retention[month-1]
            })
            
        return sublines

    def action_dowload_report_pdf(self):
        self.ensure_one()
        return {
            'name': '5TA',
            'type': 'ir.actions.act_url',
            'url': '/print/5ta?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x.id) for x in self.child_ids)},
        } 

    def action_dowload_report_tabular_5ta(self):
        for obj in self:
            values = []

            for child_id in obj.child_ids:

                uit_5ta = self.env["tramo.5ta"].search([])

                list_5ta = [[tramo.uit_from, tramo.uit_to, tramo.percentage] for tramo in uit_5ta]

                val1 = {
                    "tramo": list_5ta,
                    "fecha de 5ta": self.date_5ta or '',
                    "cliente": self.company_id.name or '',
                    "Cod.": child_id.employee_id.cod_ref or '',
                    "dni": child_id.employee_id.identification_id or '',
                    "apellidos y nombres": child_id.employee_id.name or '',
                
                    "CENTRO DE COSTO":child_id.employee_id.cod_coste_center.name or '',
                    "LOCALIDAD": child_id.employee_id.location_id.name or '',
                    "AREA/DEPARTAMENTO":child_id.employee_id.department_id.name or '',
                    
                    "fecha de ingreso": child_id.employee_id.first_contract_date or '',
                    "ingreso anterior": child_id.employee_id.amount_5ta or 0,
                    "total ingreso": child_id.salary_amount or 0,
                    "remuneracion afecta": child_id.last_month_salary or 0,
                    "proyeccion mensual": child_id.salary_projection or 0,
                    "proyeccion gratificacion": child_id.grati_projection + child_id.bon_gen or 0,
                    "identification": child_id.identification_id or '',
                }

                val3 = {
                    "uit": child_id.uit,
                    "proyeccion gratificacion nav": child_id.grati_2 + child_id.grati_9por_2 or 0,
                    "renta bruta anual": child_id.rap or 0,
                    "renta neta anual": child_id.base_5ta or 0,
                    "resultado ir": child_id.amount_retention or 0,
                    "impuesto retenido acumulado": '',
                    "impuesto retenido anterior": child_id.amount_5ta or 0,
                    "saldo": child_id.balance or 0,
                    "retencion mes": child_id.data_5ta_mensual or 0,
                    "sum acum": round(sum(obj.child_ids.mapped('salary_amount')),2),
                    "sum afec": round(sum(obj.child_ids.mapped('last_month_salary')),2),
                    "sum monto proy": round(sum(obj.child_ids.mapped('salary_projection')),2),
                    "sum grati proy": round(sum(obj.child_ids.mapped('grati_projection')),2) + round(sum(obj.child_ids.mapped('bon_gen')),2),
                    "sum bruta": round(sum(obj.child_ids.mapped('rap')),2),
                    "sum neta": round(sum(obj.child_ids.mapped('base_5ta')),2),
                    "sum result": round(sum(obj.child_ids.mapped('amount_retention')),2),
                    "sum saldo": round(sum(obj.child_ids.mapped('balance')),2),
                    "sun reten": round(sum(obj.child_ids.mapped('data_5ta_mensual')),2),
                
                }

                val = {**val1, 
                       **val3}

                values.append(val)
            obj.generate_excel(values)

    def generate_excel(self,data):
        report_xls = Excel5taReport(data, self)
        values = {
            'xls_filename': "REPORTE RETENCION TABULAR "+self.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)

    def action_open_hr_5ta(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.5ta.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros 5TA",
        }

    def unlink(self):
        self.child_ids.unlink()
        return super(imp5ta,self).unlink()

    ################################## EVENTS #########################################################################

    @api.onchange("date_5ta")
    def _compute_name(self):
        if(self.date_5ta):
            self.name = "5TA CATEGORIA - " + str(self.date_5ta.strftime("%b")).upper() + " " + str(self.date_5ta.year)

    #####################################################################################################################


class imp5taLine(models.Model):
    _name = 'hr.5ta.line'
    _description = '5TA CATEGORIA DETALLE'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(STATES_SELECTION, string="State", default='draft', tracking=True, copy=False)

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def action_payslip_approve(self):
        if any(slip.state in ('refuse', 'cancel') for slip in self):
            raise UserError(_('Cannot mark gratification as approve if not confirmed.'))
        self.write({'state': 'approve'})

    parent_id = fields.Many2one("hr.5ta",string="5TA CATEGORIA", ondelete='cascade')

    date_5ta = fields.Date(related = "parent_id.date_5ta", store=True,)

    name = fields.Char(string="Nombre", store=True,)

    first_day_contract = fields.Date(related = "employee_id.first_contract_date",  string= "Fecha de ingreso", store = True)
    last_day_contract = fields.Date(related = "employee_id.last_contract_date",  string= "Fecha de salida", store = True)
    identification_id = fields.Char(string="Num. Doc.", store=True, related = "employee_id.identification_id",)


    employee_id = fields.Many2one("hr.employee", string="Empleados", readonly=True)
    salary = fields.Float(string="Sueldo de Contrato", default= 0)
    family_asig = fields.Float(string="Asignación Familiar", readonly=True, default= 0)
    movilidad = fields.Float(string="Movilidad y Alimentación", readonly=True, default= 0)

    grati = fields.Float(string="Gratificación periodo 1", default= 0, store = True)
    grati_2 = fields.Float(string="Gratificación periodo 2", default= 0, store = True)
    
    grati_9por = fields.Float(string="Bono Extra. periodo 1", default= 0, store = True)
    grati_9por_2 = fields.Float(string="Bono Extra. periodo 2", default= 0, store = True)

    bono_input = fields.Float(string="Bono", store = True, default= 0)
    subline_ids = fields.One2many("hr.5ta.subline","line_5ta",string="Variables")


    grati_projection = fields.Float(string="Proy. de Grati.", default= 0,  compute='_compute_grati_projection', store = True)

    salary_projection = fields.Float(string="Proy. de sueldo", default= 0,  compute='_compute_salary_projection', store = True)

    rap = fields.Float(string="Rem. Bruta", default= 0,  compute='_compute_rap', store = True)

    base_5ta = fields.Float(string="Rem. Neta", default= 0,  compute='_compute_base_5ta', store = True)
    data_5ta = fields.Float(string="Imp. Anual", default= 0,  compute='_compute_data', store = True)

    data_5ta_mensual = fields.Float(string="Ret. mensual", default= 0,  store = True)
        
    uit = fields.Float(string="UIT 5ta", default= 0, store = True)
    deduction = fields.Float(string="Deducción 5ta", default = 0, store = True)

    salary_amount = fields.Float(string="Sueldo acumulado", default = 0, store = True)
    remuneration_afected = fields.Float(string="Remuneración afectada", default = 0)

    salary_amount_5ta = fields.Float(string="Otra CIA.", default = 0, store = True)
    amount_5ta = fields.Float(string="Impuesto recepcionado", default = 0, store = True)

    direct_5ta = fields.Float(string="Quinta directa", default = 0, store = True)
    last_month_salary = fields.Float(string="Rem. Men.", default = 0, store = True)
    bon_gen = fields.Float(string="Bonif.", default = 0, store = True)

    amount_retention = fields.Float(string="Result IR.", default = 0, store = True)

    balance = fields.Float(string="Saldo", default = 0, store = True)

    afected = fields.Float(string="Remuneracion bruta y total", default = 0, store = True)

    step_1 = fields.Float(string="Escalon 1", default = 0, store = True)
    step_2 = fields.Float(string="Escalon 2", default = 0, store = True)
    step_3 = fields.Float(string="Escalon 3", default = 0, store = True)
    step_4 = fields.Float(string="Escalon 4", default = 0, store = True)
    step_5 = fields.Float(string="Escalon 5", default = 0, store = True)

    tax_total = fields.Float(string="Impuesto total recepcionado", default = 0, store = True)

    lbs = fields.Float(string="LBS", default = 0, store = True)

    person_percent_max = fields.Float(string="Porcentaje de 5ta", default=0, store=True,)
    
    direct_5ta = fields.Float(string="5ta directa", default=0, store=True,)
    
    return_5ta = fields.Float(string="Devoloción de 5ta categoria", default=0, store=True,)
    
    xls_filename_line = fields.Char()
    xls_binary_line = fields.Binary('Reporte Excel')

    structure_type_abbr = fields.Char(string="Tipo de Regimen", related='employee_id.contract_id.peru_employee_regime.abbr', store=True)
    ############################## FUNCTION #############################################################
    
    ############################## REPORTS #######################################
    
    # def action_dowload_report_tabular_5ta_line(self):
    
    #     for obj in self:
    #         values = []

    #         # for child_id in obj.child_ids:

    #         uit_5ta = self.env["tramo.5ta"].search([])

    #         list_5ta = [[tramo.uit_from, tramo.uit_to, tramo.percentage] for tramo in uit_5ta]

    #         val1 = {
    #             "tramo": list_5ta,
    #             "fecha de 5ta": self.date_5ta or '',
    #         }

    #         val3 = {
    #             "uit": obj.uit,
    #             "rap": obj.rap,
    #         }

    #         val = {**val1, 
    #                 **val3}

    #         values.append(val)

    #         obj.generate_excel(values)
            
    # def generate_excel(self,data):
    #     report_xls = Excel5taLineReport(data, self)
    #     values = {
    #         'xls_filename_line': "REPORTE RETENCION VERTICAL "+self.name + ".xlsx",
    #         'xls_binary_line': base64.encodebytes(report_xls.get_content()),
    #     }
    #     self.write(values)
    
    def action_dowload_report_pdf(self):
        return {
            'name': '5TA',
            'type': 'ir.actions.act_url',
            'url': '/print/5ta?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        }
        
    ###################################################################################################################
    
    @api.depends('lbs')
    def _compute_lbs(self):
        for record in self:
            if(record.employee_id.health_regime_id.code == '02'):
                record.health_regimen = record.total * 6.75 / 100
                record.health_bool = 'Sí'
            else:
                record.health_regimen = record.total * 9 / 100
                record.health_bool = 'No'
    
    #####################################################################################################   

    ############################## EVENT ################################################################

    #####################################################################################################

    
    def unlink(self):
        
        for element in self:
            pay = self.env["hr.payslip"].search([("date_from","<=",element.date_5ta),
                                        ("date_to",">=",element.date_5ta),
                                        ("employee_id.id","=",element.employee_id.id),
                                        ])
            for line in pay.input_line_ids.filtered(lambda x: x.input_type_id.code in ["I_5TA","I_DEV_IMP_5TA"]):
                line.amount = 0

            pay.compute_sheet()

        return super(imp5taLine,self).unlink()

class imp5taSubLine(models.Model):
    _name = 'hr.5ta.subline'
    _description = 'APLICAR RETENCION'

    line_5ta = fields.Many2one("hr.5ta.line", ondelete='cascade', store=True,readonly=True)

    sequence = fields.Integer(string="Secuencia", store=True, readonly=True)
    anio = fields.Integer(string="Año", store=True, readonly=True)
    mes = fields.Char(string="Mes", store=True, readonly=True)
    retention = fields.Float(string="Retención", store=True)
