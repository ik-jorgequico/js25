# -*- coding: utf-8 -*-
from odoo import fields, models
from .sale_report_xls import SaleExcelReport
from .plame_report_txt import PlameReport


class DataSales(models.Model):
    _name = "data.sales"
    _inherit = ["account.purchases"]
    _description = "Data for Registro de ventas"
    _main_model = "account.move"
    _line_model = "data.sales.line"
    _prefix_name = "Registro de ventas"
    
    child_ids = fields.One2many(_line_model, "parent_id", _prefix_name)
    
    # - PRIVATE METHODS
    def _get_amounts(self, line):
        tc_sunat = 1.000	
        new_base = 0.00
        new_inafecto = 0.00
        new_igv = 0.00
        new_total = 0.00
        new_exonerado = 0.00
        base_desc = 0.00
        igv_desc = 0.00
        new_expo = 0.00
        
        base = line.l10n_pe_edi_amount_base
        inafecto = line.l10n_pe_edi_amount_unaffected
        exonerado = line.l10n_pe_edi_amount_exonerated
        igv = line.l10n_pe_edi_amount_igv
        total = line.amount_total
        date = line.invoice_date
        reverse_date = line.reversed_entry_id.invoice_date
        currency = line.company_id.currency_id
        company = line.company_id
        currency_line = line.currency_id
        expo = line.amount_expo
        
        # COMPARAMOS LAS MONEDAS DE LA COMPAÑIA Y DEL LINE
        if line.company_id.currency_id != line.currency_id :
            # SI SON DIFERENTES SE HACE LA CONVERSION
            if line.l10n_latam_document_type_id.code in ['07']:
                # SI ES NOTA DE CREDITO LA FECHA DE CONVERSION DEBE SER LA DE LA FACTURA Y SERA NEGATIVO EL MONTO
                rcr = self.env["res.currency.rate"].search([
                    ("name","=",reverse_date),
                    ("currency_id","=",currency_line.id),
                    ("company_id","=",company.id),
                ])
                rcr = self.env["res.currency.rate"].search([
                    ("name","=",reverse_date),
                    ("currency_id","=",currency_line.id),
                    ("company_id","=",company.id),
                ])
                tc_sunat = rcr.inverse_company_rate if rcr else 0.000			
                if line.reversed_entry_id.invoice_date.strftime("%m%Y") != line.date.strftime("%m%Y"):
                    # SI LA FECHA DE REV ES DIFERENTE A LA FECHA ACTUAL ES UN DESCUENTO
                    base_desc = line.currency_id._convert(base,currency,company,reverse_date) * -1
                    igv_desc = line.currency_id._convert(igv,currency,company,reverse_date) * -1
                    new_inafecto = line.currency_id._convert(inafecto,currency,company,reverse_date) * -1
                    new_total = line.currency_id._convert(total,currency,company,reverse_date) * -1
                    new_exonerado = line.currency_id._convert(exonerado,currency,company,reverse_date) * -1
                    new_expo = line.currency_id._convert(expo,currency,company,reverse_date) * -1
                else:
                    new_base = line.currency_id._convert(base,currency,company,reverse_date) * -1
                    new_inafecto = line.currency_id._convert(inafecto,currency,company,reverse_date) * -1
                    new_igv = line.currency_id._convert(igv,currency,company,reverse_date) * -1
                    new_total = line.currency_id._convert(total,currency,company,reverse_date) * -1
                    new_exonerado = line.currency_id._convert(exonerado,currency,company,reverse_date) * -1
                    new_expo = line.currency_id._convert(expo,currency,company,reverse_date) * -1
            else:
                # SI NO SE CONVIERTE CON LA FECHA DE LA FACTURA
                rcr = self.env["res.currency.rate"].search([
                    ("name", "=", date),
                    ("currency_id", "=", currency_line.id),
                    ("company_id", "=", company.id),
                ])
                tc_sunat = rcr.inverse_company_rate if rcr else 0.000	
                new_base = line.currency_id._convert(base,currency,company,date)
                new_inafecto = line.currency_id._convert(inafecto,currency,company,date)
                new_igv = line.currency_id._convert(igv,currency,company,date)
                new_total = line.currency_id._convert(total,currency,company,date)
                new_exonerado = line.currency_id._convert(exonerado,currency,company,date)
                new_expo = line.currency_id._convert(expo,currency,company,date)
        else:
            # SI ES LA MISMA MONEDA Y ES NC SE CONVIERTEN EN NEGATIVO
            if line.l10n_latam_document_type_id.code in ['07']:
                tc_sunat = 1.000
                if line.reversed_entry_id.invoice_date.strftime("%m%Y") != line.date.strftime("%m%Y"):
                    base_desc = base *-1
                    igv_desc = igv*-1
                    new_inafecto = inafecto*-1
                    new_total = total*-1
                    new_exonerado = exonerado*-1
                    new_expo = expo*-1
                else:
                    new_base = base *-1
                    new_inafecto = inafecto*-1
                    new_igv = igv*-1
                    new_total = total*-1
                    new_exonerado = exonerado*-1
                    new_expo = expo*-1
            else:
                # SI ES LA MISMA MONEDA Y NO ES NC, DA LO MISMO
                tc_sunat = 1.000
                new_base = base
                new_inafecto = inafecto
                new_igv = igv
                new_total = total
                new_exonerado = exonerado
                new_expo = expo

        return new_base, new_inafecto, new_igv, new_total, tc_sunat, new_exonerado, base_desc, igv_desc, new_expo
    
    def _get_cpe_rev(self, line):
        serie_cpe_rev = ''
        num_cpe_rev = ''
        type_cpe_rev = ''
        date_rev = None
        
        if line.reversed_entry_id:
            serie_cpe_rev = line.reversed_entry_id.name.split('-')[0]
            num_cpe_rev = line.reversed_entry_id.name.split('-')[1]
            type_cpe_rev = line.reversed_entry_id.l10n_latam_document_type_id.code
            date_rev = line.reversed_entry_id.invoice_date
        elif line.debit_origin_id:
            serie_cpe_rev = line.debit_origin_id.name.split('-')[0]
            num_cpe_rev = line.debit_origin_id.name.split('-')[1]
            type_cpe_rev = line.debit_origin_id.l10n_latam_document_type_id.code
            date_rev = line.debit_origin_id.invoice_date
        
        return serie_cpe_rev, num_cpe_rev, type_cpe_rev, date_rev
    
    def _get_type_sale_ple(self, line):
        type_ple = ''
        
        for li in line.invoice_line_ids:
            if li.tax_ids.type_sale_ple in ['VG']:
                type_ple = li.tax_ids.type_sale_ple
        
        return type_ple
    
    # - INHERIT METHODS
    def prepare_line_data(self, line):
        records = super(DataSales, self).prepare_line_data(line)
        
        new_base, new_inafecto, new_igv, new_total, tc_sunat, new_exonerado, base_desc, igv_desc, new_expo = self._get_amounts(line)
        serie_cpe_rev, num_cpe_rev, type_cpe_rev, date_rev = self._get_cpe_rev(line)
        type_tax = self._get_type_sale_ple(line)
        
        records.update({
            "name": f"{self._prefix_name}/{line.name}",
            "account_date": line.date,
            "entry": line.name,
            "invoice_date": line.invoice_date,
            "date_due": line.invoice_date_due,
            "type_cpe": line.l10n_latam_document_type_id.code,
            "serie_cpe": line.payment_reference.split('-')[0],
            "num_cpe": line.payment_reference.split('-')[1],
            "type_doc": line.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
            "num_doc": line.partner_id.vat,
            "company_name": line.partner_id.name,
            "currency_line": line.currency_id.name,
            "total_real": line.amount_total,
            "base_imp": new_base,
            "base_desc": base_desc,
            "igv_desc": igv_desc,
            "igv": new_igv,
            "inafecto": new_inafecto,
            "total_amount": new_total,
            "tc_sunat": tc_sunat,
            "date_reversed": date_rev or False,
            "tipcomp_reversed": type_cpe_rev,
            "serie_reversed": serie_cpe_rev,
            "num_reversed": num_cpe_rev,
            "correlativo_ple": "M00003",
            "type_sale_ple": type_tax,
            "state_ple": line.state_ple_sale,
            "exonerado": new_exonerado,
            'exportacion': new_expo,
        })
        
        return records
    
    def prepare_xls_data(self, line, count=None) -> dict:
        data = super(DataSales, self).prepare_xls_data(line, count=count)
        
        data.update({
            "BASE AG-VG": "%.2f" % line.base_imp or "%.2f" % 0.00,
            "IGV AG-VG": "%.2f" % line.igv or "%.2f" % 0.00,
            "BASE DESC": "%.2f" % line.base_desc or "%.2f" % 0.00,
            "IGV DESC": "%.2f" % line.igv_desc or "%.2f" % 0.00,
            "BASE EXP": "%.2f" % line.exportacion if not line.inafecto else "%.2f" % 0.00 or "%.2f" % 0.00,
            "EXONERADO": "%.2f" % line.exonerado  or "%.2f" % 0.00,
            "INAFECTO": "%.2f" % line.inafecto if not line.exportacion else "%.2f" % 0.00 or "%.2f" % 0.00,
        })
        
        return data
    
    def main_domain(self):
        """Inherited to extend the domain of movement for sales."""
        rec = super(DataSales, self).main_domain()
        rec.extend([
            ('journal_id.have_sale','=',True),
            ('l10n_latam_document_type_id.code','not in',['09','20','31','33','40','41','91','97','98'])
        ])
        return rec
    
    # - MAIN METHODS
    def action_generate_xls(self):
        data = self.get_xls_data(self.child_ids)
        report_xls = SaleExcelReport(data, self)
        self.write({
            'xls_filename': f"REGISTRO DE VENTAS - {self.month}/{self.year}.xlsx",
            'xls_binary': report_xls.get_content(),
        })
    
    def action_generate_ple(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_ple("0014010000")
        report_file = PlameReport(data)
        self.write({
            'ple_filename': f"{filename}.txt",
            'ple_binary': report_file.get_data_141(),
        })
    

class DataSalesLine(models.Model):
    _name = "data.sales.line"
    _inherit = "account.purchases.line"
    _inherit = "account.purchases.line"
    _description = "Data for Registro de Ventas"
    _order = 'entry asc'
    
    parent_id = fields.Many2one("data.sales", "Registro de Ventas", ondelete='cascade', store=True, readonly=True)
    
    type_sale_ple = fields.Char('Tipo Venta PLE', readonly=True)
    exonerado = fields.Float("Exonerado", digits=[20,2], readonly=True)
    base_desc = fields.Float("Base descuento", digits=[20,2], readonly=True)
    igv_desc = fields.Float("Igv descuento", digits=[20,2], readonly=True)
    exportacion = fields.Float("Exportación", digits=[20,2], readonly=True)
    