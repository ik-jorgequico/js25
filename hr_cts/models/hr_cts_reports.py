from io import BytesIO
import xlsxwriter


class CTSExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

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
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        sheet = wb.add_worksheet('TRABAJADOR')

        row = 10
        sheet.autofilter('A'+str(row)+':AA'+str(row))

        column_content_table_format = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,

        })
        column_content_table_format_top = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#C5D9F1',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })

        f1 = wb.add_format({
            'size': 10,
            'bold': 1,

        })
        f2 = wb.add_format({
            'size': 10, 
        })

        style_content_table_format = wb.add_format({
            'size': 8,
        })
        style_content_num_table_format = wb.add_format({
            'size': 8,
            'num_format': '#,##0.00',
        })
        
        style_date_content_table_format = wb.add_format({
            'size': 8,
            'num_format': 'dd/mm/yyyy',}
        )
        """
            CABECERA
        """
        sheet.write(1,2,self.obj.name,f1)
        sheet.write(3,0,"RAZON SOCIAL:",f1)
        sheet.write(3,1,self.obj.env.company.name,f2)
        sheet.write(4,0,"RUC:",f1)
        sheet.write(4,1,"",f2)
        if self.obj.env.company.vat:
            sheet.write(4,1,self.obj.env.company.vat,f2)
        sheet.write(5,0,"PERIODO:",f1)
        sheet.write(5,1,self.obj.date_from.strftime("%b %Y").upper() + "-" + self.obj.date_to.strftime("%b %Y").upper(),f2)

        """
            PRINT COLUMNS
        """
        prom_columns = []
        for dictionary in self.data:
            prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
        prom_columns = list(set(prom_columns))
        prom_columns.sort()
        
        len_prom_columns = len(prom_columns)
        
        sheet.set_column(0, 15, 20)
        sheet.set_column(15, 26 + len_prom_columns, 15)
        sheet.set_row(row - 2, 30)
        sheet.set_row(row - 1, 40)

        sheet.merge_range(row - 2, 0, row - 2, 16, 'DATOS GENERALES', column_content_table_format_top)
        sheet.merge_range(row - 2, 17, row - 2, 20 + len_prom_columns, 'BASE CALCULO', column_content_table_format_top)
        sheet.merge_range(row - 2, 21 + len_prom_columns, row - 2, 22 + len_prom_columns, 'DIAS LABORADOS O NO LABORADOS', column_content_table_format_top)
        sheet.merge_range(row - 2, 23 + len_prom_columns, row - 2, 24 + len_prom_columns, 'INGRESOS', column_content_table_format_top)
        sheet.write(row - 2, 25 + len_prom_columns, 'DESCUENTOS', column_content_table_format_top)
        
        headers = ["ID", "CODIGO", "REGIMEN", "TIPO DOC.", "DOCUMENTO", "PRIMER APELLIDO", "SEGUNDO APELLIDO", "PRIMER NOMBRE", "SEGUNDO NOMBRE", "CENTRO DE COSTO", "ZONAL", "AREA/DEPARTAMENTO", "CARGO", "BANCO CTS", "CUENTA CTS", "FECHA DE INGRESO", "FECHA DE CESE", "BÁSICO", "ASIG FAMILIAR", "1/6 GRATI", *prom_columns, "TOTAL BASE", "DIAS NO LABORADOS", "DIAS LABORADOS TOTALES", "CTS", "Total de Ingreso", "DESCUENTO", "NETO A PAGAR"]
        
        for num_col, col_name in enumerate(headers):
            sheet.write(row - 1, num_col, col_name, column_content_table_format)
        
        """
            PRINT DATA TABLE
        """
        
        for i, info in enumerate(self.data):
            sheet.write(i + row, 0, info["id"], style_content_table_format)
            sheet.write(i + row, 1, info["code"], style_content_table_format)
            sheet.write(i + row, 2, info["regime"], style_content_table_format)
            sheet.write(i + row, 3, info["doc_type"], style_content_table_format)
            sheet.write(i + row, 4, info["doc_num"], style_content_table_format)
            sheet.write(i + row, 5, info["first_lastname"], style_content_table_format)
            sheet.write(i + row, 6, info["second_lastname"], style_content_table_format)
            sheet.write(i + row, 7, info["first_name"], style_content_table_format)
            sheet.write(i + row, 8, info["second_name"], style_content_table_format)
            sheet.write(i + row, 9, info["coste_center"], style_content_table_format)
            sheet.write(i + row, 10, info["zonal"], style_content_table_format)
            sheet.write(i + row, 11, info["area"], style_content_table_format)
            sheet.write(i + row, 12, info["job"], style_content_table_format)
            sheet.write(i + row, 13, info["bank"], style_content_table_format)
            sheet.write(i + row, 14, info["num_account"], style_content_table_format)
            sheet.write(i + row, 15, info["date_first_contract"], style_date_content_table_format)
            sheet.write(i + row, 16, info["date_last_contract"], style_date_content_table_format)
            sheet.write(i + row, 17, info["salary_basic"], style_content_num_table_format)
            sheet.write(i + row, 18, info["family_asig"], style_content_num_table_format)
            sheet.write(i + row, 19, info["grati"], style_content_num_table_format)

            for ind, col_name in enumerate(prom_columns):
                sheet.write(i + row, 20 + ind, info[col_name] if col_name in info else 0, style_content_num_table_format)

            sheet.write(i + row, 20 + len_prom_columns, info["base_total"], style_content_num_table_format)
            sheet.write(i + row, 21 + len_prom_columns, info["number_leave_days"], style_content_num_table_format)
            sheet.write(i + row, 22 + len_prom_columns, info["working_days"], style_content_num_table_format)
            sheet.write(i + row, 23 + len_prom_columns, info["cts"], style_content_num_table_format)
            sheet.write(i + row, 24 + len_prom_columns, info["total_ingreso"], style_content_num_table_format)
            sheet.write(i + row, 25 + len_prom_columns, info["desc_cts"], style_content_num_table_format)
            sheet.write(i + row, 26 + len_prom_columns, info["total"], style_content_num_table_format)

        tamnio = len(self.data)
        column_total_table_format = wb.add_format({
            'size': 8,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap': True,
            'text_h_align': 2,
            'text_v_align': 2,
            'num_format': '#,##0.00',
            'border': 1
        })
        
        sheet.write(row + tamnio, 0, "TOTAL", column_total_table_format)
        for i in range(17, 26 + len_prom_columns):
            column_name = self.getColumnName(i+1)
            sheet.write(row + tamnio, i, f"=SUM({column_name}11:{column_name}{row + tamnio})",column_total_table_format)

        wb.close()
        output.seek(0)
        return output.read()
