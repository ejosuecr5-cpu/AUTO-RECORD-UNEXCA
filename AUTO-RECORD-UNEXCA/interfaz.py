import customtkinter as ctk
from tkinter import messagebox, filedialog
import hashlib
import os

import database
import pdf
import firma

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AUTO-RECORD UNEXCA")
        self.resizable(False, False)
        self._cedula_actual = None
        self._datos_actuales = None
        self._usuario_actual = None
        self._rol_actual = None
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

    # ── login ──────────────────────────────────────────────────────────────────

    def mostrar_login(self):
        self._limpiar()
        self.geometry("1080x720")

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

    # ── módulo estudiante: cédula ───────────────────────────────────────────────

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
        self.mostrar_opciones_estudiante()

    # ── módulo estudiante: opciones ─────────────────────────────────────────────

    def mostrar_opciones_estudiante(self):
        self._limpiar()
        self.geometry("500x310")

        self._btn_volver(self, self.mostrar_cedula)

        pers = self._datos_actuales["datos_personales"]
        ctk.CTkLabel(
            self, text=f"Bienvenido, {pers['nombre']} {pers['apellido']}",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(pady=(18, 4))
        ctk.CTkLabel(
            self, text=f"{pers['trayecto']}  ·  Período {pers['periodo']}",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 30))

        ctk.CTkButton(
            self, text="Exportar mi expediente (PDF)",
            width=280, height=42,
            command=self._exportar_pdf
        ).pack(pady=6)

        ctk.CTkButton(
            self, text="Validar integridad (SHA-256)",
            width=280, height=42,
            fg_color="transparent", border_width=1,
            command=self.mostrar_validar_sha
        ).pack(pady=6)

    def _exportar_pdf(self):
        try:
            nombre = pdf.generar_pdf(self._cedula_actual, self._datos_actuales)
            messagebox.showinfo("Expediente generado", f"PDF guardado como:\n{nombre}")
        except Exception as e:
            messagebox.showerror("Error al generar PDF", str(e))

    # ── módulo estudiante: validar SHA ──────────────────────────────────────────

    def mostrar_validar_sha(self):
        self._limpiar()
        self.geometry("580x460")

        self._btn_volver(self, self.mostrar_opciones_estudiante)

        ctk.CTkLabel(
            self, text="Validación de Integridad",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(pady=(18, 4))
        ctk.CTkLabel(
            self, text="Ingrese el código SHA-256 o seleccione el archivo PDF",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(pady=(0, 14))

        # fila: entrada SHA + botón
        fila_sha = ctk.CTkFrame(self, fg_color="transparent")
        fila_sha.pack(pady=4)
        self.entry_sha = ctk.CTkEntry(
            fila_sha, placeholder_text="SHA-256 del expediente...",
            width=360, height=34
        )
        self.entry_sha.grid(row=0, column=0, padx=(0, 8))
        self.entry_sha.bind("<Return>", lambda _: self._verificar_por_sha())
        ctk.CTkButton(
            fila_sha, text="Verificar", width=90, height=34,
            command=self._verificar_por_sha
        ).grid(row=0, column=1)

        ctk.CTkLabel(
            self, text="— o —",
            font=ctk.CTkFont(size=11), text_color="gray"
        ).pack(pady=6)

        ctk.CTkButton(
            self, text="Seleccionar archivo PDF",
            width=200, height=34,
            fg_color="transparent", border_width=1,
            command=self._verificar_por_archivo
        ).pack(pady=4)

        self.lbl_resultado = ctk.CTkLabel(
            self, text="",
            font=ctk.CTkFont(size=12)
        )
        self.lbl_resultado.pack(pady=(12, 4))

        self.txt_resultado = ctk.CTkTextbox(
            self, height=155,
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.txt_resultado.pack(fill="x", padx=20, pady=(0, 10))
        self.txt_resultado.configure(state="disabled")

    def _mostrar_resultado(self, es_valido, datos=None):
        self.txt_resultado.configure(state="normal")
        self.txt_resultado.delete("0.0", "end")

        if es_valido and datos:
            self.lbl_resultado.configure(
                text="✓  Documento auténtico · Integridad verificada",
                text_color="#2ecc71"
            )
            pers = datos["datos_personales"]
            lineas = [
                f"Estudiante : {pers['nombre']} {pers['apellido']}",
                f"Trayecto   : {pers['trayecto']}  |  Período: {pers['periodo']}",
                "",
                f"{'Código':<12} {'Unidad Curricular':<36} {'Nota':>5}  Estado",
                "─" * 68,
            ]
            for uc in datos["historial_academico"]:
                lineas.append(
                    f"{uc['codigo']:<12} {uc['unidad_curricular']:<36} {str(uc['nota']):>5}  {uc['estado']}"
                )
            self.txt_resultado.insert("0.0", "\n".join(lineas))

        elif es_valido:
            self.lbl_resultado.configure(
                text="✓  Documento auténtico · Sin datos de auditoría en la BD",
                text_color="#f0a500"
            )
            self.txt_resultado.insert("0.0", "El hash coincide pero el expediente no está registrado en la base de datos.")

        else:
            self.lbl_resultado.configure(
                text="✗  Verificación fallida · El documento pudo ser alterado",
                text_color="#e74c3c"
            )
            self.txt_resultado.insert("0.0", "El hash no coincide o no se encontró el expediente.")

        self.txt_resultado.configure(state="disabled")

    def _verificar_por_sha(self):
        sha = self.entry_sha.get().strip()
        if not sha:
            messagebox.showwarning("Advertencia", "Ingrese el código SHA-256.")
            return
        try:
            datos = database.buscar_expediente_por_sha(sha)
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self._mostrar_resultado(datos is not None, datos)

    def _verificar_por_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar expediente PDF",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not ruta:
            return
        try:
            with open(ruta, "rb") as f:
                sha_calculado = hashlib.sha256(f.read()).hexdigest()

            # primero buscar en BD
            datos = database.buscar_expediente_por_sha(sha_calculado)
            if datos:
                self._mostrar_resultado(True, datos)
                return

            # fallback: archivo .sha
            try:
                es_valido = firma.verificar_integridad(ruta)
                self._mostrar_resultado(es_valido)
            except FileNotFoundError:
                self._mostrar_resultado(False)

        except Exception as e:
            messagebox.showerror("Error", str(e))

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
        usuario = self.entry_user.get().strip()
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

    # ── módulo control de estudios ──────────────────────────────────────────────

    def mostrar_modulo_admin(self):
        self._limpiar()
        self.geometry("860x560")

        # encabezado
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(14, 0))
        ctk.CTkLabel(
            header, text="Control de Estudios",
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"{self._usuario_actual}  ·  {self._rol_actual}",
            font=ctk.CTkFont(size=12), text_color="gray"
        ).pack(side="left", padx=12)
        ctk.CTkButton(
            header, text="Cerrar sesión", width=110, height=28,
            fg_color="transparent", border_width=1,
            command=self.mostrar_login
        ).pack(side="right")

        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=20, pady=12)

        tab_est = tabs.add("Estudiantes")
        self._construir_tab_estudiantes(tab_est)

        tab_hist = tabs.add("Historial de Notas")
        self._construir_tab_historial(tab_hist)

        # tab gestión de usuarios (solo admin)
        if self._rol_actual == "admin":
            tab_users = tabs.add("Gestión de Usuarios")
            self._construir_tab_usuarios(tab_users)

    # ── tab estudiantes ─────────────────────────────────────────────────────────

    def _construir_tab_estudiantes(self, parent):
        # cabecera de columnas
        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(10, 2))
        for i, (txt, w) in enumerate([("Cédula", 100), ("Nombre", 180), ("Carreras inscritas", 320), ("", 90)]):
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
            ).grid(row=0, column=i, padx=3)

        lista = ctk.CTkScrollableFrame(parent)
        lista.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        estudiantes = database.listar_estudiantes_con_inscripciones()

        if not estudiantes:
            ctk.CTkLabel(
                lista, text="No hay estudiantes registrados aún.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for cedula, nombre, apellido, pnfs in estudiantes:
            fila = ctk.CTkFrame(lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            carreras_txt = ", ".join(pnfs) if pnfs else "Sin carrera asignada"
            color_carreras = "#e2e8f0" if pnfs else "#64748b"

            ctk.CTkLabel(fila, text=cedula,          width=100, font=ctk.CTkFont(size=11)).grid(row=0, column=0, padx=3)
            ctk.CTkLabel(fila, text=f"{nombre} {apellido}", width=180, font=ctk.CTkFont(size=11)).grid(row=0, column=1, padx=3)
            ctk.CTkLabel(fila, text=carreras_txt,    width=320, font=ctk.CTkFont(size=11),
                         text_color=color_carreras).grid(row=0, column=2, padx=3)
            ctk.CTkButton(
                fila, text="Ver notas", width=85, height=26,
                fg_color="transparent", border_width=1,
                command=lambda c=cedula, n=f"{nombre} {apellido}": self._abrir_detalle_notas(c, n)
            ).grid(row=0, column=3, padx=3)

    def _abrir_detalle_notas(self, cedula, nombre_completo):
        historial = database.obtener_notas_estudiante(cedula)

        win = ctk.CTkToplevel(self)
        win.title(f"Notas — {nombre_completo}")
        win.geometry("720x500")
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

        if not historial:
            ctk.CTkLabel(
                scroll, text="Este estudiante no tiene notas cargadas.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for pnf_nombre, materias in historial.items():
            # sección por PNF
            ctk.CTkLabel(
                scroll, text=pnf_nombre,
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#7dd3fc"
            ).pack(anchor="w", pady=(10, 2))

            cab = ctk.CTkFrame(scroll, fg_color="transparent")
            cab.pack(fill="x")
            for i, (txt, w) in enumerate([("Código", 90), ("Unidad Curricular", 320),
                                           ("Tray.", 50), ("Mod.", 50), ("Nota", 50), ("Estado", 90)]):
                ctk.CTkLabel(cab, text=txt, width=w,
                             font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").grid(row=0, column=i, padx=2)

            for m in materias:
                fila = ctk.CTkFrame(scroll, fg_color="transparent")
                fila.pack(fill="x", pady=1)
                nota_txt = str(m["nota"]) if m["nota"] is not None else "—"
                color = "#2ecc71" if m["estado"] == "Aprobado" else ("#e74c3c" if m["estado"] == "Reprobado" else "gray")
                for i, (val, w) in enumerate([
                    (m["codigo"], 90), (m["unidad_curricular"], 320),
                    (str(m["trayecto"]), 50), (str(m["modulo"]), 50),
                    (nota_txt, 50), (m["estado"], 90)
                ]):
                    kwargs = {"text_color": color} if i == 5 else {}
                    ctk.CTkLabel(fila, text=val, width=w,
                                 font=ctk.CTkFont(size=11), **kwargs).grid(row=0, column=i, padx=2)

    # ── tab historial de notas ───────────────────────────────────────────────────

    def _construir_tab_historial(self, parent):
        # barra de filtros
        filtros = ctk.CTkFrame(parent, fg_color="transparent")
        filtros.pack(fill="x", padx=8, pady=(10, 6))

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

        # cabecera de tabla
        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(0, 2))
        for i, (txt, w) in enumerate([("Cédula", 90), ("Estudiante", 160), ("PNF", 130),
                                       ("Materia", 190), ("Nota", 50), ("Estado", 85), ("Período", 75), ("Cargado", 120)]):
            ctk.CTkLabel(cab, text=txt, width=w,
                         font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").grid(row=0, column=i, padx=2)

        # contenedor de filas (scrollable, reemplazable)
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
                (cedula_r, 90), (estudiante, 160), (pnf, 130),
                (materia_r, 190), (nota_txt, 50), (estado, 85),
                (periodo or "—", 75), (fecha_corta, 120)
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

    def _construir_tab_usuarios(self, parent):
        # lista
        self._frame_lista = ctk.CTkScrollableFrame(parent, height=200)
        self._frame_lista.pack(fill="x", padx=8, pady=(10, 4))
        self._recargar_lista()

        # formulario nuevo usuario
        ctk.CTkLabel(
            parent, text="Crear usuario",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 4))

        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=10, pady=4)

        self.entry_new_user = ctk.CTkEntry(
            fila, placeholder_text="Usuario",
            width=150, height=32
        )
        self.entry_new_user.grid(row=0, column=0, padx=(0, 6))

        self.entry_new_pass = ctk.CTkEntry(
            fila, placeholder_text="Contraseña",
            width=150, height=32, show="●"
        )
        self.entry_new_pass.grid(row=0, column=1, padx=(0, 6))

        self.combo_rol = ctk.CTkComboBox(
            fila, values=["secretaria", "consulta"],
            width=120, height=32
        )
        self.combo_rol.set("secretaria")
        self.combo_rol.grid(row=0, column=2, padx=(0, 6))

        ctk.CTkButton(
            fila, text="Crear", width=80, height=32,
            command=self._crear_usuario
        ).grid(row=0, column=3)

    def _recargar_lista(self):
        for w in self._frame_lista.winfo_children():
            w.destroy()

        # cabecera
        cab = ctk.CTkFrame(self._frame_lista, fg_color="transparent")
        cab.pack(fill="x", pady=(0, 4))
        for i, (txt, w) in enumerate([("Usuario", 140), ("Rol", 100), ("Activo", 55), ("Acciones", 290)]):
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
            ).grid(row=0, column=i, padx=3)

        for uid, username, rol, activo in database.listar_usuarios():
            fila = ctk.CTkFrame(self._frame_lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)

            es_yo = (username == self._usuario_actual)

            ctk.CTkLabel(fila, text=username, width=140).grid(row=0, column=0, padx=3)
            ctk.CTkLabel(fila, text=rol, width=100).grid(row=0, column=1, padx=3)
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
                acc, text="Contrasena", width=85, height=26,
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
