# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import re
from datetime import datetime

from PyPDF2 import PdfFileReader, PdfFileWriter

from odoo import models
from odoo.http import request, route, Controller, content_disposition
from odoo.tools.safe_eval import safe_eval
from odoo.addons.hr_payroll.controllers.main import HrPayroll
import zipfile
from os.path import basename
import os


class HrPayrollOA(HrPayroll):

    @route(["/print/payslips"], type='http', auth='user')
    def get_payroll_report_print(self, list_ids='', **post):
        if not request.env.user.has_group('hr_payroll.group_hr_payroll_user') or not list_ids or re.search("[^0-9|,]", list_ids):
            return request.not_found()

        ids = [int(s) for s in list_ids.split(',')]
        payslips = request.env['hr.payslip'].browse(ids)

        zip_filename = datetime.now()
        zip_filename = "%s.zip" % zip_filename

        bitIO = io.BytesIO()
        zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)

        for payslip in payslips:
            pdf_writer = PdfFileWriter()

            if not payslip.struct_id or not payslip.struct_id.report_id:
                report = request.env.ref('hr_payroll.action_report_payslip', False)
            else:
                report = payslip.struct_id.report_id

            report = report.with_context(lang=payslip.employee_id.sudo().address_home_id.lang)
            pdf_content, _ = report.sudo()._render_qweb_pdf(payslip.id, data={'company_id': payslip.company_id})
            reader = PdfFileReader(io.BytesIO(pdf_content), strict=False, overwriteWarnings=False)

            for page in range(reader.getNumPages()):
                pdf_writer.addPage(reader.getPage(page))
            
            report_name = "Payslips"
            if payslip.struct_id.report_id.print_report_name:
                report_name = safe_eval(payslip.struct_id.report_id.print_report_name, 
                                        {'object': payslip})

            filename = report_name + ".pdf"
            _buffer = io.BytesIO()
            pdf_writer.write(_buffer)
            merged_pdf = _buffer.getvalue()
            _buffer.close()

            with open(filename, 'wb') as f: 
                f.write(merged_pdf)

            zip_file.write(filename , basename(filename))            
            os.remove(filename)

        zip_file.close()

        if len(payslips) == 1:
            pdfhttpheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(merged_pdf)),
                ('Content-Disposition', content_disposition(filename))
            ]

            return request.make_response(merged_pdf, headers=pdfhttpheaders)

        pdfhttpheaders = [
            ('Content-Type', 'application/x-zip-compressed'),
            ('Content-Disposition', content_disposition(zip_filename))
        ]   
        return request.make_response(bitIO.getvalue(), headers=pdfhttpheaders)
