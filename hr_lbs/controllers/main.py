# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

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



class HrLbs(Controller):

    @route(["/print/lbs"], type='http', auth='user')
    def get_lbs_report_print(self, list_ids='', **post):

        ids = [int(s) for s in list_ids.split(',')]
        lbs_lines = request.env['hr.lbs.line'].browse(ids)
        if lbs_lines:
            zip_filename = datetime.now()
            zip_filename = "%s.zip" % zip_filename

            bitIO = io.BytesIO()
            zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)

            for lbs_line in lbs_lines:
                pdf_writer = PdfFileWriter()

                if not lbs_line.parent_id or not lbs_line.parent_id.report_id:
                    report = request.env.ref('hr_lbs.action_report_lbs', False)
                else:
                    report = lbs_line.parent_id.report_id

                report = report.with_context(lang=lbs_line.employee_id.sudo().address_home_id.lang)
                pdf_content, _ = report.sudo()._render_qweb_pdf(lbs_line.id, data={'company_id': lbs_line.employee_id.company_id})
                reader = PdfFileReader(io.BytesIO(pdf_content), 
                                    strict=False, 
                                    overwriteWarnings=False)

                for page in range(reader.getNumPages()):
                    pdf_writer.addPage(reader.getPage(page))

                report_name =  "LBS " + lbs_line.employee_id.name
                if lbs_line.parent_id.report_id.print_report_name:
                    report_name = safe_eval(lbs_line.parent_id.report_id.print_report_name, 
                                            {'object': lbs_line})
                    
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

            if len(lbs_lines) == 1:
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
