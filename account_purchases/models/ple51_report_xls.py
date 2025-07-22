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
	
		sheet = workbook.add_worksheet('Diario 5.1')
		f1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True})
		f2 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False})
		f2_date = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': 'dd/mm/yyyy'})
		f2_dec = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f3 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'top': True, 'right': True, 'left': True})
		f4 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'right': True, 'left': True})
		f5 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'bottom': True, 'right': True, 'left': True})
		f6 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f7 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True, 'top': True, 'bottom': True, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		

		sheet.set_column('A:A', 16)
		sheet.set_column('B:B', 10)
		sheet.set_column('C:C', 25)
		sheet.set_column('D:D', 10)
		sheet.set_column('E:E', 12)
		sheet.set_column('F:F', 13)
		sheet.set_column('G:G', 9)
		sheet.set_column('H:H', 40)
		sheet.set_column('I:I', 15.57)
		sheet.set_column('J:J', 15.57)
		sheet.set_column('K:K', 16)

		sheet.write(0, 0, 'FORMATO 5.1: Libro Diario', f1)
		sheet.write(2, 0, 'PERIODO: ', f1)

		for periodo in self.data:
			sheet.write(2, 4, periodo['PERIODO'], f2)

		sheet.write(3, 0, 'RUC: ', f1)
		sheet.write(3, 4, self.obj.env.company.vat, f2)

		sheet.write(4, 0, 'APELLIDOS Y NOMBRES, DENOMINACION O RAZON SOCIAL: ', f1)
		sheet.write(4, 4, self.obj.env.company.name, f2)

		sheet.write(6, 0, 'NUMERO CORRELATIVO', f3)
		sheet.write(7, 0, 'DEL ASIENTO O', f4)
		sheet.write(8, 0, 'CODIGO UNICO', f4)
		sheet.write(9, 0, 'DE LA OPERACION', f5)

		sheet.write(6, 1, '', f3)
		sheet.write(7, 1, 'FECHA', f4)
		sheet.write(8, 1, 'DE LA', f4)
		sheet.write(9, 1, 'OPERACION', f5)

		sheet.write(6, 2, '', f3)
		sheet.write(7, 2, 'GLOSA O', f4)
		sheet.write(8, 2, 'DESCRIPCION DE', f4)
		sheet.write(9, 2, 'LA OPERACION', f5)

		sheet.merge_range('D7:F7', 'REFERENCIA DE LA OPERACION', f3)
		sheet.write(7, 3, 'CODIGO DEL', f3)
		sheet.write(8, 3, 'LIBRO O', f4)
		sheet.write(9, 3, 'REGISTRO', f5)

		sheet.write(7, 4, '', f3)
		sheet.write(8, 4, 'NUMERO', f4)
		sheet.write(9, 4, 'CORRELATIVO', f5)

		sheet.write(7, 5, 'NUMERO DEL', f3)
		sheet.write(8, 5, 'DOCUMENTO', f4)
		sheet.write(9, 5, 'SUSTENTATORIO', f5)

		sheet.merge_range('G7:H7', 'CUENTA CONTABLE ASOCIADA A LA OPERACION', f3)
		sheet.write(7, 6, '', f3)
		sheet.write(8, 6, 'CODIGO', f4)
		sheet.write(9, 6, '', f5)

		sheet.write(7, 7, '', f3)
		sheet.write(8, 7, 'DENOMINACION', f4)
		sheet.write(9, 7, '', f5)

		sheet.merge_range('I7:J7', 'MOVIMIENTO', f3)
		sheet.write(7, 8, '', f3)
		sheet.write(8, 8, 'DEBE', f4)
		sheet.write(9, 8, '', f5)

		sheet.write(7, 9, '', f3)
		sheet.write(8, 9, 'HABER', f4)
		sheet.write(9, 9, '', f5)

		sheet.write(6, 10, '', f3)
		sheet.write(7, 10, 'ASIENTO', f4)
		sheet.write(8, 10, '', f4)
		sheet.write(9, 10, '', f5)

		row = 9
		col = 0

		for diary in self.data:
			row += 1

			sheet.write(row, col, diary['CUO'], f2)
			sheet.write(row, col + 1, diary['FECHA'], f2_date)
			sheet.write(row, col + 2, diary['REF'], f2)
			sheet.write(row, col + 3, diary['CODE LIBRO'], f2)
			sheet.write(row, col + 4, diary['SECUENCIA LIBRO'], f2)
			sheet.write(row, col + 5, diary['NUMERO LIBRO'], f2)
			sheet.write(row, col + 6, diary['CTA CODE'], f2)
			sheet.write(row, col + 7, diary['CTA NAME'], f2)
			sheet.write(row, col + 8, float(diary['DEBITO']), f2_dec)
			sheet.write(row, col + 9, float(diary['CREDITO']), f2_dec)
			sheet.write(row, col + 10, diary['ASIENTO'], f2)

		contador = len(self.data)
		rowen = 10 + contador
		sheet.write(rowen, 7, 'TOTALES', f7)
		sheet.write(rowen, 8,'=SUM(I11:I' + str(rowen) + ')' , f7)
		sheet.write(rowen, 9, '=SUM(J11:J' + str(rowen) + ')', f7)

		# -
	
		workbook.close()
		output.seek(0)
		return base64.encodebytes(output.read())