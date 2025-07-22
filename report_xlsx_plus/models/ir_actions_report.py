# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError
from io import BytesIO
import base64


class ReportAction(models.Model):
    _inherit = "ir.actions.report"
    
    report_type = fields.Selection(selection_add=[("xlsx", "Excel")], ondelete={"xlsx": "set default"})
    file_data = fields.Binary('File Data', readonly=True)
    
    @api.model
    def render_xlsx(self, docids, data=None):
        report_sudo = self._get_report_from_name(self.report_name)
        report_model = self.env[f"report.{report_sudo.report_name}"]
        
        wb = report_model.create_workbook(docids, data)
        fp = BytesIO()
        wb.save(fp)
        fp.seek(0)
        
        return base64.b64encode(fp.read())
    
    @api.model
    def get_filename(self):
        return f"{self.print_report_name if self.print_report_name else self.report_name}", '.xlsx'
    
    def _get_report_from_name(self, report_name):
        report = self.search([('report_name', '=', report_name)], limit=1)
        if not report:
            raise UserError('Reporte con nombre "%s" no encontrado.' % report_name)
        return report
    
    def report_action(self, docids, data=None, config=True):
        report = self._get_report_from_name(self.report_name)
        
        if report.report_type == 'xlsx':
            self.file_data = self.render_xlsx(docids, data)
            xlsx_name, xlsx_extension = self.get_filename()
            
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s/%s/file_data/%s?download=true' % (self._name, self.id, xlsx_name + xlsx_extension),
                'target': 'self',
            }
        
        return super(ReportAction, self).report_action(docids, data, config)