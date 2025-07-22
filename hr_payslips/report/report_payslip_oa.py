from odoo import api, models

class PaySlipOAReport(models.AbstractModel):
    _name = 'report.hr_payslip.report_payslip_oa'

    @api.model
    def _get_report_values(self, docids, data=None):
        # get the report action back as we will need its data
        report = self.env['ir.actions.report']._get_report_from_name('hr_payslip.report_payslip_oa')
        # get the records selected for this rendering of the report
        obj = self.env[report.model].browse(docids)
        # return a custom rendering context
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': obj,
            'data': data,

        } 