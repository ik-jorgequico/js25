# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io
import re
from datetime import datetime

from PyPDF2 import PdfFileReader, PdfFileWriter

from odoo.http import request, route, Controller, content_disposition
from odoo.tools.safe_eval import safe_eval
import zipfile
from os.path import basename
import os
import xlsxwriter


class HrVacaReportExcel(Controller):

    @route(["/print/vaca-enjoyed"], type='http', auth='user')
    def get_excel_vaca_enjoyed(self, list_ids='', **post):
        ids = [int(s) for s in list_ids.split(',')]
        data = request.env['hr.vacation.acum.line'].browse(ids)
        