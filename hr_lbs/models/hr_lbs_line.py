from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class LbsLine(models.Model):
    _name = 'hr.lbs.line'
    _description = 'LBS de Empleado'

    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    date_from = fields.Date(related = "parent_id.date_from",store=True,)
    date_to = fields.Date(related = "parent_id.date_to",store=True,)
    parent_id = fields.Many2one("hr.lbs", string="LBS",ondelete='cascade',store=True,)
    name = fields.Char(string="Nombre", compute="_compute_name",store=True,default="")
    state = fields.Selection([
        ('draft', 'BORRADOR'),
        ('verify', 'EN ESPERA'),
        ('done', 'HECHO'),
        ('paid', 'PAGADO'),
        ('cancel', 'RECHAZADA')],
        string='Estado', default='draft', tracking=True,)
    
    @api.depends('employee_id')
    def _compute_name(self):
        for record in self:
            record.name = "LBS " + record.employee_id.name


    employee_id = fields.Many2one("hr.employee",string="Empleado",store=True,)
    payslip_id = fields.Many2one("hr.payslip", string="Nómina", store=True,)

    @staticmethod
    def _compute_last_contract_date(last_contract_date):
        meses = {
            1: "Enero",
            2: "Febrero",
            3: "Marzo",
            4: "Abril",
            5: "Mayo",
            6: "Junio",
            7: "Julio",
            8: "Agosto",
            9: "Septiembre",
            10: "Octubre",
            11: "Noviembre",
            12: "Diciembre",
        }

        dias = {
            0: "Domingo",
            1: "Lunes",
            2: "Martes",
            3: "Miércoles",
            4: "Jueves",
            5: "Viernes",
            6: "Sábado",
        }

        numero_mes = last_contract_date.month
        # A entero para quitar los ceros a la izquierda en caso de que existan
        numero_dia = int(last_contract_date.strftime("%w"))
        # Leer diccionario
        dia = dias.get(numero_dia)
        mes = meses.get(numero_mes)
        # Formatear
        return "{}, {} de {} del {}".format(dia, last_contract_date.day, mes, last_contract_date.year)

    @staticmethod    
    def _first_day_of_month(any_day):
        return any_day - timedelta(days=(any_day.day  - 1))
    
    @staticmethod    
    def _last_day_of_month(any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        # this will never fail 
        return next_month - timedelta(days=next_month.day)

    def _is_last_day_of_month(self,date):
            return self._last_day_of_month(date) ==  date

    def _compute_time_service(self,first_contract_date,last_contract_date):
        diff = relativedelta(last_contract_date,first_contract_date)
        days = diff.days + 1
        months = diff.months
        years = diff.years
        
        years = years or 0
        months = months or 0
        days = days or 0
        if self._last_day_of_month(last_contract_date) == last_contract_date and first_contract_date.day == 1:
            days = 0
            months += 1
            if months == 12 :
                years  += 1
                months = 0

        return str(years) + " años, " + str(months) + " meses, "+ str(days) + " dias."
    
    def _compute_family_asig(self, employee_id, date_from, date_to) :
        basic_salary = self.env["basic.salary"]._get_basic_salary_in_range(date_from,date_to)
        return basic_salary*0.1 if employee_id.children > 0 else 0
            
    def _is_compute_time_service(self,first_contract_date,last_contract_date):
            diff = relativedelta(last_contract_date,first_contract_date)
            days = diff.days + 1
            months = diff.months or 0
            days = days or 0
            if self._last_day_of_month(last_contract_date) == last_contract_date and first_contract_date.day == 1:
                days = 0
                months += 1

            if months > 0:
                return True
            
            else:
                return False
    """
        INFORMACION EMPLEADO
    """
    first_contract_date = fields.Date(string="Fecha de Ingreso" , store=True,compute="get_personal_information")
    last_contract_date = fields.Date(string="Fecha de Cese",store=True,compute="get_personal_information")
    last_contract_date_words = fields.Char(string="Fecha de Cese en Letras",store=True,compute="get_personal_information")
    time_service = fields.Char(string="Tiempo de Servicio",store=True,compute="get_personal_information")
    reason_low = fields.Char( string="Motivo de Baja",store=True,compute="get_personal_information")
    ref_emp = fields.Char(  store=True,compute="get_personal_information" )
    salary = fields.Float(string="Sueldo Contrato", store=True,)
    family_asig = fields.Float(string="Asignación Familiar",store=True,)
    have_lbs_last_day = fields.Boolean(string="Su liquidacion es a fin de mes?",store=True,)
    peru_employee_regime = fields.Many2one('peru.employee.regime',string="Regimen Laboral",compute="get_personal_information",store=True)
    
    @api.depends('date_from',"date_to","parent_id","name","employee_id","payslip_id")
    def get_personal_information(self):
        for record in self:
            if record.state == "draft":
                record.first_contract_date = record.employee_id.first_contract_date
                record.last_contract_date = record.employee_id.last_contract_date
                record.last_contract_date_words = self._compute_last_contract_date(record.last_contract_date)
                record.time_service =  self._compute_time_service(record.first_contract_date, record.last_contract_date)
                record.reason_low = record.employee_id.contract_id.reason_low_id.name
                record.ref_emp = record.employee_id.cod_ref
                record.salary = record.employee_id.contract_id.wage
                record.family_asig = self._compute_family_asig(record.employee_id, record.date_from, record.date_to, )
                record.have_lbs_last_day = self._is_last_day_of_month(record.last_contract_date)
                record.peru_employee_regime = record.employee_id.contract_id.peru_employee_regime.id
    """
        INFORMACION LOTE
        Se recolecta información de Ingresos. Si el trabajador cesa antes del 30.
    """
    incomes = fields.One2many("hr.lbs.incomes","parent_id",string="Ingresos",compute="_compute_incomes",  store=True,)

    @api.depends('employee_id','payslip_id','last_contract_date')
    def _compute_incomes(self):
        for record in self:
            if record.payslip_id and not self._is_last_day_of_month(record.last_contract_date):
                incomes = [ (0,0,{ "name":i.salary_rule_id.name, "total":i.total, }) for i in record.payslip_id.line_ids.filtered(lambda x: x.category_id.code in ["BASIC","BASIC_NA"]) if i.total > 0]
                record.write({
                    "incomes":incomes
                })

# _______________________MODIFICADO__________________________
    # @api.depends('employee_id','payslip_id','last_contract_date')
    # def _compute_incomes(self):
    #     for record in self:
    #         if record.payslip_id and not record._is_last_day_of_month(record.last_contract_date):
    #             incomes = [
    #                 (0,0,{
    #                     "name": i.salary_rule_id.name,
    #                     "total": i.total
    #                 })
    #                 for i in record.payslip_id.line_ids.filtered( lambda x: (x.salary_rule_id.have_lbs and x.total > 0)
    #                                                             or (x.category_id.code in ["BASIC","BASIC_NA"] and x.total > 0)
    #                                                             )
    #             ]
    #             record.incomes = incomes
    #         else:
    #             record.incomes = []
# _______________________MODIFICADO__________________________
    ########################################################################################################################################################################
    """
        VARIABLES
    """
    ########################################################################################################################################################################

    def _compute_sublines(self, employee, date_from_eval_prom,date_to_eval_prom,type="cts"):
        sublines = []
        line_ids = self.env["hr.payslip"].search([
                                ("date_from",">=",date_from_eval_prom),
                                ("date_to","<=",date_to_eval_prom),
                                ("employee_id","=",employee.id),
                            ]).line_ids
        
        if type=="cts":
            line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_cts == True and x.amount > 0) 
        elif type=="grati":
            line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_gratification == True and x.amount > 0) 
        elif type=="vaca":
            line_ids = line_ids.filtered(lambda x: x.salary_rule_id.have_holiday == True and x.amount > 0) 
        else :
            line_ids = line_ids.filtered(lambda x:  x.salary_rule_id.have_cts == True and x.amount > 0) 

        amount = 0
        codes = line_ids.mapped("code")
        codes = list(set(codes))
        for code in codes:
            line_ids_code = line_ids.filtered(lambda x: x.code == code)
            if len(line_ids_code) >= 3:
                amount = sum([line_id.amount for line_id in line_ids_code])
                average = amount/6
                val = {
                    "name": line_ids_code[0].name,
                    "cont": len(line_ids_code),
                    "amount": amount,
                    "average": average
                }
                sublines.append(val)
        return sublines


    ########################################################################################################################################################################
    """
        CTS
    """
    ########################################################################################################################################################################
    gratification = fields.Float(string="1/6 Graficación", compute='_compute_gratification',store=True,)
    cts = fields.One2many("hr.lbs.cts", "parent_id", compute="_compute_cts", string="CTS LBS",store=True,)
    cts_base_amount = fields.Float(string="Base Imponible de CTS", compute= "_compute_cts_base_amount", store=True,)
    cts_amount = fields.Float(string = "Monto de CTS", compute="_compute_cts_amount", store=True,)
    cts_days = fields.Float(string = "Dias de CTS", compute="_compute_cts_days", store=True,)


    def _get_gratification(self, employee, date_from, date_to):
        date_from_month = date_from.month
        date_from_year = date_from.year

        if 11<= date_from_month :
            date_from =  datetime.strptime("01/12/" + str(date_from_year), '%d/%m/%Y')
            date_to = datetime.strptime("31/12/" + str(date_from_year), '%d/%m/%Y')
        elif 1<= date_from_month <= 4 :
            date_from =  datetime.strptime("01/12/" + str(date_from_year - 1), '%d/%m/%Y')
            date_to = datetime.strptime("31/12/" + str(date_from_year - 1), '%d/%m/%Y')
        else:
            date_from = datetime.strptime("01/07/"+ str(date_from_year), '%d/%m/%Y')
            date_to = datetime.strptime("31/07/"+ str(date_from_year), '%d/%m/%Y')

        pay = self.env["hr.payslip"].search([("date_from",">=",date_from),
                                ("date_to","<=",date_to),
                                ("employee_id","=",employee.id)], limit = 1)
        
        for line in pay.line_ids.filtered(lambda input: input.code == "GRATI"):
            return abs(line.total) if (line and line.total is not None) else 0
        return 0

    @api.depends('employee_id','date_from','date_to')
    def _compute_gratification(self):
        for record in self:
            record.gratification = self._get_gratification(record.employee_id,record.date_from,record.date_to)/6

    def _calculate_cts(self,employee_id,date_from, date_to, salary, family_asig, gratification):
        date_from_year = date_from.year
        date_from_month = date_from.month
        first_contract_date = employee_id.first_contract_date
        last_contract_date = employee_id.last_contract_date

        #_logger.warning("-------CTS 1-----%s---%s" % (employee_id.name,date_from_month))

        if  1 <= date_from_month <= 4 :
            date_from_eval_prom = datetime.strptime("01/11/" + str(date_from_year - 1), '%d/%m/%Y').date()
        elif 11 <= date_from_month :
            date_from_eval_prom = datetime.strptime("01/11/" + str(date_from_year), '%d/%m/%Y').date()
        else:
            date_from_eval_prom = datetime.strptime("01/05/" + str(date_from_year), '%d/%m/%Y').date()

        #_logger.warning("-------CTS-date_from_eval_prom-----%s---%s" % (employee_id.name,date_from_eval_prom))
        
        payslip = self.env["hr.payslip"].search(
            [
                ("employee_id","=",employee_id.id),
                ("date_from",">=",date_from),
                ("date_to","<=",date_to)
            ],limit=1
        )
        #_logger.warning("-------CTS---payslip-----%s---%s" % (employee_id.name,payslip))

        if payslip:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)
        else:
            date_to_eval_prom = self._first_day_of_month(last_contract_date) - relativedelta(days=1)

        if first_contract_date > date_from_eval_prom:
            date_from_eval_prom = first_contract_date
        if last_contract_date < date_to_eval_prom:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)

        initial = date_from_eval_prom
        if (date_from_eval_prom - relativedelta(months=1)) < first_contract_date < date_from_eval_prom:
            initial = first_contract_date

        #_logger.warning("-------CTS---date_from_eval_prom----2-----%s---%s" % (employee_id.name,date_from_eval_prom))
        
        lbs_cts_variables = [(0,0,subline) for subline in self._compute_sublines(employee_id,date_from_eval_prom,date_to_eval_prom,"cts")]
        
        list_vals = []

        while initial <= last_contract_date:

            #_logger.warning("-------CTS initial-----%s" % initial)

            date_to_aux = self._last_day_of_month(initial)
            if initial <= last_contract_date <= date_to_aux:
                date_to_aux = last_contract_date

            periods_month = initial.strftime("%b %Y")

            val = {
                "date_from": initial ,
                "date_to": date_to_aux ,
                "employee_id":employee_id.id,
                "period_month":periods_month,
                "salary":salary,
                "family_asig":family_asig,
                "gratification":gratification,
                "lbs_cts_variables": lbs_cts_variables,
            }
            initial = self._first_day_of_month(initial + relativedelta(months=1)) 
            list_vals.append(val)
        #_logger.warning("-------CTS final-----%s" % list_vals)
        return list_vals

    @api.depends('employee_id','date_from','date_to','salary','family_asig','gratification','incomes')
    def _compute_cts(self):
        for record in self:
            _logger.warning("-------CTS-record in self----%s"%record)
            #if record.peru_employee_regime.abbr != "RM":
            if not record.cts and record._is_compute_time_service(record.first_contract_date, record.last_contract_date) and record.peru_employee_regime.abbr != "RM":
                _logger.warning("-------CTS _is_compute_time_service-----%s" % record._is_compute_time_service(record.first_contract_date, record.last_contract_date))
                _logger.warning("-------CTS-----%s --%s" % (record.employee_id.name, self._calculate_cts(record.employee_id,
                                                                            record.date_from,
                                                                            record.date_to,
                                                                            record.salary,
                                                                            record.family_asig, 
                                                                            record.gratification)))
                record.write({
                    "cts": [(0,0,subline) for subline in self._calculate_cts(record.employee_id,
                                                                            record.date_from,
                                                                            record.date_to,
                                                                            record.salary,
                                                                            record.family_asig, 
                                                                            record.gratification)],
                })

    @api.depends('cts')
    def _compute_cts_base_amount(self):
        for record in self:
            if len(record.cts) == 1:
                record.cts_base_amount = record.cts.base_amount
            elif len(record.cts) > 1:
                record.cts_base_amount = record.cts[0].base_amount

    @api.depends('cts')
    def _compute_cts_amount(self):
        for record in self:
            record.cts_amount = sum([i.amount for i in record.cts])

    @api.depends('cts')
    def _compute_cts_days(self):
        for record in self:
            record.cts_days = sum([i.number_days for i in record.cts])

    """
        GRATIFICACION
    """
    grati = fields.One2many( "hr.lbs.grati", "parent_id",   compute="_compute_grati",string="Gratificación",store=True,)
    grati_amount = fields.Float(string="Monto de Gratificación",compute='_compute_grati_amount',store=True,)
    boni_extra_grati_amount = fields.Float(string="Bonificación Extraordinaria", compute = "_compute_boni_extra_grati_amount", store=True,)

    @api.depends('grati')
    def _compute_grati_amount(self):
        for record in self:
            record.grati_amount = sum([i.amount for i in record.grati])

    @api.depends('grati_amount')
    def _compute_boni_extra_grati_amount(self):
        for record in self:
            if(record.employee_id.health_regime_id.code == '02'):
                record.boni_extra_grati_amount = record.grati_amount * 6.75 / 100
            else:
                record.boni_extra_grati_amount = record.grati_amount * 9 / 100

    def _calculate_grati(self,employee_id,date_from, date_to, salary, family_asig):
        date_from_year = date_from.year
        date_from_month = date_from.month
        first_contract_date = employee_id.first_contract_date
        last_contract_date = employee_id.last_contract_date

        if 1 <= date_from_month <= 6 :
            date_from_eval_prom = datetime.strptime("01/01/" + str(date_from_year), '%d/%m/%Y').date()
        else:
            date_from_eval_prom = datetime.strptime("01/07/" + str(date_from_year), '%d/%m/%Y').date()
            
        payslip = self.env["hr.payslip"].search(
            [
                ("employee_id","=",employee_id.id),
                ("date_from",">=",date_from),
                ("date_to","<=",date_to)
            ],limit=1
        )
        if payslip:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)
        else:
            date_to_eval_prom = self._first_day_of_month(last_contract_date) - relativedelta(days=1)

        if first_contract_date > date_from_eval_prom:
            date_from_eval_prom = first_contract_date
        if last_contract_date < date_to_eval_prom:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)
        
        lbs_grati_variables = [(0,0,subline) for subline in self._compute_sublines(employee_id,date_from_eval_prom,date_to_eval_prom,"grati")]
        list_vals = []
        period = date_from_eval_prom.strftime("%b") + " - " + last_contract_date.strftime("%b")

        val = {
            "date_from": date_from_eval_prom ,
            "date_to": last_contract_date ,
            "employee_id":employee_id.id,
            "period":period,
            "salary":salary,
            "family_asig":family_asig,
            "lbs_grati_variables": lbs_grati_variables,
        }
        list_vals.append(val)
        return list_vals


    def was_grati_paid(self, employee_id, date_from,  date_to, ):
        self.ensure_one()
        grati_line = self.env["hr.grati.line"].search(
            [
                ("employee_id", "=", employee_id.id),
                ("date_from", ">=", date_from),
                ("date_to", "<=", date_to),
                ("parent_id.state", "=", 'approve'),
            ],
            limit=1
        )
        
        if grati_line :
            return True
        return False
        

    @api.depends('employee_id','date_from','date_to','salary','family_asig','incomes')
    def _compute_grati(self):
        for record in self:
            if record.peru_employee_regime.abbr != "RM":
                if not record.grati and record._is_compute_time_service(record.first_contract_date, record.last_contract_date) and not record.was_grati_paid(record.employee_id, record.date_from, record.date_to,):
                    record.write({
                        "grati": [(0,0,subline) for subline in self._calculate_grati(record.employee_id,record.date_from,record.date_to, record.salary, record.family_asig, )],
                    })   
        
    """
        VACACIONES
    """
    vaca = fields.One2many("hr.lbs.vaca",  "parent_id", compute="_compute_vaca", string="Vacación",store=True,)
    vaca_amount = fields.Float(string = "Monto de Vacacion", compute="_compute_vaca_amount", store=True,)


    @api.depends('vaca')
    def _compute_vaca_amount(self):
        for record in self:
            record.vaca_amount = sum([i.amount for i in record.vaca])

    def days360(self,start_date, end_date, method=True):
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        if method:
            start_day = start_date.day
            end_day = end_date.day

            if start_day == 31:
                start_day = 30

            if method and end_day == 31 and start_day < 30:
                end_day = 1

        else:
            start_day = start_date.day
            end_day = end_date.day

            if start_day == 31 or (method and start_date.month == 2 and self.is_last_day_of_feb(start_date)):
                start_day = 30

            if end_day == 31:
                if start_day < 30:
                    end_day = 1
                elif start_date.month == 12:
                    end_day = 30
                else:
                    end_day = 30

        return (end_date.year - start_date.year) * 360 + (end_date.month - start_date.month) * 30 + (end_day - start_day)


    def _get_vacation_enjoyed(self,employee, period_date_from,period_date_to):
        period_date_from_year = period_date_from.year
        period_date_to_year  = period_date_to.year
        period = str(period_date_from_year)+"-"+str(period_date_to_year)
        afectation_days = self.env["hr.leave"].search([("employee_id","=",employee.id),
                                    ("selected_period_for_holidays","=",period),
                                    ("state","=","validate"),
                                    ("code","=",'23')])
        purchased_days = self.env["hr.vacation.purchased"].search([("employee_id","=",employee.id),
                                    ("selected_period_for_holidays","=",period)])
        
        if len(afectation_days) != 0:
            if len(purchased_days) != 0:
                return sum([i.number_real_days for i in afectation_days])+sum([i.number_real_days for i in purchased_days])
            else:
                return sum([i.number_real_days for i in afectation_days])
        else:
            if len(purchased_days) != 0 :
                return sum([i.number_real_days for i in purchased_days])
        return 0


    def _get_vacation_leave(self,employee, period_date_from,period_date_to):
        afectation_days = self.env["hr.leave"].search([("employee_id","=",employee.id),
                                                    ("date_from",">=",period_date_from),
                                                    ("date_to","<=",period_date_to),
                                                    ("state","=","validate"),
                                                    ("subtype_id.type_id.have_holiday","=",False),])
        if len(afectation_days) != 0:
            return sum([i.number_real_days for i in afectation_days])
        return 0

    def _calculate_vaca(self,employee_id,date_from, date_to, salary, family_asig):
        date_from_year = date_from.year
        date_from_month = date_from.month
        first_contract_date = employee_id.first_contract_date
        last_contract_date = employee_id.last_contract_date


        date_from_eval_prom = self._first_day_of_month(date_from - relativedelta(months=5))
        payslip = self.env['hr.payslip'].search([
                                                ("date_from","<=",date_from),
                                                 ("date_to",">=",date_to),
                                                 ("employee_id","=",employee_id.id)
                                                 ],limit=1
                                                )
        if payslip:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)
        else:
            date_to_eval_prom = self._first_day_of_month(last_contract_date) - relativedelta(days=1)

        if first_contract_date > date_from_eval_prom:
            date_from_eval_prom = first_contract_date
        if last_contract_date < date_to_eval_prom:
            date_to_eval_prom = self._last_day_of_month(last_contract_date)
        lbs_vaca_variables = [(0,0,subline) for subline in self._compute_sublines(employee_id,date_from_eval_prom,date_to_eval_prom,"vaca")]

        first_contract_date = employee_id.first_contract_date
        last_contract_date = employee_id.last_contract_date
        list_periods = self._compute_period_employee_date_to(first_contract_date,last_contract_date)
        list_vals= []
        tamanio = len(list_periods)
        for enum, periods in enumerate(list_periods):
            period_date_from = periods[0]
            period_date_to = periods[1]
            period_year_from = periods[2]
            period_year_to = periods[3]

            type_vacation =""
            if enum == tamanio - 1 :
                type_vacation = "Vacaciones Truncas"
                period_date_to += relativedelta(days=1)

            elif enum == tamanio - 2:
                type_vacation = "Vacaciones Pendientes"
            elif enum < tamanio - 2 :
                type_vacation = "Vacaciones Vencidas"
            
            if employee_id.contract_id.peru_employee_regime.abbr in ['RM','RP']:
                number_days = (self.days360(period_date_from, period_date_to,) - self._get_vacation_leave(employee_id, period_date_from,period_date_to) )/24 - self._get_vacation_enjoyed(employee_id,period_date_from,period_date_to)
            elif employee_id.contract_id.peru_employee_regime.abbr == "RG":
                number_days = (self.days360(period_date_from, period_date_to,) - self._get_vacation_leave(employee_id, period_date_from,period_date_to) )/12 - self._get_vacation_enjoyed(employee_id,period_date_from,period_date_to)

            if  number_days != 0:
                val = {
                    "type_vacation": type_vacation,
                    "employee_id":employee_id.id,
                    "date_from":period_date_from,
                    "date_to":period_date_to,
                    "number_days":round(number_days,2),
                    "salary":salary,
                    "family_asig":family_asig,
                    "lbs_vaca_variables":lbs_vaca_variables,
                    }
                list_vals.append(val)
        return list_vals
    
    def _compute_period_employee_date_to(self,first_day,date_to_cese):
        list_periods = []
        i_period = first_day
        while i_period <= date_to_cese :
            f_period = i_period + relativedelta(years=1)
            if i_period <= date_to_cese <= f_period:
                list_periods.append([i_period,date_to_cese,i_period.year,f_period.year])
                break
            list_periods.append([i_period,f_period,i_period.year,f_period.year])
            i_period = f_period
        return list_periods

    @api.depends('employee_id','date_from','date_to','salary','family_asig','incomes')
    def _compute_vaca(self):
        for record in self:
            if not record.vaca and record._is_compute_time_service(record.first_contract_date, record.last_contract_date):

                record.write({
                    "vaca": [(0,0,subline) for subline in self._calculate_vaca(record.employee_id,record.date_from,record.date_to, record.salary, record.family_asig, )],
                })

    def _another_operation(self):
        pass
    
    """
        DEVOLUCION DE QUINTA
    """
    quinta_devolucion = fields.Float(string="Quinta Devolución",store=True,)
    bruto_historic = fields.Float(string="1er Bruto", store=True,)

    def compute_sheet_import(self):
        
        if any(lbs.state not in ('draft',) for lbs in self):
            raise UserError(_('No se pueda enviar la informacion a la nomina si la LBS no esta en BORRADOR!'))

        # SE TRAE PARA NUESTRAS APORTACIONES
        pay = self.payslip_id

        self.write(
            {"sending_information":False}
        )

        input = pay.input_line_ids
        input_I_CTS_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_CTS_TRUNC")
        input_I_GRAT_LEY_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_GRAT_LEY_TRUNC")
        input_I_VACAC_TRUN = input.filtered(lambda x: x.input_type_id.code == "I_VACAC_TRUN")
        input_I_DEV_IMP_5TA = input.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
        input_I_BON_LEY_TRUC = input.filtered(lambda x: x.input_type_id.code == "I_BON_LEY_TRUNC")
        
        if input_I_CTS_TRUNC:
            input_I_CTS_TRUNC.amount = 0
        if input_I_GRAT_LEY_TRUNC:
            input_I_GRAT_LEY_TRUNC.amount = 0
        if input_I_VACAC_TRUN:
            input_I_VACAC_TRUN.amount = 0
        if input_I_DEV_IMP_5TA:
            input_I_DEV_IMP_5TA.amount = 0
        if input_I_BON_LEY_TRUC:
            input_I_BON_LEY_TRUC.amount = 0
            
        pay.input_line_ids.filtered(lambda x:x.input_type_id.id in [bon.input_type_id.id for bon in self.bons] ).unlink()
        pay.input_line_ids.filtered(lambda x:x.input_type_id.id in [de.input_type_id.id for de in self.ded] ).unlink()
        pay.compute_sheet()

        """
            CAPTURA DE INFORMACION        
        """
        self.aportations.unlink()
        self.deductions.unlink()

        # deductions = [ (0,0,{ "name":i.salary_rule_id.name, "amount_report":abs(i.total), })  for i in pay.line_ids.filtered(lambda x: x.category_id.code in ["DED"])  ]
        # __________________________MODIFICADO__________________________________
        deductions = []
        for i in pay.line_ids.filtered(lambda x: x.category_id.code in ["DED"]):
            if i.salary_rule_id.have_lbs:
                deductions.append((0,0,{"name": i.salary_rule_id.name, "amount_lbs": abs(i.total), "amount_report": 0}))
            else:
                deductions.append((0,0,{"name": i.salary_rule_id.name, "amount_report": abs(i.total), "amount_lbs": 0}))
         # __________________________MODIFICADO__________________________________

        aportations = [ (0,0,{ "name":i.salary_rule_id.name, "amount_report":abs(i.total), })  for i in pay.line_ids.filtered(lambda x: x.category_id.code in ["COMP"]) ]
        bruto = pay.line_ids.filtered(lambda x: x.code in ["GROSS"]).total
        self.write({
            "bruto_historic":bruto,
            "deductions":deductions,
            "aportations":aportations,
        })

        input = pay.input_line_ids
        input_I_CTS_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_CTS_TRUNC")
        input_I_GRAT_LEY_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_GRAT_LEY_TRUNC")
        input_I_VACAC_TRUN = input.filtered(lambda x: x.input_type_id.code == "I_VACAC_TRUN")
        input_I_BON_LEY_TRUC = input.filtered(lambda x: x.input_type_id.code == "I_BON_LEY_TRUNC")
        
        child_id = self.filtered(lambda x: x.employee_id == self.employee_id)

        cts_amount = sum([i.cts_amount for i in child_id])
        grati_amount = sum([i.grati_amount for i in child_id])
        vaca_amount = sum([i.vaca_amount for i in child_id])
        boni_extra_grati_amount = sum([i.boni_extra_grati_amount for i in child_id])

        quinta_devolucion = sum([i.quinta_devolucion for i in child_id])
        if input_I_CTS_TRUNC:
            input_I_CTS_TRUNC.amount = float(cts_amount)
        if input_I_GRAT_LEY_TRUNC:
            input_I_GRAT_LEY_TRUNC.amount = float(grati_amount)
        if input_I_VACAC_TRUN:
            input_I_VACAC_TRUN.amount = float(vaca_amount)
        if input_I_BON_LEY_TRUC:
            input_I_BON_LEY_TRUC.amount = float(boni_extra_grati_amount)
        '''
        OTROS INGRESOS
        '''
        val_list = []
        delete_line_ids = []
        for bon in child_id.bons:
            delete_line_ids.append(bon.input_type_id.id)
            val = {
                    'name': bon.input_type_id.name,
                    'sequence': 10,
                    'input_type_id': bon.input_type_id.id,
                    'amount':bon.amount,
                    'payslip_id': pay.id,}
            val_list.append(val)
            
        pay.input_line_ids.filtered(lambda x:x.input_type_id.id in delete_line_ids ).unlink()
        pay.write({
            "input_line_ids":[(0,0,val) for val in val_list]
        })
        '''
        OTRAS DEDUCCIONES
        '''
        val_list = []
        delete_line_ids = []
        for de in child_id.ded:
            delete_line_ids.append(de.input_type_id.id)
            val = {
                    'name': de.input_type_id.name,
                    'sequence': 10,
                    'input_type_id': de.input_type_id.id,
                    'amount':de.amount,
                    'payslip_id': pay.id,}
            val_list.append(val)
            
        pay.input_line_ids.filtered(lambda x:x.input_type_id.id in delete_line_ids ).unlink()
        pay.write({
            "input_line_ids":[(0,0,val) for val in val_list]
        })
        
        self._another_operation()
        
        pay.compute_sheet()
        

        """
        DEVOLUCION DE QUINTA
            
        """
        line_ids = pay.line_ids.filtered(lambda x:x.salary_rule_id.have_5ta )
        bruto = sum([i.total for i in line_ids])
        line_5ta = self.env["hr.5ta.line"].search([("employee_id","=",self.employee_id.id),
                                        ("date_5ta" ,">=",self.date_from),
                                        ("date_5ta","<=",self.date_to),
                                        ],
                                        limit = 1)
        if line_5ta:
            line_5ta.lbs = bruto - line_5ta.last_month_salary
            line_5ta._update_values()
            if line_5ta.data_5ta_mensual < 0:
                self.quinta_devolucion = abs(line_5ta.data_5ta_mensual)
        
        
        self.write(
            {"sending_information":True}
        )

    def sum_retentions(self, employee_id, date_from, date_to):
        hr_payslip_line = self.env['hr.payslip.line'].search([
            ('employee_id', '=', employee_id.id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('code', '=', '5TA'),
        ])        
        return sum([i.total for i in hr_payslip_line])

    def _current_5ta_category(self, bruto, employee_id, date_from, date_to):
        amount = bruto
        line_5ta = self.env['hr.5ta.line'].search([
            ('employee_id', '=', employee_id.id),
            ('date_5ta' , '>=', date_from),
            ('date_5ta', '<=', date_to),
        ], limit = 1)
        if line_5ta:
            line_5ta.lbs = amount
            line_5ta._update_values()

    sending_information = fields.Boolean(string='Se envio informacion?', store=True, compute='compute_sending_infomation')

    @api.depends('vaca','grati','cts')
    def compute_sending_infomation(self):
        for record in self:
            record.compute_sheet_import()

    """
        SE RECOLECTA APORTACIONES DESSUES DE RECALCULAR LBS
    """
    bruto = fields.Float(string='Base Deducciones', compute='_compute_get_payslip_calculated', store=True)
    deductions = fields.One2many('hr.lbs.deduction', 'parent_id', compute='_compute_get_payslip_calculated', string='Deducciones', store=True)
    aportations = fields.One2many('hr.lbs.input','parent_id',compute = '_compute_get_payslip_calculated', string = 'Aportaciones', store=True)

    @api.depends('sending_information')
    def _compute_get_payslip_calculated(self):
        for record in self:
            if record.sending_information and record.payslip_id:
                bruto = record.payslip_id.line_ids.filtered(lambda x: x.code == 'GROSS').total

                if self._last_day_of_month(record.last_contract_date) == record.last_contract_date:
                    record.write({"bruto": bruto - record.bruto_historic})
                    
                    for i in record.payslip_id.line_ids.filtered(lambda x: x.category_id.code == 'COMP'):
                        x = record.aportations.filtered(lambda x:x.name == i.salary_rule_id.name)
                        x.write({"total": abs(i.total)})
        
                    for i in record.payslip_id.line_ids.filtered(lambda x: x.category_id.code == 'DED'):
                        x = record.deductions.filtered(lambda x:x.name == i.salary_rule_id.name)
                        x.write({"total": abs(i.total)})

                else:
                    record.write({"bruto":bruto})
                    for i in record.payslip_id.line_ids.filtered(lambda x: x.category_id.code == 'COMP'):
                        x = record.aportations.filtered(lambda x:x.name == i.salary_rule_id.name)
                        x.write({
                            "amount_report": 0,
                            "total": abs(i.total),
                            "amount_lbs": abs(i.total),
                        })
        
                    for i in record.payslip_id.line_ids.filtered(lambda x: x.category_id.code == 'DED'):
                        x = record.deductions.filtered(lambda x:x.name == i.salary_rule_id.name)
                        x.write({
                            "amount_report": 0,
                            "total": abs(i.total),
                            "amount_lbs": abs(i.total),
                        })
    """
        OTROS INGRESOS
    """
    bons = fields.One2many('hr.lbs.bon', 'parent_id', string='Otros Ingresos', store=True)

    """
        OTROS DESCUENTOS
    """    
    ded = fields.One2many('hr.lbs.ded', 'parent_id', string='Otros Descuentos', store=True)

    """
        NETOS
    """
    
    def float_to_spanish_letters(self, number):
        def op_spanish_letters(number):
            units = {
                0: 'CERO',
                1: 'UNO',
                2: 'DOS',
                3: 'TRES',
                4: 'CUATRO',
                5: 'CINCO',
                6: 'SEIS',
                7: 'SIETE',
                8: 'OCHO',
                9: 'NUEVE'
            }
            
            tens = {
                10: 'DIEZ',
                20: 'VEINTE',
                30: 'TREINTA',
                40: 'CUARENTA',
                50: 'CINCUENTA',
                60: 'SESENTA',
                70: 'SETENTA',
                80: 'OCHENTA',
                90: 'NOVENTA'
            }
            
            special_cases = {
                11: 'ONCE',
                12: 'DOCE',
                13: 'TRECE',
                14: 'CATORCE',
                15: 'QUINCE',
                100: 'CIEN'
            }
            
            if number < 0 or number >= 1e12:
                return ""
            
            if number in special_cases:
                return special_cases[number]
            
            integer_part = int(number)
            decimal_part = int(round((number - integer_part) * 100))
            
            result = ""
            
            if integer_part == 0:
                result += units[0]
                
            elif integer_part >= 1e9:
                billions = integer_part // int(1e9)
                integer_part %= int(1e9)
                
                if billions > 1:
                    result += op_spanish_letters(billions) + " MIL"
                else:
                    result += "MIL"
                    
                if integer_part > 0:
                    result += " "
                    
            if integer_part >= 1e6:
                millions = integer_part // int(1e6)
                integer_part %= int(1e6)
                
                if millions > 1:
                    result += op_spanish_letters(millions) + " MILLONES"
                else:
                    result += "UN MILLON"
                    
                if integer_part > 0:
                    result += " "
                    
            if integer_part >= 1e3:
                thousands = integer_part // 1000
                integer_part %= 1000
                
                if thousands > 1:
                    result += op_spanish_letters(thousands) + " MIL"
                else:
                    result += "MIL"
                    
                if integer_part > 0:
                    result += " "
                    
            if integer_part >= 100:
                hundreds = integer_part // 100
                integer_part %= 100
                
                if hundreds == 1 and integer_part == 0:
                    result += special_cases[100]
                else:
                    result += units[hundreds] + "CIENTOS"
                    
                if integer_part > 0:
                    result += " "
                    
            if integer_part >= 10:
                
                if integer_part in special_cases:
                    result += special_cases[integer_part]
                    integer_part = 0
                else:
                    tens_part = integer_part // 10 * 10
                    integer_part %= 10
                    
                    if tens_part > 0:
                        result += tens[tens_part]
                        
                    if integer_part > 0:
                        result += " Y "
                        
            if integer_part > 0:
                result += units[integer_part]
            
            if decimal_part > 0:
                result += " Y"
                if decimal_part >= 10:
                    result += " " + str(decimal_part) + "/100 SOLES"
                else:
                    result += " " + units[decimal_part]

            return result
        
        result = op_spanish_letters(round(number,2))
        result = result.replace("CINCOCIENTOS","QUINIENTOS")

        #######################################################

        result = result.replace("VEINTE Y UNO","VEINTIUNO")
        result = result.replace("VEINTE Y DOS","VEINTIDOS")
        result = result.replace("VEINTE Y TRES","VEINTITRES")
        result = result.replace("VEINTE Y CUATRO","VEINTICUATRO")
        result = result.replace("VEINTE Y CINCO","VEINTICINCO")
        result = result.replace("VEINTE Y SEIS","VEINTISEIS")
        result = result.replace("VEINTE Y SIETE","VEINTISIETE")
        result = result.replace("VEINTE Y OCHO","VEINTIOCHO")
        result = result.replace("VEINTE Y NUEVE","VEINTINUEVE")

        #######################################################
        
        if not result[-5:] == "SOLES":
            result += " Y 00/100 SOLES"
        return result
    
    income_net = fields.Float(string="Ingreso Neto", compute="_income_net", store=True,)
    ded_net = fields.Float(string="Deducciones Neto", compute="_ded_net", store=True,)
    net = fields.Float(string="Neto",compute="_compute_neto", store=True)
    net_words = fields.Char(string="Neto Palabras",compute='_compute_neto_words',store=True,)

    @api.depends('incomes','bons','cts_amount','grati_amount','boni_extra_grati_amount','vaca_amount','quinta_devolucion')
    def _income_net(self):
        for record in self:
            bonifications = sum([i.amount for i in record.bons])
            incomes = sum([i.total for i in record.incomes])
            record.income_net = incomes + bonifications + record.cts_amount + record.grati_amount + record.boni_extra_grati_amount + record.vaca_amount + record.quinta_devolucion

    @api.depends('ded','deductions', )
    def _ded_net(self):
        for record in self:
            deductions_amount = sum([i.amount_lbs for i in record.deductions])
            record.ded_net = deductions_amount

    @api.depends('income_net','ded_net',)
    def _compute_neto(self):
        for record in self:
            record.net = record.income_net - record.ded_net

    @api.depends('net')
    def _compute_neto_words(self):
        for record in self:
            if record.net:
                record.net_words = self.float_to_spanish_letters(record.net)

    """
        LBS PDF
    """
    def action_dowload_report_lbs_pdf(self):
        return self.env.ref('hr_lbs.action_report_lbs').report_action(self)
        # return {
        #     'name': 'LBS',
        #     'type': 'ir.actions.act_url',
        #     'url': '/print/lbs?list_ids=%(list_ids)s' % {'list_ids': ','.join(str(x) for x in self.ids)},
        # }

    def write(self, vals):
        
        if vals.get('state') == 'paid':
            if any(slip.state != 'done' for slip in self):
                raise UserError(_('No se puede marcar como pagado si no esta confirmado (HECHO)'))
            
        if vals.get('state') in ('draft','done','cancel'):
            group_access_2 = self.env["res.groups"].search([("name","=",'Multi-compañía')], limit = 1)
            res_group_2 = group_access_2.users.filtered(lambda x: x.id == int(self.env.user))

            if(len(res_group_2) == 0):
                if any(slip.state == 'paid' for slip in self):
                    raise UserError(_('No se puede cambiar de estado si ya esta PAGADO'))
            
        res = super(LbsLine, self).write(vals)
        return res

    def unlink(self):
        if any(lbs.state not in ('draft', 'cancel') for lbs in self):
            raise UserError(_('No puedes eliminar una LBS que no este en borrador o cancelado!'))

        for record in self:
            pay = record.payslip_id
            input = pay.input_line_ids
            input_I_CTS_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_CTS_TRUNC")
            input_I_GRAT_LEY_TRUNC = input.filtered(lambda x: x.input_type_id.code == "I_GRAT_LEY_TRUNC")
            input_I_VACAC_TRUN = input.filtered(lambda x: x.input_type_id.code == "I_VACAC_TRUN")
            input_I_DEV_IMP_5TA = input.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
            input_I_BON_LEY_TRUC = input.filtered(lambda x: x.input_type_id.code == "I_BON_LEY_TRUNC")
            
            if input_I_CTS_TRUNC:
                input_I_CTS_TRUNC.amount = 0
            if input_I_GRAT_LEY_TRUNC:
                input_I_GRAT_LEY_TRUNC.amount = 0
            if input_I_VACAC_TRUN:
                input_I_VACAC_TRUN.amount = 0
            if input_I_DEV_IMP_5TA:
                input_I_DEV_IMP_5TA.amount = 0
            if input_I_BON_LEY_TRUC:
                input_I_BON_LEY_TRUC.amount = 0
                
            delete_line_ids = []
            for bon in record.bons:
                delete_line_ids.append(bon.input_type_id.id)
            pay.input_line_ids.filtered(lambda x:x.input_type_id.id in delete_line_ids ).unlink()


            delete_line_ids = []
            for bon in record.ded:
                delete_line_ids.append(bon.input_type_id.id)
            pay.input_line_ids.filtered(lambda x:x.input_type_id.id in delete_line_ids ).unlink()


            pay.compute_sheet()
        return super(LbsLine,self).unlink()

    def draft(self):
        self.state = "draft"
    

