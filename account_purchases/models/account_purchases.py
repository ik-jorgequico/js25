# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import calendar


class AccountPurchases(models.Model):
    _name = "account.purchases"
    _description = "Account Purchases"
    _line_model = ""
    _prefix_name = ""
    _main_model = ""
    
    name = fields.Char("Nombre")
    company_id = fields.Many2one('res.company', 'Compañía', default=lambda self: self.env.company)
    
    state = fields.Selection([
        ('draft','Borrador'),
        ('done','Realizado'),
    ], "Estado", default='draft')
    
    current_year = int(datetime.now().date().strftime("%Y"))
    year = fields.Selection([(str(i), str(i)) for i in range(current_year, current_year - 8, -1)], "Año", store=True, required=True)
    month = fields.Selection([
        ('01','ENERO'),
        ('02','FEBRERO'),
        ('03','MARZO'),
        ('04','ABRIL'),
        ('05','MAYO'),
        ('06','JUNIO'),
        ('07','JULIO'),
        ('08','AGOSTO'),
        ('09','SEPTIEMBRE'),
        ('10','OCTUBRE'),
        ('11','NOVIEMBRE'),
        ('12','DICIEMBRE'),
    ], "Mes", store=True, required=True)
    
    period_name = fields.Char("Periodo")
    date_from = fields.Date("Fecha Inicial")
    date_to = fields.Date("Fecha Final")
    
    indicator_o = fields.Selection([
        ('0','Cierre de operaciones-baja de inscripción en el RUC'),
        ('1','Empresa o entidad operativa'),
        ('2','Cierre del libro-no obligado a llevarlo'),
    ], "Indicador de operaciones", default='1', store=True)
    indicator_m = fields.Selection([
        ('1','Nuevos Soles'),
        ('2','US Dólares'),
    ], "Indicador de Moneda utilizada", default='1', store=True)
    indicator_c = fields.Selection([
        ('0','Sin Información'),
        ('1','Con Información'),
    ], "Indicador del contenido del libro", default='1', store=True)
    indicator_g = fields.Selection([
        ('1','Generado por PLE (Fijo)'),
    ], "Indicador de generación", default='1', store=True)
    
    xls_filename = fields.Char("Nombre archivo XLS")
    xls_binary = fields.Binary("Reporte Excel")
    ple_filename = fields.Char('Nombre archivo PLE')
    ple_binary = fields.Binary('Reporte PLE')
    
    # - STATIC METHODS
    @staticmethod
    def first_and_last_day(month: str, year: str):
        first_day_month = datetime(int(year), int(month), 1)
        last_day = calendar.monthrange(int(year), int(month))[1]
        last_day_month = datetime(int(year), int(month), last_day)
        return first_day_month, last_day_month
    
    @staticmethod
    def check_line(line):
        if not line.state_ple:
            raise UserError("No se encontró Estado para el PLE en Asiento: %s !!"  % (line.name))
        
        if not line.seriecomp_sunat or not line.numcomp_sunat:
            raise UserError("No se tiene Serie ni Numero en Asiento: %s !!"  % (line.name))
        
        if line.l10n_latam_document_type_id.code in ['01','03','07','08']:
            if len(line.seriecomp_sunat) != 4:
                raise UserError("Serie del Comprobante diferente de 4 digitos en Asiento : %s !!"  % (line.name))
            if len(line.numcomp_sunat) != 8:
                raise UserError("Numero del Comprobante diferente de 8 digitos en Asiento : %s !!"  % (line.name))
        
        if line.l10n_latam_document_type_id.code in ['05']:
            if len(line.seriecomp_sunat) != 1:
                raise UserError("Serie del Comprobante diferente de 1 digito en Asiento : %s !!"  % (line.name))
            if len(line.numcomp_sunat) > 11:
                raise UserError("Numero del Comprobante mayor de 11 digitos en Asiento : %s !!"  % (line.name))
        
        if line.l10n_latam_document_type_id.code in ['22']:
            if len(line.seriecomp_sunat) != 4:
                raise UserError("Serie del Comprobante diferente de 4 digitos en Asiento : %s !! debe ser 0820"  % (line.name) )
            if len(line.numcomp_sunat) > 20:
                raise UserError("Numero del Comprobante mayor de 20 digitos en Asiento : %s !!"  % (line.name))
        
        if line.l10n_latam_document_type_id.code in ['50','52']:
            if len(line.seriecomp_sunat) != 3:
                raise UserError("Serie del Comprobante diferente de 3 digitos en Asiento : %s !!"  % (line.name))
            if len(line.numcomp_sunat) != 6:
                raise UserError("Numero del Comprobante diferente de 6 digitos en Asiento : %s !!"  % (line.name))
    
    # - ONCHANGES
    @api.onchange("month", "year")
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.year}/{rec.month}/{rec._prefix_name or 'Registro'}" if rec.month and rec.year else "/"
    
    # - GENERATORS
    def main_domain(self):
        return [
            ('date','>=',self.date_from),
            ('date','<=',self.date_to),
            ('company_id.id','=',self.company_id.id),
            ('state','=','posted'),
        ]
    
    # - PRIVATE METHODS
    def _validate_inheritances(self):
        if not self._main_model:
            raise ValidationError(f'Debe heredar "_main_model" en {self._name}.')
        if not self._line_model:
            raise ValidationError(f'Debe heredar "_line_model" en {self._name}.')
    
    def _get_moves(self):
        self._validate_inheritances()
        self.date_from, self.date_to = self.first_and_last_day(self.month, self.year)
        domain = self.main_domain()
        return self.env[self._main_model].search(domain)
    
    # - MAIN METHODS
    def get_filename_ple(self, book_code: str):
        company_vat = self.company_id.vat or '99999999999'
        ind_o = self.indicator_o
        ind_i = self.indicator_c
        ind_m = self.indicator_m
        ind_g = self.indicator_g
        return f"LE{company_vat}{self.year}{self.month}{book_code}{ind_o}{ind_i}{ind_m}{ind_g}"
    
    def prepare_line_data(self, line):
        return {
            "parent_id": self.id,
            "date_to": self.date_to,
            "date_from": self.date_from,
            "periodo_sunat": f"{self.month}-{self.year}",
            "company_id": line.company_id.id,
            "period_ple": f"{self.year}{self.month}00",
            "cuo_sunat": line.id,
        }
    
    def prepare_xls_data(self, line, count=None):
        data = {
            "PERIODO": line.periodo_sunat or '',
            "PERIODO PLE": line.period_ple or '',
            "CUO": line.cuo_sunat or '',
            "M0002": line.correlativo_ple or '',
            "COMPANY NAME": self.company_id.name or '',
            "CORRELATIVO": line.entry or '',
            "FECHA EMISION": line.invoice_date.strftime('%d/%m/%Y') or '',  
            "FECHA VENCIMIENTO": line.date_due.strftime('%d/%m/%Y') or '',
            "TIPO CPE": line.type_cpe or '',
            "SERIE CPE": line.serie_cpe or '',
            "AÑO DUA": line.dua_year or '',
            "NUMERO CPE": line.num_cpe or '',
            "TIPO DOC": line.type_doc or '',
            "NUMERO DOC": line.num_doc or '',
            "RAZON SOCIAL": line.company_name or '',
            "TOTAL": "%.2f" % line.total_amount or "%.2f" % 0.00,
            "MONEDA": line.currency_line or '',
            "TIPO DE CAMBIO": "%.3f" % line.tc_sunat or "%.3f" % 0.00,
            "FECHA REV": line.date_reversed.strftime('%d/%m/%Y') if line.date_reversed else '',
            "TIPO REV": line.tipcomp_reversed or '',
            "SERIE REV": line.serie_reversed or '',
            "NUMERO REV": line.num_reversed or '',
            "PERCENT IGV": line.percent_igv or "%.2f" % 0.00,
            "ESTADO PLE": line.state_ple or '',
            "TOTAL REAL": "%.2f" % line.total_real or "%.2f" % 0.00,
        }
        
        if count:
            data.update({"CONTADOR": count})
        
        return data
    
    def get_xls_data(self, lines):
        return [self.prepare_xls_data(line, count=count) for count, line in enumerate(lines, start=1)]
    
    def compute_sheet(self):
        self.ensure_one()
        self._validate_inheritances()
        self.child_ids.unlink()
        
        move_ids = self._get_moves()
        
        val_list = []
        for line in move_ids:
            if self.env.context.get('check_lines'):
                self.check_line(line)
            
            data = self.prepare_line_data(line)
            val_list.append(data)
        
        self.env[self._line_model].create(val_list)
    
    # - BUTTONS
    def action_confirm(self):
        for rec in self:
            rec.state ='done'
    
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'
    
    def action_generate_xls(self):
        pass
    
    def action_generate_ple(self):
        pass
    

class AccountPurchasesLine(models.Model):
    _name = "account.purchases.line"
    _description = "Account Purchases Line"
    
    company_id = fields.Many2one('res.company', 'Compañía', store=True, readonly=True)
    
    name = fields.Char('Nombre', readonly=True)
    entry = fields.Char("Asiento", readonly=True)
    periodo_sunat = fields.Char("Periodo", readonly=True)
    date_to = fields.Date("Fecha Final", readonly=True)
    date_from = fields.Date("Fecha Inicial", readonly=True)
    invoice_date = fields.Date("Fecha Emisión", readonly=True)
    date_due = fields.Date("Fecha de Vencimiento", readonly=True)
    account_date = fields.Date("Fecha Contable", readonly=True)
    type_cpe = fields.Char("Tipo CP/Doc.")
    serie_cpe = fields.Char("Serie del CDP")
    num_cpe = fields.Char("Nro CP o Doc. Nro Inicial (Rango)")
    type_doc = fields.Char("Tipo Doc Identidad")
    num_doc = fields.Char("Num Doc.", readonly=True)
    company_name = fields.Char("Razon Social", readonly=True)
    base_imp = fields.Float("Base Imponible", digits=[20,2], readonly=True)
    igv = fields.Float("IGV", digits=[20,2], readonly=True)
    inafecto = fields.Float("Inafecto", digits=[20,2], readonly=True)
    total_amount = fields.Float("Total", digits=[20,2], readonly=True)
    num_det = fields.Char("Constancia Detracción", readonly=True)
    date_det = fields.Date("Fecha Detracción", readonly=True)
    tc_sunat = fields.Float("Tipo de Cambio", digits=[2,3], readonly=True)
    date_reversed = fields.Date("Fecha Ref", readonly=True)
    tipcomp_reversed = fields.Char("Tipo Comp Ref", readonly=True)
    serie_reversed = fields.Char("Serie Ref", readonly=True)
    num_reversed = fields.Char("Numero Ref", readonly=True)
    dua_year = fields.Char('Año Dua', readonly=True)
    period_ple = fields.Char('Periodo Para PLE', readonly=True)
    correlativo_ple = fields.Char('Correlativo PLE', readonly=True)
    state_ple = fields.Char("Estado PLE", readonly=True)
    cuo_sunat = fields.Integer("CUO", readonly=True)
    percent_igv = fields.Float('% IGV', digits=(2,0), readonly=True)
    currency_line = fields.Char("Code Moneda", readonly=True)
    total_real = fields.Float("Total Real", digits=(20,2), readonly=True)
    op_nodom = fields.Boolean("Operación no domiciliado", readonly=True)
    