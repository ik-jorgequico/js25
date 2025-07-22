from io import BytesIO
import xlsxwriter


class LBSExcelReport(object):

    def __init__(self, data, obj):
        self.data = data
        self.obj = obj

    def get_filename(self):
        return 'LBS.xlsx'
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
        sheet.autofilter('A5:CA5')

        column_content_table_format = wb.add_format({
            'size': 10,
            'bold': 1,
            'fg_color': '#ddebf7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,

        })
        column_total_table_format = wb.add_format({
            'size': 10,
            'fg_color': '#ddebf7',
            'font_color': 'black',
            'text_wrap':True,
            'text_h_align' : 2,
            'text_v_align' : 2,

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

        sheet.write(1,0,"RAZON SOCIAL:",f1)
        sheet.write(1,1,self.obj.env.company.name,f2)
        sheet.write(2,0,"RUC:",f1)
        sheet.write(2,1,"",f2)
        if self.obj.env.company.vat:
            sheet.write(2,1,self.obj.env.company.vat,f2)

        sheet.set_column('A:D', 10)
        sheet.set_column('E:H', 20)
        sheet.set_column('I:P', 10)
        sheet.set_column('Q:Q',10,style_date_content_table_format)
        sheet.set_column('R:CA', 10)
        """
            PRINT COLUMNS
        """
        len_data = len(self.data)

        cols = self.data[0].keys()
        for j,col in enumerate(cols):
            sheet.write(4,j,col,column_content_table_format)
            if j == 0:
                sheet.write(4+len_data+1,j,"TOTAL",column_total_table_format)

            elif j > 18:
                sheet.write(4+len_data+1,j,"=SUM({}{}:{}{})".format(self.getColumnName(j+1),
                                                                    6,
                                                                    self.getColumnName(j+1),
                                                                    4+len_data+1),column_total_table_format)
            else:
                sheet.write(4+len_data+1,j,"",column_total_table_format)
                

        """
            PRINT DATA TABLE
        """
        row = 5
        for i,dict in enumerate(self.data):
            for col,value in enumerate(dict.values()):
                # COLUMNAS DE FECHAS
                if col in [17,18]:
                    sheet.write(i + row,col,value,style_date_content_table_format)

                else :
                    sheet.write(i + row,col,value,style_content_table_format)

        wb.close()
        output.seek(0)
        return output.read()
