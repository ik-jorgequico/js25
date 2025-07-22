from io import BytesIO
import xlsxwriter


class AccountExcelReport(object):

	def __init__(self, data, obj, date_start, date_end):
		self.data = data
		self.obj = obj
		self.date_start = date_start
		self.date_end = date_end

	@staticmethod
	def getColumnName(n):
		result = ''
		while n > 0:
			index = (n - 1) % 26
			result += chr(index + ord('A'))
			n = (n - 1) // 26
		return result[::-1]
	
	def get_content(self):
		output = BytesIO()
		wb = xlsxwriter.Workbook(output, {'default_date_format': 'dd/mm/yyyy'})

		sheet = wb.add_worksheet('')

		row = 8
		# sheet.autofilter('A'+str(row)+':V'+str(row))

		column_chiki = wb.add_format({
			'size': 10,
			'bold': 1,
			'fg_color': '#BFBFC0',
			'font_color': 'black',
			'text_wrap':True,
			'text_h_align' : 2,
			'text_v_align' : 2,
			'border': 1,
		})

		f1 = wb.add_format({'size': 10,'bold': True,'font_color': 'black',})
		f2 = wb.add_format({'size': 10,})

		style_content_table_format = wb.add_format({'size': 10,})

		f1_number = wb.add_format({'size': 10,'num_format': '#,##0.00',})
		
		"""
			CABECERA
		"""
		for i,dict in enumerate(self.data):
			if "period" in dict:
				sheet.write(1,1, 'ASIENTO CONTABLE DEL PERIODO ' + dict["period"], f1)
		sheet.write(3,0,"RAZON SOCIAL:",f1)
		sheet.write(3,1,self.obj.env.company.name,f2)
		sheet.write(4,0,"RUC:",f1)
		sheet.write(4,1,"",f2)
		if self.obj.env.company.vat:
			sheet.write(4,1,self.obj.env.company.vat,f2)
		sheet.write(5,0,"PERIODO:",f1)
		for i,dict in enumerate(self.data):
			sheet.write(5,1,dict["period"],f2)

		"""
			PRINT COLUMNS
		"""
		prom_columns = []
		for dictionary in self.data:
			prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
		prom_columns = list(set(prom_columns))
		prom_columns.sort()
		
		sheet.set_column("A:A", 10)
		sheet.set_column("B:B", 20)
		sheet.set_column("C:C", 60)
		sheet.set_column("D:D", 20)
		sheet.set_column("E:E", 15)
		sheet.set_column("F:F", 20)
		sheet.set_column("G:G", 12)
		sheet.set_column("H:H", 9)
		sheet.set_column("I:I", 15)
		sheet.set_column("J:J", 15)
		
		sheet.write(row - 1,0,"CUENTA CONTABLE",column_chiki)
		sheet.write(row - 1,1,"REGLA",column_chiki)
		sheet.write(row - 1,2,"NOMBRE DE CUENTA CONTABLE",column_chiki)
		sheet.write(row - 1,3,"REFERENCIA",column_chiki)
		sheet.write(row - 1,4,"ETIQUETA ANALITICA",column_chiki)
		sheet.write(row - 1,5,"CUENTA ANALITICA",column_chiki)
		sheet.write(row - 1,6,"IMPORTE EN MONEDA",column_chiki)
		sheet.write(row - 1,7,"MONEDA",column_chiki)
		sheet.write(row - 1,8,"DEBITO",column_chiki)
		sheet.write(row - 1,9,"CREDITO",column_chiki)
		tamnio = len(self.data)
		column_total_table_format = wb.add_format({
			'size': 8,
			'fg_color': '#BFBFC0',
			'font_color': 'black',
			'text_wrap':True,
			'text_h_align' : 2,
			'text_v_align' : 2,
			'num_format': '#,##0.00',
			'border':1
		})
		if tamnio > 0:
			sheet.write(row + tamnio, 8, f"=SUM({self.getColumnName(9)}{row+1}:{self.getColumnName(9)}{row+tamnio})", column_total_table_format)
			sheet.write(row + tamnio, 9, f"=SUM({self.getColumnName(10)}{row+1}:{self.getColumnName(10)}{row+tamnio})", column_total_table_format)
		"""
			PRINT DATA TABLE
		"""
		
		for i,dict in enumerate(self.data):
			sheet.write(i + row,0,dict["account_code"],style_content_table_format)
			sheet.write(i + row,1,dict["rule"],style_content_table_format)
			sheet.write(i + row,2,dict["account_code_name"],style_content_table_format)
			sheet.write(i + row,3,dict["ref"],style_content_table_format)
			sheet.write(i + row,4,dict["analytic_tag"],style_content_table_format)
			sheet.write(i + row,5,dict["analytic_ac"],style_content_table_format)
			sheet.write(i + row,6,dict["amount"],f1_number)
			sheet.write(i + row,7,dict["currency"],style_content_table_format)
			sheet.write(i + row,8,dict["debit"],f1_number)
			sheet.write(i + row,9,dict["credit"],f1_number)
			
		tamnio = len(self.data)
		wb.close()
		output.seek(0)
		return output.read()
	
class AccountExcelReportProv(object):

	def __init__(self, data, obj, date_start, date_end):
		self.data = data
		self.obj = obj
		self.date_start = date_start
		self.date_end = date_end

	@staticmethod
	def getColumnName(n):
		result = ''
		while n > 0:
			index = (n - 1) % 26
			result += chr(index + ord('A'))
			n = (n - 1) // 26
		return result[::-1]
	
	def get_content(self):
		output = BytesIO()
		wb = xlsxwriter.Workbook(output, {'default_date_format': 'dd/mm/yyyy'})

		sheet = wb.add_worksheet('')

		row = 8
		# sheet.autofilter('A'+str(row)+':V'+str(row))

		column_chiki = wb.add_format({
			'size': 10,
			'bold': 1,
			'fg_color': '#BFBFC0',
			'font_color': 'black',
			'text_wrap':True,
			'text_h_align' : 2,
			'text_v_align' : 2,
			'border': 1,
		})

		f1 = wb.add_format({'size': 10,'bold': True,'font_color': 'black',})
		f2 = wb.add_format({'size': 10,})

		style_content_table_format = wb.add_format({'size': 10,})

		f1_number = wb.add_format({'size': 10,'num_format': '#,##0.00',})
		
		"""
			CABECERA
		"""
		for i,dict in enumerate(self.data):
			if "period" in dict:
				sheet.write(1,1, 'ASIENTO CONTABLE DEL PERIODO ' + dict["period"], f1)
		sheet.write(3,0,"RAZON SOCIAL:",f1)
		sheet.write(3,1,self.obj.env.company.name,f2)
		sheet.write(4,0,"RUC:",f1)
		sheet.write(4,1,"",f2)
		if self.obj.env.company.vat:
			sheet.write(4,1,self.obj.env.company.vat,f2)
		sheet.write(5,0,"PERIODO:",f1)
		for i,dict in enumerate(self.data):
			sheet.write(5,1,dict["period"],f2)

		"""
			PRINT COLUMNS
		"""
		prom_columns = []
		for dictionary in self.data:
			prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
		prom_columns = list(set(prom_columns))
		prom_columns.sort()
		
		sheet.set_column("A:A", 10)
		sheet.set_column("B:B", 60)
		sheet.set_column("C:C", 22)
		sheet.set_column("D:D", 15)
		sheet.set_column("E:E", 20)
		sheet.set_column("F:F", 15)
		sheet.set_column("G:G", 9)
		sheet.set_column("H:H", 15)
		sheet.set_column("I:I", 15)
		
		sheet.write(row - 1,0,"CUENTA CONTABLE",column_chiki)
		sheet.write(row - 1,1,"NOMBRE DE CUENTA CONTABLE",column_chiki)
		sheet.write(row - 1,2,"REFERENCIA",column_chiki)
		sheet.write(row - 1,3,"ETIQUETA ANALITICA",column_chiki)
		sheet.write(row - 1,4,"CUENTA ANALITICA",column_chiki)
		sheet.write(row - 1,5,"IMPORTE EN MONEDA",column_chiki)
		sheet.write(row - 1,6,"MONEDA",column_chiki)
		sheet.write(row - 1,7,"DEBITO",column_chiki)
		sheet.write(row - 1,8,"CREDITO",column_chiki)
		tamnio = len(self.data)
		column_total_table_format = wb.add_format({
			'size': 8,
			'fg_color': '#BFBFC0',
			'font_color': 'black',
			'text_wrap':True,
			'text_h_align' : 2,
			'text_v_align' : 2,
			'num_format': '#,##0.00',
			'border':1
		})
		if tamnio > 0:
			sheet.write(row + tamnio, 7, f"=SUM({self.getColumnName(8)}{row+1}:{self.getColumnName(8)}{row+tamnio})", column_total_table_format)
			sheet.write(row + tamnio, 8, f"=SUM({self.getColumnName(9)}{row+1}:{self.getColumnName(9)}{row+tamnio})", column_total_table_format)
		"""
			PRINT DATA TABLE
		"""
		
		for i,dict in enumerate(self.data):
			sheet.write(i + row,0,dict["account_code"],style_content_table_format)
			sheet.write(i + row,1,dict["account_code_name"],style_content_table_format)
			sheet.write(i + row,2,dict["ref"],style_content_table_format)
			sheet.write(i + row,3,dict["analytic_tag"],style_content_table_format)
			sheet.write(i + row,4,dict["analytic_ac"],style_content_table_format)
			sheet.write(i + row,5,dict["amount"],f1_number)
			sheet.write(i + row,6,dict["currency"],style_content_table_format)
			sheet.write(i + row,7,dict["debit"],f1_number)
			sheet.write(i + row,8,dict["credit"],f1_number)
			
		tamnio = len(self.data)
		wb.close()
		output.seek(0)
		return output.read()