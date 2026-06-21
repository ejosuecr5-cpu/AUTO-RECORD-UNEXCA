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
        self.geometry("700x520")

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

        # tab notas recientes
        tab_notas = tabs.add("Notas Recientes")
        self._construir_tab_notas(tab_notas)

        # tab gestión de usuarios (solo admin)
        if self._rol_actual == "admin":
            tab_users = tabs.add("Gestión de Usuarios")
            self._construir_tab_usuarios(tab_users)

    def _construir_tab_notas(self, parent):
        cab = ctk.CTkFrame(parent, fg_color="transparent")
        cab.pack(fill="x", padx=8, pady=(10, 2))
        for i, (txt, w) in enumerate([("Cédula", 90), ("Estudiante", 180), ("PNF", 150),
                                       ("Materia", 200), ("Nota", 50), ("Estado", 90), ("Período", 80)]):
            ctk.CTkLabel(
                cab, text=txt, width=w,
                font=ctk.CTkFont(size=11, weight="bold"), text_color="gray"
            ).grid(row=0, column=i, padx=2)

        lista = ctk.CTkScrollableFrame(parent, height=320)
        lista.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        filas = database.obtener_notas_recientes(30)
        if not filas:
            ctk.CTkLabel(
                lista, text="No hay notas cargadas aún.",
                font=ctk.CTkFont(size=12), text_color="gray"
            ).pack(pady=20)
            return

        for cedula, estudiante, pnf, materia, nota, estado, periodo, fecha in filas:
            fila = ctk.CTkFrame(lista, fg_color="transparent")
            fila.pack(fill="x", pady=1)
            nota_txt = str(nota) if nota is not None else "—"
            color_estado = "#2ecc71" if estado == "Aprobado" else ("#e74c3c" if estado == "Reprobado" else "gray")
            for i, (val, w) in enumerate([
                (cedula, 90), (estudiante, 180), (pnf, 150),
                (materia, 200), (nota_txt, 50), (estado, 90), (periodo or "—", 80)
            ]):
                kwargs = {"text_color": color_estado} if i == 5 else {}
                ctk.CTkLabel(fila, text=val, width=w, font=ctk.CTkFont(size=11),
                             **kwargs).grid(row=0, column=i, padx=2)

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
