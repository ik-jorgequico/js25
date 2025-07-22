from io import BytesIO
import xlsxwriter


class PayrollAnnualizerExcelReport(object):

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

    def get_content(self):

        output = BytesIO()
        wb = xlsxwriter.Workbook(output, {
            'default_date_format': 'dd/mm/yyyy'
        })

        for col in self.data:
            if col != "employee":
                sheet = wb.add_worksheet(str(col))
                style_column_table_format = wb.add_format({
                    'size': 10,
                    'bold': 1,
                    'fg_color': '#BFBFC0',
                    'font_color': 'black',
                    'text_wrap': True,
                    'text_h_align': 2,
                    'num_format': '#,##0.00',
                    'border': 1,
                })

                style_data_table_format = wb.add_format({
                    'size': 10,
                    'text_wrap': True,
                    'text_h_align': 2,
                    'text_v_align': 2,
                    'num_format': '#,##0.00',
                    'border': 1,

                })

                style_type_table_format = wb.add_format({
                    'size': 10,
                    'bold': 1,
                    'font_color': 'black',
                    'text_wrap': True,
                    'text_h_align': 2,
                    'text_v_align': 2,

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
                    'num_format': 'dd/mm/yy', }
                )

                LIMIT = 1
                sheet.write(
                    LIMIT, 0, "REPORTE DE REMUNERACIONES - RETRIBUCIONES ANUALIZADA PERSONAL:", f1)
                sheet.write(LIMIT + 1, 0, "Año "+ str(col) , f1)

                LIMIT = 4
                
                sheet.write(LIMIT, 0, "Nombre:", f1)
                sheet.write(LIMIT, 1, self.data["employee"]["Nombre"], f2)

                sheet.write(LIMIT + 1, 0, "Doc:", f1)
                sheet.write(LIMIT + 1, 1, self.data["employee"]["Num Documento"], f2)

                sheet.write(LIMIT + 2, 0, "Centro de Costo:", f1)
                sheet.write(LIMIT + 2, 1, self.data["employee"]["Centro de Costo"], f2)

                sheet.write(LIMIT + 3, 0, "Puesto:", f1)
                sheet.write(LIMIT + 3, 1, self.data["employee"]["Puesto"], f2)

                sheet.write(LIMIT + 4, 0, "Zonal:", f1)
                sheet.write(LIMIT + 4, 1, self.data["employee"]["Zonal"], f2)


                sheet.write(LIMIT, 4, "Codigo:", f1)
                sheet.write(LIMIT, 5, self.data["employee"]["Codigo"], f2)

                sheet.write(LIMIT + 1, 4, "Estado:", f1)
                sheet.write(LIMIT + 1, 5, self.data["employee"]["Estado"], f2)

                sheet.write(LIMIT + 2, 4, "Fecha Ingreso:", f1)
                sheet.write(LIMIT + 2, 5, self.data["employee"]["Fecha Ingreso"], f2)

                sheet.write(LIMIT + 3, 4, "Fecha Cese:", f1)
                sheet.write(LIMIT + 3, 5, self.data["employee"]["Fecha Cese"], f2)



                sheet.set_column('A:A', 13)
                
                sheet.set_column('B:Z', 10)
                """
                    PRINT COLUMNS
                """
                LIMIT = 12
                spaces_type = 0
                for type in self.data[col]:
                    # IMPRIME TABLA
                    for j, month in enumerate(self.data[col][type]):
                        len_spaces_month = len(
                            self.data[col][type][month].keys())
                        if len_spaces_month != 0:
                            # IMPRIME TIPO INGRESO, DEDUCCION O APORTACION
                            sheet.write(LIMIT + spaces_type - 1, 0,
                                        type, style_type_table_format)
                            # IMPRIME MESES
                            sheet.write(LIMIT + spaces_type, j+1,
                                        month, style_column_table_format)
                            for cont, description in enumerate(self.data[col][type][month]):
                                # IMPRIME CONCEPTOS
                                sheet.write(LIMIT + spaces_type + cont + 1,
                                            0, description, style_column_table_format)
                                # IMPRIME MONTOS
                                sheet.write(LIMIT + spaces_type + cont + 1, j+1,
                                            self.data[col][type][month][description], style_data_table_format)
                                # IMPRIME TOTAL
                                if j+2 == 13:
                                    sheet.write(LIMIT + spaces_type + cont + 1,
                                                13,
                                                '=SUM({}{}:{}{})'.format(self.getColumnName(2),
                                                                         LIMIT + spaces_type + cont + 2,
                                                                         self.getColumnName(13),
                                                                         LIMIT + spaces_type + cont + 2),
                                                style_column_table_format)

                            # IMPRIME TOTAL
                            sheet.write(LIMIT + spaces_type + len_spaces_month +
                                        1, 0, "TOTAL", style_column_table_format)
                            sheet.write(LIMIT + spaces_type, 13,
                                        "TOTAL", style_column_table_format)
                            sheet.write(LIMIT + spaces_type + len_spaces_month + 1,
                                        j+1,
                                        '=SUM({}{}:{}{})'.format(self.getColumnName(j+2),
                                                                 int(LIMIT +
                                                                     spaces_type + 2),
                                                                 self.getColumnName(
                                                                     j+2),
                                                                 int(LIMIT + spaces_type + len_spaces_month + 1)),
                                        style_column_table_format)
                            if j+2 == 13:
                        
                                sheet.write(LIMIT + spaces_type + len_spaces_month + 1,
                                            13,
                                            '=SUM({}{}:{}{})'.format(self.getColumnName(2),
                                                                        LIMIT + spaces_type + len_spaces_month + 2,
                                                                        self.getColumnName(13),
                                                                        LIMIT + spaces_type + len_spaces_month + 2),
                                                style_column_table_format)
                    spaces_type += len_spaces_month + 4

        wb.close()
        output.seek(0)
        return output.read()
