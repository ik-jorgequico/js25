# -*- coding: utf-8 -*-
from odoo import fields, models
from .ple51_report_xls import ExcelReport
from .plame_report_txt import PlameReport


class DataPle51(models.Model):
    _name = "data.ple51"
    _inherit = ["account.purchases"]
    _description = "Data for Libro Diario"
    _main_model = "account.move.line"
    _line_model = "data.ple51.line"
    _prefix_name = "Libro diario"
    
    child_ids = fields.One2many(_line_model, "parent_id", "Registros")
    
    @staticmethod
    def _get_book_data(line):
        code_book = sequence_book = num_book = ''
        if line.journal_id.type == 'purchase' and line.journal_id.have_purchase == True:
            code_book = '8'
            sequence_book = line.move_id.name.split('/')[0]
            num_book = line.move_id.name.split('/')[3]
        elif line.journal_id.type == 'sale' and line.journal_id.have_sale == True:
            code_book = '14'
            sequence_book = line.move_id.name.split('-')[0]
            num_book = line.move_id.name.split('-')[1]
        elif line.journal_id.type == 'cash' or line.journal_id.type == 'bank':
            code_book = '1'
            sequence_book = line.move_id.name.split('/')[0]
            num_book = line.move_id.name.split('/')[2]
        else:
            code_book = '5'
            sequence_book = line.move_id.name.split('/')[0]
            num_book = line.move_id.name.split('/')[3]
        return code_book, sequence_book, num_book
    
    @staticmethod
    def _get_cpe(line):
        serie_cpe = num_cpe = ''
        if line.move_id.journal_id.type == 'sale':
            serie_cpe = line.move_id.name.split('-')[0]
            num_cpe = line.move_id.name.split('-')[1]
        elif line.move_id.journal_id.type == 'purchase':
            serie_cpe = line.move_id.seriecomp_sunat
            num_cpe = line.move_id.numcomp_sunat
        return serie_cpe, num_cpe
    
    def prepare_line_data(self, line):
        records = super(DataPle51, self).prepare_line_data(line)
        
        code_book, sequence_book, num_book = self._get_book_data(line)
        serie_cpe, num_cpe = self._get_cpe(line)
        
        records.update({
            "name": f"{self._prefix_name}/{line.move_name}",
            "invoice_date": line.date if not line.move_id.invoice_date else line.move_id.invoice_date,
            "date": line.date,
            "ref": line.move_id.glosa_sunat or line.ref or line.move_name,
            "code_book": code_book,
            "sequence_book": sequence_book,
            "num_book": num_book,
            "chart_code": line.account_id.code,
            "chart_name": line.account_id.name,
            "debit": line.debit,
            "credit": line.credit,
            "entry": line.move_id.name,
            "correlativo_ple": line.sequence_ple,	
            "state_ple": '1',
            "type_doc": line.move_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code or line.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            "num_doc": line.move_id.partner_id.vat or line.partner_id.vat,
            "type_cpe": line.move_id.l10n_latam_document_type_id.code or '00',
            "serie_cpe": serie_cpe if serie_cpe else sequence_book,
            "num_cpe": num_cpe if num_cpe else num_book,
            "date_due": line.move_id.invoice_date_due,
            "currency": line.currency_id.name,
        })
        
        return records
    
    def main_domain(self):
        return [
            ('date','>=',self.date_from),
            ('date','<=',self.date_to),
            ('company_id.id','=',self.company_id.id),
            ('parent_state','=','posted'),
        ]
    
    def prepare_xls_data(self, line, count=None) -> dict:
        data = super(DataPle51, self).prepare_xls_data(line, count=count)
        
        data.update({
            "SECUENCIA": line.correlativo_ple or '',
            "ASIENTO": line.entry or '',
            "FECHA": line.date.strftime('%d/%m/%Y') or '',
            "REF": line.ref or '',
            "CODE LIBRO": line.code_book or '',
            "SECUENCIA LIBRO": line.sequence_book or '',
            "NUMERO LIBRO": line.num_book or '',
            "CTA CODE": line.chart_code or '',
            "CTA NAME": line.chart_name or '',
            "DEBITO": "%.2f" % line.debit or "%.2f" % 0.00,
            "CREDITO": "%.2f" % line.credit or "%.2f" % 0.00,
            "MONEDA": line.currency or '',
            "FECHA EMISION": line.invoice_date.strftime('%d/%m/%Y') or '',
            "FECHA VENC": line.date_due.strftime('%d/%m/%Y') if line.date_due else '',
        })
        
        return data
    
    def action_generate_xls(self):
        data = self.get_xls_data(self.child_ids)
        report_xls = ExcelReport(data, self)
        self.write({
            'xls_filename': f"LIBRO DIARIO - {self.month}/{self.year}.xlsx",
            'xls_binary': report_xls.get_content(),
        })
    
    def action_generate_ple(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_ple("0005010000")
        report_file = PlameReport(data)
        self.write({
            'ple_filename': f"{filename}.txt",
            'ple_binary': report_file.get_data_ple51(),
        })
    

class DataPle51Line(models.Model):
    _name = "data.ple51.line"
    _inherit = ["account.purchases.line"]
    _description = "Data for Libro Diario"
    _order = 'entry asc'
    
    parent_id = fields.Many2one("data.ple51", "Registro Libro Diario", ondelete='cascade', store=True, readonly=True)
    
    date = fields.Date("Fecha Contable", readonly=True)
    ref = fields.Char("Glosa", readonly=True)
    code_book = fields.Char("Codigo Libro", readonly=True)
    sequence_book = fields.Char("Secuencia Libro", readonly=True)
    num_book = fields.Char("Numero Libro", readonly=True)
    chart_code = fields.Char("Codigo Cuenta", readonly=True)
    chart_name = fields.Char("Nombre Cuenta", readonly=True)
    debit = fields.Float("Debe", digits=(20,2), readonly=True)
    credit = fields.Float("Haber", digits=(20,2), readonly=True)
    currency = fields.Char("Moneda", readonly=True)
    