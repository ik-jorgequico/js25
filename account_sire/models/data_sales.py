# -*- coding: utf-8 -*-
from odoo import models, api
from .sire_report_txt import SireReport


class DataSales(models.Model):
    _name = "data.sales"
    _inherit = ["data.sales", "account.purchases"]
    _description = "Data Sales"
    _res_model = "account.sire.sales"
    
    def prepare_xls_data(self, line, count=None):
        data = super(DataSales, self).prepare_xls_data(line, count=count)
        
        data.update({
            "COMPANY RUC": self.company_id.vat or '',
            "VALIDA SIRE": dict(line._fields['sire_check'].selection).get(line.sire_check),
        })
        
        return data
    
    def validate_sire_domain(self, line):
        domain = super(DataSales, self).validate_sire_domain(line)
        
        l_expo = self.get_list_nums(line.exportacion)
        l_base_dg = self.get_list_nums(line.base_imp)
        l_desc_base_dg = self.get_list_nums(line.base_desc)
        l_igv_dg = self.get_list_nums(line.igv)
        l_desc_igv_dg = self.get_list_nums(line.igv_desc)
        l_exonerado = self.get_list_nums(line.exonerado)
        
        domain.extend([
            ('expo','in',l_expo),
            ('base_dg','in',l_base_dg),
            ('desc_base_dg','in',l_desc_base_dg),
            ('igv_dg','in',l_igv_dg),
            ('desc_igv_dg','in',l_desc_igv_dg),
            ('exonerado','in',l_exonerado),
        ]) 
        
        if line.type_cpe.zfill(2) != '03' and line.tipcomp_reversed.zfill(2) != '03':
            domain.extend([('vendor_doc','=',line.num_doc)])
        
        return domain
    
    def action_sire_replace(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_sire("0014040002")
        report_file = SireReport(data)
        self.write({
            'sire_replace_filename': f"{filename}.txt",
            'sire_replace_binary': report_file.get_replace_rvie(),
        })
    
    def compute_sheet(self):
        """Inherited for SIRE context"""
        self = self.with_context(sire_context=True)
        return super(DataSales, self).compute_sheet()
    

class DataSalesLine(models.Model):
    _name = "data.sales.line"
    _inherit = ["data.sales.line", "account.purchases.line"]
    _description = "Data Sales Line"
    
    @api.depends('company_id', 'type_cpe', 'serie_cpe', 'num_cpe')
    def _compute_car_odoo(self):
        for rec in self:
            if rec.company_id.vat and rec.type_cpe and rec.serie_cpe and rec.num_cpe:
                rec.car_odoo = rec.company_id.vat + rec.type_cpe + rec.serie_cpe + rec.num_cpe.zfill(10)
            else:
                rec.car_odoo = False
    
