from borb.pdf import Document, Page, SingleColumnLayout, Paragraph, PDF
from borb.pdf.canvas.layout.table.table import Table, TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from datetime import date
import os
import models


# -------------------------------------------------------------------
# Función auxiliar para evitar sobrescribir archivos
# -------------------------------------------------------------------
def guardar_pdf(pdf, nombre_archivo):
    ruta_pdf = os.path.join("pdf", nombre_archivo)
    os.makedirs("pdf", exist_ok=True)

    # ⚠️ Si el archivo ya existe, no se vuelve a generar
    if os.path.exists(ruta_pdf):
        print(f"📄 El PDF ya existe: {ruta_pdf}")
        return nombre_archivo

    with open(ruta_pdf, "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)
    print(f"✅ PDF generado: {ruta_pdf}")
    return nombre_archivo


# -------------------------------------------------------------------
# REPORTE 7 - TURNOS CANCELADOS
# -------------------------------------------------------------------
def generar_pdf_turnos_cancelados(turnos: list[models.Turno], anio: int, mes: str, cantidad: int):
    pdf = Document()
    page = Page()
    pdf.add_page(page)
    layout = SingleColumnLayout(page)

    layout.add(Paragraph(f"Reporte de Turnos Cancelados - {mes.capitalize()} {anio}",
                         font_size=18, font="Helvetica-Bold"))
    layout.add(Paragraph(f"Cantidad total de turnos cancelados: {cantidad}", font_size=12))
    layout.add(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", font_size=10))

    # Tabla
    table = FixedColumnWidthTable(number_of_rows=len(turnos) + 1, number_of_columns=4)
    headers = ["Fecha", "Hora", "DNI", "Nombre"]

    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    for t in turnos:
        table.add(Paragraph(t.fecha.strftime("%d/%m/%Y")))
        table.add(Paragraph(t.hora.strftime("%H:%M")))
        table.add(Paragraph(str(t.persona.dni)))
        table.add(Paragraph(f"{t.persona.apellido}, {t.persona.nombre}"))

    layout.add(table)

    nombre_archivo = f"reporte_cancelados_{mes}_{anio}.pdf"
    return guardar_pdf(pdf, nombre_archivo)


# -------------------------------------------------------------------
# REPORTE 5 - TURNOS CONFIRMADOS
# -------------------------------------------------------------------
def generar_pdf_turnos_confirmados(turnos: list[models.Turno], anio: int, mes: str, cantidad: int):
    pdf = Document()
    page = Page()
    pdf.add_page(page)
    layout = SingleColumnLayout(page)

    layout.add(Paragraph(f"Reporte de Turnos Confirmados - {mes.capitalize()} {anio}",
                         font_size=18, font="Helvetica-Bold"))
    layout.add(Paragraph(f"Cantidad total de turnos confirmados: {cantidad}", font_size=12))
    layout.add(Paragraph(f"Generado el {date.today().strftime('%d/%m/%Y')}", font_size=10))

    # Tabla
    table = FixedColumnWidthTable(number_of_rows=len(turnos) + 1, number_of_columns=4)
    headers = ["Fecha", "Hora", "DNI", "Nombre"]

    for h in headers:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold")))

    for t in turnos:
        table.add(Paragraph(t.fecha.strftime("%d/%m/%Y")))
        table.add(Paragraph(t.hora.strftime("%H:%M")))
        table.add(Paragraph(str(t.persona.dni)))
        table.add(Paragraph(f"{t.persona.apellido}, {t.persona.nombre}"))

    layout.add(table)

    nombre_archivo = f"reporte_confirmados_{mes}_{anio}.pdf"
    return guardar_pdf(pdf, nombre_archivo)
