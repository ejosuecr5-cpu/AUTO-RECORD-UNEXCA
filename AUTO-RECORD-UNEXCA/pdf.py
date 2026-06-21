from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf(cedula, datos_estudiante):
    """
    Genera el expediente académico en PDF.
    Retorna el nombre del archivo generado.
    Lanza Exception si falla la construcción del PDF.
    """
    nombre_archivo = f"expediente_{cedula}.pdf"

    doc = SimpleDocTemplate(
        nombre_archivo,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    story = []

    styles = getSampleStyleSheet()
    style_titulo    = ParagraphStyle(name='T1', fontName='Helvetica-Bold', fontSize=16, leading=20, alignment=1, spaceAfter=15)
    style_subtitulo = ParagraphStyle(name='T2', fontName='Helvetica-Bold', fontSize=12, leading=16, spaceAfter=10)
    style_texto     = styles['Normal']

    story.append(Paragraph("UNIVERSIDAD NACIONAL EXPERIMENTAL DE LA GRAN CARACAS (UNEXCA)", style_titulo))
    story.append(Paragraph("EXPEDIENTE ACADÉMICO DE PREGRADO", ParagraphStyle(name='Sub', fontName='Helvetica', fontSize=13, alignment=1, spaceAfter=20)))
    story.append(Spacer(1, 10))

    pers = datos_estudiante["datos_personales"]
    story.append(Paragraph("<b>Datos del Alumno:</b>", style_subtitulo))
    story.append(Paragraph(f"<b>Nombre Completo:</b> {pers['nombre']} {pers['apellido']}", style_texto))
    story.append(Paragraph(f"<b>Cédula de Identidad:</b> {cedula}", style_texto))
    story.append(Paragraph(f"<b>Ubicación Académica:</b> {pers['trayecto']} - {pers['periodo']}", style_texto))
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Historial Académico:</b>", style_subtitulo))
    tabla_datos = [["Código", "Unidad Curricular", "Nota", "Estado"]]
    for uc in datos_estudiante["historial_academico"]:
        tabla_datos.append([uc["codigo"], uc["unidad_curricular"], str(uc["nota"]), uc["estado"]])

    tabla_historial = Table(tabla_datos, colWidths=[70, 260, 60, 90])
    tabla_historial.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN',      (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN',      (2, 0), (2, -1), 'CENTER'),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f9f9f9")),
        ('GRID',       (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING',    (0, 0), (-1, -1), 6),
    ]))

    story.append(tabla_historial)
    doc.build(story)

    return nombre_archivo
