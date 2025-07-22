from io import BytesIO
import xlsxwriter


class LiquidationsExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj


    def get_content(self):
        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        sheet = wb.add_worksheet('Utilidades')

        row = 10
        sheet.autofilter('A'+str(row)+':T'+str(row))

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
        column_content_table_format_top = wb.add_format({
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
            'num_format': 'dd/mm/yy',}
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
        sheet.set_column('F:T', 12)
        

        """
            PRINT COLUMNS
        """
        cols = self.data[0].keys()
        for j,col in enumerate(cols):
            sheet.write(row-1,j,col,column_content_table_format)

        """
            PRINT DATA TABLE
        """
        for i,dict in enumerate(self.data):
            for col,value in enumerate(dict.values()):
                # COLUMNAS DE FECHAS
                if col in [3,4]:
                    sheet.write(i + row,col,value,style_date_content_table_format)

                else :
                    sheet.write(i + row,col,value,style_content_table_format)
                #sheet.write(i + row,col,value,style_content_table_format)

        wb.close()
        output.seek(0)
        return output.read()


