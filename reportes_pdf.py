from borb.pdf import Document, Page, SingleColumnLayout, Paragraph, PDF
from borb.pdf.canvas.layout.table.table import TableCell
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.image.image import Image
from borb.pdf.canvas.layout.layout_element import Alignment
from borb.pdf.canvas.layout.table.flexible_column_width_table import FlexibleColumnWidthTable
from datetime import date
from pathlib import Path
import os
import qrcode
import models

# -------------------------------------------------------------------
# Ruta del logo (ajustada a carpeta static)
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "static" / "UnlaLogo_.png"

# -------------------------------------------------------------------
# Función auxiliar para sobrescribir siempre el archivo
# -------------------------------------------------------------------
def guardar_pdf(pdf, nombre_archivo):
    ruta_pdf = os.path.join("pdf", nombre_archivo)
    os.makedirs("pdf", exist_ok=True)

    with open(ruta_pdf, "wb") as pdf_file_handle:
        PDF.dumps(pdf_file_handle, pdf)
    print(f"✅ PDF generado: {ruta_pdf}")
    return nombre_archivo


# -------------------------------------------------------------------
# REPORTE 7 - TURNOS CANCELADOS
# -------------------------------------------------------------------
def generar_pdf_turnos_cancelados(agrupado: dict, anio: int, mes: str):
    pdf = Document()
    page = Page()
    pdf.add_page(page)
    layout = SingleColumnLayout(page)

    # Logo centrado
    if LOGO_PATH.exists():
        layout.add(Image(LOGO_PATH, width=64, height=64, horizontal_alignment=Alignment.CENTERED))
    else:
        print(f"[WARN] Logo no encontrado en: {LOGO_PATH}")

    # Título centrado
    layout.add(Paragraph(f"Reporte de Turnos Cancelados - {mes.capitalize()} {anio}",
                         font_size=18, font="Helvetica-Bold",
                         horizontal_alignment=Alignment.CENTERED))

    total = sum(len(turnos) for turnos in agrupado.values())
    layout.add(Paragraph(f"Cantidad total de turnos cancelados: {total}", font_size=12))

    # 👉 recorrer personas
    for persona_id, turnos in agrupado.items():
        persona = turnos[0].persona

        layout.add(Paragraph(
            f"{persona.apellido}, {persona.nombre} (DNI: {persona.dni})",
            font_size=14,
            font="Helvetica-Bold"
        ))

        table = FixedColumnWidthTable(number_of_rows=len(turnos) + 1, number_of_columns=2)

        # encabezados con fondo gris
        table.add(TableCell(Paragraph("Fecha", font="Helvetica-Bold"), background_color=HexColor("E0E0E0")))
        table.add(TableCell(Paragraph("Hora", font="Helvetica-Bold"), background_color=HexColor("E0E0E0")))

        # turnos con filas alternadas
        for i, t in enumerate(turnos):
            bg_color = HexColor("FFFFFF") if i % 2 == 0 else HexColor("F5F5F5")
            table.add(TableCell(Paragraph(t.fecha.strftime("%d/%m/%Y")), background_color=bg_color))
            table.add(TableCell(Paragraph(t.hora.strftime("%H:%M")), background_color=bg_color))

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

    # Logo
    if LOGO_PATH.exists():
        layout.add(Image(LOGO_PATH, width=64, height=64, horizontal_alignment=Alignment.CENTERED))

    # 👉 QR general al sistema
    qr_img = qrcode.make("http://127.0.0.1:8000/turnos")
    qr_path = "static/qr_general.png"
    qr_img.save(qr_path)
    layout.add(Image(Path(qr_path), width=64, height=64, horizontal_alignment=Alignment.CENTERED))

    # Título
    layout.add(Paragraph(f"Reporte de Turnos Confirmados - {mes.capitalize()} {anio}",
                         font_size=18, font="Helvetica-Bold",
                         horizontal_alignment=Alignment.CENTERED))

    layout.add(Paragraph(f"Cantidad total de turnos confirmados: {cantidad}", font_size=12))

    # Agrupar turnos por persona
    agrupado = {}
    for t in turnos:
        pid = t.persona.id
        agrupado.setdefault(pid, []).append(t)

    # Recorrer personas
    for persona_id, lista_turnos in agrupado.items():
        persona = lista_turnos[0].persona

        layout.add(Paragraph(
            f"{persona.apellido}, {persona.nombre} (DNI: {persona.dni})",
            font_size=14,
            font="Helvetica-Bold"
        ))

        # 👉 Tabla de turnos con QR por turno
        table = FixedColumnWidthTable(number_of_rows=len(lista_turnos) + 1, number_of_columns=3)

        # encabezados
        encabezados = ["Fecha", "Hora", "QR"]
        for h in encabezados:
            table.add(TableCell(Paragraph(h, font="Helvetica-Bold"), background_color=HexColor("E0E0E0")))

        # filas con QR único por turno
        for i, t in enumerate(lista_turnos):
            bg_color = HexColor("FFFFFF") if i % 2 == 0 else HexColor("F5F5F5")

            # fecha y hora
            table.add(TableCell(Paragraph(t.fecha.strftime("%d/%m/%Y")), background_color=bg_color))
            table.add(TableCell(Paragraph(t.hora.strftime("%H:%M")), background_color=bg_color))

            # QR único por turno
            qr_link = f"http://127.0.0.1:8000/reportes/qr/confirmar/{t.id}"
            qr_img = qrcode.make(qr_link)
            qr_path = f"static/qr_turno_{t.id}.png"
            qr_img.save(qr_path)

            table.add(TableCell(Image(Path(qr_path), width=48, height=48), background_color=bg_color))

        layout.add(table)

    nombre_archivo = f"reporte_confirmados_{mes}_{anio}.pdf"
    return guardar_pdf(pdf, nombre_archivo)



# -------------------------------------------------------------------
# REPORTE - LISTADO DE PERSONAS
# -------------------------------------------------------------------
def generar_pdf_personas(personas: list[models.Persona], titulo: str = "Listado de Personas"):
    pdf = Document()
    page = Page()
    pdf.add_page(page)
    layout = SingleColumnLayout(page)

    # Logo centrado
    if LOGO_PATH.exists():
        layout.add(Image(LOGO_PATH, width=64, height=64, horizontal_alignment=Alignment.CENTERED))

    # Título
    layout.add(Paragraph(titulo, font_size=18, font="Helvetica-Bold", horizontal_alignment=Alignment.CENTERED))
    layout.add(Paragraph(f"Cantidad total de personas: {len(personas)}", font_size=12))

    # 👉 Tabla con datos principales
    table = FixedColumnWidthTable(number_of_rows=len(personas) + 1, number_of_columns=4)

    # Encabezados
    encabezados = ["Apellido", "Nombre", "DNI", "Activo"]
    for h in encabezados:
        table.add(TableCell(Paragraph(h, font="Helvetica-Bold"), background_color=HexColor("E0E0E0")))

    # Filas alternadas
    for i, p in enumerate(personas):
        bg_color = HexColor("FFFFFF") if i % 2 == 0 else HexColor("F5F5F5")
        table.add(TableCell(Paragraph(p.apellido), background_color=bg_color))
        table.add(TableCell(Paragraph(p.nombre), background_color=bg_color))
        table.add(TableCell(Paragraph(str(p.dni)), background_color=bg_color))
        table.add(TableCell(Paragraph("Sí" if p.activo else "No"), background_color=bg_color))

    # 👉 Corregido: sin horizontal_alignment en layout.add()
    layout.add(table)

    # 👉 Emails como detalle debajo
    layout.add(Paragraph(" "))  # espacio
    layout.add(Paragraph("Detalles de contacto:", font_size=14, font="Helvetica-Bold"))

    for p in personas:
        email_text = p.email if p.email else "-"
        layout.add(Paragraph(f"{p.apellido}, {p.nombre} – Email: {email_text}", font_size=10))

    nombre_archivo = "reporte_personas_hibrido.pdf"
    return guardar_pdf(pdf, nombre_archivo)