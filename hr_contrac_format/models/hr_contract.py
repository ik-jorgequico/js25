from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta
from datetime import  timedelta, datetime, date
import base64
from num2words import num2words 

from odoo.exceptions import UserError, ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Hr Contract'
    
    labor = fields.Selection([
        ('Labor hibrida', 'Labor híbrida'),
        ('Labor teletrabajo', 'Labor teletrabajo'),
        ('Labor presencial', 'Labor presencial')
    ], string="Lugar de trabajo")
    
    
    work_type = fields.Selection([
        ('ADM', 'ADM'),
        ('OPERATIVO (GERENTES, JEFES, LOGISTICOS)', 'OPERATIVO (GERENTES, JEFES, LOGISTICOS)'),
        ('VENDEDOR, REPARTIDO Y COBRADOR', 'VENDEDOR, REPARTIDO Y COBRADOR'),
        # Nuevo para A&R
        ('COORDINADOR','COORDINADOR'),
        ('SUPERVISOR','SUPERVISOR'),
        ('VENDEDOR - MASIVO','VENDEDOR - MASIVO'),
        ('ASESOR DE VENTAS','ASESOR DE VENTAS'),
        ('PART TIME','PART TIME'),
   

    ], string="Tipo de trabajo", default='ADM')
    
    pdf_filename = fields.Char()
    pdf_binary = fields.Binary('Contrato PDF')  
    
    year_contract = fields.Integer('Años de duración de contrato', compute="compute_date", store=True) 
    month_contract = fields.Integer('Meses de duración de contrato', compute="compute_date", store=True) 
    day_contract = fields.Integer('Días de duración de contrato', compute="compute_date", store=True) 
    
    salary_word = fields.Char('Sueldo en texto', compute="compute_remuneration", store=True) 
    move_word = fields.Char('Movilidad en texto', compute="compute_remuneration", store=True) 
    
    month_start_word = fields.Char('Mes de inicio de contrato en texto', compute="month_word", store=True) 
    month_end_word = fields.Char('Mes de fin de contrato en texto', compute="month_word", store=True) 
    
    previous_contract = fields.Many2one('hr.contract', compute="compute_contract", store=True)
    
    def send_contract_email(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        if not self.contract_file:
            self.compute_contract_format()
        
        try:
            if(self.previous_contract):
                template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_renovation')
                template_id.attachment_ids = [(4, self.contract_file.id)]
            else:
                if(self.work_type == 'ADM'):
                    if self.labor == 'Labor hibrida':
                        template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_hybrid')
                        template_id.attachment_ids = [(4, self.contract_file.id)]
                    elif self.labor == 'Labor teletrabajo':
                        template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_teletrabajo')
                        template_id.attachment_ids = [(4, self.contract_file.id)]
                    elif self.labor == 'Labor presencial':
                        template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_teletrabajo')
                        template_id.attachment_ids = [(4, self.contract_file.id)]
                    else:
                        raise ValidationError(_("Seleccione una labor."))
                elif self.work_type == 'OPERATIVO (GERENTES, JEFES, LOGISTICOS)':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_operative')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'VENDEDOR, REPARTIDO Y COBRADOR':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_format_seller')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'COORDINADOR':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_ayr_vendor_mass')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'SUPERVISOR':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_ayr_supervisor_ventas')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'VENDEDOR - MASIVO':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_ayr_part_time')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'ASESOR DE VENTAS':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_ayr_coordinador')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                elif self.work_type == 'PART TIME':
                    template_id = self.env.ref('hr_contrac_format.ir_template_contract_ayr_asesor_ventas')
                    template_id.attachment_ids = [(4, self.contract_file.id)]
                else:
                    raise ValidationError(_("Seleccione un tipo de trabajo."))
                                    
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False

        ctx = {
            'default_model': 'hr.contract',
            'default_res_ids': self.ids,
            'default_use_template': bool(template_id.id),
            'default_template_id': template_id.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    
    def _last_day_of_month(self, any_day): 
        next_month = any_day.replace(day=28) + timedelta(days=4) 
        return next_month - timedelta(days=next_month.day)

    def get_float_to_spanish_letters(self,number):
        '''
        Convierte los numeros de los sueldos a palabras en español ,
        por ejemplo: 1000.50 -> MIL Y CINCUENTA/100 SOLES
        '''
        
        if number < 0 or number >= 1e12:
            return ""   
        
        integer_part = int(number)
        decimal_part = int(round((number - integer_part) * 100))
        
        result = num2words(integer_part, lang='es').capitalize()
        
        if decimal_part < 10:
            result += " con 0" + str(decimal_part) + "/100 soles"
        else:
            result += " con " + str(decimal_part) + "/100 soles"

        return result
    
    @api.depends('date_start', 'date_end')
    def month_word(self):
        month_list = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
        for element in self:
            if element.date_start:
                element.month_start_word =  month_list[element.date_start.month-1]
            if element.date_end:
                element.month_end_word = month_list[element.date_end.month-1]

    def difference_in_years_months_days(self, date_b, date_a):
        diff = relativedelta(date_a, date_b)
        days = diff.days + 1
        months = diff.months
        years = diff.years
        years = years or 0
        months = months or 0
        days = days or 0
        if self._last_day_of_month(date_a) == date_a and date_b.day == 1:
            days = 0
            months += 1
            if months == 12 :
                years  += 1
                months = 0
        return years, months, days

    def compute_contract_format(self):
        if(self.previous_contract):
            report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_renovation_report', self.id)

            self.pdf_filename = "RENOVACIÓN - " + self.employee_id.name
        else:
            if self.work_type == 'ADM':
                if(self.labor == 'Labor hibrida'):
                    report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_vendor_mass', self.id)
                elif(self.labor == 'Labor teletrabajo'):
                    report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_adm_teletrabajo', self.id)
                elif(self.labor == 'Labor presencial'):
                    report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_adm_teletrabajo', self.id)
                else:
                    raise ValidationError(_("Seleccione una labor."))
                    
            elif self.work_type == 'OPERATIVO (GERENTES, JEFES, LOGISTICOS)':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_operative_operative_report', self.id)

            elif self.work_type == 'VENDEDOR, REPARTIDO Y COBRADOR':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_operative_seller_report', self.id)

            elif self.work_type == 'COORDINADOR':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_coordinador', self.id)

            elif self.work_type == 'SUPERVISOR':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_supervisor_ventas', self.id)

            elif self.work_type == 'VENDEDOR - MASIVO':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_vendor_mass', self.id)

            elif self.work_type == 'ASESOR DE VENTAS':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_asesor_ventas', self.id)
            
            elif self.work_type == 'PART TIME':
                report_template_id = self.env['ir.actions.report']._render_qweb_pdf('hr_contrac_format.report_ayr_part_time', self.id)
            
            else:
                raise ValidationError(_("Seleccione un tipo de trabajo."))
            
            self.pdf_filename = "CONTRATO - " + self.employee_id.name
        return report_template_id[0]
    
    @api.onchange("work_type")
    def _change_data(self):
        if(self.work_type != 'ADM'):
            self.labor = None
    
    @api.depends('date_end')
    def compute_date(self):
        for element in self:
            if(element.date_end):
                element.year_contract, element.month_contract, element.day_contract = self.difference_in_years_months_days(element.date_start, element.date_end)
    
    @api.depends('employee_id')
    def compute_contract(self):
        data = self.env['hr.contract'].search([], order = "id asc")
        for element in self:
            data_contract = data.filtered(lambda x: x.employee_id.id == element.employee_id.id)
            if(len(data_contract) > 1 and data_contract[0].id != element.id):
                try:
                    index = data_contract.mapped("id").index(element.id)
                    element.previous_contract = data_contract[index-1].id
                except:
                    element.previous_contract = data_contract[-1].id
            else:
                element.previous_contract = None

    @api.depends('wage') 
    def compute_remuneration(self):
        for element in self:
            element.salary_word = self.get_float_to_spanish_letters(element.wage)
            element.move_word = self.get_float_to_spanish_letters(element.move_sa)