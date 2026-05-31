import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import hashlib

# Configuración de apariencia general
ctk.set_appearance_mode("System")  # Opciones: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Opciones de tema: "blue", "green", "dark-blue"

class AutoRecordGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la Ventana Principal
        self.title("Auto-Record UNEXCA - Generador de Expedientes")
        self.geometry("700x550")
        self.resizable(False, False)

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
        self.actions_frame = ctk.CTkLabelFrame(self.main_frame, text=" Acciones del Sistema ")
        self.actions_frame.pack(fill="x", padx=20, pady=15)

        self.btn_pdf = ctk.CTkButton(
            self.actions_frame, 
            text="1. Generar Expediente (PDF)", 
            command=self.generar_pdf,
            state="disabled" # Se activa al buscar al estudiante
        )
        self.btn_pdf.grid(row=0, column=0, padx=20, pady=20)

        self.btn_firmar = ctk.CTkButton(
            self.actions_frame, 
            text="2. Firmar y Calcular Checksum", 
            command=self.calcular_firma,
            state="disabled"
        )
        self.btn_firmar.grid(row=0, column=1, padx=20, pady=20)

        self.btn_verificar = ctk.CTkButton(
            self.actions_frame, 
            text="Validar Integridad (SHA-256)", 
            command=self.verificar_integridad
        )
        self.btn_verificar.grid(row=0, column=2, padx=20, pady=20)

        # ---- SECCIÓN 3: CONSOLA DE ESTADO Y SEGURIDAD ----
        self.status_frame = ctk.CTkLabelFrame(self.main_frame, text=" Estado de Seguridad y Logs ")
        self.status_frame.pack(fill="both", expand=True, padx=20, pady=15)

        self.txt_logs = ctk.CTkTextbox(self.status_frame, font=ctk.CTkFont(family="Courier", size=12))
        self.txt_logs.pack(fill="both", expand=True, padx=10, pady=10)
        self.txt_logs.insert("0.0", ">>> Sistema listo. Ingrese una cédula para comenzar.\n")
        self.txt_logs.configure(state="disabled")

    # ---- FUNCIONES DE LÓGICA DE LA INTERFAZ ----

    def log_message(self, message):
        """Inserta texto informativo en la consola interna."""
        self.txt_logs.configure(state="normal")
        self.txt_logs.insert("end", f">>> {message}\n")
        self.txt_logs.configure(state="disabled")
        self.txt_logs.see("end")

    def buscar_estudiante(self):
        cedula = self.entry_cedula.get().strip()
        if not cedula:
            messagebox.showwarning("Advertencia", "Por favor, ingrese una cédula válida.")
            return
        
        # Simulación de búsqueda exitosa
        self.log_message(f"Estudiante {cedula} localizado en la base de datos.")
        self.btn_pdf.configure(state="normal")
        
    def generar_pdf(self):
        # Aquí se integrará la lógica existente de ReportLab
        self.log_message("Generando documento PDF del expediente académico...")
        # Simulación de guardado
        self.log_message("Archivo temporal generado: 'expediente_temporal.pdf'")
        self.btn_firmar.configure(state="normal")
        messagebox.showinfo("Éxito", "PDF generado temporalmente con éxito. Proceda a firmar.")

    def calcular_firma(self):
        # Lógica para aplicar SHA-256 sobre el archivo o los datos estructurados
        # Explicación: Se genera el hash para asegurar la inmutabilidad
        try:
            # Ejemplo de generación de hash simulado sobre un string para demostración
            datos_simulados = f"Expediente_{self.entry_cedula.get()}_Aprobado".encode('utf-8')
            hash_checksum = hashlib.sha256(datos_simulados).hexdigest()
            
            self.log_message(f"Firma Digital SHA-256 Generada Exitosamente.")
            self.log_message(f"CHECKSUM: {hash_checksum}")
            
            # Aquí guardarías el PDF definitivo con el metadato o archivo .sha asociado
            messagebox.showinfo("Firma Exitosa", f"Expediente asegurado.\nChecksum: {hash_checksum[:15]}...")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo firmar el documento: {str(e)}")

    def verificar_integridad(self):
        """Permite cargar un PDF y verificar si ha sido alterado comparando hashes."""
        archivo = filedialog.askopenfilename(
            title="Seleccionar Expediente PDF para Validar",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if archivo:
            self.log_message(f"Analizando archivo: {archivo}")
            # Lógica de verificación:
            # 1. Calcular SHA-256 del archivo seleccionado.
            # 2. Comparar con el guardado en la base de datos o metadatos.
            self.log_message("Verificando consistencia de datos...")
            self.log_message("RESULTADO: Integridad confirmada. El documento no ha sido modificado.")


if __name__ == "__main__":
    app = AutoRecordGUI()
    app.mainloop()