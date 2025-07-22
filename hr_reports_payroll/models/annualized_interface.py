from .annualized_reports import PayrollAnnualizerExcelReport
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import  timedelta, datetime, date
import base64
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class AnnualizedInterface(models.Model):
    # locale.setlocale(locale.LC_ALL, ("es_ES", "UTF-8"))

    _name = 'annualized.interface'
    _description = 'Reporte Nomina Anualizado'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Compañia', default=lambda self: self.env.company)

    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    child_ids = fields.One2many('annualized.interface.line',"parent_id",string="Registros de Empleados",store=True,)
    date_from = fields.Date(string="Fecha de Inicio", store=True, required=True, )
    date_to = fields.Date(string="Fecha Fin", store=True,required=True, )
    date_initial_years = fields.Date(string="Primer Dia de los Periodos", store=True,compute="_update_dates")
    date_final_years = fields.Date(string="Ultimo de los Periodos", store=True,compute="_update_dates")
    date_initial_month = fields.Date(string="Primer Dia desde el primer mes",  store=True,compute="_update_dates")
    date_final_month = fields.Date(string="Ultimo dia del ultimo mes", store=True,compute="_update_dates")
    child_ids_count = fields.Integer(compute='_compute_child_ids_count')

    
    def action_open_annualized_interface(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "annualized.interface.line",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.child_ids.ids]],
            "name": "Registros Anualizados",
        }

    @api.depends('child_ids')
    def _compute_child_ids_count(self):
        for record in self:
            record.child_ids_count = len(record.child_ids)
    @staticmethod
    def _first_day_of_month(any_day):
        return any_day - timedelta(days=(any_day.day  - 1))

    def _last_day_of_month(self,any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)

    @api.onchange('date_from', 'date_to')
    def _payslip_run_id_name(self):
        if self.date_from and self.date_to:
            self.name = "REPORTE ANUALIZADO " +  self.date_from.strftime("%Y %b") +  " - " + self.date_to.strftime("%Y %b")

    @api.depends('date_from','date_to')
    def _update_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                record.date_initial_years = self._first_day_of_month(self.date_from.replace(month=1))
                record.date_final_years = self._last_day_of_month(self.date_to.replace(month=12))
                record.date_initial_month = self._first_day_of_month(self.date_from)
                record.date_final_month = self._last_day_of_month(self.date_to)

    def compute_sheet(self):
        self.ensure_one()
        self.child_ids.child_ids.unlink()
        self.child_ids.unlink()
        val_list = []

        employees = self.env["hr.payslip"].search(
                                            [
                                                ("date_from",">=",self.date_initial_month),
                                                ("date_to","<=",self.date_final_month),
                                                ("company_id","=",self.company_id.id),
                                            ]).mapped("employee_id")
        if employees:
            for employee in employees:
                val = {
                    "employee_id":employee.id,
                    "parent_id":self.id,
                    "date_from":self.date_initial_month,
                    "date_to":self.date_final_month,
                }
                val_list.append(val)
        self.env["annualized.interface.line"].create(val_list)
        return  self.env.cr.commit()

class AnnualizedInterfaceLine(models.Model):

    _name = 'annualized.interface.line'
    _description = 'Reporte Nomina Anualizado de Personas'
    name = fields.Char(store=True,compute='compute_name',)


    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')
    date_from = fields.Date(string="Fecha de Inicio", store=True,)
    date_to = fields.Date(string="Fecha Fin", store=True,)
    employee_id = fields.Many2one("hr.employee",string="Empleado", store=True,)
    first_contract_date = fields.Date(string = "Fecha Inicio", compute ="_compute_dates", store=True,)
    last_contract_date = fields.Date(string="Fecha Cese", compute ="_compute_dates",  store=True,)
    ref_emp = fields.Char(related="employee_id.cod_ref", store=True,)
    job = fields.Char(related="employee_id.job_id.name", string="Puesto", store=True,)
    parent_id = fields.Many2one("annualized.interface", store=True,)
    child_ids = fields.One2many('annualized.interface.line.amount',"parent_id",string="Montos de Empleados", store=True,compute="_compute_child_ids")

    total_incomes = fields.Float(string="Total Ingresos",store=True,compute="_compute_total")
    total_deductions = fields.Float(string="Total Deducciones",store=True,compute="_compute_total")
    total_aportations = fields.Float(string="Total Aportaciones",store=True,compute="_compute_total")
    xls_filename = fields.Char()
    xls_binary = fields.Binary('Reporte Excel')

    # structure_type_abbr = fields.Char(string="Tipo de Régimen",related='employee_id.contract_id.peru_employee_regime.abbr',store=True)


    @api.depends('employee_id')
    def compute_name(self):
        for record in self:
            record.name = "Reporte Anualizado " +\
                        record.employee_id.name +\
                        " " +\
                        record.date_from.strftime("%Y %b") +\
                        "-" +\
                        record.date_to.strftime("%Y %b")

    @api.depends('employee_id')
    def _compute_dates(self):
        for record in self:
            record.first_contract_date = record.employee_id.first_contract_date
            record.last_contract_date = record.employee_id.last_contract_date

    @staticmethod
    def _last_day_of_month(any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)

    def _generate_dates(self,employee_id,date_from,date_to):
        initial = date_from
        list_months = []
        while initial < date_to:
            final = self._last_day_of_month(initial)
            """
                PAYSLIP LINE
            """
            hr_payslip_line = self.env["hr.payslip.line"].search([
                ("date_from",">=",initial),
                ("date_to","<=",final),
                ("employee_id","=",employee_id.id),
                ("company_id","=",self.parent_id.company_id.id),
            ])

            for line in hr_payslip_line:
                if line.total  != 0 and line.salary_rule_id.category_id.code in ["BASIC","BASIC_NA","DED","COMP"]:
                    val = {
                        "date_from":initial,
                        "date_to":final,
                        "employee_id":employee_id.id,
                        "year_period":line.date_to.strftime("%Y"),
                        "month_period":line.date_to.strftime("%m"),
                        "period":line.date_to.strftime("%Y-%b"), 

                    }
                    if line.salary_rule_id.category_id.code in ["BASIC","BASIC_NA"]:
                        val["type"] = "incomes"
                    elif line.salary_rule_id.category_id.code == "DED":
                        val["type"] = "deductions"
                    elif line.salary_rule_id.category_id.code == "COMP":
                        val["type"] = "aportations"
                    else:
                        val["type"] = "others"
                    
                    val["amount"] = abs(line.total)
                    val["description"] =line.salary_rule_id.name
                    list_months.append(val)
            initial += relativedelta(months=1)
        return list_months

    @api.depends('employee_id','date_from','date_to')
    def _compute_child_ids(self):
        for record in self:
            record.write(
                {
                "child_ids":[(0,0,val) for val in self._generate_dates(record.employee_id,record.date_from,record.date_to)],
                }
            )

    @api.depends('child_ids')
    def _compute_total(self):
        for record in self:
            record.total_incomes = sum([i.amount for i in record.child_ids if i.type == "incomes"])
            record.total_deductions = sum([i.amount for i in record.child_ids if i.type == "deductions"])
            record.total_aportations = sum([i.amount for i in record.child_ids if i.type == "aportations"])

    def action_dowload_report_tabular_annualized(self):
        self.ensure_one()
        year_period = self.child_ids.mapped("year_period")
        dict_months = {
            "01":"ENE",
            "02":"FEB",
            "03":"MAR",
            "04":"ABR",
            "05":"MAY",
            "06":"JUN",
            "07":"JUL",
            "08":"AGO",
            "09":"SET",
            "10":"OCT",
            "11":"NOV",
            "12":"DIC",
        }
        months =  list(dict_months.keys())
        dict_types = {
            "incomes":"BENEFICIOS",
            "deductions":"DEDUCCIONES",
            "aportations":"APORTACIONES"
        }
        types = list(dict_types.keys())
        vals ={}
        vals["employee"] = {
            "Codigo":self.ref_emp,
            "Nombre":self.employee_id.name,
            # "structure_type_abbr": self.employee_id.contract_id.peru_employee_regime.abbr,
            "Puesto":self.job if self.job else "" ,
            "Fecha Ingreso":self.first_contract_date.strftime("%d-%m-%Y"),
            "Fecha Cese":self.last_contract_date.strftime("%d-%m-%Y") if self.last_contract_date else "",
            "Estado": "INACTIVO" if self.last_contract_date else "ACTIVO",
            "Centro de Costo":self.employee_id.cod_coste_center.name if self.employee_id.cod_coste_center else '',
            "Zonal": self.employee_id.location_id.name or '' ,
            "Num Documento":self.employee_id.identification_id or '',
        }

        for year in year_period:
            vals[year] = {}
            for type in types:
                ktype = dict_types[type]
                vals[year][ktype]={}
                child_id = self.child_ids.filtered(lambda x:x.type == type and x.year_period == year)
                descriptions = child_id.mapped("description")
                for month in months:
                    kmonth = dict_months[month]
                    vals[year][ktype][kmonth] = {}
                    for description in descriptions:
                        child = child_id.filtered(lambda x : x.month_period == month and x.description == description)
                        if child:
                            vals[year][ktype][kmonth][description] = child.amount
                        else:
                            vals[year][ktype][kmonth][description] = 0
        return self.generate_excel(vals)
            

    def generate_excel(self, data):
        report_xls = PayrollAnnualizerExcelReport(data, self)
        values = {
            'xls_filename': "REPORTE PLANILLA ANUALIZADO " + self.employee_id.name + ".xlsx",
            'xls_binary': base64.encodebytes(report_xls.get_content()),
        }
        self.write(values)


class AnnualizedInterfaceAmount(models.Model):
    _name = 'annualized.interface.line.amount'
    _description     = 'Montos del Reporte Anualizado'

    description = fields.Char(name="Descripcion",store=True,)
    type = fields.Selection(selection=[("incomes","Beneficios"),("deductions","Deducciones"),("aportations","Aportaciones"),("others","Otros")],store=True,)
    amount = fields.Float(string="Monto",store=True,)
    month = fields.Char(string="Mes",store=True,)
    year = fields.Char(string="Año",store=True,)
    date_from = fields.Date(string="Fecha de Inicio", store=True, compute ="_compute_date_from")
    date_to = fields.Date(string="Fecha Fin", store=True,related="parent_id.date_to")
    employee_id = fields.Many2one("hr.employee",string="Empleado", store=True,)
    payslip_id = fields.Many2one("hr.payslip", store=True,)
    parent_id = fields.Many2one("annualized.interface.line", store=True,)
    period = fields.Char(string="Fecha Nomina", store=True, compute="_compute_period")
    year_period = fields.Char(string="Año de Nomina", store=True, compute="_compute_period")
    month_period = fields.Char(string="Mes de Nomina", store=True, compute="_compute_period")