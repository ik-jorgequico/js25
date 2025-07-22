from io import BytesIO
import xlsxwriter


class PayslipExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

    def get_filename(self):
        return 'Planilla.xlsx'
    @staticmethod
    def getColumnName(n):
        result = ''
        while n > 0:
            index = (n - 1) % 26
            result += chr(index + ord('A'))
            n = (n - 1) // 26
        return result[::-1]

    def printf(self,wb,data,page):
        sheet = wb.add_worksheet(page)
        sheet.autofilter('A7:CA7')

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

        column_total_table_format = wb.add_format({
            'size': 8,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'num_format': '#,##0.00',
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
        column_num_table_format = wb.add_format({
            'size': 8,
            'num_format': '#,##0.00'

        })
        style_date_content_table_format = wb.add_format({
            'size': 8,
            'num_format': 'dd/mm/yyyy',}
        )

        sheet.write(1,0,"RAZON SOCIAL:",f1)
        sheet.write(1,1,self.obj.env.company.name,f2)
        sheet.write(2,0,"RUC:",f1)
        sheet.write(2,1,"",f2)
        if self.obj.env.company.vat:
            sheet.write(2,1,self.obj.env.company.vat,f2)
        sheet.write(3,0,"PERIODO:",f1)
        sheet.write(3,1,self.obj.payslip_run_id.date_start.strftime("%b %Y").upper().upper(),f2)

        sheet.set_column('A:D', 10)
        sheet.set_column('E:H', 20)
        sheet.set_column('I:P', 10)
        sheet.set_column('Q:Q',10,style_date_content_table_format)
        sheet.set_column('R:CA', 10)
        """
            PRINT COLUMNS
            """
        dias_columns = []
        inc_columns = []
        ded_columns = []
        apo_columns = []
        for dictionary in data:
            dias_columns += [i for i in list(dictionary.keys()) if i[:5]=="Dias_"]
            inc_columns += [i for i in list(dictionary.keys()) if i[:4]=="Inc_"]
            ded_columns += [i for i in list(dictionary.keys()) if i[:4]=="Ded_"]
            apo_columns += [i for i in list(dictionary.keys()) if i[:4]=="Apo_"]

        dias_columns = list(set(dias_columns))
        dias_columns.sort()
        len_dias_columns = len(dias_columns) 

        inc_columns = list(set(inc_columns))
        inc_columns.sort()

        
        initial_inc = []
        
        if "Inc_REMUNERACIÓN BÁSICA" in inc_columns:
            initial_inc.append("Inc_REMUNERACIÓN BÁSICA")
            inc_columns.remove("Inc_REMUNERACIÓN BÁSICA")
        
        if "Inc_ASIGNACIÓN FAMILIAR" in inc_columns:
            initial_inc.append("Inc_ASIGNACIÓN FAMILIAR")
            inc_columns.remove("Inc_ASIGNACIÓN FAMILIAR")
        initial_inc += inc_columns
        inc_columns = initial_inc.copy()
        len_inc_columns = len(inc_columns) 


        ded_columns = list(set(ded_columns))
        ded_columns.sort()
        len_ded_columns = len(ded_columns) 

        apo_columns = list(set(apo_columns))
        apo_columns.sort()
        len_apo_columns = len(apo_columns) 

        row = 7


        """
            COLUMNAS
        """
        sheet.merge_range(row - 2,0,row - 2,21, 'DATOS GENERALES', column_content_table_format_top)
        sheet.write(row - 1,0,"ID",column_content_table_format)
        sheet.write(row - 1,1,"CODIGO",column_content_table_format)
        sheet.write(row - 1,2,"REGIMEN LABORAL",column_content_table_format) 
        sheet.write(row - 1,3,"TIPO DOCUMENTO",column_content_table_format)
        sheet.write(row - 1,4,"NUM DOCUMENTO",column_content_table_format)
        sheet.write(row - 1,5,"PRIMER APELLIDO",column_content_table_format)
        sheet.write(row - 1,6,"SEGUNDO APELLIDO",column_content_table_format)
        sheet.write(row - 1,7,"PRIMER NOMBRE",column_content_table_format)
        sheet.write(row - 1,8,"SEGUNDO NOMBRE",column_content_table_format)
        sheet.write(row - 1,9,"CENTRO DE COSTO",column_content_table_format)
        sheet.write(row - 1,10,"LOCALIDAD",column_content_table_format)
        sheet.write(row - 1,11,"AREA/DEPARTAMENTO",column_content_table_format)
        sheet.write(row - 1,12,"CARGO/PUESTO DE TRABAJO",column_content_table_format)
        sheet.write(row - 1,13,"AFP",column_content_table_format)
        sheet.write(row - 1,14,"TIPO COMISION AFP",column_content_table_format)
        sheet.write(row - 1,15,"CUSPP",column_content_table_format)
        sheet.write(row - 1,16,"BANCO HABERES",column_content_table_format)
        sheet.write(row - 1,17,"CUENTA HABERES",column_content_table_format)
        sheet.write(row - 1,18,"FECHA INGRESO",column_content_table_format)
        sheet.write(row - 1,19,"FECHA CESE",column_content_table_format)
        sheet.write(row - 1,20,"SISTEMA DE SALUD",column_content_table_format)
        sheet.write(row - 1,21,"SALARIO BASICO",column_content_table_format)

        if len_dias_columns == 1:
            sheet.write(row - 1,22,"DIAS LABORADOS Y NO LABORADOS",column_content_table_format_top)
        elif len_dias_columns > 0:
            sheet.merge_range(row - 2,22,row - 2,22+len_dias_columns-1, 'DIAS LABORADOS Y NO LABORADOS', column_content_table_format_top)
        for ind,col_name in enumerate(dias_columns):
                sheet.write(row - 1,22+ind,col_name[5:],column_content_table_format)

        sheet.merge_range(row - 2,22+len_dias_columns,row - 2,22+len_dias_columns+len_inc_columns, 'INGRESOS AFECTOS Y NO AFECTOS', column_content_table_format_top)
        for ind,col_name in enumerate(inc_columns):
                sheet.write(row - 1,22+ind+len_dias_columns,col_name[4:],column_content_table_format)
        sheet.write(row - 1,22+len_dias_columns+len_inc_columns,"TOTAL INGRESO",column_content_table_format)

        sheet.merge_range(row - 2,23+len_dias_columns+len_inc_columns,row - 2,23+len_dias_columns+len_inc_columns+len_ded_columns, 'DEDUCCIONES', column_content_table_format_top)
        for ind,col_name in enumerate(ded_columns):
                sheet.write(row - 1,23+ind+len_dias_columns+len_inc_columns,col_name[4:],column_content_table_format)
        sheet.write(row - 1,23+len_dias_columns+len_inc_columns+len_ded_columns,"TOTAL DEDUCCION",column_content_table_format)
                

        sheet.merge_range(row - 2,24+len_dias_columns+len_inc_columns+len_ded_columns,row - 2,23+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns, 'APORTACIONES', column_content_table_format_top)
        for ind,col_name in enumerate(apo_columns):
                sheet.write(row - 1,24+ind+len_dias_columns+len_inc_columns+len_ded_columns,col_name[4:],column_content_table_format)
        sheet.write(row - 1,24+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns,"TOTAL APORTACIONES",column_content_table_format)

        sheet.write(row - 1,25+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns,"NETO",column_content_table_format)

        for i,dict in enumerate(data):
            
            sheet.write(i + row,0,dict["ID"],style_content_table_format)
            sheet.write(i + row,1,dict["CODIGO"],style_content_table_format)
            sheet.write(i + row,2,str(dict["REGIMEN LABORAL"]),style_content_table_format)
            sheet.write(i + row,3,dict["TIPO DOCUMENTO"],style_content_table_format)
            sheet.write(i + row,4,dict["NUM DOCUMENTO"],style_content_table_format)
            sheet.write(i + row,5,dict["PRIMER APELLIDO"],style_content_table_format)
            sheet.write(i + row,6,dict["SEGUNDO APELLIDO"],style_content_table_format)
            sheet.write(i + row,7,dict["PRIMER NOMBRE"],style_content_table_format)
            sheet.write(i + row,8,dict["SEGUNDO NOMBRE"],style_content_table_format)
            sheet.write(i + row,9,dict["CENTRO DE COSTO"],style_content_table_format)
            sheet.write(i + row,10,dict["LOCALIDAD"],style_content_table_format)
            sheet.write(i + row,11,dict["AREA/DEPARTAMENTO"],style_content_table_format)
            sheet.write(i + row,12,dict["CARGO/PUESTO DE TRABAJO"],style_content_table_format)
            sheet.write(i + row,13,dict["AFP"],style_content_table_format)
            sheet.write(i + row,14,dict["TIPO COMISION AFP"],style_content_table_format)
            sheet.write(i + row,15,dict["CUSPP"],style_content_table_format)
            sheet.write(i + row,16,dict["BANCO HABERES"],style_content_table_format)
            sheet.write(i + row,17,dict["CUENTA HABERES"],style_content_table_format)
            sheet.write(i + row,18,dict["FECHA INGRESO"],style_date_content_table_format)
            sheet.write(i + row,19,dict["FECHA CESE"],style_date_content_table_format)
            sheet.write(i + row,20,dict["SISTEMA DE SALUD"],style_content_table_format)
            sheet.write(i + row,21,dict["SALARIO BASICO"],column_num_table_format)

            for ind,col_name in enumerate(dias_columns):
                if col_name in dict:
                    sheet.write(i + row,22+ind,dict[col_name],style_content_table_format)
                else :
                    sheet.write(i + row,22+ind,0,style_content_table_format)
            

            for ind,col_name in enumerate(inc_columns):
                if col_name in dict:
                    sheet.write(i + row,22+len_dias_columns+ind,dict[col_name],column_num_table_format)
                else :
                    sheet.write(i + row,22+len_dias_columns+ind,0,column_num_table_format)
            sheet.write(i + row,22+len_dias_columns+len_inc_columns,dict["TOTAL INGRESO"],column_num_table_format)

            for ind,col_name in enumerate(ded_columns):
                if col_name in dict:
                    sheet.write(i + row,23+len_dias_columns+ind+len_inc_columns,dict[col_name],column_num_table_format)
                else :
                    sheet.write(i + row,23+len_dias_columns+ind+len_inc_columns,0,column_num_table_format)
            sheet.write(i + row,23+len_dias_columns+len_inc_columns+len_ded_columns,dict["TOTAL DEDUCCION"],column_num_table_format)


            for ind,col_name in enumerate(apo_columns):
                if col_name in dict:
                    sheet.write(i + row,24+len_dias_columns+ind+len_inc_columns+len_ded_columns,dict[col_name],column_num_table_format)
                else :
                    sheet.write(i + row,24+len_dias_columns+ind+len_inc_columns+len_ded_columns,0,column_num_table_format)
            sheet.write(i + row,24+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns,dict["TOTAL APORTACIONES"],column_num_table_format)

            sheet.write(i + row,25+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns,dict["NETO"],column_num_table_format)
            

            tamnio = len(data)
            sheet.write(row + tamnio,0,"TOTAL",column_total_table_format)
            for i in range(21,26+len_dias_columns+len_inc_columns+len_ded_columns+len_apo_columns):
                sheet.write(row + tamnio,i,"=SUM({}{}:{}{})".format(self.getColumnName(i+1),
                                                                    row+1,
                                                                    self.getColumnName(i+1),
                                                                    row + tamnio),column_total_table_format)
            # sheet.write(i + row,27,dict["REGIMEN"],column_num_table_format)
        return wb

    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })
        data_pay = self.data["pay"]
        data_lbs = self.data["lbs"]
        wb = self.printf(wb,data_pay,"NOMINA")
        wb =  self.printf(wb,data_lbs,"LIQUIDACION")
        wb.close()
        output.seek(0)
        return output.read()
