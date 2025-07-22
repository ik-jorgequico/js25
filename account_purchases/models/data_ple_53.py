# -*- coding: utf-8 -*-
from odoo import fields, models
from .plame_report_txt import PlameReport


class DataPle53(models.Model):
    _name = "data.ple53"
    _inherit = ["account.purchases"]
    _description = "Data for Plan Contable - Libro Diario 5.3"
    _line_model = "data.ple53.line"
    _prefix_name = "Plan contable"
    _main_model = "account.account"
    
    child_ids = fields.One2many(_line_model, "parent_id", "Registros")
    
    def prepare_line_data(self, line):
        records = super(DataPle53, self).prepare_line_data(line)
        
        records.update({
            "name": f"{self._prefix_name}/Línea",
            "chart_code": line.code,
            "chart_name": line.name[:100] if len(line.name)>100 else line.name,
            "chart_type": '01',
            "state_ple": '1',
        })
        
        return records
    
    def prepare_xls_data(self, line, count=None) -> dict:
        data = super(DataPle53, self).prepare_xls_data(line, count=count)
        
        data.update({
            "CTA CODE": line.chart_code or '',
            "CTA NAME": line.chart_name or '',
            "CTA TIPO": line.chart_type or '',
        })
        
        return data
    
    def main_domain(self):
        return [('company_id.id','=',self.company_id.id)]
    
    def action_generate_ple(self):
        data = self.get_xls_data(self.child_ids)
        filename = self.get_filename_ple("0005030000")
        report_file = PlameReport(data)
        self.write({
            'ple_filename': f"{filename}.txt",
            'ple_binary': report_file.get_data_ple53(),
        })
    

class DataPle53Line(models.Model):
    _name = "data.ple53.line"
    _inherit = ["account.purchases.line"]
    _description = "Lines for Plan Contable - Libro Diario 5.3"
    
    parent_id = fields.Many2one("data.ple53", "Registro Plan Contable", ondelete='cascade', store=True, readonly=True)
    
    chart_code = fields.Char("Codigo Cuenta", readonly=True)
    chart_name = fields.Char("Nombre Cuenta", readonly=True)
    chart_type = fields.Char("Tipo Cuenta", readonly=True)