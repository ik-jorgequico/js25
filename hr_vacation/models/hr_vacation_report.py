from io import BytesIO
import xlsxwriter


class VacationExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj


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
            'fg_color': '#ddebf7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,
            'border': 1,

        })
        column_content_table_format_title = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#ff9729',
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

        sheet.set_column('C:E', 20)
        sheet.set_column('F:H', 10)
        """
            PRINT COLUMNS
        """
        prom_columns = []
        for dictionary in self.data:
            prom_columns += [i for i in list(dictionary.keys()) if i[:5]=="Prom_"]
        prom_columns = list(set(prom_columns))
        prom_columns.sort()
        print(prom_columns)
        len_prom_columns = len(prom_columns) 

        
        sheet.set_row(row - 2,30)
        sheet.set_row(row - 1,40)

        sheet.merge_range(row - 2,0,row - 2,4, 'DATOS GENERALES', column_content_table_format_title)
        sheet.write(row - 1,0,"Cod.",column_content_table_format)
        sheet.write(row - 1,1,"Doc.",column_content_table_format)
        sheet.write(row - 1,2,"Apellidos y Nombres",column_content_table_format)
        sheet.write(row - 1,3,"Fecha Ingreso",column_content_table_format)
        sheet.write(row - 1,4,"Puesto",column_content_table_format)
        sheet.write(row - 1,5,"Periodo",column_content_table_format)
        sheet.write(row - 1,6,"Cantidad de Periodos",column_content_table_format)
        sheet.write(row - 1,7,"Dias Generados",column_content_table_format)
        sheet.write(row - 1,8,"Vacaciones Gozadas",column_content_table_format)
        sheet.write(row - 1,9,"Pendientes",column_content_table_format)
        sheet.write(row - 1,10,"Vacaciones Vencidas",column_content_table_format)
        sheet.write(row - 1,11,"Vacaciones Truncas",column_content_table_format)


        """
            PRINT DATA TABLE
        """
        
        for i,dict in enumerate(self.data):
            sheet.write(i + row,0,dict["Cod."],style_content_table_format)
            sheet.write(i + row,1,dict["Doc."],style_content_table_format)
            sheet.write(i + row,2,dict["Apellidos y Nombres"],style_content_table_format)
            sheet.write(i + row,3,dict["Fecha Ingreso"],style_date_content_table_format)
            sheet.write(i + row,4,dict["Puesto"],style_content_table_format)
            sheet.write(i + row,5,dict["Periodo"],style_content_table_format)
            sheet.write(i + row,6,dict["Cantidad de Periodos"],style_content_table_format)
            sheet.write(i + row,7,dict["Dias Generados"],style_content_table_format)
            sheet.write(i + row,8,dict["Vacaciones Gozadas"],style_content_table_format)
            sheet.write(i + row,9,dict["Pendientes"],style_content_table_format)
            sheet.write(i + row,10,dict["Vacaciones Vencidas"],style_content_table_format)
            sheet.write(i + row,11,dict["Vacaciones Truncas"],style_content_table_format)

        

        wb.close()
        output.seek(0)
        return output.read()
