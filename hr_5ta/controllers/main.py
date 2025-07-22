# -*- coding: utf-8 -*-
import io
import re
from datetime import datetime

from PyPDF2 import PdfFileReader, PdfFileWriter

from odoo import models
from odoo.http import request, route, Controller, content_disposition
from odoo.tools.safe_eval import safe_eval
import zipfile
from os.path import basename
import os

class HrCts(Controller):

    @route(["/print/5ta"], type='http', auth='user')
    def get_payroll_report_print(self, list_ids='', **post):
        

        ids = [int(s) for s in list_ids.split(',')]
        lines_5ta = request.env['hr.5ta.line'].browse(ids)
        if lines_5ta:
            zip_filename = datetime.now()
            zip_filename = "%s.zip" % zip_filename

            bitIO = io.BytesIO()
            zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)

            for line_5ta in lines_5ta:
                pdf_writer = PdfFileWriter()

                if not line_5ta.parent_id or not line_5ta.parent_id.report_id:
                    report = request.env.ref('hr_5ta.action_report_5ta', False)
                else:
                    report = line_5ta.parent_id.report_id

                report = report.with_context(lang=line_5ta.employee_id.sudo().address_home_id.lang)
                pdf_content, _ = report.sudo()._render_qweb_pdf(line_5ta.id, data={'company_id': line_5ta.employee_id.company_id})
                reader = PdfFileReader(io.BytesIO(pdf_content), 
                                    strict=False, 
                                    overwriteWarnings=False)

                for page in range(reader.getNumPages()):
                    pdf_writer.addPage(reader.getPage(page))

                report_name =  "5TA " + line_5ta.employee_id.name
                if line_5ta.parent_id.report_id.print_report_name:
                    report_name = safe_eval(line_5ta.parent_id.report_id.print_report_name, 
                                            {'object': line_5ta})

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

            if len(lines_5ta) == 1:
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
