from io import BytesIO
import xlsxwriter


class GratiExcelReport(object):
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
        wb = xlsxwriter.Workbook(output, {'default_date_format': 'dd/mm/yyyy'})

        sheet = wb.add_worksheet('Prov. Gratificación')

        row = 8
        sheet.autofilter('A'+str(row)+':AN'+str(row))

        column_content_table_format = wb.add_format({
            'size': 10, #Tamaño de la fuente
            'bold': 1, 
            'fg_color': '#BFBFC0',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,
        })

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
            'num_format': 'dd/mm/yyyy',
        })
        
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
        
        sheet.set_column(0,3, 10)
        sheet.set_column(4,11, 20)
        sheet.set_column(12,32+len_prom_columns, 15)
        # sheet.set_row(row - 2,30)
        sheet.set_row(row - 1,40)

        # sheet.merge_range(row - 2,0,row - 2,15, 'DATOS GENERALES', column_content_table_format_top)
        sheet.write(row - 1,0,"ID",column_chiki)
        sheet.write(row - 1,1,"CÓDIGO",column_chiki)
        sheet.write(row - 1,2,"TIPO DOC.",column_chiki)
        sheet.write(row - 1,3,"DOCUMENTO",column_content_table_format)
        sheet.write(row - 1,4,"PRIMER APELLIDO",column_content_table_format)
        sheet.write(row - 1,5,"SEGUNDO APELLIDO",column_content_table_format)
        sheet.write(row - 1,6,"PRIMER NOMBRE",column_content_table_format)
        sheet.write(row - 1,7,"SEGUNDO NOMBRE",column_content_table_format)
        sheet.write(row - 1,8,"CENTRO DE COSTO",column_content_table_format)
        sheet.write(row - 1,9,"CUENTA ANALÍTICA",column_content_table_format)
        sheet.write(row - 1,10,"ZONAL",column_chiki)
        sheet.write(row - 1,11,"AREA/DEPARTAMENTO",column_content_table_format)
        sheet.write(row - 1,12,"CARGO",column_content_table_format)
        sheet.write(row - 1,13,"REGIMEN",column_content_table_format)
        sheet.write(row - 1,14,"F INGRESO",column_chiki)
        sheet.write(row - 1,15,"F CESE",column_chiki)
        sheet.write(row - 1,16,"BÁSICO",column_content_table_format)
        sheet.write(row - 1,17,"ASIG. FAMILIAR",column_content_table_format)
        sheet.write(row - 1,18,"PROM. VARIABLES",column_content_table_format)
        for ind,col_name in enumerate(prom_columns):
                sheet.write(row - 1,19+ind,col_name,column_content_table_format)
        sheet.write(row - 1,19+len_prom_columns,"BASE COMPUTABLE",column_content_table_format)
        
        # sheet.merge_range(row - 2, 20+len_prom_columns,row - 2, 21+len_prom_columns, 'DIAS LABORADOS O NO LABORADOS', column_content_table_format_top)
        sheet.write(row - 1,20+len_prom_columns,"DIAS NO LABORADOS",column_content_table_format)
        sheet.write(row - 1,21+len_prom_columns,"DIAS LABORADOS MES",column_content_table_format)
        sheet.write(row - 1,22+len_prom_columns,"DIAS ACUMULADOS",column_content_table_format)

        # sheet.merge_range(row - 2, 22+len_prom_columns,row - 2, 23+len_prom_columns, 'PROVISION', column_content_table_format_top)
        sheet.write(row - 1,23+len_prom_columns,"PROVISIÓN MES",column_content_table_format)
        sheet.write(row - 1,24+len_prom_columns,"PROVISIÓN ACUMULADA",column_content_table_format)
        sheet.write(row - 1,25+len_prom_columns,"PROVISIÓN ACTUAL",column_content_table_format)
        # sheet.merge_range(row - 2, 24+len_prom_columns,row - 2, 25+len_prom_columns, 'DESCUENTOS', column_content_table_format_top)
        sheet.write(row - 1,26+len_prom_columns,"LBS",column_content_table_format)
        sheet.write(row - 1,27+len_prom_columns,"BONIFICACIÓN MES",column_content_table_format)
        sheet.write(row - 1,28+len_prom_columns,"BONIFICACIÓN ACUMULADA",column_content_table_format)
        sheet.write(row - 1,29+len_prom_columns,"BONIFICACIÓN ACTUAL",column_content_table_format)
        sheet.write(row - 1,30+len_prom_columns,"BONIFICACIÓN LBS",column_content_table_format) 
        sheet.write(row - 1,31+len_prom_columns,"PROVISIÓN TOTAL MES",column_content_table_format) 
        """
            PRINT DATA TABLE
        """
        
        for i,dict in enumerate(self.data):
            sheet.write(i + row,0,dict["ID"],style_content_table_format)
            sheet.write(i + row,1,dict["Cod."],style_content_table_format)
            sheet.write(i + row,2,dict["Tipo_doc"],style_content_table_format)
            sheet.write(i + row,3,dict["documento"],style_content_table_format)
            sheet.write(i + row,4,dict["PRIMER APELLIDO"],style_content_table_format)
            sheet.write(i + row,5,dict["SEGUNDO APELLIDO"],style_content_table_format)
            sheet.write(i + row,6,dict["PRIMER NOMBRE"],style_content_table_format)
            sheet.write(i + row,7,dict["SEGUNDO NOMBRE"],style_content_table_format)
            sheet.write(i + row,8,dict["centro de costo"],style_content_table_format)
            sheet.write(i + row,9,dict["cuenta analitica"],style_content_table_format)
            sheet.write(i + row,10,dict["zonal"],style_content_table_format)
            sheet.write(i + row,11,dict["area"],style_content_table_format)
            sheet.write(i + row,12,dict["cargo"],style_content_table_format)
            sheet.write(i + row,13,dict["regime"],style_content_table_format)
            sheet.write(i + row,14,dict["fecha de ingreso"],style_date_content_table_format)
            sheet.write(i + row,15,dict["FECHA CESE"],style_date_content_table_format)
            sheet.write(i + row,16,dict["Salario Basico"],style_content_num_table_format)
            sheet.write(i + row,17,dict["Asig Familiar"],style_content_num_table_format)
            sheet.write(i + row,18,dict["Sumatorio Promedios"],style_content_num_table_format)

            for ind,col_name in enumerate(prom_columns):
                if col_name in dict:
                    sheet.write(i + row,19+ind,dict[col_name],style_content_num_table_format)
                else :
                    sheet.write(i + row,19+ind,0,style_content_num_table_format)

            sheet.write(i + row,19+len_prom_columns,dict["Total Base"],style_content_num_table_format)
            sheet.write(i + row,20+len_prom_columns,dict["Dias No Laborados"],style_content_num_table_format)
            sheet.write(i + row,21+len_prom_columns,dict["Dias Laborados"],style_content_num_table_format)
            sheet.write(i + row,22+len_prom_columns,dict["Dias Acumulados Ant"],style_content_num_table_format)
            sheet.write(i + row,23+len_prom_columns,dict["Provision Mes"],style_content_num_table_format)
            sheet.write(i + row,24+len_prom_columns,dict["Provision Ant"],style_content_num_table_format)
            sheet.write(i + row,25+len_prom_columns,dict["Total Acum"],style_content_num_table_format)
            sheet.write(i + row,26+len_prom_columns,dict["lbs"],style_content_num_table_format) ,
            sheet.write(i + row,27+len_prom_columns,dict["bonificacion mes"],style_content_num_table_format)
            sheet.write(i + row,28+len_prom_columns,dict["bonificacion Ant"],style_content_num_table_format)
            sheet.write(i + row,29+len_prom_columns,dict["bonificacion Acum"],style_content_num_table_format)
            sheet.write(i + row,30+len_prom_columns,dict["bonificacion LBS"],style_content_num_table_format)
            sheet.write(i + row,31+len_prom_columns,dict["Total Acum"] + dict["bonificacion Acum"] ,style_content_num_table_format)

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
        sheet.write(row + tamnio,15,"TOTAL",column_total_table_format)
        for i in range(16,32+len_prom_columns):
            sheet.write(row + tamnio,i,"=SUM({}{}:{}{})".format(self.getColumnName(i+1),
                                                                row+1,
                                                                self.getColumnName(i+1),
                                                                row + tamnio),column_total_table_format)


        wb.close()
        output.seek(0)
        return output.read()
