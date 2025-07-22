from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class HrDefaultData(models.Model):
    _name = 'hr.default.data'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'Data por default cuando se creen compañias'

    name = fields.Char('Nombre', tracking=True)
    company_id = fields.Many2one('res.company',string="Compañia Destino",required=True, tracking=True)
    origin_id = fields.Many2one('res.company',string="Compañia Origen", default=1, required=True, tracking=True)

    @api.onchange('company_id','origin_id')
    def _get_name(self):
        if self.company_id and self.origin_id:
            self.name = "IMPORTA CONFIG: " + self.origin_id.name + " a " + self.company_id.name

    def _get_estructura_type(self,company_id):
        calendar_id = self.env['resource.calendar'].search([('company_id','=',company_id.id)],limit=1)
        type = self.env['hr.payroll.structure.type'].search([('name','=','Régimen Laboral Peruano'),('company_id','=', company_id.id)])
        if not type: 
            estructura_type = self.env['hr.payroll.structure.type'].create({
                'name': 'Régimen Laboral Peruano',
                'wage_type': 'monthly',
                'country_id': company_id.country_id.id,
                'abbr': 'RLP',
                'default_resource_calendar_id': calendar_id.id,
                'default_schedule_pay': 'monthly',
                'default_struct_id': 1,
                'default_work_entry_type_id': 1,
                'company_id':company_id.id,
            })
        else:
            estructura_type = type
        return estructura_type
    
    def _create_categs(self,company_id,origin_id):
        #Buscamos si hay castegorias del destino, si no hay prosigue la funcion
        if self.env['hr.salary.rule.category'].search_count([('company_id','=',company_id.id)]) == 0:
            #ahora buscamos las categorias del origen, para copiarlas 
            categ = self.env['hr.salary.rule.category'].sudo().search([('company_id','=',origin_id.id)])
            if categ:
                for c in categ:
                    vals = [{
                        'name': c.name,
                        'code': c.code,
                        'company_id': company_id.id, #definimos que la company es el destino nuevo
                    }]
                    _logger.warning("categorias a crear--------------- %s" % vals)
                    self.env['hr.salary.rule.category'].sudo().create(vals)

    def _get_estructure(self,company_id,type):
        report_id = self.env['ir.actions.report'].sudo().search([('name','=','Recibo de nómina')],limit=1)
        estr = self.env['hr.payroll.structure'].search([('name','=','Mensual'),('company_id','=',company_id.id)])
        if not estr:
            estructure = self.env['hr.payroll.structure'].sudo().create({
                'name': "Mensual",
                'company_id': company_id.id,
                'type_id': type.id,
                'abbr': 'MENSUAL',
                'use_worked_day_lines': True,
                'country_id': company_id.country_id.id,
                'report_id': report_id.id,
                'schedule_pay': 'monthly',
            })
        else:
            estructure = estr

        type.write({'default_struct_id':estructure.id})
        estructure.rule_ids.unlink()
        return estructure

    def _get_rule(self,company_id,origin_id,estructure):
        default_rules = self.env['hr.salary.rule'].sudo().search([('company_id','=',origin_id.id)])
        if self.env['hr.salary.rule'].search_count([('company_id','=',company_id.id)]) == 0:
            if default_rules:
                for rule in default_rules:
                    cat = self.env['hr.salary.rule.category'].search([('company_id','=',company_id.id),('code','=',rule.category_id.code)],limit = 1)
                    self.env['hr.salary.rule'].create({
                        'name':rule.name,
                        'category_id': cat.id,
                        'code': rule.code,
                        'appears_on_utilities':rule.appears_on_utilities,
                        'sequence': rule.sequence,
                        'company_id': company_id.id,
                        'appears_on_payslip':rule.appears_on_payslip,
                        'is_affected': rule.is_affected,
                        'struct_id': estructure.id,
                        'active': rule.active,
                        'condition_select':rule.condition_select,
                        'condition_python':rule.condition_python,
                        'amount_select':rule.amount_select,
                        'amount_python_compute': rule.amount_python_compute,
                        'have_5ta': rule.have_5ta,
                        'have_5ta_direct': rule.have_5ta_direct,
                        'have_5ta_grati': rule.have_5ta_grati,
                        'have_cts': rule.have_cts,
                        'have_gratification': rule.have_gratification,
                        'have_utilities': rule.have_utilities,
                        'have_holiday': rule.have_holiday,
                        'plame_id': rule.plame_id.id,
                        'appears_report_payroll':rule.appears_report_payroll,
                    })
        return default_rules

    def _get_inputs(self,company_id,origin_id,estructure):
        default_inputs = self.env['hr.payslip.input.type'].sudo().search([('company_id','=',origin_id.id)]) ## 46
        if self.env['hr.payslip.input.type'].search_count([('company_id','=',company_id.id)]) == 0:
            if default_inputs:
                for input in default_inputs:
                    self.env['hr.payslip.input.type'].create({
                        'name':input.name,
                        'country_id': company_id.country_id.id,
                        'struct_ids': [(6, 0, [estructure.id])] if input.struct_ids else False,
                        'code': input.code,
                        'is_affected': input.is_affected,
                        'company_id': company_id.id,
                    })
    def _get_regimen(self,company_id,estructura_type):
        r_g = r_p = r_m = None
        
        if self.env['peru.employee.regime'].search_count([('name','=',"Régimen General"),('company_id','=',company_id.id)]) == 0:
            r_g = self.env['peru.employee.regime'].create({
                'name': "Régimen General",
                'company_id': company_id.id,
                'structure_type_id': estructura_type.id,
                'abbr': 'RG',
            })
        
        if self.env['peru.employee.regime'].search_count([('name','=',"Régimen Pequeña"),('company_id','=',company_id.id)]) == 0:
            r_p = self.env['peru.employee.regime'].create({
                'name': "Régimen Pequeña",
                'company_id': company_id.id,
                'structure_type_id': estructura_type.id,
                'abbr': 'RP',
            })

        if self.env['peru.employee.regime'].search_count([('name','=',"Régimen Micro"),('company_id','=',company_id.id)]) == 0:
            r_m = self.env['peru.employee.regime'].create({
                'name': "Régimen Micro",
                'company_id': company_id.id,
                'structure_type_id': estructura_type.id,
                'abbr': 'RM',
            })
        return r_g, r_p , r_m

    def _get_times_work(self, company_id, origin):
        time_work = self.env['resource.calendar'].search([('name', '=', 'Estándar de 40 horas a la semana'),('company_id', '=', company_id.id)])
        time_work_origin = self.env['resource.calendar'].sudo().search([('name', '=', 'Estándar de 48 horas a la semana'),('company_id', '=', origin.id)])
        if time_work:
            time_work.attendance_ids.unlink()
            time_work.write({
                'name': 'Estándar de 48 horas a la semana',
                'hours_per_day': 08.00,
                'full_time_required_hours': 48.00,
                'tz' : 'America/Lima',
                'attendance_ids': [(0, 0, {
                    'name': att.name,
                    'dayofweek': att.dayofweek,
                    'day_period': att.day_period,
                    'hour_from': att.hour_from,
                    'hour_to': att.hour_to,
                    'work_entry_type_id': att.work_entry_type_id.id,
                }) for att in time_work_origin.attendance_ids]
            })
        return time_work


    def _get_update_data(self,origin):
        ## actualizar empresa default y dejar data para peru
        time_work = self.env['resource.calendar'].search([('name','=','Standard 40 hours/week'),('company_id','=',origin.id)])
        if time_work:
            time_work.name = 'Estándar de 48 horas a la semana'
            time_work.full_time_required_hours = 48.00
            time_work.tz = 'America/Lima'
            time_work.attendance_ids = [(0, 0, {
                'name': 'Saturday Morning',
                'dayofweek': '5',
                'day_period': 'morning',
                'hour_from': 8.0,
                'hour_to': 12.0,
                'work_entry_type_id':None,
            }), 
            (0, 0, {
                'name': 'Saturday Afternoon',
                'dayofweek': '5',
                'day_period': 'afternoon',
                'hour_from': 13.0,
                'hour_to': 17.0,
                'work_entry_type_id':None,
            })]

        # Delete data to company origin TODO, corregir los nombres de las reglas y agregas las adicionales para la version 17

        # delete_data = {
        #     'hr.payroll.structure.type': ['Worker', 'Employee'],
        #     'hr.salary.rule': ['Salario neto', 'Reembolso', 'Bruto', 'Salario básico total']
        # }

        # for model, names in delete_data.items():
        #     records = self.env[model].search([('name', 'in', names), ('company_id', '=', origin.id)])
        #     if records:
        #         records.unlink()            
            
    def _get_default_data(self,company,origin):

        ## Tiempo de trabajo
        self._get_times_work(company,origin)

        ## Tipo de Estructura
        estructura_type = self._get_estructura_type(company)
    
        ## categoria de reglas
        self._create_categs(company, origin)

        ## Estructura Salarial
        estructure = self._get_estructure(company,estructura_type)
        
        ## REGLAS
        self._get_rule(company,origin,estructure)

        ## INPUTS
        self._get_inputs(company,origin,estructure)

        ## Regimen Laboral
        self._get_regimen(company,estructura_type)



    def action_default_data(self):

        if self.origin_id.id ==1:
            if self.company_id.id == 1:
                self._get_update_data(self.origin_id)
            else:
                self._get_default_data(self.company_id,self.origin_id)
        else:
            raise UserError(_("Solo puedes importar configuracion desde la compañia default."))





