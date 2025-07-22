# -*- coding: utf-8 -*-

from io import BytesIO
import xlsxwriter
from odoo.addons.account_purchases.models.purchase_report_xls import ExcelReport

class ExcelReportV(ExcelReport):

	def __init__(self, data, obj):
		self.data = data
		self.obj = obj

	def get_content(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output,{'default_date_format': 'dd/mm/yyyy'})

		# -
	
		if not self.data[0]['OPERACION']:
			sheet = workbook.add_worksheet('Compras 8.1')
		else:
			sheet = workbook.add_worksheet('Compras 8.2')

		f1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True})
		f2 = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False})
		f2_date = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': 'dd/mm/yyyy'})
		f2_dec = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f3 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'top': True, 'right': True, 'left': True})
		f4 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'right': True, 'left': True})
		f5 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'bottom': True, 'right': True, 'left': True})
		f6 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False, 'num_format': '#,##0.000'})
		f7 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True, 'top': True, 'bottom': True, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f8 = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': '0%'})

		sheet.set_column('A:A', 17)
		sheet.set_column('B:B', 11)
		sheet.set_column('C:C', 11)
		sheet.set_column('D:D', 4)
		sheet.set_column('E:E', 4)
		sheet.set_column('F:F', 6)
		sheet.set_column('G:G', 9)
		sheet.set_column('H:H', 4.57)
		sheet.set_column('I:I', 10)
		sheet.set_column('J:J', 34)
		sheet.set_column('K:R', 11)
		sheet.set_column('S:S', 13)
		sheet.set_column('T:T', 13)
		sheet.set_column('U:U', 11)
		sheet.set_column('V:V', 5)
		sheet.set_column('W:W', 11)
		sheet.set_column('X:X', 4)
		sheet.set_column('Y:Y', 5)
		sheet.set_column('Z:Z', 9)
		sheet.set_column('AA:AA', 5)
		sheet.set_column('AB:AB', 11)

		for operation in self.data:
			if not operation['OPERACION']:
				sheet.write(0, 0, 'FORMATO 8.1: REGISTRO DE COMPRAS', f1)
			else:
				sheet.write(0, 0, 'FORMATO 8.2: REGISTRO DE COMPRAS - INFORMACION DE OPERACIONES CON SUJETOS NO DOMICILIADOS', f1)

		sheet.write(2, 0, 'PERIODO: ', f1)
		for mes in self.data:
			sheet.write(2, 7, mes['PERIODO'], f2)

		sheet.write(3, 0, 'RUC: ', f1)
		sheet.write(3, 7, self.obj.env.company.vat, f2)

		sheet.write(4, 0, 'APELLIDOS Y NOMBRES, DENOMINACION O RAZON SOCIAL: ', f1)
		sheet.write(4, 7, self.obj.env.company.name, f2)

		sheet.write(6, 0, 'NUMERO', f3)
		sheet.write(7, 0, 'CORRELATIVO', f4)
		sheet.write(8, 0, 'DEL REGISTRO O', f4)
		sheet.write(9, 0, 'CODIGO UNICO', f4)
		sheet.write(10, 0, 'DE LA OPERACION', f4)
		sheet.write(11, 0, '', f5)

		sheet.write(6, 1, 'FECHA DE', f3)
		sheet.write(7, 1, 'EMISION DEL', f4)
		sheet.write(8, 1, 'COMPROBANTE', f4)
		sheet.write(9, 1, 'DE PAGO', f4)
		sheet.write(10, 1, 'O DOCUMENTO', f4)
		sheet.write(11, 1, '', f5)

		sheet.write(6, 2, '', f3)
		sheet.write(7, 2, 'FECHA', f4)
		sheet.write(8, 2, 'DE', f4)
		sheet.write(9, 2, 'VCMTO', f4)
		sheet.write(10, 2, '', f4)
		sheet.write(11, 2, '', f5)

		sheet.merge_range('D7:G7', 'COMPROBANTE DE PAGO', f3)
		sheet.merge_range('D8:G8', 'O DOCUMENTO', f5)
		sheet.write(8, 3, '', f3)
		sheet.write(9, 3, 'TIPO', f4)
		sheet.write(10, 3, '', f4)
		sheet.write(11, 3, '', f5)

		sheet.write(8, 4, '', f3)
		sheet.write(9, 4, 'SERIE', f4)
		sheet.write(10, 4, '', f4)
		sheet.write(11, 4, '', f5)

		sheet.write(8, 5, '', f3)
		sheet.write(9, 5, 'AÑO', f4)
		sheet.write(10, 5, 'DUA', f4)
		sheet.write(11, 5, 'O DSI', f5)

		sheet.write(8, 6, '', f3)
		sheet.write(9, 6, 'NUMERO', f4)
		sheet.write(10, 6, '', f4)
		sheet.write(11, 6, '', f5)

		sheet.merge_range('H7:J7', 'INFORMACION DEL', f3)
		sheet.merge_range('H8:J8', 'PROVEEDOR', f5)
		sheet.merge_range('H9:I9', 'DOC. IDENTIDAD', f5)
		sheet.write(9, 7, '', f4)
		sheet.write(10, 7, 'TIPO', f4)
		sheet.write(11, 7, '', f5)

		sheet.write(9, 8, '', f4)
		sheet.write(10, 8, 'NUMERO', f4)
		sheet.write(11, 8, '', f5)

		sheet.write(8, 9, 'APELLIDOS Y NOMBRES,', f4)
		sheet.write(9, 9, 'DENOMINACION', f4)
		sheet.write(10, 9, 'O RAZON SOCIAL', f4)
		sheet.write(11, 9, '', f5)

		sheet.merge_range('K7:L7', 'ADQUISIONES GRAVADAS', f3)
		sheet.merge_range('K8:L8', 'DESTINADAS A OPERACIONES', f4)
		sheet.merge_range('K9:L9', 'GRAVADAS Y/O DE EXPORTACION', f4)
		sheet.merge_range('K10:L10', '', f5)
		sheet.write(10, 10, 'BASE', f4)
		sheet.write(11, 10, 'IMPONIBLE', f5)

		sheet.write(10, 11, '', f4)
		sheet.write(11, 11, 'IGV', f5)

		sheet.merge_range('M7:N7', 'ADQUISIONES GRAVADAS', f3)
		sheet.merge_range('M8:N8', 'DESTINADAS A OPERACIONES', f4)
		sheet.merge_range('M9:N9', 'GRAVADAS Y/O DE EXPORTACION', f4)
		sheet.merge_range('M10:N10', ' Y OPERACIONES NO GRAVADAS', f5)
		sheet.write(10, 12, 'BASE', f4)
		sheet.write(11, 12, 'IMPONIBLE', f5)

		sheet.write(10, 13, '', f4)
		sheet.write(11, 13, 'IGV', f5)

		sheet.merge_range('O7:P7', 'ADQUISIONES GRAVADAS', f3)
		sheet.merge_range('O8:P8', 'DESTINADAS A OPERACIONES', f4)
		sheet.merge_range('O9:P9', 'NO GRAVADAS', f4)
		sheet.merge_range('O10:P10', '', f5)
		sheet.write(10, 14, 'BASE', f4)
		sheet.write(11, 14, 'IMPONIBLE', f5)

		sheet.write(10, 15, '', f4)
		sheet.write(11, 15, 'IGV', f5)

		sheet.write(6, 16, '', f3)
		sheet.write(7, 16, 'VALOR', f4)
		sheet.write(8, 16, 'DE LAS', f4)
		sheet.write(9, 16, 'ADQUISIONES', f4)
		sheet.write(10, 16, 'NO', f4)
		sheet.write(11, 16, 'GRAVADAS', f5)

		sheet.write(6, 17, '', f3)
		sheet.write(7, 17, 'OTROS', f4)
		sheet.write(8, 17, 'TRIBUTOS', f4)
		sheet.write(9, 17, 'Y', f4)
		sheet.write(10, 17, 'CARGOS', f4)
		sheet.write(11, 17, '', f5)

		sheet.write(6, 18, '', f3)
		sheet.write(7, 18, '', f4)
		sheet.write(8, 18, 'IMPORTE', f4)
		sheet.write(9, 18, 'TOTAL', f4)
		sheet.write(10, 18, '', f4)
		sheet.write(11, 18, '', f5)

		sheet.merge_range('T7:U7', 'CONSTANCIA DE DEPOSITO', f3)
		sheet.merge_range('T8:U8', 'DE DETRACCION', f5)
		sheet.merge_range('T9:U9', '', f5)
		sheet.write(9, 19, '', f4)
		sheet.write(10, 19, 'NUMERO', f4)
		sheet.write(11, 19, '', f5)

		sheet.write(9, 20, 'FECHA', f4)
		sheet.write(10, 20, 'DE', f4)
		sheet.write(11, 20, 'EMISION', f5)

		sheet.write(6, 21, '', f3)
		sheet.write(7, 21, '', f4)
		sheet.write(8, 21, 'TIPO', f4)
		sheet.write(9, 21, 'DE', f4)
		sheet.write(10, 21, 'CAMBIO', f4)
		sheet.write(11, 21, '', f5)

		sheet.merge_range('W7:Z7', 'REFERENCIA DEL COMPROBANTE DE PAGO', f3)
		sheet.merge_range('W8:Z8', 'O DOCUMENTO ORIGINAL', f5)
		sheet.merge_range('W9:Z9', 'QUE SE MODIFICA', f5)
		sheet.write(9, 22, '', f4)
		sheet.write(10, 22, 'FECHA', f4)
		sheet.write(11, 22, '', f5)

		sheet.write(9, 23, '', f4)
		sheet.write(10, 23, 'TIPO', f4)
		sheet.write(11, 23, '', f5)

		sheet.write(9, 24, '', f4)
		sheet.write(10, 24, 'SERIE', f4)
		sheet.write(11, 24, '', f5)

		sheet.write(9, 25, '', f4)
		sheet.write(10, 25, 'NUMERO', f4)
		sheet.write(11, 25, '', f5)

		sheet.write(6, 26, '', f3)
		sheet.write(7, 26, '', f4)
		sheet.write(8, 26, '', f4)
		sheet.write(9, 26, '', f4)
		sheet.write(10, 26, 'IGV', f4)
		sheet.write(11, 26, '', f5)

		sheet.write(6, 27, '', f3)
		sheet.write(7, 27, '', f4)
		sheet.write(8, 27, '', f4)
		sheet.write(9, 27, 'VALIDA', f4)
		sheet.write(10, 27, 'SIRE', f4)
		sheet.write(11, 27, '', f5)

		row = 11
		col = 0

		for purchases in self.data:
			row += 1
			sheet.write(row, col, purchases['CORRELATIVO'], f2)
			sheet.write(row, col + 1, purchases['FECHA EMISION'], f2_date)
			sheet.write(row, col + 2, purchases['FECHA VENCIMIENTO'], f2_date)
			sheet.write(row, col + 3, purchases['TIPO CPE'], f2)
			sheet.write(row, col + 4, purchases['SERIE CPE'], f2)
			sheet.write(row, col + 5, purchases['AÑO DUA'], f2)
			sheet.write(row, col + 6, purchases['NUMERO CPE'], f2)
			sheet.write(row, col + 7, purchases['TIPO DOC'], f2)
			sheet.write(row, col + 8, purchases['NUMERO DOC'], f2)
			sheet.write(row, col + 9, purchases['RAZON SOCIAL'], f2)
			sheet.write(row, col + 10, float(purchases['BASE AG-VG']), f2_dec)
			sheet.write(row, col + 11, float(purchases['IGV AG-VG']), f2_dec)
			sheet.write(row, col + 12, float(purchases['BASE AG-VGNG']), f2_dec)
			sheet.write(row, col + 13, float(purchases['IGV AG-VGNG']), f2_dec)
			sheet.write(row, col + 14, float(purchases['BASE AG-NO']), f2_dec)
			sheet.write(row, col + 15, float(purchases['IGV AG-NO']), f2_dec)
			sheet.write(row, col + 16, float(purchases['INAFECTO']), f2_dec)
			sheet.write(row, col + 17, float(purchases['OTROS CARGOS']), f2_dec)
			sheet.write(row, col + 18, float(purchases['TOTAL']), f2_dec)
			sheet.write(row, col + 19, purchases['CONSTANCIA'], f2)
			sheet.write(row, col + 20, purchases['FECHA CONSTANCIA'], f2_date)
			sheet.write(row, col + 21, float(purchases['TIPO DE CAMBIO']), f6)
			sheet.write(row, col + 22, purchases['FECHA REV'], f2_date)
			sheet.write(row, col + 23, purchases['TIPO REV'], f2)
			sheet.write(row, col + 24, purchases['SERIE REV'], f2)
			sheet.write(row, col + 25, purchases['NUMERO REV'], f2)
			sheet.write(row, col + 26, purchases['PERCENT IGV'], f2)
			sheet.write(row, col + 27, purchases['VALIDA SIRE'], f2)

		contador = len(self.data)
		rowen = 13 + contador
		sheet.write(rowen, 9, 'TOTALES', f7)
		sheet.write(rowen, 10,'=SUM(K13:K' + str(rowen) + ')' , f7)
		sheet.write(rowen, 11, '=SUM(L13:L' + str(rowen) + ')', f7)
		sheet.write(rowen, 12, '=SUM(M13:M' + str(rowen) + ')', f7)
		sheet.write(rowen, 13, '=SUM(N13:N' + str(rowen) + ')', f7)
		sheet.write(rowen, 14, '=SUM(O13:O' + str(rowen) + ')', f7)
		sheet.write(rowen, 15, '=SUM(P13:P' + str(rowen) + ')', f7)
		sheet.write(rowen, 16, '=SUM(Q13:Q' + str(rowen) + ')', f7)
		sheet.write(rowen, 17, '=SUM(R13:R' + str(rowen) + ')', f7)
		sheet.write(rowen, 18, '=SUM(S13:S' + str(rowen) + ')', f7)

		# -
	
		workbook.close()
		output.seek(0)
		return output.read()