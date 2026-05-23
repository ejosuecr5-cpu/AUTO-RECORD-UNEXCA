#2. Auto-Record UNEXCA
#Generador de expedientes académicos con firma digital (checksum) para evitar alteración

import hashlib
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generar_checksum(expediente):
    # Cálculo de hash sobre datos canónicos
    datos_json = json.dumps(expediente, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(datos_json.encode('utf-8')).hexdigest()

def generar_pdf_exp(ed, checksum, ruta_pdf):
    c = canvas.Canvas(ruta_pdf, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Expediente Académico (UNEXCA)")
    c.setFont("Helvetica", 12)
    c.drawString(100, height - 80, f"Nombre: {ed['nombre']}")
    c.drawString(100, height - 100, f"Cédula: {ed['cedula']}")
    c.drawString(100, height - 120, f"Carrera: {ed['carrera']}")
    c.drawString(100, height - 150, "Materias:")

    y = height - 170
    for mat in ed["materias"]:
        c.drawString(120, y, f"- {mat['nombre']}: {mat['nota']}")
        y -= 20

    # Línea de firma digital (checksum)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(100, y-20, f"Firma digital (SHA-256): {checksum}")

    c.save()
    print(f"PDF generado en: {ruta_pdf}")

def validar_integridad(expediente, checksum):
    return generar_checksum(expediente) == checksum

# Ejemplo de uso:
expediente = {
    "nombre": "Ana Pérez",
    "cedula": "12345678",
    "carrera": "Ingeniería Informática",
    "materias": [
        {"nombre": "Matemática I", "nota": 18},
        {"nombre": "Física I", "nota": 15}
    ]
}
checksum = generar_checksum(expediente)
generar_pdf_exp(expediente, checksum, "expediente_ANA_PEREZ.pdf")

# Validación (por ejemplo, al recibir el expediente y el checksum del PDF)
es_valido = validar_integridad(expediente, checksum)
print("¿El expediente es válido?", es_valido)

