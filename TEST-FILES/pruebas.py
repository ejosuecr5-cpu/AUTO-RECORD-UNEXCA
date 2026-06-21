
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime

def exportar_expediente_a_pdf(expediente_con_firma, archivo_salida="expediente.pdf"):
    expediente = expediente_con_firma["expediente"]
    firma = expediente_con_firma["firma_digital"]

    c = canvas.Canvas(archivo_salida, pagesize=letter)
    width, height = letter
    y = height - 50

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Expediente Académico")
    y -= 40

    # Datos personales
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Nombre: {expediente['nombre']}")
    y -= 20
    c.drawString(50, y, f"Cédula: {expediente['cedula']}")
    y -= 20
    c.drawString(50, y, f"Carrera: {expediente['carrera']}")
    y -= 20
    c.drawString(50, y, f"Expediente generado en: {expediente['creado_en']}")
    y -= 30

    # Sección de materias
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Historial académico:")
    y -= 20
    c.setFont("Helvetica", 12)
    materias = expediente.get("materias", [])
    if materias:
        for materia in materias:
            nombre_materia = materia.get('nombre', 'N/D')
            nota = materia.get('nota', 'N/D')
            c.drawString(60, y, f"- {nombre_materia}: {nota}")
            y -= 18
            if y < 50:  # Salto a nueva página si es necesario
                c.showPage()
                y = height - 50
    else:
        c.drawString(60, y, "Sin materias registradas.")
        y -= 18

    # Firma digital
    y -= 20
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y, f"Firma digital (SHA-256): {firma}")
    y -= 10
    c.setFont("Helvetica-Oblique", 8)
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawString(50, y, f"Documento exportado el: {fecha_actual}")
    
    c.save()
    print("Expediente exportado exitosamente a", archivo_salida)

    