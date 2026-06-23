import sqlite3
import hashlib
import csv
import re
import os
from datetime import datetime

DB_PATH = "unexca.db"
_ANO_ACTUAL = datetime.now().year

# ── interno ────────────────────────────────────────────────────────────────────

def _hash(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _normalizar_periodo_inscripcion(valor):
    """
    Acepta '2026' o '2026-1'; siempre devuelve 'YYYY-1'.
    Los ingresos de carrera siempre son en el primer período del año.
    """
    valor = str(valor).strip()
    if re.fullmatch(r'\d{4}', valor):
        return f"{valor}-1"
    if re.fullmatch(r'\d{4}-1', valor):
        return valor
    raise ValueError(
        f"Formato de año inválido: '{valor}'. Use un año de 4 dígitos (Ej: 2026)."
    )

def _asegurar_db():
    if not os.path.exists(DB_PATH):
        import crear_db
        crear_db.crear_base_de_datos()
    else:
        with sqlite3.connect(DB_PATH) as conn:
            # Migración 1: password_texto
            cols = [r[1] for r in conn.execute("PRAGMA table_info(usuarios_sistema)").fetchall()]
            if "password_texto" not in cols:
                conn.execute("ALTER TABLE usuarios_sistema ADD COLUMN password_texto TEXT DEFAULT ''")
                conn.commit()

            # Migración 2: roles nuevos (admin, control_estudios, secretaria)
            schema_us = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios_sistema'"
            ).fetchone()
            if schema_us and "control_estudios" not in schema_us[0]:
                conn.executescript("""
                    ALTER TABLE usuarios_sistema RENAME TO _us_old;
                    CREATE TABLE usuarios_sistema (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        username       TEXT    UNIQUE NOT NULL,
                        password_hash  TEXT    NOT NULL,
                        password_texto TEXT    NOT NULL DEFAULT '',
                        rol            TEXT    NOT NULL DEFAULT 'secretaria'
                                               CHECK(rol IN ('admin','control_estudios','secretaria')),
                        activo         INTEGER NOT NULL DEFAULT 1,
                        ultimo_acceso  TEXT
                    );
                    INSERT INTO usuarios_sistema
                        (id,username,password_hash,password_texto,rol,activo,ultimo_acceso)
                    SELECT id, username, password_hash,
                           COALESCE(password_texto,''),
                           CASE WHEN rol='consulta' THEN 'secretaria' ELSE rol END,
                           activo, ultimo_acceso
                    FROM _us_old;
                    DROP TABLE _us_old;
                """)
                conn.commit()

            # Migración 3: inscripciones.fecha_inicio → periodo
            cols_insc = [r[1] for r in conn.execute("PRAGMA table_info(inscripciones)").fetchall()]
            if "fecha_inicio" in cols_insc and "periodo" not in cols_insc:
                conn.execute("ALTER TABLE inscripciones RENAME COLUMN fecha_inicio TO periodo")
                conn.commit()

            # Migración 4a: activo en estudiantes
            cols_est = [r[1] for r in conn.execute("PRAGMA table_info(estudiantes)").fetchall()]
            if "activo" not in cols_est:
                conn.execute("ALTER TABLE estudiantes ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
                conn.commit()

            # Migración 4b: activo en materias_cursadas
            cols_mc = [r[1] for r in conn.execute("PRAGMA table_info(materias_cursadas)").fetchall()]
            if "activo" not in cols_mc:
                conn.execute("ALTER TABLE materias_cursadas ADD COLUMN activo INTEGER NOT NULL DEFAULT 1")
                conn.commit()

            # Migración 5: restaurar pnf_id NOT NULL en materias_cursadas
            # (cada nota —incluso trayecto inicial— está asociada a un PNF específico;
            #  si hay registros con pnf_id NULL de la migración anterior, se asignan
            #  al primer PNF inscrito del estudiante, o se eliminan si no tiene ninguno)
            mc_cols = {r[1]: r[3] for r in conn.execute("PRAGMA table_info(materias_cursadas)").fetchall()}
            if mc_cols.get("pnf_id", 1) == 0:   # notnull=0 → está nullable → hay que restaurar
                # Asignar PNF a registros huérfanos
                conn.execute("""
                    UPDATE materias_cursadas
                    SET pnf_id = (
                        SELECT i.pnf_id FROM inscripciones i
                        WHERE i.estudiante_id = materias_cursadas.estudiante_id
                        ORDER BY i.id LIMIT 1
                    )
                    WHERE pnf_id IS NULL
                """)
                # Eliminar los que no tienen inscripción
                conn.execute("DELETE FROM materias_cursadas WHERE pnf_id IS NULL")
                conn.executescript("""
                    ALTER TABLE materias_cursadas RENAME TO _mc_old;
                    CREATE TABLE materias_cursadas (
                        id             INTEGER PRIMARY KEY AUTOINCREMENT,
                        estudiante_id  INTEGER NOT NULL REFERENCES estudiantes(id),
                        unidad_id      INTEGER NOT NULL REFERENCES unidades_curriculares(id),
                        pnf_id         INTEGER NOT NULL REFERENCES pnf(id),
                        periodo        TEXT    NOT NULL,
                        nota           REAL,
                        estado         TEXT    NOT NULL DEFAULT 'Pendiente',
                        fecha_registro TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
                    );
                    INSERT INTO materias_cursadas SELECT * FROM _mc_old;
                    DROP TABLE _mc_old;
                """)
                conn.commit()

# ── lógica de aprobación ───────────────────────────────────────────────────────

def _base_nombre(nombre):
    """Elimina el sufijo 'Módulo I/II' del nombre de una UC."""
    return re.sub(r'\s+[Mm][oóÓO]dulo\s+II?\s*$', '', nombre).strip()

def _es_proyecto(nombre):
    return "proyecto" in nombre.lower()

def _calcular_estado(nombre, nota, companion_nota=None):
    """
    - Proyecto: mínimo 16 en cada módulo (sin excepción de promedio).
    - Regular de 2 módulos: ambos ≥ 10 OR promedio ≥ 12.
    - Regular de 1 módulo: ≥ 10.
    """
    if companion_nota is not None:
        if _es_proyecto(nombre):
            return "Aprobado" if nota >= 16 and companion_nota >= 16 else "Reprobado"
        else:
            aprobado = (nota >= 10 and companion_nota >= 10) or ((nota + companion_nota) / 2 >= 12)
            return "Aprobado" if aprobado else "Reprobado"
    else:
        minima = 16 if _es_proyecto(nombre) else 10
        return "Aprobado" if nota >= minima else "Reprobado"

def _buscar_companion(cur, uc_id, pnf_id):
    """
    Busca la UC hermana (Módulo I ↔ II) de la UC dada.
    Retorna (companion_id, companion_nombre) o None.
    """
    row = cur.execute(
        "SELECT nombre, trayecto, modulo, pnf_id FROM unidades_curriculares WHERE id = ?",
        (uc_id,)
    ).fetchone()
    if not row:
        return None
    nombre, trayecto, modulo, uc_pnf_id = row
    if uc_pnf_id is None:      # trayecto inicial no tiene hermanas
        return None

    base = _base_nombre(nombre)
    if base == nombre:         # no termina en Módulo I/II
        return None

    other_mod = 2 if modulo == 1 else 1
    return cur.execute("""
        SELECT id, nombre FROM unidades_curriculares
        WHERE pnf_id = ? AND trayecto = ? AND modulo = ? AND nombre LIKE ?
    """, (uc_pnf_id, trayecto, other_mod, f"{base}%")).fetchone()

# ── PNF ────────────────────────────────────────────────────────────────────────

def obtener_pnfs():
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id, codigo, nombre FROM pnf ORDER BY nombre").fetchall()

def listar_ucs_por_pnf(pnf_codigo):
    """Retorna (codigo, nombre) de todas las UCs del PNF + trayecto inicial."""
    with sqlite3.connect(DB_PATH) as conn:
        pnf = conn.execute("SELECT id FROM pnf WHERE codigo = ?", (pnf_codigo,)).fetchone()
        if not pnf:
            return []
        return conn.execute("""
            SELECT codigo, nombre FROM unidades_curriculares
            WHERE pnf_id = ? OR es_trayecto_inicial = 1
            ORDER BY trayecto, modulo, codigo
        """, (pnf[0],)).fetchall()

def obtener_inscripciones_estudiante(cedula):
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

def registrar_estudiante(cedula, nombre, apellido, fecha_nacimiento, lugar_residencia):
    """Registra un nuevo estudiante. Lanza ValueError si la cédula ya existe."""
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        if conn.execute("SELECT 1 FROM estudiantes WHERE cedula = ?", (cedula,)).fetchone():
            raise ValueError(f"La cédula '{cedula}' ya está registrada.")
        conn.execute(
            "INSERT INTO estudiantes (cedula, nombre, apellido, fecha_nacimiento, lugar_residencia) "
            "VALUES (?, ?, ?, ?, ?)",
            (cedula, nombre.strip(), apellido.strip(), fecha_nacimiento.strip(), lugar_residencia.strip())
        )
        conn.commit()

def inscribir_estudiante(cedula, pnf_codigo, anio_o_periodo):
    """
    Inscribe un estudiante en un PNF.
    Acepta el año de ingreso (ej: 2026) o el período explícito (2026-1).
    No se permiten años futuros (mayor al año actual).
    """
    periodo = _normalizar_periodo_inscripcion(anio_o_periodo)
    anio = int(periodo.split("-")[0])
    if anio > _ANO_ACTUAL:
        raise ValueError(f"No se pueden registrar inscripciones en años futuros (máximo {_ANO_ACTUAL}).")

    with sqlite3.connect(DB_PATH) as conn:
        est = conn.execute("SELECT id FROM estudiantes WHERE cedula = ?", (cedula,)).fetchone()
        if not est:
            raise ValueError(f"Estudiante '{cedula}' no encontrado.")
        pnf = conn.execute("SELECT id FROM pnf WHERE codigo = ?", (pnf_codigo.upper(),)).fetchone()
        if not pnf:
            raise ValueError(f"PNF '{pnf_codigo}' no encontrado.")
        if conn.execute(
            "SELECT 1 FROM inscripciones WHERE estudiante_id = ? AND pnf_id = ?",
            (est[0], pnf[0])
        ).fetchone():
            raise ValueError(f"El estudiante ya está inscrito en '{pnf_codigo}'.")
        conn.execute(
            "INSERT INTO inscripciones (estudiante_id, pnf_id, periodo) VALUES (?, ?, ?)",
            (est[0], pnf[0], periodo)
        )
        conn.commit()

def registrar_nota(cedula, uc_codigo, pnf_codigo, periodo, nota):
    """
    Registra o actualiza la nota de un estudiante en una UC.
    Toda nota —incluyendo trayecto inicial— está ligada al PNF bajo el que se cursa.
    Si el estudiante luego entra a otra carrera, debe volver a cursar el trayecto inicial
    para esa nueva carrera.
    Lanza ValueError si el estudiante ya aprobó esa UC en ese PNF.
    Retorna el estado calculado ('Aprobado' / 'Reprobado').
    """
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()

        est = cur.execute(
            "SELECT id, activo FROM estudiantes WHERE cedula = ?", (cedula,)
        ).fetchone()
        if not est:
            raise ValueError(f"Estudiante '{cedula}' no encontrado.")
        est_id, est_activo = est
        if not est_activo:
            raise ValueError(
                f"El estudiante '{cedula}' está dado de baja. No se pueden cargar nuevas notas."
            )

        uc = cur.execute(
            "SELECT id, nombre FROM unidades_curriculares WHERE codigo = ?", (uc_codigo,)
        ).fetchone()
        if not uc:
            raise ValueError(f"Unidad curricular '{uc_codigo}' no encontrada.")
        uc_id, uc_nombre = uc

        pnf = cur.execute("SELECT id FROM pnf WHERE codigo = ?", (pnf_codigo.upper(),)).fetchone()
        if not pnf:
            raise ValueError(f"PNF '{pnf_codigo}' no encontrado.")
        pnf_id = pnf[0]

        # Verificar inscripción en el PNF
        if not cur.execute(
            "SELECT 1 FROM inscripciones WHERE estudiante_id=? AND pnf_id=?",
            (est_id, pnf_id)
        ).fetchone():
            raise ValueError(
                f"El estudiante '{cedula}' no está inscrito en el PNF '{pnf_codigo.upper()}'."
            )

        # Bloqueo si ya aprobó en este PNF (solo cuentan notas activas)
        if cur.execute("""
            SELECT 1 FROM materias_cursadas
            WHERE estudiante_id=? AND unidad_id=? AND pnf_id=? AND estado='Aprobado' AND activo=1
        """, (est_id, uc_id, pnf_id)).fetchone():
            raise ValueError(f"El estudiante ya aprobó '{uc_nombre}' en este PNF.")

        # Hermana (Módulo I ↔ II) — solo aplica a UCs de carrera
        companion = _buscar_companion(cur, uc_id, pnf_id)
        companion_nota = None
        if companion:
            comp_row = cur.execute("""
                SELECT nota FROM materias_cursadas
                WHERE estudiante_id=? AND unidad_id=? AND pnf_id=?
                ORDER BY fecha_registro DESC LIMIT 1
            """, (est_id, companion[0], pnf_id)).fetchone()
            if comp_row:
                companion_nota = comp_row[0]

        estado = _calcular_estado(uc_nombre, nota, companion_nota)

        existing = cur.execute("""
            SELECT id FROM materias_cursadas
            WHERE estudiante_id=? AND unidad_id=? AND pnf_id=? AND periodo=?
        """, (est_id, uc_id, pnf_id, periodo)).fetchone()

        if existing:
            cur.execute("""
                UPDATE materias_cursadas
                SET nota=?, estado=?, fecha_registro=datetime('now','localtime')
                WHERE id=?
            """, (nota, estado, existing[0]))
        else:
            cur.execute("""
                INSERT INTO materias_cursadas (estudiante_id, unidad_id, pnf_id, periodo, nota, estado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (est_id, uc_id, pnf_id, periodo, nota, estado))

        if companion and companion_nota is not None:
            comp_estado = _calcular_estado(companion[1], companion_nota, nota)
            cur.execute("""
                UPDATE materias_cursadas SET estado=?
                WHERE estudiante_id=? AND unidad_id=? AND pnf_id=?
            """, (comp_estado, est_id, companion[0], pnf_id))

        conn.commit()
        return estado

def buscar_estudiante(cedula, pnf_id=None):
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        row = cur.execute(
            "SELECT id, nombre, apellido, fecha_nacimiento, lugar_residencia "
            "FROM estudiantes WHERE cedula = ?", (cedula,)
        ).fetchone()
        if not row:
            return None
        est_id, nombre, apellido, fecha_nac, lugar_res = row

        if pnf_id:
            materias = cur.execute("""
                SELECT uc.codigo, uc.nombre, mc.nota, mc.estado, uc.trayecto, uc.modulo
                FROM materias_cursadas mc
                JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
                WHERE mc.estudiante_id = ? AND mc.pnf_id = ?
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
                "nombre": nombre, "apellido": apellido, "cedula": cedula,
                "fecha_nacimiento": fecha_nac, "lugar_residencia": lugar_res, "pnf": pnf_nombre,
            },
            "historial_academico": [
                {"codigo": r[0], "unidad_curricular": r[1], "nota": r[2],
                 "estado": r[3], "trayecto": r[4], "modulo": r[5]}
                for r in materias
            ]
        }

def buscar_expediente_por_sha(sha):
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT e.cedula, exp.pnf_id FROM expedientes exp
            JOIN estudiantes e ON exp.estudiante_id = e.id
            WHERE exp.firma_sha256 = ?
        """, (sha,)).fetchone()
        if not row:
            return None
        return buscar_estudiante(row[0], row[1])

def listar_estudiantes_con_inscripciones():
    """Retorna (cedula, nombre, apellido, [pnfs], activo)."""
    with sqlite3.connect(DB_PATH) as conn:
        estudiantes = conn.execute(
            "SELECT id, cedula, nombre, apellido, activo FROM estudiantes ORDER BY apellido, nombre"
        ).fetchall()
        result = []
        for est_id, cedula, nombre, apellido, activo in estudiantes:
            pnfs = conn.execute("""
                SELECT p.nombre FROM inscripciones i JOIN pnf p ON i.pnf_id = p.id
                WHERE i.estudiante_id = ? ORDER BY p.nombre
            """, (est_id,)).fetchall()
            result.append((cedula, nombre, apellido, [r[0] for r in pnfs], bool(activo)))
        return result

def obtener_notas_estudiante(cedula):
    """
    Retorna dict: { pnf_nombre: [ {id, codigo, unidad_curricular, nota, estado, trayecto, modulo, activo} ] }
    Incluye notas dadas de baja (activo=0) para consulta; el campo activo indica su estado.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        est = cur.execute("SELECT id FROM estudiantes WHERE cedula = ?", (cedula,)).fetchone()
        if not est:
            return {}
        filas = cur.execute("""
            SELECT p.nombre, mc.id, uc.codigo, uc.nombre, mc.nota, mc.estado,
                   uc.trayecto, uc.modulo, mc.activo
            FROM materias_cursadas mc
            JOIN pnf p ON mc.pnf_id = p.id
            JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
            WHERE mc.estudiante_id = ?
            ORDER BY p.nombre, uc.trayecto, uc.modulo, uc.codigo, mc.activo DESC
        """, (est[0],)).fetchall()
        result = {}
        for pnf, nota_id, codigo, nombre, nota, estado, trayecto, modulo, activo in filas:
            result.setdefault(pnf, []).append({
                "id": nota_id, "codigo": codigo, "unidad_curricular": nombre,
                "nota": nota, "estado": estado, "trayecto": trayecto,
                "modulo": modulo, "activo": bool(activo)
            })
        return result

def obtener_notas_recientes(limit=50, cedula=None, materia=None):
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
            SELECT e.cedula, e.nombre || ' ' || e.apellido,
                   p.nombre,
                   uc.nombre, mc.nota, mc.estado, mc.periodo, mc.fecha_registro
            FROM materias_cursadas mc
            JOIN estudiantes e ON mc.estudiante_id = e.id
            JOIN pnf p ON mc.pnf_id = p.id
            JOIN unidades_curriculares uc ON mc.unidad_id = uc.id
            {where}
            ORDER BY mc.fecha_registro DESC LIMIT ?
        """, params).fetchall()

# ── tipos de error CSV ─────────────────────────────────────────────────────────

ERR_CAMPO_FALTANTE          = "CAMPO_FALTANTE"
ERR_CEDULA_DUPLICADA        = "CEDULA_DUPLICADA"
ERR_ESTUDIANTE_NO_ENCONTRADO = "ESTUDIANTE_NO_ENCONTRADO"
ERR_CARRERA_NO_ENCONTRADA   = "CARRERA_NO_ENCONTRADA"
ERR_MATERIA_NO_ENCONTRADA   = "MATERIA_NO_ENCONTRADA"
ERR_ESTUDIANTE_NO_INSCRITO  = "ESTUDIANTE_NO_INSCRITO"
ERR_MATERIA_APROBADA        = "MATERIA_APROBADA"
ERR_NOTA_INVALIDA           = "NOTA_INVALIDA"
ERR_ANIO_INVALIDO           = "ANIO_INVALIDO"
ERR_YA_INSCRITO             = "YA_INSCRITO"


def _err(linea, tipo, detalle):
    return {"linea": linea, "tipo": tipo, "detalle": detalle}


# ── importación CSV ────────────────────────────────────────────────────────────

def _validar_csv_estudiantes(filepath):
    """Valida el CSV sin tocar la BD. Retorna lista de errores."""
    errores = []
    cedulas_en_archivo = set()
    with sqlite3.connect(DB_PATH) as conn:
        with open(filepath, newline='', encoding='utf-8') as f:
            for i, row in enumerate(csv.DictReader(f, delimiter=';'), 2):
                cedula   = row.get('cedula', '').strip()
                nombre   = row.get('nombre', '').strip()
                apellido = row.get('apellido', '').strip()
                fecha    = row.get('fecha_nacimiento', '').strip()
                lugar    = row.get('lugar_residencia', '').strip()

                if not all([cedula, nombre, apellido, fecha, lugar]):
                    errores.append(_err(i, ERR_CAMPO_FALTANTE,
                        "Faltan campos obligatorios (cedula, nombre, apellido, fecha_nacimiento, lugar_residencia)."))
                    continue

                if cedula in cedulas_en_archivo:
                    errores.append(_err(i, ERR_CEDULA_DUPLICADA,
                        f"La cédula '{cedula}' aparece más de una vez en el archivo."))
                    continue
                cedulas_en_archivo.add(cedula)

                if conn.execute("SELECT 1 FROM estudiantes WHERE cedula=?", (cedula,)).fetchone():
                    errores.append(_err(i, ERR_CEDULA_DUPLICADA,
                        f"La cédula '{cedula}' ya existe en la base de datos."))
    return errores


def _validar_csv_inscripciones(filepath):
    errores = []
    with sqlite3.connect(DB_PATH) as conn:
        with open(filepath, newline='', encoding='utf-8') as f:
            for i, row in enumerate(csv.DictReader(f, delimiter=';'), 2):
                cedula    = row.get('cedula', '').strip()
                pnf_cod   = row.get('pnf_codigo', '').strip()
                anio_val  = row.get('anio', row.get('periodo', '')).strip()

                if not all([cedula, pnf_cod, anio_val]):
                    errores.append(_err(i, ERR_CAMPO_FALTANTE,
                        "Faltan campos obligatorios (cedula, pnf_codigo, anio)."))
                    continue

                try:
                    periodo = _normalizar_periodo_inscripcion(anio_val)
                    anio = int(periodo.split("-")[0])
                    if anio > _ANO_ACTUAL:
                        raise ValueError()
                except Exception:
                    errores.append(_err(i, ERR_ANIO_INVALIDO,
                        f"Año '{anio_val}' inválido o futuro (máximo {_ANO_ACTUAL})."))
                    continue

                est = conn.execute("SELECT id FROM estudiantes WHERE cedula=?", (cedula,)).fetchone()
                if not est:
                    errores.append(_err(i, ERR_ESTUDIANTE_NO_ENCONTRADO,
                        f"La cédula '{cedula}' no está registrada."))
                    continue

                pnf = conn.execute("SELECT id FROM pnf WHERE codigo=?", (pnf_cod.upper(),)).fetchone()
                if not pnf:
                    errores.append(_err(i, ERR_CARRERA_NO_ENCONTRADA,
                        f"El PNF '{pnf_cod}' no existe."))
                    continue

                if conn.execute(
                    "SELECT 1 FROM inscripciones WHERE estudiante_id=? AND pnf_id=?",
                    (est[0], pnf[0])
                ).fetchone():
                    errores.append(_err(i, ERR_YA_INSCRITO,
                        f"'{cedula}' ya está inscrito en '{pnf_cod}'."))
    return errores


def _validar_csv_notas(filepath):
    errores = []
    with sqlite3.connect(DB_PATH) as conn:
        with open(filepath, newline='', encoding='utf-8') as f:
            for i, row in enumerate(csv.DictReader(f, delimiter=';'), 2):
                cedula    = row.get('cedula', '').strip()
                uc_codigo = row.get('uc_codigo', '').strip()
                pnf_cod   = row.get('pnf_codigo', '').strip()
                periodo   = row.get('periodo', '').strip()
                nota_str  = row.get('nota', '').strip()

                if not all([cedula, uc_codigo, pnf_cod, periodo, nota_str]):
                    errores.append(_err(i, ERR_CAMPO_FALTANTE,
                        "Faltan campos obligatorios (cedula, uc_codigo, pnf_codigo, periodo, nota)."))
                    continue

                try:
                    nota_val = float(nota_str.replace(',', '.'))
                    if not (0 <= nota_val <= 20):
                        raise ValueError()
                except Exception:
                    errores.append(_err(i, ERR_NOTA_INVALIDA,
                        f"Nota '{nota_str}' inválida. Debe ser un número entre 0 y 20."))
                    continue

                est = conn.execute(
                    "SELECT id, activo FROM estudiantes WHERE cedula=?", (cedula,)
                ).fetchone()
                if not est:
                    errores.append(_err(i, ERR_ESTUDIANTE_NO_ENCONTRADO,
                        f"La cédula '{cedula}' no está registrada."))
                    continue
                if not est[1]:
                    errores.append(_err(i, ERR_ESTUDIANTE_NO_ENCONTRADO,
                        f"El estudiante '{cedula}' está dado de baja. No se pueden cargar nuevas notas."))
                    continue

                pnf = conn.execute("SELECT id FROM pnf WHERE codigo=?", (pnf_cod.upper(),)).fetchone()
                if not pnf:
                    errores.append(_err(i, ERR_CARRERA_NO_ENCONTRADA,
                        f"El PNF '{pnf_cod}' no existe."))
                    continue

                uc = conn.execute(
                    "SELECT id, nombre FROM unidades_curriculares WHERE codigo=?", (uc_codigo,)
                ).fetchone()
                if not uc:
                    errores.append(_err(i, ERR_MATERIA_NO_ENCONTRADA,
                        f"La unidad curricular '{uc_codigo}' no existe."))
                    continue

                if not conn.execute(
                    "SELECT 1 FROM inscripciones WHERE estudiante_id=? AND pnf_id=?",
                    (est[0], pnf[0])
                ).fetchone():
                    errores.append(_err(i, ERR_ESTUDIANTE_NO_INSCRITO,
                        f"'{cedula}' no está inscrito en el PNF '{pnf_cod}'."))
                    continue

                if conn.execute("""
                    SELECT 1 FROM materias_cursadas
                    WHERE estudiante_id=? AND unidad_id=? AND pnf_id=? AND estado='Aprobado' AND activo=1
                """, (est[0], uc[0], pnf[0])).fetchone():
                    errores.append(_err(i, ERR_MATERIA_APROBADA,
                        f"'{cedula}' ya aprobó '{uc[1]}' en '{pnf_cod}'. No se puede sobreescribir."))
    return errores


def importar_csv_estudiantes(filepath):
    """
    Valida el CSV completo. Si hay errores, retorna (0, errores) sin escribir nada.
    Si todo es válido, importa todos los registros y retorna (total, []).
    """
    errores = _validar_csv_estudiantes(filepath)
    if errores:
        return 0, errores
    success = 0
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter=';'):
            registrar_estudiante(
                row['cedula'].strip(), row['nombre'].strip(),
                row['apellido'].strip(), row['fecha_nacimiento'].strip(),
                row['lugar_residencia'].strip()
            )
            success += 1
    return success, []


def importar_csv_inscripciones(filepath):
    """
    Valida el CSV completo. Si hay errores, retorna (0, errores) sin escribir nada.
    """
    errores = _validar_csv_inscripciones(filepath)
    if errores:
        return 0, errores
    success = 0
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter=';'):
            anio_val = row.get('anio', row.get('periodo', '')).strip()
            inscribir_estudiante(row['cedula'].strip(), row['pnf_codigo'].strip(), anio_val)
            success += 1
    return success, []


def importar_csv_notas(filepath):
    """
    Valida el CSV completo. Si hay errores, retorna (0, errores) sin escribir nada.
    """
    errores = _validar_csv_notas(filepath)
    if errores:
        return 0, errores
    success = 0
    with open(filepath, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f, delimiter=';'):
            registrar_nota(
                row['cedula'].strip(), row['uc_codigo'].strip(),
                row['pnf_codigo'].strip(), row['periodo'].strip(),
                float(row['nota'].replace(',', '.'))
            )
            success += 1
    return success, []


def generar_plantilla_csv(tipo, destino):
    cabeceras = {
        'estudiantes':   ['cedula', 'nombre', 'apellido', 'fecha_nacimiento', 'lugar_residencia'],
        'inscripciones': ['cedula', 'pnf_codigo', 'anio'],
        'notas':         ['cedula', 'uc_codigo', 'pnf_codigo', 'periodo', 'nota'],
    }
    with open(destino, 'w', newline='', encoding='utf-8') as f:
        f.write(';'.join(cabeceras[tipo]) + '\n')

# ── dar de baja / reactivar ────────────────────────────────────────────────────

def dar_baja_nota(nota_id):
    """Marca una entrada de nota como inactiva (baja). La nota sigue en la BD para auditoría."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE materias_cursadas SET activo=0 WHERE id=?", (nota_id,))
        conn.commit()

def reactivar_nota(nota_id):
    """Reactiva una nota previamente dada de baja."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE materias_cursadas SET activo=1 WHERE id=?", (nota_id,))
        conn.commit()

def dar_baja_estudiante(cedula):
    """
    Marca un estudiante como inactivo. Sus notas se conservan para consulta
    pero no se pueden agregar nuevas entradas.
    """
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("SELECT id FROM estudiantes WHERE cedula=?", (cedula,)).fetchone()
        if not r:
            raise ValueError(f"Estudiante '{cedula}' no encontrado.")
        conn.execute("UPDATE estudiantes SET activo=0 WHERE id=?", (r[0],))
        conn.commit()

def reactivar_estudiante(cedula):
    """Reactiva un estudiante dado de baja."""
    with sqlite3.connect(DB_PATH) as conn:
        r = conn.execute("SELECT id FROM estudiantes WHERE cedula=?", (cedula,)).fetchone()
        if not r:
            raise ValueError(f"Estudiante '{cedula}' no encontrado.")
        conn.execute("UPDATE estudiantes SET activo=1 WHERE id=?", (r[0],))
        conn.commit()

# ── usuarios ───────────────────────────────────────────────────────────────────

def inicializar_admin():
    _asegurar_db()
    with sqlite3.connect(DB_PATH) as conn:
        if not conn.execute("SELECT 1 FROM usuarios_sistema WHERE username = 'admin'").fetchone():
            conn.execute(
                "INSERT INTO usuarios_sistema (username, password_hash, password_texto, rol) "
                "VALUES (?, ?, ?, ?)",
                ("admin", _hash("admin123"), "admin123", "admin")
            )
            conn.commit()

def verificar_credenciales(username, password):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT rol FROM usuarios_sistema "
            "WHERE username = ? AND password_hash = ? AND activo = 1",
            (username, _hash(password))
        ).fetchone()
        return row[0] if row else None

def crear_usuario(username, password, rol):
    with sqlite3.connect(DB_PATH) as conn:
        if conn.execute("SELECT 1 FROM usuarios_sistema WHERE username = ?", (username,)).fetchone():
            raise ValueError(f"El usuario '{username}' ya existe.")
        conn.execute(
            "INSERT INTO usuarios_sistema (username, password_hash, password_texto, rol) "
            "VALUES (?, ?, ?, ?)",
            (username, _hash(password), password, rol)
        )
        conn.commit()

def listar_usuarios():
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            "SELECT id, username, rol, activo FROM usuarios_sistema ORDER BY username"
        ).fetchall()

def obtener_password(username):
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
