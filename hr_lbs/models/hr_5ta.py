from odoo import api, fields, models, _
from datetime import  timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError, UserError
import base64

class Lbs5taLine(models.Model):
    _inherit = 'hr.5ta.line'
    _description = 'LBS 5ta Line'

    def step_uit(self, value, date):
        tramo_5ta = self.env["tramo.5ta"].search([], order = 'id asc')
        uit_5ta = self.env["uit.table"].search([("year","=", date.year)], limit=1)  
        list_tramo, list_value = [], []

        if(uit_5ta):
            if(value < 0):
                return [0,0,0,0,0,0]
            list_tramo = [((tramo.uit_from * uit_5ta.value, tramo.uit_to * uit_5ta.value, tramo.percentage)) if tramo.uit_from * uit_5ta.value <= value else (0, 0, 0) for tramo in tramo_5ta ]

        if(list_tramo):
            list_value = [((step[1] - step[0])*step[2]/100) if (value > step[1]) else ((value - step[0])*step[2]/100) for step in list_tramo]

        return [sum(list_value), list_value[0], list_value[1], list_value[2], list_value[3], list_value[4]]
    
    def month_5ta_employee(self, data_5ta,  date_5ta, employee_id, amount_5ta):
        payslip_line = self.env["hr.payslip.line"].search([("employee_id", "=", employee_id.id)], order = 'id desc')

        for i in range(1, date_5ta.month+1):
            list_5ta = [payslip_line.filtered(lambda x: x.date_from <= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.date_to >= (date_5ta - relativedelta(months=(date_5ta.month-i))) and x.code == 'I_5TA').total]
        
        amount_retention = sum(list_5ta)
        
        balance = data_5ta - sum(list_5ta) - amount_5ta

        if(1 <= date_5ta.month <= 3):
            total = balance / 12
        elif(date_5ta.month == 4):
            total = balance / 9
        elif(5 <= date_5ta.month <= 7):
            total = balance / 8
        elif(date_5ta.month == 7):
            total = balance / 5
        elif(8 <= date_5ta.month <= 11):
            total = balance / 4
        else:
            total = balance / 1

        return [balance, total, amount_retention]
    
    def compute_sheet_import(self):
        payslip = self.env['hr.payslip'].search([("date_from","<=",self.date_5ta),
                                                 ("date_to",">=",self.date_5ta),
                                                 ("employee_id","=",self.employee_id.id)])

        if self.data_5ta_mensual > 0:
            final_input_1 = payslip.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_5TA")
            final_input_1.amount = float(self.data_5ta_mensual)

            final_input_2 = payslip.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
            final_input_2.amount = 0
        else:
            final_input_1 = payslip.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_5TA")
            final_input_1.amount = 0

            final_input_2 = payslip.input_line_ids.filtered(lambda x: x.input_type_id.code == "I_DEV_IMP_5TA")
            final_input_2.amount = float(self.data_5ta_mensual)


        payslip.compute_sheet()

    def _update_values(self):
        self.ensure_one()
        if self.lbs > 0:
            new_rap = self.rap + self.lbs - self.grati_projection - self.salary_projection - self.bon_gen
        else :
            new_rap = self.rap
        self.base_5ta = new_rap - 7*self.uit
        self.data_5ta = self.step_uit(self.base_5ta, self.date_5ta)[0]

        self.data_5ta_mensual = self.data_5ta - self.amount_retention

        self.compute_sheet_import()