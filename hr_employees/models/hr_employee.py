# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models,_
from datetime import datetime, timedelta, time
# from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
# from oa_development.hr_analysis.models.hr_analysis_holidays import HrAnalysisHolidays
from odoo.exceptions import UserError
import passlib.context
import base64
import random
import string
import logging

_logger = logging.getLogger(__name__)

DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
        ['pbkdf2_sha512', 'plaintext'],
        # deprecated algorithms are still verified as usual, but ``needs_update``
        # will indicate that the stored hash should be replaced by a more recent
        # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
        # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
        deprecated=['plaintext'],
    )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    last_contract_date = fields.Date(string = "Fecha Cese", compute = '_compute_last_contract_date' , store=True, required=False, )
    # last_contract_date = fields.Date(string="Fecha Cese",related='contract_id.last_contract_date',store=True,readonly=False)
    job_id = fields.Many2one('hr.job', store=True, compute='_depends_contract_job_id', readonly=False, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Job Position')
    first_name = fields.Char(string="Primer Nombre", store=True, )
    second_name = fields.Char(string="Segundo Nombre", store=True, )
    first_last_name =  fields.Char(string="Primer Apellido", store=True, )
    second_last_name = fields.Char(string="Segundo Apellido", store=True, )
    family_asig = fields.Boolean(string="Tiene asignacion familiar?", store=True,default=True)
    cod_ref = fields.Char(string="Código", store=True, compute='_compute_cod_ref')
    salary_amount = fields.Float(string="Sueldo recepcionado", store = True)
    amount_5ta = fields.Float(string="Impuesto recepcionado", store = True)
    reception_date = fields.Date(string="Fecha de recepción", store = True)
    last_company = fields.Char(string="Compañia anterior", store = True)
    children_number = fields.Integer(string="Número de Hijos", store=True) 
    location_id = fields.Many2one("hr.table.location", string="Localidad", store=True)
    type_work_assistance = fields.Selection([('Fiscalizado','Fiscalizado'), ('No Fiscalizado','No Fiscalizado')], string='Tipo de Asistencia Laboral', store=True)
    country_id = fields.Many2one(string="Country", comodel_name='res.country', help="Country for which this tag is available, when applied on taxes.")
    l10n_latam_identification_type_id = fields.Many2one('l10n_latam.identification.type', string="Tipo de Identificación")
    bank_cts_id = fields.Many2one('res.partner.bank', 'Cuenta Bancaria CTS')
    cod_coste_center = fields.Many2one('account.analytic.plan', string='Etiqueta Contable', store=True)
    # cod_coste_center_plan = fields.Many2one('account.analytic.plan', string='Etiqueta Contable', store=True)

    cod_coste_center_account = fields.One2many("hr.cod.coste.employees",'employee_id', string="Centro de Costos", store=True)
    # cod_coste_center_account_total = fields.Float(string="Porcentaje Total de Activos de Ce.Co.", store = True, required=True, compute="compute_cod_coste_center_account_total")
    cod_coste_center_account_total = fields.Float(string="Porc. Total de Activos de Ce.Co.", store = True, )
    is_passed = fields.Boolean(string="¿Es válido el centro de costo?", store=True,compute='compute_is_passed',)
    work_email = fields.Char('Work Email', store=True, compute='compute_work_email')
    
    year_certificate = fields.Char(string="Año de Egreso", store=True)
    year_essalud = fields.Char(string="Fecha de Regimen de Salud", store=True)
    year_afp = fields.Char(string="Fecha de Afiliacion de AFP", store=True)
    
    ficha_file = fields.Many2one('ir.attachment', string='Ficha Incorporacion Personal PDF', store=True)
    ficha_record = fields.Binary('Ficha Incorporacion Personal')
    ficha_filename = fields.Char()
    
    dec_domi_file = fields.Many2one('ir.attachment', string='Declaracion Jurada de Domicilio PDF', store=True)
    dec_domi_record = fields.Binary('Declaracion Jurada de Domicilio')
    dec_domi_filename = fields.Char()
    
    cargo_file = fields.Many2one('ir.attachment', string='Cargo RIT PDF', store=True)
    cargo_record = fields.Binary('Cargo RIT')
    cargo_filename = fields.Char()
    
    dec_5ta_file = fields.Many2one('ir.attachment', string='Declaracion Jurada 5ta PDF', store=True)
    dec_5ta_record = fields.Binary('Declaracion Jurada 5ta')
    dec_5ta_filename = fields.Char()
    
    entrega_file = fields.Many2one('ir.attachment', string='Entrega RISST PDF', store=True)
    entrega_record = fields.Binary('Constancia Entrega RISST')
    entrega_filename = fields.Char()
    
    sctr_id = fields.Many2one('hr.sctr', string="Aseguradora", store=True, compute="_compute_child_ids_sctr_employee")
    child_ids_sctr_employee = fields.One2many("hr.sctr.employee","parent_id", string="Historial - SCTR", store=True)

    pension_system_id = fields.Many2one(comodel_name='pension.system', string='Sistema de pensiones', groups="hr.group_hr_user")
    cod_cuspp = fields.Char(string="CUSPP", store=True)
    pension_mode = fields.Selection([('flujo', 'Flujo'), ('mixto', 'Mixto')], string='Tipo Pensión', store=True)
    
    cell_phone_private = fields.Char(string = "Celular", related="address_id.mobile", store=True)
    relationship = fields.Char(string = "Parentesco", store=True)
    child_ids_health = fields.One2many("hr.employee.health","parent_id", string="Historial - Régimen de Salud")
    child_ids_pension = fields.One2many("hr.employee.pension","parent_id", string="Historial - Régimen de Pensión")
    health_regime_id = fields.Many2one('health.regime', string="Régimen de Salud", store=True, compute="_compute_regime")
    age = fields.Char(string="Edad", store=True, compute="_compute_age")
    address_home_id = fields.Many2one('res.partner',string="Direccion privada",compute="_compute_address_home_id",store=True)

    @api.depends('address_id')
    def _compute_address_home_id(self):
        for r in self:
            r.address_home_id = r.address_id.id

    def get_gerente_firma_url(self):
        if self.company_id.gerente_firma:
            return '/web/image?model=res.company&id=%d&field=gerente_firma' % self.company_id.id
    
    @api.depends('child_ids_sctr_employee')
    def _compute_child_ids_sctr_employee(self):
        if not self.child_ids_sctr_employee:
            self.sctr_id = False
        else:
            for element in self.child_ids_sctr_employee:
                if element:
                    if element.cod_active==True:
                        self.sctr_id =  element.employee_sctr_id
    
    @api.depends('child_ids_health', 'child_ids_pension')
    def _compute_regime(self):
        for element in self:
            if len(element.child_ids_health):
                element.health_regime_id = element.child_ids_health[len(element.child_ids_health)-1].regimen_id

            if len(element.child_ids_pension):  
                element.pension_mode = element.child_ids_pension[len(element.child_ids_pension)-1].pension_mode
                element.pension_system_id = element.child_ids_pension[len(element.child_ids_pension)-1].pension_system_id
                element.cod_cuspp = element.child_ids_pension[len(element.child_ids_pension)-1].cod_cuspp

    def calculate_age(self, birthdate):
        current_date = datetime.now()
        age = current_date.year - birthdate.year - ((current_date.month, current_date.day) < (birthdate.month, birthdate.day))
        return age

    @api.depends('birthday')
    def _compute_age(self, cron = 1):
        for element in self:
            if cron == 0:
                if element.birthday and element.contract_id.state == "open":
                    element.age = self.calculate_age(element.birthday)
            else:
                if element.birthday:
                    element.age = self.calculate_age(element.birthday)
    
    def send_file(self):
        
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']

        if not self.ficha_file and not self.dec_domi_file and not self.cargo_file and not self.dec_5ta_file and not self.entrega_file:
            self.generate_file()
        
        try:
            template_id = self.env.ref('hr_employees.mail_template_new_employee')
            template_id.attachment_ids = [(4, self.ficha_file.id),(4, self.dec_domi_file.id),(4, self.cargo_file.id),(4, self.dec_5ta_file.id),(4, self.entrega_file.id)]
        except ValueError:
            template_id = False
            
        try:
            compose_form_id = ir_model_data._xmlid_lookup('mail.email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
            
        ctx = {
            'default_model': 'hr.employee',
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
    
    def generate_file(self):
        list_record, list_file, list_name = [], [], []
        name_value = ['Ficha Incorporacion Personal', 'Declaracion Jurada de Domicilio',' Cargo RIT', 'Declaracion Jurada 5ta', 'Constancia Entrega RISST']

        i = 0
        for id_report in ['report_entry_forms', 'report_dec_street', 'report_cargo_rits', 'report_dec_no_5tas', 'report_cargo_rissts']:
            # report_template_id = self.env.ref('hr_employees.' + id_report ).with_context(force_report_rendering=True)._render_qweb_pdf(self.id)

            report_template_id = self.env['ir.actions.report']._render_qweb_pdf("hr_employees."+id_report, self.id)

            record = base64.b64encode(report_template_id[0])
            
            ir_values = {
                'name': name_value[i]+'.pdf',
                'type': 'binary',
                'datas': record,
                'store_fname': record,
                'mimetype': 'application/x-pdf',
            }
            
            list_name.append(name_value[i])
            list_record.append(record)
            file = self.env['ir.attachment'].create(ir_values)
            list_file.append(file)
            i += 1
            
        self.ficha_file, self.dec_domi_file, self.cargo_file, self.dec_5ta_file, self.entrega_file = list_file
        self.ficha_record, self.dec_domi_record, self.cargo_record, self.dec_5ta_record, self.entrega_record = list_record 
        self.ficha_filename, self.dec_domi_filename, self.cargo_filename, self.dec_5ta_filename, self.entrega_filename = list_name
    
    @api.onchange('cod_coste_center_account','cod_coste_center_account.total','cod_coste_center_account.percent')
    def compute_cod_coste_center_account_total(self):
        for record in self:
            record.cod_coste_center_account_total = sum(i.percent for i in record.cod_coste_center_account if i.is_active )
            record.is_passed = True if record.cod_coste_center_account_total == 100 else False

    @api.depends('cod_coste_center_account_total')
    def compute_is_passed(self):
        for record in self:
            record.is_passed = True if record.cod_coste_center_account_total == 100 else False

    # @api.model_create_multi
    # def create(self,vals_list):
    #     for vals in vals_list:
    #         cod_coste_center_account = vals.get("cod_coste_center_account") or []
    #         if not cod_coste_center_account:
    #             raise UserError('Agregar Centro de Costo')
            
    #     return super(HrEmployee,self).create(vals_list)

    # def write(self,values):
    #     if 'cod_coste_center_account' in values:
    #         cod_coste_center_account = values["cod_coste_center_account"]

    #         for line in cod_coste_center_account:
    #             if line[2] and line[0]==1:
    #                 code = self.cod_coste_center_account.browse(line[1])
    #                 if not code.date_from :
    #                     raise UserError('Debe haber Fecha de Ingreso')
    #                 if 'date_to' in line[2] and line[2]["date_to"] and code.date_from > datetime.strptime(line[2]["date_to"],"%Y-%m-%d").date():
    #                     raise UserError('Fecha Fin debe ser menor a las Fechas de Ingresos')

    #         cod_coste_center_account_aux = self.cod_coste_center_account
    #         if len(cod_coste_center_account_aux) > 0:
    #             line_del = [line[1] for line in cod_coste_center_account if line[0] == 2]
    #             cod_coste_center_account_aux = cod_coste_center_account_aux.filtered(lambda x:x.id not in  line_del  )
    #             if len(cod_coste_center_account_aux) == 0:
    #                 raise UserError('Agregar Centro Contable')

    #     res = super(HrEmployee,self).write(values)
    #     if 'is_passed' in values:
    #         if not values["is_passed"]:
    #             raise UserError('El porcentaje total no es 100%')
    #     else:
    #         if not self.is_passed:
    #             raise UserError('El porcentaje total no es 100%')
    #     return res

    @api.depends('contract_id.job_id')
    def _depends_contract_job_id(self):
        for record in self:
            if record.contract_id.job_id :
                record.job_id = record.contract_id.job_id

    @api.onchange('first_name', 'second_name', 'first_last_name', 'second_last_name')
    def _onchange_name_employee(self):
        first_last_name = self.first_last_name if self.first_last_name else ""
        second_last_name = " "  + self.second_last_name if self.second_last_name else ""
        first_name = " "  + self.first_name if self.first_name else ""
        second_name = " "  + self.second_name if self.second_name else ""
        self.name =  first_last_name + second_last_name + first_name +  second_name
    
    ##############################
    
    # def generate_password(self, length=12):
    #     lowercase_chars = string.ascii_lowercase
    #     uppercase_chars = string.ascii_uppercase
    #     digits = string.digits
    #     special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'

    #     all_chars = lowercase_chars + uppercase_chars + digits + special_chars
    #     if length < 12: length = 12
    #     pswd = ''.join(random.choice(all_chars) for _ in range(length))

    #     return pswd

    # def _crypt_context(self):
    #     return DEFAULT_CRYPT_CONTEXT
    
    # def _set_password(self, users, password):
    #     ctx = self._crypt_context()
    #     hash_password = ctx.hash if hasattr(ctx, 'hash') else ctx.encrypt
    #     self._set_encrypted_password(users, hash_password(password), password)

    # def _set_encrypted_password(self, users, pw, pwd_portal):
    #     assert self._crypt_context().identify(pw) != 'plaintext'
        
    #     users.write({
    #         'password' : pw,
    #         'pwd_portal': pwd_portal,
    #     })
        
    #     self.env.cr.commit()

    @api.depends('name')
    def _compute_cod_ref(self):
        for val in self:
            if val.id:
                val.cod_ref = "E" + str(val.id).zfill(5)
                
                # if val.company_id.portal_user:
                #     value = {
                #         'name' : val.name,
                #         'login' : val.cod_ref,
                #         'sel_groups_1_9_10': '9',
                #         'lang': 'es_PE',
                #     }
                    
                #     users = self.env["res.users"].create(value)
                    # pwd = self.generate_password(16)
                    # self._set_password(users, pwd)
                

    @api.depends('contract_id.reason_low_id')
    def _compute_last_contract_date(self):
        for record in self:
            if record.contract_id.reason_low_id:
                record.last_contract_date = record.contract_id.last_contract_date

    @api.depends('private_email')
    def compute_work_email(self):
        for record in self:
            if record.private_email:
                record.work_email = record.private_email
