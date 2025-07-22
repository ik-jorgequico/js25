from io import BytesIO
import xlsxwriter


class VacationCalculateExcelReport(object):

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
        sheet.autofilter('A'+str(row)+':L'+str(row))

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

        style_content_table_format_float = wb.add_format({
            'size': 8,
            'num_format': '#,##0.00'

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
        sheet.write(5,1,self.obj.date_from_eval.strftime("%b %Y").upper(),f2)

        """
            PRINT COLUMNS
        """
        asig_columns = []
        prom_columns = []
        ded_columns = []

        for dictionary in self.data:
            asig_columns += [i for i in list(dictionary.keys()) if i[:4]=="ASIG"]
            prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
            ded_columns += [i for i in list(dictionary.keys()) if i[:4]=="Ded_"]
        
        len_asig_columns = len(asig_columns) 

        prom_columns = list(set(prom_columns))
        prom_columns.sort()
        len_prom_columns = len(prom_columns) 
        
        ded_columns = list(set(ded_columns))
        ded_columns.sort()
        len_ded_columns = len(ded_columns) 

        sheet.set_column(0,15, 20)
        sheet.set_column(15,26+len_prom_columns+len_asig_columns, 15)
        sheet.set_row(row - 2,30)
        sheet.set_row(row - 1,40)

        sheet.merge_range(row - 2,0,row - 2,16, 'DATOS GENERALES', column_content_table_format_top)
        sheet.write(row - 1,0,"ID",column_content_table_format)
        sheet.write(row - 1,1,"CODIGO",column_content_table_format)
        sheet.write(row - 1,2,"TIPO DOCUMENTO",column_content_table_format)
        sheet.write(row - 1,3,"NUM DOCUMENTO",column_content_table_format)
        sheet.write(row - 1,4,"PRIMER APELLIDO",column_content_table_format)
        sheet.write(row - 1,5,"SEGUNDO APELLIDO",column_content_table_format)
        sheet.write(row - 1,6,"PRIMER NOMBRE",column_content_table_format)
        sheet.write(row - 1,7,"SEGUNDO NOMBRE",column_content_table_format)
        sheet.write(row - 1,8,"CENTRO DE COSTO",column_content_table_format)
        sheet.write(row - 1,9,"LOCALIDAD",column_content_table_format)
        sheet.write(row - 1,10,"AREA",column_content_table_format)
        sheet.write(row - 1,11,"CARGO",column_content_table_format)
        sheet.write(row - 1,12,"BANCO HABERES",column_content_table_format)
        sheet.write(row - 1,13,"CUENTA HABERES",column_content_table_format)
        sheet.write(row - 1,14,"FECHA INGRESO",column_content_table_format)
        sheet.write(row - 1,15,"FECHA CESE",column_content_table_format)
        sheet.write(row - 1,16,"¿COMPRA DE VAC?",column_content_table_format)
        sheet.merge_range(row - 2,17,row - 2,19+len_asig_columns+len_prom_columns, 'BASE CALCULO', column_content_table_format_top)
        sheet.write(row - 1,17,"DIAS VAC",column_content_table_format)
        sheet.write(row - 1,18,"SUELDO",column_content_table_format)
        for ind,col_name in enumerate(asig_columns):
            sheet.write(row - 1,19+ind,col_name,column_content_table_format)
        for ind,col_name in enumerate(prom_columns):
            sheet.write(row - 1,19+ind+len_asig_columns,col_name,column_content_table_format)
        sheet.write(row - 1,19+len_asig_columns+len_prom_columns,"BASE IMPONIBLE",column_content_table_format)
        sheet.write(row - 2,20+len_asig_columns+len_prom_columns,"INGRESOS",column_content_table_format_top)
        sheet.write(row - 1,20+len_asig_columns+len_prom_columns,"BRUTO",column_content_table_format)
        sheet.write(row - 1,21+len_asig_columns+len_prom_columns,"TOTAL INGRESO AFECTO",column_content_table_format)

        for i,dict in enumerate(self.data):
            sheet.write(i + row,0,dict["ID"],style_content_table_format)
            sheet.write(i + row,1,dict["CODIGO"],style_content_table_format)
            sheet.write(i + row,2,dict["TIPO DOCUMENTO"],style_content_table_format)
            sheet.write(i + row,3,dict["NUM DOCUMENTO"],style_content_table_format)
            sheet.write(i + row,4,dict["PRIMER APELLIDO"],style_content_table_format)
            sheet.write(i + row,5,dict["SEGUNDO APELLIDO"],style_content_table_format)
            sheet.write(i + row,6,dict["PRIMER NOMBRE"],style_content_table_format)
            sheet.write(i + row,7,dict["SEGUNDO NOMBRE"],style_content_table_format)
            sheet.write(i + row,8,dict["CENTRO DE COSTO"],style_content_table_format)
            sheet.write(i + row,9,dict["LOCALIDAD"],style_content_table_format)
            sheet.write(i + row,10,dict["AREA/DEPARTAMENTO"],style_content_table_format)
            sheet.write(i + row,11,dict["CARGO/PUESTO DE TRABAJO"],style_content_table_format)
            sheet.write(i + row,12,dict["BANCO HABERES"],style_content_table_format)
            sheet.write(i + row,13,dict["CUENTA HABERES"],style_content_table_format)
            sheet.write(i + row,14,dict["FECHA INGRESO"],style_date_content_table_format)
            sheet.write(i + row,15,dict["FECHA CESE"],style_date_content_table_format)
            sheet.write(i + row,16,dict["ES COMPRA VAC?"],style_content_table_format)
            sheet.write(i + row,17,dict["DIAS VACACIONES"],style_content_table_format)
            sheet.write(i + row,18,dict["SUELDO"],style_content_table_format_float)
            
            for ind,col_name in enumerate(asig_columns):
                if col_name in dict:
                    sheet.write(i + row,19+ind,dict[col_name],style_content_table_format_float)
                else :
                    sheet.write(i + row,19+ind,0,style_content_table_format_float)

            for ind,col_name in enumerate(prom_columns):
                if col_name in dict:
                    sheet.write(i + row,19+ind+len_asig_columns,dict[col_name],style_content_table_format_float)
                else :
                    sheet.write(i + row,19+ind+len_asig_columns,0,style_content_table_format_float)

            sheet.write(i + row,19+len_asig_columns+len_prom_columns,dict["BASE IMPONIBLE"],style_content_table_format_float)
            sheet.write(i + row,20+len_asig_columns+len_prom_columns,dict["BRUTO"],style_content_table_format_float)
            sheet.write(i + row,21+len_asig_columns+len_prom_columns,dict["TOTAL INGRESO AFECTO"],style_content_table_format_float)

        tamnio = len(self.data)
        column_total_table_format = wb.add_format({
            'size': 8,
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border':1,
            'num_format': '#,##0.00'

        })
        sheet.write(row + tamnio,0,"TOTAL",column_total_table_format)
        for i in range(17,22+len_prom_columns+len_asig_columns):
            sheet.write(row + tamnio,i,"=SUM({}{}:{}{})".format(self.getColumnName(i+1),
                                                                11,
                                                                self.getColumnName(i+1),
                                                                row + tamnio),column_total_table_format)
        wb.close()
        output.seek(0)
        return output.read()
