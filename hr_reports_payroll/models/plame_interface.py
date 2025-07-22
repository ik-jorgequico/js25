from .plame_reports import PlameReport
from odoo import api, fields, models
import base64


class PlameLines(models.Model):
    _name = 'plame.lines'
    _description = '[22] Ingresos, tributos y descuentos'

    code = fields.Char(string='CÓDIGO')
    name = fields.Char(string='DESCRIPCIÓN DE LOS INGRESOS, TRIBUTOS Y DESCUENTOS')
    essalud_seguro_regular = fields.Boolean(string='ESSALUD SEGURO REGULAR TRABAJADOR')
    essalud_cbssp = fields.Boolean(string='ESSALUD - CBSSP - SEG TRAB PESQUERO')
    essalud_seguro_agrario = fields.Boolean(string='ESSALUD SEGURO AGRARIO / ACUICULTOR')
    essalud_sctr = fields.Boolean(string='ESSALUD SCTR')
    imp_extra_solidaridad = fields.Boolean(string='IMPUESTO EXTRAORD. DE SOLIDARIDAD (8)')
    fondo_der_artista = fields.Boolean(string='FONDO DERECHOS SOCIALES DEL ARTISTA')
    senati = fields.Boolean(string='SENATI')
    sistema_nacional_pensiones = fields.Boolean(string='SISTEMA NACIONAL DE PENSIONES 19990')
    sistema_privado_pensiones = fields.Boolean(string='SISTEMA PRIVADO DE PENSIONES')
    fondo_compl_jub = fields.Boolean(string='FONDO COMPL DE JUBIL MIN, MET Y SIDER (1)')
    reg_esp_pesquero = fields.Boolean(string='RÉG.ESP. PENSIONESTRAB. PESQUERO')
    rent5ta = fields.Boolean(string='RENTA 5TA CATEGORÍA RETENCIONES')
    essalud_regular_pension = fields.Boolean(string='ESSALUD SEGURO REGULAR PENSIONISTA')
    contrib_sol_asist = fields.Boolean(string='CONTRIB. SOLIDARIA ASISTENCIA PREVIS.')


class PlameFiles(models.Model):
    _name = 'plame.files'
    _description = 'Reportes Plame'

    date_from = fields.Date(
        string='Fecha de Inicio',
        required=True,
        store=True,
    )
    name = fields.Char("Reporte Plame")
    payslip_run_id = fields.Many2one('hr.payslip.run',
                                     string="Lote",
                                     store=True,
                                     )

    date_to = fields.Date(
        string='Fecha de Fin',
        required=True,
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    rem_filename = fields.Char(string='Nombre archivo .rem')
    rem_binary = fields.Binary(string='.Rem')
    jor_filename = fields.Char(string='Nombre archivo .jor')
    jor_binary = fields.Binary(string='.Jor')
    snl_filename = fields.Char(string='Nombre archivo .snl')
    snl_binary = fields.Binary(string='.Sni')
    for_filename = fields.Char(string='Nombre archivo .for')
    for_binary = fields.Binary(string='.For')

    @api.onchange('payslip_run_id')
    def _payslip_run_id_dates_name(self):
        if self.payslip_run_id:
            self.date_from = self.payslip_run_id.date_start
            self.date_to = self.payslip_run_id.date_end
            self.name = "REPORTE PLAME " + self.payslip_run_id.name

    def generate_files(self):
        data_rem, data_jor, data_snl, data_for = self._get_data()
        filename = self._get_filename()
        report_file = PlameReport(data_rem, data_jor, data_snl, data_for, filename, self)

        values = {
            'rem_filename': report_file.get_filename('rem'),
            'rem_binary': base64.encodebytes(report_file.get_content_rem() or '\n'.encode()),
            'jor_filename': report_file.get_filename('jor'),
            'jor_binary': base64.encodebytes(report_file.get_content_jor() or '\n'.encode()),
            'snl_filename': report_file.get_filename('snl'),
            'snl_binary': base64.encodebytes(report_file.get_content_snl() or '\n'.encode()),
            'for_filename': report_file.get_filename('for'),
            'for_binary': base64.encodebytes(report_file.get_content_for() or '\n'.encode()),
        }
        self.write(values)

    """
        -> rem_data, data_jor, data_snl, data_for
    """
    def _get_data(self):
        rem_data, jor_data, snl_data, data_for = [], [], [], []
        slip_ids = self.payslip_run_id.slip_ids
        line_ids = slip_ids.line_ids
        worked_days_line_ids = slip_ids.worked_days_line_ids
        employees = line_ids.mapped('employee_id')

        codes_pl = line_ids.filtered(lambda x:x.salary_rule_id.plame_id != False).mapped('salary_rule_id.plame_id.code')
        codes_pl = set(list(codes_pl))
        
        codes_wk = worked_days_line_ids.filtered(lambda x: x.work_entry_type_id.is_leave).mapped('code')
        codes_wk = list(set(codes_wk))

        exception_records = []
        for employee in employees:
            lines_filtered = line_ids.filtered(lambda x : x.employee_id == employee )

            """
                data_rem
            """
            for code_pl in codes_pl:
                pays = lines_filtered.filtered(lambda x : x.salary_rule_id.plame_id.code==code_pl)
                pay = pays
                if len(pays) > 1:
                    pay = pays[0]

                document_type = employee.l10n_latam_identification_type_id.l10n_pe_vat_code if employee.l10n_latam_identification_type_id else '00'
                if document_type == '1': ## DNI
                    document_type = '01'
                elif document_type == '4': ## CEDULA EXTRANJERIA
                    document_type = '04'

                document_number = employee.identification_id if pay.employee_id.identification_id else '00000000'
                amount = abs(sum([pay.amount for pay in pays]))

                if employee.pension_system_id.name == "ONP":
                    codes_always_appear =  [ "0121","0803","0605"]
                elif employee.pension_system_id.name in ("INTEGRA" ,"HABITAT","PROFUTURO","PRIMA"):
                    codes_always_appear = [ "0608","0606","0601","0121","0803","0605"]

                id_record = str(document_number)+str(code_pl)

                if id_record not in exception_records:
                    if amount > 0 or code_pl in codes_always_appear:
                        val = {
                            'document_type': document_type,
                            'document_number': document_number,
                            'plame_code': code_pl,
                            'amount': "%.2f" % amount,
                            'paid_amount':"%.2f" % amount
                        }
                        rem_data.append(val)
                exception_records.append(id_record)


            """
                data_jor
            """
            worked_days_line_id = worked_days_line_ids.filtered(lambda x : x.employee_id == employee )
            ord_hours = sum(line.number_of_hours for line in worked_days_line_id.filtered( lambda x: x.code in ['WORK100', 'GLOBAL'] ))
            hours_extra = 0
                
            min_extra = self.convert_float_to_time(hours_extra)

            document_type = employee.l10n_latam_identification_type_id.l10n_pe_vat_code if employee.l10n_latam_identification_type_id else '00'
            if document_type == '1': ## DNI
                document_type = '01'
            elif document_type == '4': ## CEDULA EXTRANJERIA
                document_type = '04'

            document_number = employee.identification_id if employee.identification_id else '00000000'
            ord_hours = int(ord_hours) if ord_hours < 360 else 360
            ord_min =  0
            hours_extra = int(hours_extra) if hours_extra < 360 else 360

            jor_data.append({
                'document_type': document_type,
                'document_number': document_number,
                'ord_hours': ord_hours,
                'ord_min': ord_min ,
                'hours_extra': hours_extra,
                'min_extra': min_extra
            })


            """
                snl_data
            """
            for code_wk in codes_wk:
                days = sum(line.number_of_days for line in worked_days_line_id.filtered(lambda x: x.code == code_wk))
                if days > 0:
                    document_type = employee.l10n_latam_identification_type_id.l10n_pe_vat_code if employee.l10n_latam_identification_type_id else '00'
                    if document_type == '1': ## DNI
                        document_type = '01'
                    elif document_type == '4': ## CEDULA EXTRANJERIA
                        document_type = '04'

                    document_number = employee.identification_id if employee.identification_id else '00000000'
                    ### Se entiende que los codigos tienen la estructura LEAVE01
                    ### Donde 01 es el codigo segun SUNAT
                    code_wk = code_wk[5:]
                    snl_data.append({
                        'document_type': document_type,
                        'document_number': document_number,
                        'code': code_wk,
                        'days': int(days)
                    })

            """
                data_for
            """


        return rem_data, jor_data, snl_data, data_for

    @staticmethod
    def convert_float_to_time(value):
        if isinstance(value, str):
            value = float(value)
        int_val = int(value)
        value = value - int_val
        new_val = (value * 60) / 10
        return int(new_val)

    def _get_filename(self):
        code_file_plame = '0601' #self.env['ir.config_parameter'].sudo().get_param('hr_reports_payroll.code_file_plame', default='----')
        year = self.date_from.strftime('%Y')
        month = self.date_from.strftime('%m')
        company_vat = self.company_id.vat or '99999999'

        filename = '{}{}{}{}'.format(code_file_plame, year, month, company_vat)
        return filename

