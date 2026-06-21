import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import hashlib
import json
import os

# Librerías de ReportLab para la construcción del documento académico
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuración de apariencia general
ctk.set_appearance_mode("System")  # Opciones: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Opciones de tema: "blue", "green", "dark-blue"

class AutoRecordGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---- CONFIGURACIÓN DE LA VENTANA PRINCIPAL ----
        self.title("Auto-Record UNEXCA - Generador de Expedientes")
        self.geometry("900x650")
        self.resizable(True, True)

        # ---- TÍTULO DE LA APLICACIÓN ----
        self.title_label = ctk.CTkLabel(
            self,
            text="AUTO-RECORD UNEXCA",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)

        # ---- CONTENEDOR PRINCIPAL ----
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=10)

        # ---- SECCIÓN 1: DATOS DEL ESTUDIANTE ----
        self.student_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.student_frame.pack(fill="x", padx=20, pady=15)

        self.lbl_cedula = ctk.CTkLabel(self.student_frame, text="Cédula / ID Estudiante:", font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_cedula.grid(row=0, column=0, sticky="w", pady=5)

        self.entry_cedula = ctk.CTkEntry(self.student_frame, placeholder_text="Ej. V-12345678", width=250)
        self.entry_cedula.grid(row=0, column=1, padx=10, pady=5)

        self.btn_buscar = ctk.CTkButton(self.student_frame, text="Buscar Historial", width=120, command=self.buscar_estudiante)
        self.btn_buscar.grid(row=0, column=2, padx=5, pady=5)

        # ---- SECCIÓN 2: ACCIONES ----
        self.actions_frame = ctk.CTkFrame(self.main_frame)
        self.actions_frame.pack(fill="x", padx=20, pady=15)

        # Distribución uniforme de columnas
        self.actions_frame.columnconfigure(0, weight=1)
        self.actions_frame.columnconfigure(1, weight=1)
        self.actions_frame.columnconfigure(2, weight=1)

        self.btn_pdf = ctk.CTkButton(
            self.actions_frame,
            text="1. Generar Expediente (PDF)",
            command=self.generar_pdf,
            state="disabled"
        )
        self.btn_pdf.grid(row=0, column=0, padx=20, pady=20, sticky="ew")

        self.btn_firmar = ctk.CTkButton(
            self.actions_frame,
            text="2. Firmar y Calcular Checksum",
            command=self.calcular_firma,
            state="disabled"
        )
        self.btn_firmar.grid(row=0, column=1, padx=20, pady=20, sticky="ew")

        self.btn_verificar = ctk.CTkButton(
            self.actions_frame,
            text="Validar Integridad (SHA-256)",
            command=self.verificar_integridad
        )
        self.btn_verificar.grid(row=0, column=2, padx=20, pady=20, sticky="ew")

        # ---- SECCIÓN 3: CONSOLA DE ESTADO Y LOGS ----
        self.status_frame = ctk.CTkFrame(self.main_frame)
        self.status_frame.pack(fill="both", expand=True, padx=20, pady=15)

        self.lbl_status_title = ctk.CTkLabel(
            self.status_frame,
            text="Estado de Seguridad y Logs",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_status_title.pack(anchor="w", padx=15, pady=(10, 0))

        self.txt_logs = ctk.CTkTextbox(self.status_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.txt_logs.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt_logs.insert("0.0", ">>> Sistema listo. Ingrese una cédula para comenzar.\n")
        self.txt_logs.configure(state="disabled")

        # Variables de control interno (Declaradas una sola vez)
        self.datos_estudiante_actual = None
        self.archivo_pdf_generado = None

    # ---- MÉTODOS DE LÓGICA Y EVENTOS ----
    def log_message(self, message):
        """Inserta texto informativo en el componente de logs."""
        self.txt_logs.configure(state="normal")
        self.txt_logs.insert("end", f">>> {message}\n")
        self.txt_logs.configure(state="disabled")
        self.txt_logs.see("end")

    def buscar_estudiante(self):
        """Busca el estudiante en el archivo estudiantes.json local."""
        cedula = self.entry_cedula.get().strip()

        # Validación limpia de campo vacío
        if not cedula:
            messagebox.showwarning("Advertencia", "Por favor, ingrese una cédula válida.")
            return

        archivo_datos = "estudiantes.json"

        if os.path.exists(archivo_datos):
            with open(archivo_datos, "r", encoding="utf-8") as f:
                try:
                    base_datos = json.load(f)
                    if cedula in base_datos:
                        self.datos_estudiante_actual = base_datos[cedula]
                        alumno = self.datos_estudiante_actual["datos_personales"]

                        self.log_message(f"Estudiante localizado: {alumno['nombre']} {alumno['apellido']} ({alumno['trayecto']})")
                        self.btn_pdf.configure(state="normal")
                        self.btn_firmar.configure(state="disabled")
                    else:
                        self.log_message(f"Error: La cédula {cedula} no está registrada.")
                        self.btn_pdf.configure(state="disabled")
                        self.btn_firmar.configure(state="disabled")
                except json.JSONDecodeError:
                    self.log_message("Error: El archivo 'estudiantes.json' tiene un formato inválido.")
        else:
            self.log_message("Error: No se encontró el archivo de datos 'estudiantes.json'.")

    def generar_pdf(self):
        """Construye el documento PDF real con las notas del estudiante."""
        if not self.datos_estudiante_actual:
            return

        cedula = self.entry_cedula.get().strip()
        nombre_archivo = f"expediente_{cedula}.pdf"

        try:
            doc = SimpleDocTemplate(nombre_archivo, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            story = []

            styles = getSampleStyleSheet()
            style_titulo = ParagraphStyle(name='T1', fontName='Helvetica-Bold', fontSize=16, leading=20, alignment=1, spaceAfter=15)
            style_subtitulo = ParagraphStyle(name='T2', fontName='Helvetica-Bold', fontSize=12, leading=16, spaceAfter=10)
            style_texto = styles['Normal']

            # Encabezado institucional
            story.append(Paragraph("UNIVERSIDAD NACIONAL EXPERIMENTAL DE LA GRAN CARACAS (UNEXCA)", style_titulo))
            story.append(Paragraph("EXPEDIENTE ACADÉMICO DE PREGRADO", ParagraphStyle(name='Sub', fontName='Helvetica', fontSize=13, alignment=1, spaceAfter=20)))
            story.append(Spacer(1, 10))

            # Datos Personales
            pers = self.datos_estudiante_actual["datos_personales"]
            story.append(Paragraph("<b>Datos del Alumno:</b>", style_subtitulo))
            story.append(Paragraph(f"<b>Nombre Completo:</b> {pers['nombre']} {pers['apellido']}", style_texto))
            story.append(Paragraph(f"<b>Cédula de Identidad:</b> {cedula}", style_texto))
            story.append(Paragraph(f"<b>Ubicación Académica:</b> {pers['trayecto']} - {pers['periodo']}", style_texto))
            story.append(Spacer(1, 15))

            # Tabla de Notas
            story.append(Paragraph("<b>Historial Académico:</b>", style_subtitulo))
            tabla_datos = [["Código", "Unidad Curricular", "Nota", "Estado"]]
            for uc in self.datos_estudiante_actual["historial_academico"]:
                tabla_datos.append([uc["codigo"], uc["unidad_curricular"], str(uc["nota"]), uc["estado"]])

            tabla_historial = Table(tabla_datos, colWidths=[70, 260, 60, 90])
            tabla_historial.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f9f9f9")),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(tabla_historial)
            doc.build(story)

            self.archivo_pdf_generado = nombre_archivo
            self.log_message(f"Archivo PDF generado: '{nombre_archivo}'")
            self.btn_firmar.configure(state="normal")
            messagebox.showinfo("Éxito", f"PDF creado como '{nombre_archivo}'. Proceda a firmar.")

        except Exception as e:
            messagebox.showerror("Error", f"Fallo al construir el PDF: {str(e)}")

    def calcular_firma(self):
        """Genera una firma hash SHA-256 basada en el contenido binario del PDF."""
        if not self.archivo_pdf_generado or not os.path.exists(self.archivo_pdf_generado):
            messagebox.showerror("Error", "No se encuentra el archivo PDF para firmar.")
            return

        try:
            with open(self.archivo_pdf_generado, "rb") as f:
                hash_checksum = hashlib.sha256(f.read()).hexdigest()

            nombre_firma = self.archivo_pdf_generado.replace(".pdf", ".sha")
            with open(nombre_firma, "w") as f_sha:
                f_sha.write(hash_checksum)

            self.log_message("Firma criptográfica generada y guardada.")
            self.log_message(f"SHA-256: {hash_checksum}")
            messagebox.showinfo("Firma Exitosa", f"Sello digital guardado como '{nombre_firma}'")
        except Exception as e:
            messagebox.showerror("Error", f"Error al firmar: {str(e)}")

    def verificar_integridad(self):
        """Compara el hash de un PDF seleccionado contra su firma .sha guardada."""
        archivo = filedialog.askopenfilename(title="Validar Expediente PDF", filetypes=[("Archivos PDF", "*.pdf")])
        if archivo:
            self.log_message(f"Validando archivo: {os.path.basename(archivo)}")
            try:
                with open(archivo, "rb") as f:
                    hash_actual = hashlib.sha256(f.read()).hexdigest()

                archivo_sha = archivo.replace(".pdf", ".sha")
                if os.path.exists(archivo_sha):
                    with open(archivo_sha, "r") as f_sha:
                        hash_guardado = f_sha.read().strip()

                    if hash_actual == hash_guardado:
                        self.log_message("RESULTADO: Integridad validada. El documento es auténtico.")
                        messagebox.showinfo("Éxito", "El documento no ha sido modificado.")
                    else:
                        self.log_message("ALERTA: El archivo fue alterado o la firma no coincide.")
                        messagebox.showerror("Fallo", "Los hashes criptográficos no coinciden.")
                else:
                    self.log_message("Falta archivo de verificación (.sha).")
            except Exception as e:
                self.log_message(f"Error: {str(e)}")

if __name__ == "__main__":
    app = AutoRecordGUI()
    app.mainloop()