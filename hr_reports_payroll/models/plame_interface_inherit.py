from .plame_reports import PlameReport
from odoo import api, fields, models
import base64
import pytz

from datetime import timedelta, datetime, date


class PlameFilesInherit(models.Model):
    _inherit = 'plame.files'

    concepts_ids = fields.One2many(
        "plame.files.concepts", "interface_id", store=True, string="Data para Liquidacion de Impuestos")

    date_period_report = fields.Char(store=True,compute='_compute_date_period_report',)

    @api.depends('date_from')
    def _compute_date_period_report(self):
        for record in self:
            record.date_period_report = record.date_from.strftime("%m/%Y")

    report_file_tax_settlement = fields.Many2one(
        'ir.attachment', string='Entrega', store=True)
    report_filename_tax_settlement = fields.Char(string='Nombre reporte')
    report_binary_tax_settlement = fields.Binary(string='PDF Impuestos')
    datetime_now = fields.Char(store=True,)

    def _get_filename(self):
        code_file_plame = '0601' #self.env['ir.config_parameter'].sudo().get_param('hr_reports_payroll.code_file_plame', default='----')
        year = self.date_from.strftime('%Y')
        month = self.date_from.strftime('%m')
        company_vat = self.company_id.vat or '99999999'

        filename = '{}{}{}{}'.format(code_file_plame, year, month, company_vat)
        return filename

    def get_amount_line(self, pay, code):
        '''
            BASE IMPONIBLE
        '''
        for line in pay.line_ids.filtered(lambda input: input.code == code):
            return abs(line.total) if (line and line.total) else 0
        return 0

    def get_amount_lbs(self, pay, code):
        for line in pay.line_ids.filtered(lambda input: input.code == code):
            return abs(line.total) if (line and line.total is not None) else 0
        return 0

    @staticmethod
    def _last_day_of_month(any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        # this will never fail
        return next_month - timedelta(days=next_month.day)

    def _is_last_day_of_month(self, date):
        if date:
            return self._last_day_of_month(date) == date

    def _get_data_concepts(self, list_codes,):
        self.ensure_one()
        pay_bi, pay_amount, lbs_bi, lbs_amount = 0, 0, 0, 0
        pays = self.payslip_run_id.slip_ids
        payslip_pay = pays.filtered(lambda x: not x.lbs_id or (
            x.lbs_id and self._is_last_day_of_month(x.employee_id.last_contract_date)))
        payslip_lbs = pays.filtered(lambda x: x.lbs_id)
    
        if list_codes:

            if list_codes == [("I.R. 5ta", "5TA"),("I.R. 5ta Directa", "5TA_DIRECT"),]:
                for pay in payslip_pay:
                    aux = 0
                    for code in list_codes:
                        if not pay.lbs_id:
                            aux += self.get_amount_line(pay, code[1])
                        else:
                            x = pay.lbs_id.deductions.filtered( lambda x: x.name == code[0])
                            aux += x.amount_report if x else 0
                            x = pay.lbs_id.aportations.filtered( lambda x: x.name == code[0])
                            aux += x.amount_report if x else 0
                    if not pay.lbs_id:
                        pay_amount += aux
                        amount_bruto = sum(line.total for line in pay.line_ids.filtered(
                            lambda x: x.salary_rule_id.have_5ta == True))
                        pay_bi += amount_bruto
                    else:
                        pay_amount += aux
                        amount_bruto = sum(line.total for line in pay.line_ids.filtered(
                            lambda x: x.salary_rule_id.have_5ta == True and x.salary_rule_id.appears_report_payroll))
                        pay_bi += amount_bruto 

                for pay in payslip_lbs:
                    aux = 0
                    for code in list_codes:
                        if not self._is_last_day_of_month(pay.employee_id.last_contract_date):
                            aux += self.get_amount_line(pay, code[1])
                        else:
                            x = pay.lbs_id.deductions.filtered( lambda x: x.name == code[0])
                            aux += x.amount_lbs if x else 0
                            x = pay.lbs_id.aportations.filtered( lambda x: x.name == code[0])
                            aux += x.amount_lbs if x else 0
                    if not self._is_last_day_of_month(pay.employee_id.last_contract_date):
                        lbs_amount += aux
                        amount_bruto = sum(line.total for line in pay.line_ids.filtered(
                                lambda x: x.salary_rule_id.have_5ta == True))
                        lbs_bi += amount_bruto
                    else:
                        lbs_amount += aux
                        amount_bruto = sum(line.total for line in pay.line_ids.filtered(
                                lambda x: x.salary_rule_id.have_5ta == True and not x.salary_rule_id.appears_report_payroll))
                        lbs_bi += amount_bruto
                        
            else:
                for pay in payslip_pay:
                    aux = 0
                    for code in list_codes:
                        if not pay.lbs_id:
                            aux += self.get_amount_line(pay, code[1])
                        else:
                            x = pay.lbs_id.deductions.filtered( lambda x: x.name == code[0])
                            aux += x.amount_report if x else 0
                            x = pay.lbs_id.aportations.filtered( lambda x: x.name == code[0])
                            aux += x.amount_report if x else 0
                    if not pay.lbs_id:
                        if aux > 0:
                            pay_amount += aux
                            amount_bruto = self.get_amount_line(pay, "GROSS")
                            pay_bi += amount_bruto
                    else:
                        if aux > 0:
                            pay_amount += aux
                            amount_bruto = self.get_amount_line(pay, "GROSS")
                            pay_bi += amount_bruto - pay.lbs_id.bruto

                for pay in payslip_lbs:
                    aux = 0
                    for code in list_codes:
                        if not self._is_last_day_of_month(pay.employee_id.last_contract_date):
                            aux += self.get_amount_line(pay, code[1])
                        else:
                            x = pay.lbs_id.deductions.filtered( lambda x: x.name == code[0])
                            aux += x.amount_lbs if x else 0
                            x = pay.lbs_id.aportations.filtered( lambda x: x.name == code[0])
                            aux += x.amount_lbs if x else 0
                    if not self._is_last_day_of_month(pay.employee_id.last_contract_date):
                        if aux > 0:
                            lbs_amount += aux
                            amount_bruto = self.get_amount_line(pay, "GROSS")
                            lbs_bi += amount_bruto
                    else:
                        if aux > 0:
                            lbs_amount += aux
                            amount_bruto = pay.lbs_id.bruto
                            lbs_bi += amount_bruto
        
            return round(pay_bi, 2), round(pay_amount, 2), round(lbs_bi, 2), round(lbs_amount, 2)
        return pay_bi, pay_amount, lbs_bi, lbs_amount

    def generate_files_liq_taxes(self):
        list_rules = {"ONP": [("ONP", "ONP")],
                      "ESSALUD": [("Essalud 6.75%", "ESS_REG_675"), ("Essalud 9%", "ESS_REG_9"), ('Essalud - Eps','ESS_EPS')],
                      "5TA CATEGORIA": [("I.R. 5ta", "5TA"),("I.R. 5ta Directa", "5TA_DIRECT"),],
                      "4TA CATEGORIA": [],

                      }
        groups = ['PLANILLA DE REMUNERACIONES', 'PLANILLA DE LIQUIDACIONES',
                  'SUB-TOTAL', 'CREDITO E.P.S.', 'DEVOLUCION 5TA DEL MES']
        labels = ["B.I.", "TRIBUTO"]
        slip_ids = self.payslip_run_id.slip_ids
        values = []
        pay_bi, pay_amount, lbs_bi, lbs_amount = 0, 0, 0, 0
        for rule in list_rules:
            pay_bi, pay_amount, lbs_bi, lbs_amount = self._get_data_concepts(
                list_rules[rule])

            """
            "PLANILLA DE REMUNERACIONES"
            """
            group = "PLANILLA DE REMUNERACIONES"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": pay_bi
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": pay_amount
            })
            """
            PLANILLA DE LIQUIDACIONES
            """
            group = "PLANILLA DE LIQUIDACIONES"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": lbs_bi
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": lbs_amount
            })
            """
            SUB-TOTAL
            """
            group = "SUB-TOTAL"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": pay_bi + lbs_bi
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id,
                "group": group, "concept": rule, "label": label, "amount": pay_amount + lbs_amount
            })
            """
            CREDITO E.P.S.
            """
            group = "CREDITO E.P.S."
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            """
            DEVOLUCION 5TA DEL MES
            """
            group = "DEVOLUCION 5TA DEL MES"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            """
            TOTAL
            """
            group = "TOTAL"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            """
            TOTAL IMPUESTOS A PAGAR SUNAT
            """
            group = "TOTAL IMPUESTOS A PAGAR SUNAT"
            label = "B.I."
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            label = "TRIBUTO"
            values.append({
                "interface_id": self.id, "group": group, "concept": rule, "label": label, "amount": 0
            })
            

        self.concepts_ids.unlink()
        self.write({
            "concepts_ids": [(0, 0, val) for val in values]
        })

        """
            ACTUALIZACION DE EXCEPCIONES
        """
        line_ids = self.payslip_run_id.slip_ids.line_ids

        group = "CREDITO E.P.S."
        label = "TRIBUTO"
        rule = "ESSALUD"
        amount = abs(sum(line.total for line in line_ids.filtered( lambda x:  x.code == "ESS_EPS")))
        concepts_id = self.concepts_ids.filtered(lambda x: x.group == group and x.label == label and x.concept == rule)
        concepts_id.write({
            "amount":amount
        })

        group = "DEVOLUCION 5TA DEL MES"
        label = "TRIBUTO"
        rule = "5TA CATEGORIA"
        amount = abs(sum(line.total for line in line_ids.filtered( lambda x:  x.code == "DEV_IMP_5TA")))
        concepts_id = self.concepts_ids.filtered(lambda x: x.group == group and x.label == label and x.concept == rule)
        concepts_id.write({
            "amount":amount
        })

        """
            ACTUALIZACION DE TOTALES
        """
        labels = ["B.I.", "TRIBUTO"]
        total_amount = 0
        for rule in list_rules:
            concepts_id = self.concepts_ids.filtered(lambda x: x.concept == rule)
            for label in labels:
                rec = concepts_id.filtered(lambda x: x.label == label and x.concept == rule)
                x = rec.filtered(lambda x: x.group == "SUB-TOTAL").amount
                y1 = rec.filtered(lambda x: x.group == "CREDITO E.P.S.").amount
                y2 = rec.filtered(lambda x: x.group == 'DEVOLUCION 5TA DEL MES').amount
                result = rec.filtered(lambda x:x.group == "TOTAL")
                r = round(x - y1 - y2)

                if r > 0:
                    result.write({"amount":r})
                else :
                    r = 0

                if label == "TRIBUTO":
                    res = rec.filtered(lambda x:x.group == "TOTAL IMPUESTOS A PAGAR SUNAT")
                    res.write({"amount":r})
                    total_amount += r

        self.write({
            "concepts_ids": [(0, 0, {
                "interface_id": self.id, "group":'TOTAL A PAGAR' , "concept": "", "label": "", "amount": total_amount
            })]
        })

        '''
            CREACION DE REPORTE
        '''
        id_report = "report_plame_tax_settlements"
        report_template_id = self.env['ir.actions.report']._render_qweb_pdf(f"hr_reports_payroll.report_plame_tax_settlements", self.id)        
        # report_template_id = self.env.ref('hr_reports_payroll.' + id_report).with_context(
        #     force_report_rendering=True)._render_qweb_pdf(self.id)
        record = base64.b64encode(report_template_id[0])
        name = "Liquidación de Impuestos"
        ir_value = {
            'name': name,
            'type': 'binary',
            'datas': record,
            'store_fname': record,
            'mimetype': 'application/x-pdf',
        }
        file = self.env['ir.attachment'].create(ir_value)
        peru_timezone  = pytz.timezone("America/Lima")
        current_time = datetime.now(peru_timezone)
        self.write({
            "report_file_tax_settlement": file,
            "report_filename_tax_settlement": name,
            "report_binary_tax_settlement": record,
            "datetime_now":"Fecha de Generación : "+current_time.strftime("%d/%m/%Y, %H:%M:%S")
        }
        )


class PlameFilesInheritConcepts(models.Model):
    _name = "plame.files.concepts"
    _description = "Plame Concepts"
    
    interface_id = fields.Many2one(
        "plame.files", string="Registro", store=True,)

    group = fields.Char(string="Grupo", store=True,)
    concept = fields.Char(string="Concepto", store=True,)
    label = fields.Char(string="Rotulo", store=True,)
    amount = fields.Float(string="Monto", store=True,)
