# -*- coding: utf-8 -*-
from io import BytesIO
import xlsxwriter
import base64


class ExcelReport(object):

	def __init__(self, data, obj):
		self.data = data
		self.obj = obj

	def get_content(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output, {'default_date_format': 'dd/mm/yyyy'})

		# -
	
		sheet = workbook.add_worksheet('Major 6.1')
		f1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True})
		f2 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False})
		f2_date = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': 'dd/mm/yyyy'})
		f2_dec = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f3 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'top': True, 'right': True, 'left': True})
		f4 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'right': True, 'left': True, 'top': True, 'bottom': True})
		f5 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'bottom': True, 'right': True, 'left': True})
		f6 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f7 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True, 'top': True, 'bottom': True, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})

		sheet.set_column('A:A', 10)
		sheet.set_column('B:B', 15)
		sheet.set_column('C:C', 32)
		sheet.set_column('D:D', 10.72)
		sheet.set_column('E:E', 49)
		sheet.set_column('F:F', 12)
		sheet.set_column('G:G', 12)
		sheet.set_column('H:H', 15.71)

		sheet.write(0, 0, 'FORMATO 6.1: Libro Mayor', f1)

		sheet.write(2, 0, 'PERIODO: ', f1)
		for periodo in self.data:
			sheet.write(2, 4, periodo['PERIODO'], f2)

		sheet.write(3, 0, 'RUC: ', f1)
		sheet.write(3, 4, self.obj.env.company.vat, f2)

		sheet.write(4, 0, 'APELLIDOS Y NOMBRES, DENOMINACION O RAZON SOCIAL: ', f1)
		sheet.write(4, 4, self.obj.env.company.name, f2)

		sheet.write(6, 0, 'FECHA DE LA', f3)
		sheet.write(7, 0, 'OPERACION', f5)

		sheet.write(6, 1, 'NUMERO CORRELATIVO', f3)
		sheet.write(7, 1, 'DEL LIBRO DIARIO', f5)

		sheet.write(6, 2, 'DESCRIPCION O GLOSA', f3)
		sheet.write(7, 2, 'DE LA OPERACION', f5)

		sheet.merge_range('D7:E7', 'CUENTA CONTABLE ASOCIADA A LA OPERACION', f3)
		sheet.write(7, 3, 'CODIGO', f4)
		sheet.write(7, 4, 'NOMBRE DE LA CUENTA', f4)

		sheet.merge_range('F7:G7', 'MOVIMIENTO', f3)
		sheet.write(7, 5, 'DEUDOR', f4)
		sheet.write(7, 6, 'ACREEDOR', f4)

		sheet.write(6, 7, '', f3)
		sheet.write(7, 7, 'ASIENTO', f5)

		row = 7
		col = 0

		for major in self.data:
			row += 1

			sheet.write(row, col, major['FECHA'], f2_date)
			sheet.write(row, col + 1, major['CUO'], f2)
			sheet.write(row, col + 2, major['REF'], f2)
			sheet.write(row, col + 3, major['CTA CODE'], f2)
			sheet.write(row, col + 4, major['CTA NAME'], f2)
			sheet.write(row, col + 5, float(major['DEBITO']), f2_dec)
			sheet.write(row, col + 6, float(major['CREDITO']), f2_dec)
			sheet.write(row, col + 7, major['ASIENTO'], f2)

		contador = len(self.data)
		rowen = 8 + contador
		sheet.write(rowen, 4, 'TOTALES', f7)
		sheet.write(rowen, 5,'=SUM(F9:F' + str(rowen) + ')' , f7)
		sheet.write(rowen, 6, '=SUM(G9:G' + str(rowen) + ')', f7)

		# -
	
		workbook.close()
		output.seek(0)
		return base64.encodebytes(output.read())