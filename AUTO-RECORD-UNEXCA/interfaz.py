import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw
import hashlib
import os

import database
import pdf
import firma

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# ── períodos académicos disponibles ───────────────────────────────────────────

def _periodos_academicos():
    opciones = []
    for year in range(2020, 2033):
        opciones.extend([f"{year}-1", f"{year}-2", f"{year}-V"])
    return opciones

# ── iconos PIL ─────────────────────────────────────────────────────────────────

def _mk_icon(forma, size=44):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fg = (255, 255, 255, 255)
    s = size

    if forma == "estudiantes":
        # cabeza
        d.ellipse([s//3, 2, s*2//3, s//3], fill=fg)
        # cuerpo / hombros
        d.ellipse([s//8, s//2, s*7//8, s+4], fill=fg)

    elif forma == "historial":
        # hoja con líneas
        d.rounded_rectangle([4, 2, s-4, s-2], radius=4, fill=fg)
        acc = (80, 120, 200, 255)
        for y in [s//4, s*2//5, s*3//5, s*3//4]:
            d.rectangle([10, y, s-10, y+3], fill=acc)

    elif forma == "registro":
        # lápiz diagonal
        d.polygon([(6, s-10), (s-10, 6), (s-4, 12), (12, s-4)], fill=fg)
        d.polygon([(6, s-10), (12, s-4), (4, s-2)], fill=fg)
        d.rectangle([s-8, 2, s-2, 10], fill=fg)

    elif forma == "importar":
        # flecha abajo con bandeja
        cx = s // 2
        d.polygon([
            (cx, s*2//3), (cx-10, s//2), (cx-6, s//2),
            (cx-6, s//4), (cx+6, s//4), (cx+6, s//2), (cx+10, s//2)
        ], fill=fg)
        d.rectangle([4, s-8, s-4, s-4], fill=fg)

    elif forma == "usuarios":
        # llave
        d.ellipse([4, 4, 22, 22], outline=fg, width=3)
        d.line([(18, 18), (s-4, s-4)], fill=fg, width=3)
        d.line([(s-10, s-10), (s-10, s-5)], fill=fg, width=3)
        d.line([(s-16, s-6), (s-16, s-1)], fill=fg, width=3)

    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AUTO-RECORD UNEXCA")
        self.resizable(False, False)
        self._cedula_actual = None
        self._datos_actuales = None
        self._usuario_actual = None
        self._rol_actual = None
        self._iconos = {}
        database.inicializar_admin()
        self.mostrar_login()

    # ── utilidades ─────────────────────────────────────────────────────────────

    def _limpiar(self):
        for w in self.winfo_children():
            w.destroy()

    def _btn_volver(self, parent, destino):
        ctk.CTkButton(
            parent, text="← Volver", width=85, height=26,
            fg_color="transparent", border_width=1, text_color="gray",
            command=destino
        ).pack(anchor="w", padx=20, pady=(14, 0))

    def _icono(self, forma):
        if forma not in self._iconos:
            self._iconos[forma] = _mk_icon(forma)
        return self._iconos[forma]

    # ── login ──────────────────────────────────────────────────────────────────

    def mostrar_login(self):
        self._limpiar()
        self.geometry("480x340")

        ctk.CTkLabel(
            self, text="AUTO-RECORD UNEXCA",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(52, 4))

        ctk.CTkLabel(
            self, text="Sistema de Gestión de Expedientes",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 38))

        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack()

        ctk.CTkButton(
            fila, text="Soy Estudiante", width=175, height=44,
            command=self.mostrar_cedula
        ).grid(row=0, column=0, padx=12)

        ctk.CTkButton(
            fila, text="Control de Estudios", width=175, height=44,
            fg_color="#1d6b1a", hover_color="#145213",
            command=self.mostrar_login_admin
        ).grid(row=0, column=1, padx=12)

        ctk.CTkLabel(
            self, text="UNEXCA · 2025",
            font=ctk.CTkFont(size=10), text_color="gray"
        ).pack(side="bottom", pady=12)

    # ── módulo estudiante ───────────────────────────────────────────────────────

    def mostrar_cedula(self):
        self._limpiar()
        self.geometry("460x268")

        self._btn_volver(self, self.mostrar_login)

        ctk.CTkLabel(
            self, text="Acceso Estudiante",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self, text="Ingrese su número de cédula",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 16))

        self.entry_ced = ctk.CTkEntry(
            self, placeholder_text="Ej. V-12345678",
            width=240, height=36
        )
        self.entry_ced.pack(pady=4)
        self.entry_ced.bind("<Return>", lambda _: self._verificar_cedula())
        self.entry_ced.focus()

        ctk.CTkButton(
            self, text="Continuar →", width=140, height=36,
            command=self._verificar_cedula
        ).pack(pady=14)

    def _verificar_cedula(self):
        cedula = self.entry_ced.get().strip()
        if not cedula:
            messagebox.showwarning("Advertencia", "Ingrese una cédula.")
            return
        try:
            datos = database.buscar_estudiante(cedula)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if not datos:
            messagebox.showerror("No encontrado", f"La cédula '{cedula}' no está registrada.")
            return
        self._cedula_actual = cedula
        self._datos_actuales = datos
        self._cargar_modulo_estudiante()

    # ── módulo estudiante: estructura ───────────────────────────────────────────

    def _cargar_modulo_estudiante(self):
        self._limpiar()
        self.geometry("940x580")

        pers = self._datos_actuales["datos_personales"]
        nombre_est = f"{pers['nombre']} {pers['apellido']}"

        # Encabezado persistente
        hdr = ctk.CTkFrame(self, height=48, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(12, 0))
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="AUTO-RECORD UNEXCA",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(side="left")
        ctk.CTkLabel(hdr, text=f"  {nombre_est}  ·  {self._cedula_actual}",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(side="left")
        ctk.CTkButton(hdr, text="Cerrar sesión", width=110, height=28,
                      fg_color="transparent", border_width=1,
                      command=self.mostrar_login).pack(side="right")

        ctk.CTkFrame(self, height=1, fg_color="gray").pack(fill="x", padx=0, pady=(8, 0))

        self._frame_cuerpo_est = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_cuerpo_est.pack(fill="both", expand=True)

        self._mostrar_dashboard_estudiante()

    def _limpiar_cuerpo_est(self):
        for w in self._frame_cuerpo_est.winfo_children():
            w.destroy()

    # ── dashboard estudiante ────────────────────────────────────────────────────

    def _mostrar_dashboard_estudiante(self):
        self._limpiar_cuerpo_est()

        pers = self._datos_actuales["datos_personales"]
        ctk.CTkLabel(self._frame_cuerpo_est,
                     text=f"Bienvenido, {pers['nombre']} {pers['apellido']}",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(42, 4))
        ctk.CTkLabel(self._frame_cuerpo_est, text="¿Qué desea hacer?",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 38))

        secciones = [
            ("registro",  "Generar\nExpediente"),
            ("historial", "Mis\nExpedientes"),
            ("usuarios",  "Validar\nIntegridad SHA"),
        ]
        fila = ctk.CTkFrame(self._frame_cuerpo_est, fg_color="transparent")
        fila.pack()
        for col, (forma, etiqueta) in enumerate(secciones):
            ctk.CTkButton(
                fila, text=etiqueta, image=self._icono(forma),
                compound="top", width=185, height=160, corner_radius=16,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda n=forma: self._abrir_seccion_est(n)
            ).grid(row=0, column=col, padx=18)

    def _abrir_seccion_est(self, nombre):
        self._limpiar_cuerpo_est()

        titulos = {
            "registro":  "Generar Expediente",
            "historial": "Mis Expedientes",
            "usuarios":  "Validar Integridad SHA",
        }
        barra = ctk.CTkFrame(self._frame_cuerpo_est, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(14, 6))
        ctk.CTkLabel(barra, text=titulos.get(nombre, nombre),
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        ctk.CTkButton(barra, text="← Menú principal", width=140, height=28,
                      fg_color="transparent", border_width=1,
                      command=self._mostrar_dashboard_estudiante).pack(side="right")

        contenido = ctk.CTkFrame(self._frame_cuerpo_est, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=10, pady=4)

        if nombre == "registro":
            self._seccion_est_generar(contenido)
        elif nombre == "historial":
            self._seccion_est_historial(contenido)
        elif nombre == "usuarios":
            self._seccion_est_sha(contenido)

    # ── sección: generar expediente ─────────────────────────────────────────────

    def _seccion_est_generar(self, parent):
        pnfs = database.obtener_pnfs_inscritos(self._cedula_actual)

        if not pnfs:
            ctk.CTkLabel(parent,
                text="No tienes carreras inscritas.\nContacta a Control de Estudios.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=60)
            return

        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(expand=True, pady=24)

        pnf_opciones = [f"{cod} – {nom}" for cod, nom, _ in pnfs]
        self._gen_pnf_map = {f"{cod} – {nom}": (cod, nom, niv) for cod, nom, niv in pnfs}

        ctk.CTkLabel(frame, text="Carrera (PNF):",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=0, column=0, sticky="e", padx=(0, 12), pady=10)
        self._gen_pnf_combo = ctk.CTkComboBox(frame, values=pnf_opciones, width=360, height=34)
        self._gen_pnf_combo.set(pnf_opciones[0])
        self._gen_pnf_combo.grid(row=0, column=1, pady=10, sticky="w")

        ctk.CTkLabel(frame, text="Nivel académico:",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=1, column=0, sticky="e", padx=(0, 12), pady=10)
        self._gen_nivel_combo = ctk.CTkComboBox(
            frame, values=["TSU", "Licenciatura"], width=200, height=34
        )
        self._gen_nivel_combo.set("TSU")
        self._gen_nivel_combo.grid(row=1, column=1, pady=10, sticky="w")

        self._gen_lbl_msg = ctk.CTkLabel(frame, text="",
                                          font=ctk.CTkFont(size=10), text_color="gray")
        self._gen_lbl_msg.grid(row=2, column=0, columnspan=2, pady=4)

        ctk.CTkButton(frame, text="Generar Expediente", width=260, height=38,
                      command=self._ejecutar_generar_expediente).grid(
            row=3, column=0, columnspan=2, pady=16)

    def _ejecutar_generar_expediente(self):
        pnf_sel = self._gen_pnf_combo.get()
        nivel   = self._gen_nivel_combo.get()
        cedula  = self._cedula_actual

        if pnf_sel not in self._gen_pnf_map:
            messagebox.showwarning("Advertencia", "Seleccione una carrera válida.")
            return

        pnf_cod, pnf_nom, _ = self._gen_pnf_map[pnf_sel]

        if not database.hay_notas_aprobadas(cedula, pnf_cod, nivel):
            messagebox.showwarning(
                "Sin notas aprobadas",
                f"No tienes notas aprobadas para {pnf_nom} ({nivel}).\n"
                "El expediente no puede generarse hasta tener al menos una materia aprobada."
            )
            return

        try:
            datos_est = database.buscar_estudiante(cedula)["datos_personales"]
            notas     = database.obtener_notas_para_expediente(cedula, pnf_cod, nivel)
            ruta, sha = pdf.generar_expediente(cedula, pnf_cod, nivel, datos_est, notas)
            database.registrar_expediente(cedula, pnf_cod, nivel, ruta, sha)

            self._gen_lbl_msg.configure(
                text=f"Guardado: {os.path.basename(ruta)}",
                text_color="#2ecc71"
            )
            messagebox.showinfo(
                "Expediente generado",
                f"El expediente fue guardado exitosamente en:\n{ruta}\n\n"
                f"SHA-256: {sha[:48]}…"
            )
        except Exception as e:
            messagebox.showerror("Error al generar", str(e))

    # ── sección: mis expedientes ────────────────────────────────────────────────

    def _seccion_est_historial(self, parent):
        import shutil as _shutil

        expedientes = database.listar_expedientes_estudiante(self._cedula_actual)

        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(4, 2))
        for i, (txt, w) in enumerate([
            ("Carrera", 200), ("Nivel", 140), ("Generado", 135), ("Status", 90), ("", 100)
        ]):
            ctk.CTkLabel(cab, text=txt, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").grid(
                row=0, column=i, padx=3)

        lista = ctk.CTkScrollableFrame(parent)
        lista.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        if not expedientes:
            ctk.CTkLabel(lista, text="No has generado expedientes aún.",
                         font=ctk.CTkFont(size=12), text_color="gray").pack(pady=28)
            return

        for exp in expedientes:
            if exp['nivel'] == 'TSU':
                titulo_nivel = "Técnico Superior Universitario"
            else:
                titulo_nivel = exp['nivel_superior_label']

            color_status = "#2ecc71" if exp['status'] == 'Vigente' else "#f59e0b"

            fila = ctk.CTkFrame(lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            ctk.CTkLabel(fila, text=exp['pnf_nombre'], width=200,
                         font=ctk.CTkFont(size=11), anchor="w").grid(row=0, column=0, padx=3)
            ctk.CTkLabel(fila, text=titulo_nivel, width=140,
                         font=ctk.CTkFont(size=10), anchor="w").grid(row=0, column=1, padx=3)
            ctk.CTkLabel(fila, text=exp['fecha'][:16], width=135,
                         font=ctk.CTkFont(size=10)).grid(row=0, column=2, padx=3)
            ctk.CTkLabel(fila, text=exp['status'], width=90,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=color_status).grid(row=0, column=3, padx=3)
            ctk.CTkButton(
                fila, text="Descargar", width=95, height=26,
                fg_color="transparent", border_width=1,
                font=ctk.CTkFont(size=10),
                command=lambda ruta=exp['ruta_pdf']: self._descargar_expediente(ruta)
            ).grid(row=0, column=4, padx=3)

    def _descargar_expediente(self, ruta_original):
        import shutil
        if not os.path.exists(ruta_original):
            messagebox.showerror(
                "Archivo no encontrado",
                f"El archivo ya no está disponible en:\n{ruta_original}\n\n"
                "Puede generar un nuevo expediente desde 'Generar Expediente'."
            )
            return
        destino = filedialog.asksaveasfilename(
            title="Guardar copia del expediente",
            defaultextension=".pdf",
            initialfile=os.path.basename(ruta_original),
            filetypes=[("PDF", "*.pdf")]
        )
        if destino:
            shutil.copy2(ruta_original, destino)
            messagebox.showinfo("Descarga completada", f"Expediente guardado en:\n{destino}")

    # ── sección: validar SHA ────────────────────────────────────────────────────

    def _seccion_est_sha(self, parent):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(expand=True, pady=20)

        ctk.CTkLabel(
            frame,
            text="Seleccione el archivo PDF del expediente para verificar su autenticidad.",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(pady=(0, 18))

        resultado_frame = ctk.CTkFrame(frame, fg_color="transparent")

        ctk.CTkButton(
            frame, text="Seleccionar archivo PDF…", width=260, height=36,
            command=lambda: self._verificar_sha_archivo(resultado_frame)
        ).pack(pady=8)

        resultado_frame.pack(fill="x", pady=14)

    def _verificar_sha_archivo(self, resultado_frame):
        ruta = filedialog.askopenfilename(
            title="Seleccionar expediente PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not ruta:
            return

        for w in resultado_frame.winfo_children():
            w.destroy()

        try:
            with open(ruta, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()

            info = database.buscar_expediente_por_sha(sha)

            if info:
                ctk.CTkLabel(resultado_frame,
                    text="Documento auténtico · Integridad verificada",
                    font=ctk.CTkFont(size=13, weight="bold"), text_color="#2ecc71"
                ).pack(pady=(0, 8))
                color_status = "#2ecc71" if info['status'] == 'Vigente' else "#f59e0b"
                lineas = [
                    f"Estudiante: {info['nombre']}  ·  {info['cedula']}",
                    f"Carrera: {info['pnf']}",
                    f"Nivel: {info['nivel']}",
                    f"Fecha de generación: {info['fecha']}",
                ]
                for linea in lineas:
                    ctk.CTkLabel(resultado_frame, text=linea,
                                 font=ctk.CTkFont(size=10), text_color="gray").pack()
                ctk.CTkLabel(resultado_frame,
                    text=f"Status: {info['status']}",
                    font=ctk.CTkFont(size=10, weight="bold"), text_color=color_status
                ).pack(pady=2)
                ctk.CTkLabel(resultado_frame,
                    text=f"SHA-256: {sha}",
                    font=ctk.CTkFont(family="Courier", size=8), text_color="gray"
                ).pack()
            else:
                # Intentar verificar contra archivo .sha legacy (expedientes anteriores)
                ruta_sha = ruta.replace('.pdf', '.sha')
                if os.path.exists(ruta_sha):
                    with open(ruta_sha) as f:
                        sha_guardado = f.read().strip()
                    if sha == sha_guardado:
                        ctk.CTkLabel(resultado_frame,
                            text="Documento íntegro (no registrado en el sistema actual)",
                            font=ctk.CTkFont(size=12, weight="bold"), text_color="#f59e0b"
                        ).pack(pady=(0, 4))
                    else:
                        ctk.CTkLabel(resultado_frame,
                            text="Verificación fallida · El documento pudo ser alterado",
                            font=ctk.CTkFont(size=12, weight="bold"), text_color="#e74c3c"
                        ).pack()
                else:
                    ctk.CTkLabel(resultado_frame,
                        text="Documento no encontrado en el sistema",
                        font=ctk.CTkFont(size=12, weight="bold"), text_color="#e74c3c"
                    ).pack(pady=(0, 4))
                    ctk.CTkLabel(resultado_frame,
                        text="No se puede verificar la autenticidad de este archivo.",
                        font=ctk.CTkFont(size=10), text_color="gray"
                    ).pack()
                ctk.CTkLabel(resultado_frame,
                    text=f"SHA-256 calculado: {sha}",
                    font=ctk.CTkFont(family="Courier", size=8), text_color="gray"
                ).pack(pady=(4, 0))

        except Exception as e:
            ctk.CTkLabel(resultado_frame, text=f"Error: {e}",
                         text_color="#e74c3c").pack()

    # ── login control de estudios ───────────────────────────────────────────────

    def mostrar_login_admin(self):
        self._limpiar()
        self.geometry("460x300")

        self._btn_volver(self, self.mostrar_login)

        ctk.CTkLabel(
            self, text="Control de Estudios",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(22, 4))
        ctk.CTkLabel(
            self, text="Acceso restringido",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 18))

        self.entry_user = ctk.CTkEntry(
            self, placeholder_text="Usuario",
            width=240, height=36
        )
        self.entry_user.pack(pady=4)
        self.entry_user.focus()

        self.entry_pass = ctk.CTkEntry(
            self, placeholder_text="Contraseña",
            width=240, height=36, show="●"
        )
        self.entry_pass.pack(pady=4)
        self.entry_pass.bind("<Return>", lambda _: self._autenticar_admin())

        ctk.CTkButton(
            self, text="Ingresar", width=140, height=36,
            command=self._autenticar_admin
        ).pack(pady=16)

    def _autenticar_admin(self):
        usuario  = self.entry_user.get().strip()
        password = self.entry_pass.get()
        if not usuario or not password:
            messagebox.showwarning("Advertencia", "Complete todos los campos.")
            return
        try:
            rol = database.verificar_credenciales(usuario, password)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        if rol:
            self._usuario_actual = usuario
            self._rol_actual = rol
            self.mostrar_modulo_admin()
        else:
            messagebox.showerror("Acceso denegado", "Usuario o contraseña incorrectos.")

    # ── módulo control de estudios: estructura ──────────────────────────────────

    def mostrar_modulo_admin(self):
        self._limpiar()
        self.geometry("1040x640")

        # encabezado persistente
        self._frame_header = ctk.CTkFrame(self, height=48, fg_color="transparent")
        self._frame_header.pack(fill="x", padx=20, pady=(12, 0))
        self._frame_header.pack_propagate(False)

        ctk.CTkLabel(
            self._frame_header, text="AUTO-RECORD UNEXCA",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(side="left")

        rol_display = {
            "admin": "Administrador",
            "control_estudios": "Control de Estudios",
            "secretaria": "Secretaría"
        }.get(self._rol_actual, self._rol_actual)

        ctk.CTkLabel(
            self._frame_header,
            text=f"  {self._usuario_actual}  ·  {rol_display}",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(side="left")

        ctk.CTkButton(
            self._frame_header, text="Cerrar sesión", width=110, height=28,
            fg_color="transparent", border_width=1,
            command=self.mostrar_login
        ).pack(side="right")

        # separador
        ctk.CTkFrame(self, height=1, fg_color="gray").pack(fill="x", padx=0, pady=(8, 0))

        # área de contenido intercambiable
        self._frame_cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        self._frame_cuerpo.pack(fill="both", expand=True)

        self._mostrar_dashboard_admin()

    def _limpiar_cuerpo(self):
        for w in self._frame_cuerpo.winfo_children():
            w.destroy()

    # ── dashboard (menú de iconos) ──────────────────────────────────────────────

    def _mostrar_dashboard_admin(self):
        self._limpiar_cuerpo()

        ctk.CTkLabel(
            self._frame_cuerpo,
            text="¿Qué desea hacer?",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(50, 6))

        ctk.CTkLabel(
            self._frame_cuerpo,
            text="Seleccione una opción para continuar",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 50))

        secciones = [
            ("estudiantes", "Estudiantes"),
            ("historial",   "Historial"),
            ("registro",    "Registro"),
            ("importar",    "Importar CSV"),
        ]
        if self._rol_actual == "admin":
            secciones.append(("usuarios", "Usuarios"))

        # Ocultar Registro e Importar para secretaria
        if self._rol_actual == "secretaria":
            secciones = [s for s in secciones if s[0] in ("estudiantes", "historial")]

        fila = ctk.CTkFrame(self._frame_cuerpo, fg_color="transparent")
        fila.pack()

        for col, (forma, etiqueta) in enumerate(secciones):
            icono = self._icono(forma)
            card = ctk.CTkButton(
                fila,
                text=etiqueta,
                image=icono,
                compound="top",
                width=155,
                height=155,
                corner_radius=16,
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda f=forma: self._abrir_seccion_admin(f)
            )
            card.grid(row=0, column=col, padx=14)

    def _abrir_seccion_admin(self, nombre):
        self._limpiar_cuerpo()

        titulos = {
            "estudiantes": "Estudiantes",
            "historial":   "Historial de Notas",
            "registro":    "Registro",
            "importar":    "Importar CSV",
            "usuarios":    "Gestión de Usuarios",
        }

        # barra superior de la sección
        barra = ctk.CTkFrame(self._frame_cuerpo, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkLabel(
            barra,
            text=titulos.get(nombre, nombre),
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            barra, text="← Menú principal",
            width=140, height=28,
            fg_color="transparent", border_width=1,
            command=self._mostrar_dashboard_admin
        ).pack(side="right")

        # contenedor del contenido
        contenido = ctk.CTkFrame(self._frame_cuerpo, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=10, pady=4)

        if nombre == "estudiantes":
            self._seccion_estudiantes(contenido)
        elif nombre == "historial":
            self._seccion_historial(contenido)
        elif nombre == "registro":
            self._seccion_registro(contenido)
        elif nombre == "importar":
            self._seccion_importar(contenido)
        elif nombre == "usuarios":
            self._seccion_usuarios(contenido)

    # ── sección: estudiantes ────────────────────────────────────────────────────

    def _seccion_estudiantes(self, parent):
        es_admin = (self._rol_actual == "admin")

        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(4, 2))
        cols_header = [("Cédula", 100), ("Nombre", 180), ("Carreras inscritas", 280), ("Estado", 70), ("", 170 if es_admin else 90)]
        for i, (txt, w) in enumerate(cols_header):
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
            ).grid(row=0, column=i, padx=3)

        self._lista_est_frame = ctk.CTkScrollableFrame(parent)
        self._lista_est_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._poblar_lista_estudiantes()

    def _poblar_lista_estudiantes(self):
        es_admin = (self._rol_actual == "admin")
        for w in self._lista_est_frame.winfo_children():
            w.destroy()

        estudiantes = database.listar_estudiantes_con_inscripciones()

        if not estudiantes:
            ctk.CTkLabel(
                self._lista_est_frame, text="No hay estudiantes registrados aún.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for cedula, nombre, apellido, pnfs, activo in estudiantes:
            fila = ctk.CTkFrame(self._lista_est_frame, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            carreras_txt = ", ".join(pnfs) if pnfs else "Sin carrera asignada"
            color_carreras = "gray" if not pnfs else None
            color_nombre = "gray" if not activo else None

            ctk.CTkLabel(fila, text=cedula, width=100,
                         font=ctk.CTkFont(size=11), text_color=color_nombre or "white").grid(row=0, column=0, padx=3)
            ctk.CTkLabel(fila, text=f"{nombre} {apellido}", width=180,
                         font=ctk.CTkFont(size=11), text_color=color_nombre or "white").grid(row=0, column=1, padx=3)
            ctk.CTkLabel(fila, text=carreras_txt, width=280,
                         font=ctk.CTkFont(size=11),
                         text_color=color_carreras or (color_nombre or "white")).grid(row=0, column=2, padx=3)

            estado_txt = "Activo" if activo else "BAJA"
            estado_color = "#2ecc71" if activo else "#e74c3c"
            ctk.CTkLabel(fila, text=estado_txt, width=70,
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=estado_color).grid(row=0, column=3, padx=3)

            acc = ctk.CTkFrame(fila, fg_color="transparent")
            acc.grid(row=0, column=4, padx=3)

            ctk.CTkButton(
                acc, text="Ver notas", width=80, height=26,
                fg_color="transparent", border_width=1,
                command=lambda c=cedula, n=f"{nombre} {apellido}": self._abrir_detalle_notas(c, n)
            ).pack(side="left", padx=2)

            if es_admin:
                if activo:
                    ctk.CTkButton(
                        acc, text="Dar de baja", width=85, height=26,
                        fg_color="#7f1d1d", hover_color="#991b1b",
                        command=lambda c=cedula: self._dar_baja_estudiante(c)
                    ).pack(side="left", padx=2)
                else:
                    ctk.CTkButton(
                        acc, text="Reactivar", width=85, height=26,
                        fg_color="#14532d", hover_color="#166534",
                        command=lambda c=cedula: self._reactivar_estudiante(c)
                    ).pack(side="left", padx=2)

    def _dar_baja_estudiante(self, cedula):
        if not messagebox.askyesno(
            "Confirmar baja",
            f"¿Dar de baja al estudiante '{cedula}'?\n\nSus notas se conservarán para consulta, "
            "pero no se podrán agregar nuevas entradas."
        ):
            return
        try:
            database.dar_baja_estudiante(cedula)
            self._poblar_lista_estudiantes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reactivar_estudiante(self, cedula):
        try:
            database.reactivar_estudiante(cedula)
            self._poblar_lista_estudiantes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _abrir_detalle_notas(self, cedula, nombre_completo):
        es_admin = (self._rol_actual == "admin")

        win = ctk.CTkToplevel(self)
        win.title(f"Notas — {nombre_completo}")
        win.geometry("860x520")
        win.resizable(True, True)
        win.grab_set()

        ctk.CTkLabel(
            win, text=nombre_completo,
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(pady=(16, 2))
        ctk.CTkLabel(
            win, text=f"Cédula: {cedula}",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        def refrescar():
            win.destroy()
            self._abrir_detalle_notas(cedula, nombre_completo)

        historial = database.obtener_notas_estudiante(cedula)

        if not historial:
            ctk.CTkLabel(
                scroll, text="Este estudiante no tiene notas cargadas.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for pnf_nombre, materias in historial.items():
            ctk.CTkLabel(
                scroll, text=pnf_nombre,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#7dd3fc"
            ).pack(anchor="w", pady=(10, 2))

            col_ancho = [("Código", 80), ("Unidad Curricular", 240),
                         ("Tray.", 45), ("Mod.", 45), ("Nota", 45), ("Estado", 85)]
            if es_admin:
                col_ancho.append(("", 95))

            cab = ctk.CTkFrame(scroll, fg_color="transparent")
            cab.pack(fill="x")
            for i, (txt, w) in enumerate(col_ancho):
                ctk.CTkLabel(cab, text=txt, width=w,
                             font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").grid(row=0, column=i, padx=2)

            for m in materias:
                activo = m.get("activo", True)
                nota_txt = str(m["nota"]) if m["nota"] is not None else "—"

                if not activo:
                    # nota dada de baja: mostrar en gris, sin acción
                    fila = ctk.CTkFrame(scroll, fg_color="#1a1a1a")
                    fila.pack(fill="x", pady=1)
                    for i, (val, w) in enumerate([
                        (m["codigo"], 80), (m["unidad_curricular"], 240),
                        (str(m["trayecto"]), 45), (str(m["modulo"]), 45),
                        (nota_txt, 45), (m["estado"], 85)
                    ]):
                        ctk.CTkLabel(fila, text=val, width=w,
                                     font=ctk.CTkFont(size=11), text_color="gray").grid(row=0, column=i, padx=2)
                    if es_admin:
                        ctk.CTkLabel(fila, text="BAJA", width=95,
                                     font=ctk.CTkFont(size=10, weight="bold"),
                                     text_color="#6b7280").grid(row=0, column=len(col_ancho)-1, padx=2)
                else:
                    fila = ctk.CTkFrame(scroll, fg_color="transparent")
                    fila.pack(fill="x", pady=1)
                    color = "#2ecc71" if m["estado"] == "Aprobado" else ("#e74c3c" if m["estado"] == "Reprobado" else "gray")
                    for i, (val, w) in enumerate([
                        (m["codigo"], 80), (m["unidad_curricular"], 240),
                        (str(m["trayecto"]), 45), (str(m["modulo"]), 45),
                        (nota_txt, 45), (m["estado"], 85)
                    ]):
                        kwargs = {"text_color": color} if i == 5 else {}
                        ctk.CTkLabel(fila, text=val, width=w,
                                     font=ctk.CTkFont(size=11), **kwargs).grid(row=0, column=i, padx=2)
                    if es_admin:
                        nota_id = m["id"]
                        ctk.CTkButton(
                            fila, text="Dar de baja", width=90, height=22,
                            fg_color="#7f1d1d", hover_color="#991b1b",
                            font=ctk.CTkFont(size=10),
                            command=lambda nid=nota_id: self._dar_baja_nota(nid, refrescar)
                        ).grid(row=0, column=len(col_ancho)-1, padx=2)

    def _dar_baja_nota(self, nota_id, callback_refresh):
        if not messagebox.askyesno(
            "Confirmar baja",
            "¿Dar de baja esta entrada de nota?\n\nSe preservará en la base de datos pero "
            "será ignorada para los cálculos de aprobación."
        ):
            return
        try:
            database.dar_baja_nota(nota_id)
            callback_refresh()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ── sección: historial de notas ─────────────────────────────────────────────

    def _seccion_historial(self, parent):
        filtros = ctk.CTkFrame(parent, fg_color="transparent")
        filtros.pack(fill="x", padx=8, pady=(4, 6))

        ctk.CTkLabel(filtros, text="Filtrar:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=(0, 6))

        self._entry_filtro_ced = ctk.CTkEntry(filtros, placeholder_text="Cédula", width=150, height=30)
        self._entry_filtro_ced.grid(row=0, column=1, padx=4)

        self._entry_filtro_mat = ctk.CTkEntry(filtros, placeholder_text="Materia", width=200, height=30)
        self._entry_filtro_mat.grid(row=0, column=2, padx=4)

        ctk.CTkButton(
            filtros, text="Buscar", width=80, height=30,
            command=self._aplicar_filtro_historial
        ).grid(row=0, column=3, padx=4)

        ctk.CTkButton(
            filtros, text="Limpiar", width=75, height=30,
            fg_color="transparent", border_width=1,
            command=self._limpiar_filtro_historial
        ).grid(row=0, column=4, padx=4)

        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(0, 2))
        for i, (txt, w) in enumerate([("Cédula", 90), ("Estudiante", 150), ("PNF", 120),
                                       ("Materia", 200), ("Nota", 50), ("Estado", 85),
                                       ("Período", 75), ("Cargado", 110)]):
            ctk.CTkLabel(cab, text=txt, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").grid(row=0, column=i, padx=2)

        self._frame_historial = ctk.CTkScrollableFrame(parent)
        self._frame_historial.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self._poblar_historial()

    def _poblar_historial(self, cedula=None, materia=None):
        for w in self._frame_historial.winfo_children():
            w.destroy()

        filas = database.obtener_notas_recientes(50, cedula, materia)

        if not filas:
            ctk.CTkLabel(
                self._frame_historial,
                text="No se encontraron registros.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for cedula_r, estudiante, pnf, materia_r, nota, estado, periodo, fecha in filas:
            fila = ctk.CTkFrame(self._frame_historial, fg_color="transparent")
            fila.pack(fill="x", pady=1)
            nota_txt = str(nota) if nota is not None else "—"
            fecha_corta = str(fecha)[:16] if fecha else "—"
            color = "#2ecc71" if estado == "Aprobado" else ("#e74c3c" if estado == "Reprobado" else "gray")
            for i, (val, w) in enumerate([
                (cedula_r, 90), (estudiante, 150), (pnf, 120),
                (materia_r, 200), (nota_txt, 50), (estado, 85),
                (periodo or "—", 75), (fecha_corta, 110)
            ]):
                kwargs = {"text_color": color} if i == 5 else {}
                ctk.CTkLabel(fila, text=val, width=w,
                             font=ctk.CTkFont(size=11), **kwargs).grid(row=0, column=i, padx=2)

    def _aplicar_filtro_historial(self):
        ced = self._entry_filtro_ced.get().strip() or None
        mat = self._entry_filtro_mat.get().strip() or None
        self._poblar_historial(ced, mat)

    def _limpiar_filtro_historial(self):
        self._entry_filtro_ced.delete(0, "end")
        self._entry_filtro_mat.delete(0, "end")
        self._poblar_historial()

    # ── sección: registro individual ────────────────────────────────────────────

    def _seccion_registro(self, parent):
        sub = ctk.CTkTabview(parent)
        sub.pack(fill="both", expand=True)

        self._sub_registro_estudiante(sub.add("Estudiante"))
        self._sub_registro_inscripcion(sub.add("Inscripción"))
        self._sub_registro_nota(sub.add("Nota"))

    def _sub_registro_estudiante(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        campos_simples = [
            ("Cédula *",             "cedula"),
            ("Nombre *",             "nombre"),
            ("Apellido *",           "apellido"),
            ("Lugar de residencia *", "lugar_res"),
        ]
        self._est_entries = {}
        for i, (lbl, key) in enumerate(campos_simples):
            ctk.CTkLabel(frame, text=lbl, font=ctk.CTkFont(size=11)).grid(
                row=i, column=0, sticky="w", padx=8, pady=4)
            e = ctk.CTkEntry(frame, width=300, height=32)
            e.grid(row=i, column=1, columnspan=3, padx=8, pady=4)
            self._est_entries[key] = e

        # fecha de nacimiento: día / mes / año
        fila_fecha = len(campos_simples)
        ctk.CTkLabel(frame, text="Fecha nacimiento *", font=ctk.CTkFont(size=11)).grid(
            row=fila_fecha, column=0, sticky="w", padx=8, pady=4)

        meses = ["01","02","03","04","05","06","07","08","09","10","11","12"]
        self._est_dia   = ctk.CTkEntry(frame, width=60, height=32, placeholder_text="DD")
        self._est_mes   = ctk.CTkComboBox(frame, values=meses, width=72, height=32)
        self._est_anio  = ctk.CTkEntry(frame, width=80, height=32, placeholder_text="AAAA")
        self._est_mes.set("01")
        self._est_dia.grid( row=fila_fecha, column=1, padx=(8,2), pady=4)
        self._est_mes.grid( row=fila_fecha, column=2, padx=2, pady=4)
        self._est_anio.grid(row=fila_fecha, column=3, padx=(2,8), pady=4)

        ctk.CTkLabel(frame, text="DD  /  MM  /  AAAA",
                     font=ctk.CTkFont(size=9), text_color="gray").grid(
            row=fila_fecha+1, column=1, columnspan=3, sticky="w", padx=8)

        def guardar():
            vals = {k: e.get().strip() for k, e in self._est_entries.items()}
            dia  = self._est_dia.get().strip()
            mes  = self._est_mes.get().strip()
            anio = self._est_anio.get().strip()

            if not all(vals.values()) or not dia or not mes or not anio:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            if not dia.isdigit() or not anio.isdigit() or not (1 <= int(dia) <= 31) or not (1900 <= int(anio) <= 2025):
                messagebox.showerror("Error", "Fecha de nacimiento inválida.")
                return

            fecha_nac = f"{anio}-{mes}-{dia.zfill(2)}"
            try:
                database.registrar_estudiante(
                    vals['cedula'], vals['nombre'], vals['apellido'],
                    fecha_nac, vals['lugar_res']
                )
                for e in self._est_entries.values():
                    e.delete(0, "end")
                self._est_dia.delete(0, "end")
                self._est_anio.delete(0, "end")
                self._est_mes.set("01")
                messagebox.showinfo("Éxito", f"Estudiante '{vals['cedula']}' registrado.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(frame, text="Registrar Estudiante", width=220, height=34,
                      command=guardar).grid(row=fila_fecha+2, column=0, columnspan=4, pady=16)

    def _sub_registro_inscripcion(self, parent):
        import datetime as _dt
        ano_actual = _dt.datetime.now().year

        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        pnfs = database.obtener_pnfs()
        pnf_opciones = [f"{cod} – {nom}" for _, cod, nom in pnfs]
        self._insc_pnf_map = {f"{cod} – {nom}": cod for _, cod, nom in pnfs}

        ctk.CTkLabel(frame, text="Cédula del estudiante *", font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)
        self._insc_cedula = ctk.CTkEntry(frame, width=300, height=32)
        self._insc_cedula.grid(row=0, column=1, columnspan=2, padx=8, pady=4)

        ctk.CTkLabel(frame, text="PNF *", font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, sticky="w", padx=8, pady=4)
        self._insc_pnf_combo = ctk.CTkComboBox(frame, values=pnf_opciones, width=300, height=32)
        if pnf_opciones:
            self._insc_pnf_combo.set(pnf_opciones[0])
        self._insc_pnf_combo.grid(row=1, column=1, columnspan=2, padx=8, pady=4)

        ctk.CTkLabel(frame, text="Año de ingreso *", font=ctk.CTkFont(size=11)).grid(
            row=2, column=0, sticky="w", padx=8, pady=4)

        # selector de año: combo con valores hasta el año actual
        anos = [str(a) for a in range(2018, ano_actual + 1)]
        self._insc_anio = ctk.CTkComboBox(frame, values=anos, width=120, height=32)
        self._insc_anio.set(str(ano_actual))
        self._insc_anio.grid(row=2, column=1, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(frame,
                     text=f"El ingreso siempre es en el período -1 del año.\nAño máximo: {ano_actual}",
                     font=ctk.CTkFont(size=9), text_color="gray").grid(
            row=3, column=1, columnspan=2, sticky="w", padx=8)

        def guardar():
            cedula  = self._insc_cedula.get().strip()
            pnf_sel = self._insc_pnf_combo.get()
            anio    = self._insc_anio.get().strip()
            if not cedula or not pnf_sel or not anio:
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            pnf_cod = self._insc_pnf_map.get(pnf_sel, pnf_sel)
            try:
                database.inscribir_estudiante(cedula, pnf_cod, anio)
                self._insc_cedula.delete(0, "end")
                messagebox.showinfo(
                    "Éxito",
                    f"Inscripción registrada:\n{cedula} en {pnf_cod} — Período {anio}-1"
                )
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(frame, text="Registrar Inscripción", width=220, height=34,
                      command=guardar).grid(row=4, column=0, columnspan=3, pady=16)

    def _sub_registro_nota(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=20, pady=10)

        pnfs = database.obtener_pnfs()
        pnf_opciones = [f"{cod} – {nom}" for _, cod, nom in pnfs]
        self._nota_pnf_map = {f"{cod} – {nom}": cod for _, cod, nom in pnfs}
        self._nota_uc_map  = {}
        periodos = _periodos_academicos()

        ctk.CTkLabel(frame, text="Cédula del estudiante *", font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, sticky="w", padx=8, pady=4)
        self._nota_cedula = ctk.CTkEntry(frame, width=300, height=32)
        self._nota_cedula.grid(row=0, column=1, padx=8, pady=4)

        ctk.CTkLabel(frame, text="PNF *", font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, sticky="w", padx=8, pady=4)
        self._nota_pnf_combo = ctk.CTkComboBox(frame, values=pnf_opciones, width=300, height=32,
                                                command=self._actualizar_ucs_nota)
        if pnf_opciones:
            self._nota_pnf_combo.set(pnf_opciones[0])
        self._nota_pnf_combo.grid(row=1, column=1, padx=8, pady=4)

        ctk.CTkLabel(frame, text="Unidad Curricular *", font=ctk.CTkFont(size=11)).grid(
            row=2, column=0, sticky="w", padx=8, pady=4)
        self._nota_uc_combo = ctk.CTkComboBox(frame, values=[], width=300, height=32)
        self._nota_uc_combo.grid(row=2, column=1, padx=8, pady=4)

        ctk.CTkLabel(frame, text="Período *", font=ctk.CTkFont(size=11)).grid(
            row=3, column=0, sticky="w", padx=8, pady=4)
        self._nota_periodo = ctk.CTkComboBox(frame, values=periodos, width=160, height=32)
        self._nota_periodo.set("2026-1")
        self._nota_periodo.grid(row=3, column=1, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(frame, text="Nota * (0 – 20)", font=ctk.CTkFont(size=11)).grid(
            row=4, column=0, sticky="w", padx=8, pady=4)
        self._nota_valor = ctk.CTkEntry(frame, width=120, height=32, placeholder_text="15")
        self._nota_valor.grid(row=4, column=1, padx=8, pady=4, sticky="w")

        self._nota_lbl_estado = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self._nota_lbl_estado.grid(row=5, column=0, columnspan=2, pady=6)

        def guardar():
            cedula   = self._nota_cedula.get().strip()
            pnf_sel  = self._nota_pnf_combo.get()
            uc_sel   = self._nota_uc_combo.get()
            periodo  = self._nota_periodo.get().strip()
            nota_txt = self._nota_valor.get().strip()
            if not all([cedula, pnf_sel, uc_sel, periodo, nota_txt]):
                messagebox.showwarning("Advertencia", "Todos los campos son obligatorios.")
                return
            try:
                nota_val = float(nota_txt.replace(",", "."))
                if not (0 <= nota_val <= 20):
                    raise ValueError("La nota debe estar entre 0 y 20.")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return
            pnf_cod = self._nota_pnf_map.get(pnf_sel, pnf_sel)
            uc_cod  = self._nota_uc_map.get(uc_sel, uc_sel.split(" ")[0])
            try:
                estado = database.registrar_nota(cedula, uc_cod, pnf_cod, periodo, nota_val)
                color  = "#2ecc71" if estado == "Aprobado" else "#e74c3c"
                self._nota_lbl_estado.configure(text=f"Estado: {estado}", text_color=color)
                messagebox.showinfo("Nota registrada", f"Nota guardada.\nEstado calculado: {estado}")
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(frame, text="Registrar Nota", width=220, height=34,
                      command=guardar).grid(row=6, column=0, columnspan=2, pady=14)

        if pnf_opciones:
            self._actualizar_ucs_nota(pnf_opciones[0])

    def _actualizar_ucs_nota(self, pnf_seleccionado):
        pnf_cod = self._nota_pnf_map.get(pnf_seleccionado, pnf_seleccionado)
        ucs = database.listar_ucs_por_pnf(pnf_cod)
        opciones = [f"{cod} – {nom}" for cod, nom in ucs]
        self._nota_uc_map = {f"{cod} – {nom}": cod for cod, nom in ucs}
        self._nota_uc_combo.configure(values=opciones)
        if opciones:
            self._nota_uc_combo.set(opciones[0])

    # ── sección: importar CSV ───────────────────────────────────────────────────

    def _seccion_importar(self, parent):
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True, padx=4, pady=4)

        secciones = [
            (
                "Estudiantes", "estudiantes",
                "Columnas: cedula ; nombre ; apellido ; fecha_nacimiento ; lugar_residencia",
                database.importar_csv_estudiantes,
            ),
            (
                "Inscripciones", "inscripciones",
                "Columnas: cedula ; pnf_codigo ; anio   (Ej: 2026 — siempre ingresa en período -1)",
                database.importar_csv_inscripciones,
            ),
            (
                "Notas", "notas",
                "Columnas: cedula ; uc_codigo ; pnf_codigo ; periodo ; nota",
                database.importar_csv_notas,
            ),
        ]

        for titulo, tipo, desc, fn_importar in secciones:
            sec = ctk.CTkFrame(frame, corner_radius=10)
            sec.pack(fill="x", pady=8, padx=4)

            ctk.CTkLabel(sec, text=f"Importar {titulo}",
                         font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(sec, text=desc,
                         font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", padx=14, pady=(0, 8))

            fila_btn = ctk.CTkFrame(sec, fg_color="transparent")
            fila_btn.pack(fill="x", padx=14, pady=(0, 12))

            def descargar(t=tipo):
                ruta = filedialog.asksaveasfilename(
                    title=f"Guardar plantilla {t}",
                    defaultextension=".csv",
                    initialfile=f"plantilla_{t}.csv",
                    filetypes=[("CSV", "*.csv")]
                )
                if ruta:
                    database.generar_plantilla_csv(t, ruta)
                    messagebox.showinfo("Plantilla guardada", f"Guardada en:\n{ruta}")

            def cargar(fn=fn_importar, t=titulo):
                ruta = filedialog.askopenfilename(
                    title=f"Seleccionar CSV de {t}",
                    filetypes=[("CSV con punto y coma", "*.csv")]
                )
                if not ruta:
                    return
                try:
                    ok, errores = fn(ruta)
                except Exception as e:
                    messagebox.showerror("Error al leer el archivo", str(e))
                    return

                if errores:
                    self._mostrar_errores_csv(t, errores)
                else:
                    messagebox.showinfo(
                        f"Importacion exitosa",
                        f"Se importaron {ok} registro(s) de {t} correctamente."
                    )

            ctk.CTkButton(fila_btn, text="Descargar plantilla", width=170, height=30,
                          fg_color="transparent", border_width=1,
                          command=descargar).pack(side="left", padx=(0, 10))
            ctk.CTkButton(fila_btn, text=f"Cargar CSV de {titulo}", width=190, height=30,
                          command=cargar).pack(side="left")

    # ── modal de errores CSV ────────────────────────────────────────────────────

    def _mostrar_errores_csv(self, titulo, errores):
        """
        Muestra un popup con la lista de errores de validación del CSV.
        Cada error incluye línea, tipo y detalle. No se importó ningún dato.
        """
        # Colores por tipo de error
        colores = {
            "CAMPO_FALTANTE":           "#f59e0b",
            "CEDULA_DUPLICADA":         "#f59e0b",
            "ESTUDIANTE_NO_ENCONTRADO": "#ef4444",
            "CARRERA_NO_ENCONTRADA":    "#ef4444",
            "MATERIA_NO_ENCONTRADA":    "#ef4444",
            "ESTUDIANTE_NO_INSCRITO":   "#f97316",
            "MATERIA_APROBADA":         "#8b5cf6",
            "NOTA_INVALIDA":            "#ef4444",
            "ANIO_INVALIDO":            "#ef4444",
            "YA_INSCRITO":              "#f59e0b",
        }

        win = ctk.CTkToplevel(self)
        win.title(f"Errores en CSV — {titulo}")
        win.geometry("780x520")
        win.resizable(True, True)
        win.grab_set()

        # Encabezado
        hdr = ctk.CTkFrame(win, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            hdr,
            text=f"El archivo no fue importado — se encontraron {len(errores)} error(es)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#ef4444"
        ).pack(side="left")

        ctk.CTkLabel(
            win,
            text="Corrija todos los errores en el archivo CSV y vuelva a intentarlo.",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(anchor="w", padx=16, pady=(0, 8))

        # Cabecera de tabla
        cab = ctk.CTkFrame(win, fg_color="transparent")
        cab.pack(fill="x", padx=16, pady=(0, 2))
        for txt, w in [("Línea", 60), ("Tipo de error", 200), ("Detalle", 440)]:
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray",
                anchor="w"
            ).pack(side="left", padx=2)

        # Filas de errores
        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        for err in errores:
            fila = ctk.CTkFrame(scroll, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            color = colores.get(err["tipo"], "#94a3b8")
            ctk.CTkLabel(fila, text=str(err["linea"]), width=60,
                         font=ctk.CTkFont(size=11), anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(fila, text=err["tipo"], width=200,
                         font=ctk.CTkFont(size=11), text_color=color, anchor="w").pack(side="left", padx=2)
            ctk.CTkLabel(fila, text=err["detalle"], width=440,
                         font=ctk.CTkFont(size=11), anchor="w", wraplength=430).pack(side="left", padx=2)

        ctk.CTkButton(
            win, text="Cerrar", width=100,
            command=win.destroy
        ).pack(pady=(0, 12))

    # ── sección: gestión de usuarios ────────────────────────────────────────────

    def _seccion_usuarios(self, parent):
        self._frame_lista = ctk.CTkScrollableFrame(parent, height=220)
        self._frame_lista.pack(fill="x", padx=8, pady=(4, 4))
        self._recargar_lista()

        ctk.CTkLabel(
            parent, text="Crear usuario",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(12, 4))

        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=10, pady=4)

        self.entry_new_user = ctk.CTkEntry(fila, placeholder_text="Usuario", width=150, height=32)
        self.entry_new_user.grid(row=0, column=0, padx=(0, 6))

        self.entry_new_pass = ctk.CTkEntry(fila, placeholder_text="Contraseña", width=150, height=32, show="●")
        self.entry_new_pass.grid(row=0, column=1, padx=(0, 6))

        self.combo_rol = ctk.CTkComboBox(
            fila, values=["control_estudios", "secretaria"],
            width=155, height=32
        )
        self.combo_rol.set("control_estudios")
        self.combo_rol.grid(row=0, column=2, padx=(0, 6))

        ctk.CTkButton(fila, text="Crear", width=80, height=32,
                      command=self._crear_usuario).grid(row=0, column=3)

    def _recargar_lista(self):
        for w in self._frame_lista.winfo_children():
            w.destroy()

        cab = ctk.CTkFrame(self._frame_lista, fg_color="transparent")
        cab.pack(fill="x", pady=(0, 4))
        for i, (txt, w) in enumerate([("Usuario", 140), ("Rol", 130), ("Activo", 55), ("Acciones", 300)]):
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
            ).grid(row=0, column=i, padx=3)

        for uid, username, rol, activo in database.listar_usuarios():
            fila = ctk.CTkFrame(self._frame_lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            es_yo = (username == self._usuario_actual)

            ctk.CTkLabel(fila, text=username, width=140).grid(row=0, column=0, padx=3)
            ctk.CTkLabel(fila, text=rol, width=130).grid(row=0, column=1, padx=3)
            ctk.CTkLabel(
                fila, text="Sí" if activo else "No", width=55,
                text_color="#2ecc71" if activo else "#e74c3c"
            ).grid(row=0, column=2, padx=3)

            acc = ctk.CTkFrame(fila, fg_color="transparent")
            acc.grid(row=0, column=3, padx=3)

            ctk.CTkButton(
                acc,
                text="Desactivar" if activo else "Activar",
                width=85, height=26,
                fg_color="transparent", border_width=1,
                state="disabled" if es_yo else "normal",
                command=lambda un=username, a=activo: self._toggle_usuario(un, a)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                acc, text="Contraseña", width=85, height=26,
                fg_color="transparent", border_width=1,
                command=lambda un=username: self._cambiar_password(un)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                acc, text="Ver clave", width=80, height=26,
                fg_color="transparent", border_width=1,
                command=lambda un=username: self._ver_password(un)
            ).pack(side="left", padx=2)

    def _crear_usuario(self):
        usuario  = self.entry_new_user.get().strip()
        password = self.entry_new_pass.get()
        rol      = self.combo_rol.get()
        if not usuario or not password:
            messagebox.showwarning("Advertencia", "Complete usuario y contraseña.")
            return
        try:
            database.crear_usuario(usuario, password, rol)
            self.entry_new_user.delete(0, "end")
            self.entry_new_pass.delete(0, "end")
            self._recargar_lista()
            messagebox.showinfo("Éxito", f"Usuario '{usuario}' creado.")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _toggle_usuario(self, username, activo_actual):
        if username == self._usuario_actual:
            messagebox.showwarning("Acción no permitida", "No puedes revocar tu propio acceso.")
            return
        database.set_activo(username, 0 if activo_actual else 1)
        self._recargar_lista()

    def _ver_password(self, username):
        clave = database.obtener_password(username)
        if clave:
            messagebox.showinfo("Contraseña", f"Usuario: {username}\nContraseña: {clave}")
        else:
            messagebox.showinfo("Contraseña", f"No hay contraseña registrada para '{username}'.")

    def _cambiar_password(self, username):
        dialogo = ctk.CTkInputDialog(
            text=f"Nueva contraseña para '{username}':",
            title="Cambiar contraseña"
        )
        nueva = dialogo.get_input()
        if nueva:
            database.cambiar_password(username, nueva)
            messagebox.showinfo("Éxito", "Contraseña actualizada.")


if __name__ == "__main__":
    app = App()
    app.mainloop()
