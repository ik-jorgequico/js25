# -*- coding: utf-8 -*-
from io import BytesIO
import xlsxwriter
import base64


class SaleExcelReport(object):

	def __init__(self, data, obj):
		self.data = data
		self.obj = obj

	def get_content(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output,{'default_date_format': 'dd/mm/yyyy'})

		# -
	
		sheet = workbook.add_worksheet('Ventas 14.1')
		f1 = workbook.add_format({'font_size': 12, 'align': 'vcenter', 'bold': True})
		
		f2_date = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': 'dd/mm/yyyy'})
		f2_dec = workbook.add_format({'font_size': 9, 'align': 'vcenter', 'bold': False, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})
		f2 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False})
		f3 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'top': True, 'right': True, 'left': True})
		f4 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'right': True, 'left': True})
		f5 = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True, 'bottom': True, 'right': True, 'left': True})
		f6 = workbook.add_format({'font_size': 8, 'align': 'vcenter', 'bold': False, 'num_format': '#,##0.000'})
		f7 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bold': True, 'top': True, 'bottom': True, 'num_format': '_ * #,##0.00_ ;_ * -#,##0.00_ ;_ * "-"??_ ;_ @_ '})

		sheet.set_column('A:A', 11)
		sheet.set_column('B:B', 11)
		sheet.set_column('C:C', 11)
		sheet.set_column('D:D', 4)
		sheet.set_column('E:E', 9)
		sheet.set_column('F:F', 7)
		sheet.set_column('G:G', 4)
		sheet.set_column('H:H', 10)
		sheet.set_column('I:I', 34)
		sheet.set_column('J:Q', 10)
		sheet.set_column('R:R', 6)		
		sheet.set_column('S:S', 9)
		sheet.set_column('T:T', 5)
		sheet.set_column('U:U', 9)
		sheet.set_column('V:V', 6)
		sheet.set_column('W:W', 6)
		sheet.set_column('X:X', 6)

		sheet.write(0, 0, 'FORMATO 14.1: REGISTRO DE VENTAS E INGRESOS', f1)
		sheet.write(2, 0, 'PERIODO: ', f1)
		for mes in self.data:
			sheet.write(2, 7, mes['PERIODO'], f2)

		sheet.write(3, 0, 'RUC: ', f1)
		sheet.write(3, 7, self.obj.env.company. vat, f2)

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
		sheet.write(10, 2, 'Y/O PAGO', f4)
		sheet.write(11, 2, '', f5)

		sheet.merge_range('D7:F7', 'COMPROBANTE DE PAGO', f3)
		sheet.merge_range('D8:F8', 'O DOCUMENTO', f5)
		sheet.write(8, 3, '', f3)
		sheet.write(9, 3, 'TIPO', f4)
		sheet.write(10, 3, '', f4)
		sheet.write(11, 3, '', f5)

		sheet.write(8, 4, '', f3)
		sheet.write(9, 4, 'SERIE O NRO', f4)
		sheet.write(10, 4, 'MAQ. REGIST.', f4)
		sheet.write(11, 4, '', f5)

		sheet.write(8, 5, '', f3)
		sheet.write(9, 5, 'NUMERO', f4)
		sheet.write(10, 5, '', f4)
		sheet.write(11, 5, '', f5)

		sheet.merge_range('G7:I7', 'INFORMACION DEL CLIENTE', f3)
		sheet.merge_range('G8:I8', '', f5)
		sheet.merge_range('G9:H9', 'DOC. IDENTIDAD', f5)
		sheet.write(9, 6, '', f4)
		sheet.write(10, 6, 'TIPO', f4)
		sheet.write(11, 6, '', f5)

		sheet.write(9, 7, '', f4)
		sheet.write(10, 7, 'NUMERO', f4)
		sheet.write(11, 7, '', f5)

		sheet.write(8, 8, 'APELLIDOS Y NOMBRES,', f4)
		sheet.write(9, 8, 'O RAZON SOCIAL', f4)
		sheet.write(10, 8, '', f4)
		sheet.write(11, 8, '', f5)

		sheet.write(6, 9, 'VALOR', f3)
		sheet.write(7, 9, 'FACTURADO', f4)
		sheet.write(8, 9, 'DE LA', f4)
		sheet.write(9, 9, 'EXPORTACION', f4)
		sheet.write(10, 9, '', f4)
		sheet.write(11, 9, '', f5)

		sheet.write(6, 10, 'BASE', f3)
		sheet.write(7, 10, 'IMPONIBLE', f4)
		sheet.write(8, 10, 'DE LA', f4)
		sheet.write(9, 10, 'OPERACION', f4)
		sheet.write(10, 10, 'GRAVADA', f4)
		sheet.write(11, 10, '', f5)

		sheet.write(6, 11, '', f3)
		sheet.write(7, 11, 'DESCUENTO', f4)
		sheet.write(8, 11, 'DE LA', f4)
		sheet.write(9, 11, 'BASE', f4)
		sheet.write(10, 11, 'IMPONIBLE', f4)
		sheet.write(11, 11, '', f5)

		sheet.merge_range('M7:N7', 'IMPORTE TOTAL DE LA', f3)
		sheet.merge_range('M8:N8', 'OPERACION', f5)
		sheet.write(8, 12, '', f4)
		sheet.write(9, 12, 'EXONERADA', f4)
		sheet.write(10, 12, '', f4)
		sheet.write(11, 12, '', f5)

		sheet.write(8, 13, '', f4)
		sheet.write(9, 13, 'INAFECTA', f4)
		sheet.write(10, 13, '', f4)
		sheet.write(11, 13, '', f5)

		sheet.write(6, 14, '', f3)
		sheet.write(7, 14, '', f4)
		sheet.write(8, 14, 'ISC', f4)
		sheet.write(9, 14, '', f4)
		sheet.write(10, 14, '', f4)
		sheet.write(11, 14, '', f5)

		sheet.write(6, 15, '', f3)
		sheet.write(7, 15, 'IGV', f4)
		sheet.write(8, 15, 'Y/O', f4)
		sheet.write(9, 15, 'IPM', f4)
		sheet.write(10, 15, '', f4)
		sheet.write(11, 15, '', f5)

		sheet.write(6, 16, '', f3)
		sheet.write(7, 16, '', f4)
		sheet.write(8, 16, 'DESCUENTO', f4)
		sheet.write(9, 16, 'DEL IGV', f4)
		sheet.write(10, 16, '', f4)
		sheet.write(11, 16, '', f5)

		sheet.write(6, 17, '', f3)
		sheet.write(7, 17, '', f4)
		sheet.write(8, 17, 'OTROS', f4)
		sheet.write(9, 17, 'TRIBUTOS', f4)
		sheet.write(10, 17, '', f4)
		sheet.write(11, 17, '', f5)

		sheet.write(6, 18, '', f3)
		sheet.write(7, 18, '', f4)
		sheet.write(8, 18, 'IMPORTE', f4)
		sheet.write(9, 18, 'TOTAL', f4)
		sheet.write(10, 18, '', f4)
		sheet.write(11, 18, '', f5)

		sheet.write(6, 19, '', f3)
		sheet.write(7, 19, 'TIPO', f4)
		sheet.write(8, 19, 'DE', f4)
		sheet.write(9, 19, 'CAMBIO', f4)
		sheet.write(10, 19, '', f4)
		sheet.write(11, 19, '', f5)

		sheet.merge_range('U7:X7', 'REFERENCIA DEL COMPROBANTE DE PAGO', f3)
		sheet.merge_range('U8:X8', 'O DOCUMENTO ORIGINAL QUE SE MODIFICA', f5)
		sheet.write(8, 20, '', f4)
		sheet.write(9, 20, 'FECHA', f4)
		sheet.write(10, 20, '', f4)
		sheet.write(11, 20, '', f5)

		sheet.write(8, 21, '', f4)
		sheet.write(9, 21, 'TIPO', f4)
		sheet.write(10, 21, '', f4)
		sheet.write(11, 21, '', f5)

		sheet.write(8, 22, '', f4)
		sheet.write(9, 22, 'SERIE', f4)
		sheet.write(10, 22, '', f4)
		sheet.write(11, 22, '', f5)

		sheet.write(8, 23, '', f4)
		sheet.write(9, 23, 'NUMERO', f4)
		sheet.write(10, 23, '', f4)
		sheet.write(11, 23, '', f5)

		sheet.write(6, 24, '', f3)
		sheet.write(7, 24, '', f4)
		sheet.write(8, 24, '', f4)
		sheet.write(9, 24, 'VALIDA', f4)
		sheet.write(10, 24, 'SIRE', f4)
		sheet.write(11, 24, '', f5)

		row = 11
		col = 0

		for sales in self.data:
			row += 1
			sheet.write(row, col, sales['CORRELATIVO'], f2)
			sheet.write(row, col + 1, sales['FECHA EMISION'], f2_date)
			sheet.write(row, col + 2, sales['FECHA VENCIMIENTO'], f2_date)
			sheet.write(row, col + 3, sales['TIPO CPE'], f2)
			sheet.write(row, col + 4, sales['SERIE CPE'], f2)
			sheet.write(row, col + 5, sales['NUMERO CPE'], f2)
			sheet.write(row, col + 6, sales['TIPO DOC'], f2)
			sheet.write(row, col + 7, sales['NUMERO DOC'], f2)
			sheet.write(row, col + 8, sales['RAZON SOCIAL'], f2)

			sheet.write(row, col + 9, float(sales['BASE EXP']), f2_dec)
			sheet.write(row, col + 10, float(sales['BASE AG-VG']), f2_dec)
			sheet.write(row, col + 11, float(sales['BASE DESC']), f2_dec)
			sheet.write(row, col + 12, float( sales['EXONERADO']), f2_dec)
			sheet.write(row, col + 13, float(sales['INAFECTO']), f2_dec)
			sheet.write(row, col + 14, 0.00, f2_dec)
			sheet.write(row, col + 15, float(sales['IGV AG-VG']), f2_dec)
			sheet.write(row, col + 16, float(sales['IGV DESC']), f2_dec)
			sheet.write(row, col + 17, 0.00, f2_dec)
			sheet.write(row, col + 18, float(sales['TOTAL']), f2_dec)
			sheet.write(row, col + 19, float(sales['TIPO DE CAMBIO']), f6)
			sheet.write(row, col + 20, sales['FECHA REV'], f2_date)
			sheet.write(row, col + 21, sales['TIPO REV'], f2)
			sheet.write(row, col + 22, sales['SERIE REV'], f2)
			sheet.write(row, col + 23, sales['NUMERO REV'], f2)
			sheet.write(row, col + 24, sales['VALIDA SIRE'], f2)

		contador = len(self.data)
		rowen = 13 + contador
		sheet.write(rowen, 8, 'TOTALES', f7)
		sheet.write(rowen, 9,'=SUM(J13:J' + str(rowen) + ')' , f7)
		sheet.write(rowen, 10, '=SUM(K13:K' + str(rowen) + ')', f7)
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
		return base64.encodebytes(output.read())