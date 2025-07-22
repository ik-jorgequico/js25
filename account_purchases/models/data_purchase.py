# -*- coding: utf-8 -*-
from odoo import fields, models
from .purchase_report_xls import ExcelReport
from .plame_report_txt import PlameReport


class DataPurchase(models.Model):
    _name = "data.purchase"
    _inherit = ["account.purchases"]
    _description = "Data for Registro de Compras"
    _line_model = "data.purchase.line"
    _prefix_name = "Registro de compras"
    _main_model = "account.move"
    
    sunat_validate_filename = fields.Char('Nombre archivo Validar')
    sunat_validate_binary = fields.Binary('Validar Sunat')
    
    child_ids = fields.One2many(_line_model, "parent_id", _prefix_name)
    
    # - PRIVATE METHODS
    def _get_amounts(self, line):
        tc_sunat = 1.000	
        new_base = 0.00
        new_inafecto = 0.00
        new_igv = 0.00
        new_total = 0.00
        new_others = 0.00
        
        base = line.l10n_pe_edi_amount_base
        inafecto = line.l10n_pe_edi_amount_unaffected
        igv = line.l10n_pe_edi_amount_igv
        total = line.amount_total
        date = line.invoice_date
        reverse_date = line.reversed_entry_id.invoice_date
        currency = line.company_id.currency_id
        company = line.company_id
        currency_line = line.currency_id
        others = line.amount_others_purchase
        
        # check if currency in account.move is same that company currency (PEN)
        if line.company_id.currency_id != line.currency_id:
            if line.l10n_latam_document_type_id.code in ['07']:
                rcr = self.env["res.currency.rate"].search([
                    ("name","=",reverse_date),
                    ("currency_id","=",currency_line.id),
                    ("company_id","=",company.id),
                ])
                tc_sunat = rcr.inverse_company_rate if rcr else 0.000
                new_base = line.currency_id._convert(base,currency,company,reverse_date) * -1
                new_inafecto = line.currency_id._convert(inafecto,currency,company,reverse_date) * -1
                new_igv = line.currency_id._convert(igv,currency,company,reverse_date) * -1
                new_total = line.currency_id._convert(total,currency,company,reverse_date) * -1
                new_others = line.currency_id._convert(others,currency,company,reverse_date) * -1
            else:
                rcr = self.env["res.currency.rate"].search([
                    ("name","=",date),
                    ("currency_id","=",currency_line.id),
                    ("company_id","=",company.id),
                ])
                tc_sunat = rcr.inverse_company_rate if rcr else 0.000	
                new_base = line.currency_id._convert(base,currency,company,date)
                new_inafecto = line.currency_id._convert(inafecto,currency,company,date)
                new_igv = line.currency_id._convert(igv,currency,company,date)
                new_total = line.currency_id._convert(total,currency,company,date)
                new_others = line.currency_id._convert(others,currency,company,date)
        else:
            if line.l10n_latam_document_type_id.code in ['07']:
                tc_sunat = 1.000
                new_base = base *-1
                new_inafecto = inafecto*-1
                new_igv = igv*-1
                new_total = total*-1
                new_others = others*-1
            else:
                tc_sunat = 1.000
                new_base = base
                new_inafecto = inafecto
                new_igv = igv
                new_total = total
                new_others = others

        return new_base, new_inafecto, new_igv, new_total, tc_sunat, new_others
    
    def _get_type_purchase_ple(self, line):
        type_ple = ''
        amount_ple = 0.00
        
        for li in line.invoice_line_ids:
            if li.tax_ids.type_purchase_ple in ['AG-VG','AG-VGNG','AG-NO']:
                type_ple = li.tax_ids.type_purchase_ple
                amount_ple = li.tax_ids.amount
        
        return type_ple, amount_ple
    
    def _get_cpe_rev(self, line):
        serie_cpe_rev = ''
        num_cpe_rev = ''
        type_cpe_rev = ''
        date_rev = None
        
        if line.reversed_entry_id:
            type_cpe_rev = line.reversed_entry_id.l10n_latam_document_type_id.code
            serie_cpe_rev = line.reversed_entry_id.seriecomp_sunat
            num_cpe_rev = line.reversed_entry_id.numcomp_sunat
            date_rev = line.reversed_entry_id.invoice_date
        elif line.debit_origin_id:
            type_cpe_rev = line.debit_origin_id.l10n_latam_document_type_id.code
            serie_cpe_rev = line.debit_origin_id.seriecomp_sunat
            num_cpe_rev = line.debit_origin_id.numcomp_sunat
            date_rev = line.debit_origin_id.invoice_date
        else:
            type_cpe_rev = line.reversal_type
            serie_cpe_rev = line.l10n_pe_edi_reversal_serie
            num_cpe_rev = line.l10n_pe_edi_reversal_number
            date_rev = line.l10n_pe_edi_reversal_date
        
        return serie_cpe_rev, num_cpe_rev, type_cpe_rev, date_rev
    
    # - INHERIT METHODS
    def main_domain(self):
        """Inherited to extend the domain of movement for purchases."""
        rec = super(DataPurchase, self).main_domain()
        rec.extend([
            ('journal_id.have_purchase','=',True),
            ('l10n_latam_document_type_id.code','not in',['09','20','31','33','40','41','91','97','98'])
        ])
        return rec
    
    def prepare_line_data(self, line):
        records = super(DataPurchase, self).prepare_line_data(line)
        new_base, new_inafecto, new_igv, new_total, tc_sunat, new_others = self._get_amounts(line)
        type_tax, amount_tax = self._get_type_purchase_ple(line)
        serie_cpe_rev, num_cpe_rev, type_cpe_rev, date_rev = self._get_cpe_rev(line)
        
        records.update({
            "name": f"{self._prefix_name}/{line.name}",
            "account_date": line.date,
            "entry": line.name,
            "invoice_date": line.invoice_date,
            "date_due": line.invoice_date_due,
            "type_cpe": line.l10n_latam_document_type_id.code,
            "serie_cpe": line.ref.split('-')[0],
            "num_cpe": line.ref.split('-')[1],
            "type_doc": line.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            "num_doc": line.partner_id.vat,
            "company_name": line.partner_id.name,
            "currency_line": line.currency_id.name,
            "total_real": line.amount_total,
            "base_imp": new_base,
            "igv": new_igv,
            "inafecto": new_inafecto,
            "total_amount": new_total,
            "num_det": line.num_det,
            "date_det": line.date_det,
            "tc_sunat": tc_sunat,
            "date_reversed": date_rev,
            "tipcomp_reversed": type_cpe_rev,
            "serie_reversed": serie_cpe_rev,
            "num_reversed": num_cpe_rev,
            "dua_year": line.invoice_date.strftime("%Y") if line.l10n_latam_document_type_id.code in ['50','53'] else '',
            "correlativo_ple": "M00002",
            "type_purchase_ple": type_tax,
            "percent_igv": amount_tax,
            "state_ple": line.state_ple,
            'op_nodom': line.op_nodom,
            'others': new_others,
        })
        
        return records
    
    def prepare_xls_data(self, line, count=None) -> dict:
        data = super(DataPurchase, self).prepare_xls_data(line, count=count)
        
        data.update({
            "BASE AG-VG": "%.2f" % line.base_imp if line.type_purchase_ple == 'AG-VG' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "IGV AG-VG": "%.2f" % line.igv if line.type_purchase_ple == 'AG-VG' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "BASE AG-VGNG": "%.2f" % line.base_imp if line.type_purchase_ple == 'AG-VGNG' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "IGV AG-VGNG": "%.2f" % line.igv if line.type_purchase_ple == 'AG-VGNG' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "BASE AG-NO": "%.2f" % line.base_imp if line.type_purchase_ple == 'AG-NO' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "IGV AG-NO": "%.2f" % line.igv if line.type_purchase_ple == 'AG-NO' else "%.2f" % 0.00 or "%.2f" % 0.00,
            "INAFECTO": "%.2f" % line.inafecto or "%.2f" % 0.00,
            "CONSTANCIA": line.num_det or '',
            "FECHA CONSTANCIA":line.date_det.strftime('%d/%m/%Y') if line.date_det else '',
            "OPERACION": line.op_nodom,
        })
        
        return data
    
    def compute_sheet(self):
        """Inherited to check lines."""
        self = self.with_context(check_lines=True)
        return super(DataPurchase, self).compute_sheet()
    
    # - BUTTONS
    def action_generate_xls(self):
        data = self.get_xls_data(self.child_ids)
        report_xls = ExcelReport(data, self)
        self.write({
            'xls_filename': f"REGISTRO DE COMPRAS - {self.month}/{self.year}.xlsx",
            'xls_binary': report_xls.get_content(),
        })
    
    def action_generate_ple(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_ple("0008010000")
        report_file = PlameReport(data)
        self.write({
            'ple_filename': f"{filename}.txt",
            'ple_binary': report_file.get_content_data(),
        })
    
    def action_generate_sunat_validate(self):
        data = self.get_xls_data(self.child_ids)
        filename = f"Validación Sunat - {self.month}-{self.year}"
        report_file = PlameReport(data)
        self.write({
            'sunat_validate_filename': f"{filename}.txt",
            'sunat_validate_binary': report_file.get_data_sunat_validate(),
        })
    

class DataPurchaseLine(models.Model):
    _name = "data.purchase.line"
    _inherit = ["account.purchases.line"]
    _description = "Data for Registro de Compras"
    _order = 'entry asc'
    
    parent_id = fields.Many2one("data.purchase", "Registro de Compras", ondelete='cascade', store=True, readonly=True)
    
    type_purchase_ple = fields.Char('Tipo Compra PLE', readonly=True)
    others = fields.Float("Otros Cargos", digits=(20,2), readonly=True)
