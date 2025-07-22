# -*- coding: utf-8 -*-
from odoo import models, api
from .sire_report_txt import SireReport


class DataPurchase(models.Model):
    _name = "data.purchase"
    _inherit = ["data.purchase", "account.purchases"]
    _description = "Data Purchase"
    _res_model = "account.sire.purchase"
    
    def prepare_xls_data(self, line, count=None):
        data = super(DataPurchase, self).prepare_xls_data(line, count=count)
        
        data.update({
            "COMPANY RUC": self.company_id.vat or '',
            "OTROS CARGOS": "%.2f" % line.others or "%.2f" % 0.00,
            "VALIDA SIRE": dict(line._fields['sire_check'].selection).get(line.sire_check),
        })
        
        return data
    
    def validate_sire_domain(self, line):
        domain = super(DataPurchase, self).validate_sire_domain(line)
        
        base_dg = line.base_imp if line.type_purchase_ple == 'AG-VG' else 0.0
        igv_dg = line.igv if line.type_purchase_ple == 'AG-VG' else 0.0
        base_dgng = line.base_imp if line.type_purchase_ple == 'AG-VGNG' else 0.0
        igv_dgng = line.igv if line.type_purchase_ple == 'AG-VGNG' else 0.0
        base_dng = line.base_imp if line.type_purchase_ple == 'AG-NO' else 0.0
        igv_dng = line.igv if line.type_purchase_ple == 'AG-NO' else 0.0
        otros = line.others or 0.0
        
        l_base_dg = self.get_list_nums(base_dg)
        l_igv_dg = self.get_list_nums(igv_dg)
        l_base_dgng = self.get_list_nums(base_dgng)
        l_igv_dgng = self.get_list_nums(igv_dgng)
        l_base_dng = self.get_list_nums(base_dng)
        l_igv_dng = self.get_list_nums(igv_dng)
        l_otros = self.get_list_nums(otros)
        
        domain.extend([
            ('base_dg','in',l_base_dg),
            ('igv_dg','in',l_igv_dg),
            ('base_dgng','in',l_base_dgng),
            ('igv_dgng','in',l_igv_dgng),
            ('base_dng','in',l_base_dng),
            ('igv_dng','in',l_igv_dng),
            ('otros','in',l_otros),
        ])
        
        return domain
    
    def action_sire_replace(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_sire("0008040002")
        report_file = SireReport(data)
        self.write({
            'sire_replace_filename': f"{filename}.txt",
            'sire_replace_binary': report_file.get_replace_data(),
        })
    
    def compute_sheet(self):
        """Inherited for SIRE context"""
        self = self.with_context(sire_context=True)
        return super(DataPurchase, self).compute_sheet()
    

class DataPurchaseLine(models.Model):
    _name = "data.purchase.line"
    _inherit = ["data.purchase.line", "account.purchases.line"]
    _description = "Data Purchase Line"
    
    @api.depends('num_doc', 'type_cpe', 'serie_cpe', 'num_cpe')
    def _compute_car_odoo(self):
        for rec in self:
            rec.car_odoo = rec.num_doc + rec.type_cpe + rec.serie_cpe + rec.num_cpe.zfill(10)
    