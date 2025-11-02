from borb.pdf import Document, Page, SingleColumnLayout, Paragraph, PDF
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.table.table import Table, TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from decimal import Decimal
from datetime import date
import models

def generar_pdf_turnos_cancelados(turnos: list[models.Turno], anio: int, mes: str, cantidad: int):
    # Crear documento PDF
    pdf = Document()
    page = Page()
    pdf.add_page(page)

    layout = SingleColumnLayout(page)

    # Título
    layout.add(Paragraph(f"Reporte de Turnos Cancelados - {mes.capitalize()} {anio}", font_size=18, font="Helvetica-Bold"))
    layout.add(Paragraph(f"Cantidad total de turnos cancelados: {cantidad}", font_size=12))
    layout.add(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", font_size=10))

    # Tabla
    table = FixedColumnWidthTable(number_of_rows=len(turnos)+1, number_of_columns=4)

    # Encabezados
    headers = ["Fecha", "Hora", "DNI", "Nombre"]
    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    # Filas
    for t in turnos:
        table.add(Paragraph(t.fecha.strftime("%d/%m/%Y")))
        table.add(Paragraph(t.hora.strftime("%H:%M")))
        table.add(Paragraph(str(t.persona.dni)))
        table.add(Paragraph(f"{t.persona.apellido}, {t.persona.nombre}"))

    layout.add(table)

    # Guardar archivo
    nombre_archivo = f"reportecancelados{mes}_{anio}.pdf"
    with open(nombre_archivo, "wb") as pdf_file_handle:
         PDF.dumps(pdf_file_handle, pdf)
    return nombre_archivo