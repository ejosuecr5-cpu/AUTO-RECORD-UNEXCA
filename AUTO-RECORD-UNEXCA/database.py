import sqlite3
import hashlib
import os

DB_PATH = "unexca.db"

# ── interno ────────────────────────────────────────────────────────────────────

def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _asegurar_db():
    if not os.path.exists(DB_PATH):
        import crear_db
        crear_db.crear_base_de_datos()
    else:
        # Migración: agregar password_texto si la BD ya existía sin esa columna
        with sqlite3.connect(DB_PATH) as conn:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios_sistema)").fetchall()]
            if "password_texto" not in cols:
                conn.execute("ALTER TABLE usuarios_sistema ADD COLUMN password_texto TEXT DEFAULT ''")
                conn.commit()

# ── PNF ────────────────────────────────────────────────────────────────────────

def obtener_pnfs():
    """Retorna lista de (id, codigo, nombre) de todos los PNF."""
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id, codigo, nombre FROM pnf ORDER BY nombre").fetchall()

def obtener_inscripciones_estudiante(cedula):
    """
    Retorna los PNF en los que está inscrito el estudiante.
    Lista de (pnf_id, pnf_nombre, activo).
    """
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("""
            SELECT p.id, p.nombre, i.activo
            FROM inscripciones i
            JOIN pnf p ON i.pnf_id = p.id
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE e.cedula = ?
            ORDER BY p.nombre
        """, (cedula,)).fetchall()

# ── estudiantes ────────────────────────────────────────────────────────────────

def buscar_estudiante(cedula, pnf_id=None):
    """
    Busca un estudiante por cédula.
    Si pnf_id se indica, el historial incluye sólo materias de ese PNF + trayecto inicial.
    Si pnf_id es None, devuelve todos los registros.
    Retorna dict con datos_personales e historial_academico, o None si no existe.
    """
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT id, nombre, apellido, fecha_nacimiento, lugar_residencia "
            "FROM estudiantes WHERE cedula = ?",
            (cedula,)
        ).fetchone()
        if not row:
            return None
        est_id, nombre, apellido, fecha_nac, lugar_res = row

        if pnf_id:
            materias = cur.execute("""
                SELECT uc.codigo, uc.nombre, mc.nota, mc.estado, uc.trayecto, uc.modulo
                FROM materias_cursadas mc
                JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
                WHERE mc.estudiante_id = ?
                  AND (mc.pnf_id = ? OR uc.es_trayecto_inicial = 1)
                ORDER BY uc.trayecto, uc.modulo, uc.codigo
            """, (est_id, pnf_id)).fetchall()
            pnf_nombre = cur.execute("SELECT nombre FROM pnf WHERE id = ?", (pnf_id,)).fetchone()
            pnf_nombre = pnf_nombre[0] if pnf_nombre else None
        else:
            materias = cur.execute("""
                SELECT uc.codigo, uc.nombre, mc.nota, mc.estado, uc.trayecto, uc.modulo
                FROM materias_cursadas mc
                JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
                WHERE mc.estudiante_id = ?
                ORDER BY mc.pnf_id, uc.trayecto, uc.modulo, uc.codigo
            """, (est_id,)).fetchall()
            pnf_nombre = None

        return {
            "datos_personales": {
                "nombre":           nombre,
                "apellido":         apellido,
                "cedula":           cedula,
                "fecha_nacimiento": fecha_nac,
                "lugar_residencia": lugar_res,
                "pnf":              pnf_nombre,
            },
            "historial_academico": [
                {
                    "codigo":            r[0],
                    "unidad_curricular": r[1],
                    "nota":              r[2],
                    "estado":            r[3],
                    "trayecto":          r[4],
                    "modulo":            r[5],
                }
                for r in materias
            ]
        }

def buscar_expediente_por_sha(sha):
    """
    Busca un expediente por su firma SHA-256.
    Retorna los datos del estudiante con el PNF del expediente, o None.
    """
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT e.cedula, exp.pnf_id
            FROM expedientes exp
            JOIN estudiantes e ON exp.estudiante_id = e.id
            WHERE exp.firma_sha256 = ?
        """, (sha,)).fetchone()
        if not row:
            return None
        cedula, pnf_id = row
        return buscar_estudiante(cedula, pnf_id)

def listar_estudiantes_con_inscripciones():
    """
    Retorna todos los estudiantes con sus PNF inscritos.
    Lista de (cedula, nombre, apellido, [pnf_nombre, ...]).
    """
    with sqlite3.connect(DB_PATH) as conn:
        estudiantes = conn.execute(
            "SELECT id, cedula, nombre, apellido FROM estudiantes ORDER BY apellido, nombre"
        ).fetchall()
        result = []
        for est_id, cedula, nombre, apellido in estudiantes:
            pnfs = conn.execute("""
                SELECT p.nombre FROM inscripciones i
                JOIN pnf p ON i.pnf_id = p.id
                WHERE i.estudiante_id = ?
                ORDER BY p.nombre
            """, (est_id,)).fetchall()
            result.append((cedula, nombre, apellido, [r[0] for r in pnfs]))
        return result

def obtener_notas_estudiante(cedula):
    """
    Retorna todas las notas de un estudiante agrupadas por PNF.
    Dict: { pnf_nombre: [ {codigo, unidad_curricular, nota, estado, trayecto, modulo}, ... ] }
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        est = cur.execute("SELECT id FROM estudiantes WHERE cedula = ?", (cedula,)).fetchone()
        if not est:
            return {}
        est_id = est[0]
        filas = cur.execute("""
            SELECT p.nombre, uc.codigo, uc.nombre, mc.nota, mc.estado, uc.trayecto, uc.modulo
            FROM materias_cursadas mc
            JOIN pnf p ON mc.pnf_id = p.id
            JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
            WHERE mc.estudiante_id = ?
            ORDER BY p.nombre, uc.trayecto, uc.modulo, uc.codigo
        """, (est_id,)).fetchall()
        result = {}
        for pnf, codigo, nombre, nota, estado, trayecto, modulo in filas:
            result.setdefault(pnf, []).append({
                "codigo": codigo, "unidad_curricular": nombre,
                "nota": nota, "estado": estado,
                "trayecto": trayecto, "modulo": modulo
            })
        return result

def obtener_notas_recientes(limit=50, cedula=None, materia=None):
    """
    Retorna notas cargadas con filtros opcionales.
    Lista de (cedula, estudiante, pnf, materia, nota, estado, periodo, fecha_registro).
    """
    condiciones, params = [], []
    if cedula:
        condiciones.append("e.cedula LIKE ?")
        params.append(f"%{cedula}%")
    if materia:
        condiciones.append("uc.nombre LIKE ?")
        params.append(f"%{materia}%")
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    params.append(limit)
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(f"""
            SELECT e.cedula,
                   e.nombre || ' ' || e.apellido,
                   p.nombre,
                   uc.nombre,
                   mc.nota,
                   mc.estado,
                   mc.periodo,
                   mc.fecha_registro
            FROM materias_cursadas mc
            JOIN estudiantes e  ON mc.estudiante_id = e.id
            JOIN pnf p          ON mc.pnf_id = p.id
            JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
            {where}
            ORDER BY mc.fecha_registro DESC
            LIMIT ?
        """, params).fetchall()

# ── usuarios ───────────────────────────────────────────────────────────────────

def inicializar_admin():
    """Crea el usuario admin por defecto si no existe."""
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        existe = conn.execute(
            "SELECT 1 FROM usuarios_sistema WHERE username = 'admin'"
        ).fetchone()
        if not existe:
            conn.execute(
                "INSERT INTO usuarios_sistema (username, password_hash, password_texto, rol) VALUES (?, ?, ?, ?)",
                ("admin", _hash("admin123"), "admin123", "admin")
            )
            conn.commit()

def verificar_credenciales(username, password):
    """Retorna el rol si las credenciales son válidas y el usuario está activo, o None."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT rol FROM usuarios_sistema "
            "WHERE username = ? AND password_hash = ? AND activo = 1",
            (username, _hash(password))
        ).fetchone()
        return row[0] if row else None

def crear_usuario(username, password, rol):
    """Crea un nuevo usuario. Lanza ValueError si el username ya existe."""
    with sqlite3.connect(DB_PATH) as conn:
        if conn.execute("SELECT 1 FROM usuarios_sistema WHERE username = ?", (username,)).fetchone():
            raise ValueError(f"El usuario '{username}' ya existe.")
        conn.execute(
            "INSERT INTO usuarios_sistema (username, password_hash, password_texto, rol) VALUES (?, ?, ?, ?)",
            (username, _hash(password), password, rol)
        )
        conn.commit()

def listar_usuarios():
    """Retorna lista de (id, username, rol, activo)."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT id, username, rol, activo FROM usuarios_sistema ORDER BY username"
        ).fetchall()

def obtener_password(username):
    """Retorna la contraseña en texto plano de un usuario."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT password_texto FROM usuarios_sistema WHERE username = ?", (username,)
        ).fetchone()
        return row[0] if row else ""

def cambiar_password(username, nueva_password):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE usuarios_sistema SET password_hash = ?, password_texto = ? WHERE username = ?",
            (_hash(nueva_password), nueva_password, username)
        )
        conn.commit()

def set_activo(username, activo):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE usuarios_sistema SET activo = ? WHERE username = ?",
            (activo, username)
        )
        conn.commit()
