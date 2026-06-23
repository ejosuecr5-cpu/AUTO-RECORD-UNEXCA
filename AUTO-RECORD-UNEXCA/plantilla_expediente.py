"""
plantilla_expediente.py — Configuración visual del expediente académico.

Modifique este archivo para personalizar el diseño sin tocar pdf.py.
Sintaxis similar a variables CSS: cada constante controla un aspecto visual.
Los valores entre llaves {var} son marcadores que se reemplazan automáticamente
al momento de generar el PDF.
"""

import os
import sys

# ── Directorio de salida ─────────────────────────────────────────────────────
# Carpeta donde se guardan los PDFs generados.
# Por defecto: subcarpeta "record_generados" junto al ejecutable o al script.
_BASE = os.path.dirname(
    sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
)
DIRECTORIO_SALIDA = os.path.join(_BASE, "record_generados")

# ── Institución ──────────────────────────────────────────────────────────────
NOMBRE_CORTO = "UNEXCA"
NOMBRE_LARGO = "Universidad Nacional Experimental de la Gran Caracas"
LOGO_PATH    = None   # ruta absoluta a imagen .png/.jpg, o None para omitir

# ── Texto del documento ──────────────────────────────────────────────────────
TITULO_DOCUMENTO = "EXPEDIENTE ACADÉMICO"

# Títulos por nivel.
# {nombre_pnf}      → nombre de la carrera (viene de la BD)
# {nivel_superior}  → "Licenciatura" o "Ingeniería" (viene de la BD)
TITULO_TSU      = "Técnico Superior Universitario"
TITULO_SUPERIOR = "{nivel_superior} en {nombre_pnf}"

PIE_PAGINA   = "Documento generado electrónicamente · Sistema AUTO-RECORD UNEXCA"
LABEL_SHA    = "Verificación SHA-256"

# Etiquetas de secciones
LABEL_TRAYECTO_INICIAL = "TRAYECTO INICIAL"
LABEL_TRAYECTO         = "TRAYECTO {n}"   # {n} se reemplaza por número romano: I, II, III…

# Columnas — tabla de materias anuales (Módulo I + Módulo II)
LABEL_UNIDAD_CURRICULAR = "Unidad Curricular"
LABEL_MOD1              = "Sem. I"
LABEL_MOD2              = "Sem. II"
LABEL_DEFINITIVA        = "Definitiva"

# Columnas — tabla de materias semestrales y trayecto inicial
LABEL_CODIGO = "Código"
LABEL_NOTA   = "Nota"

# ── Colores (R, G, B) — escala 0–255 ────────────────────────────────────────
COLOR_HEADER_FONDO    = (10,  40, 100)    # Fondo del bloque institución + encabezado alumno
COLOR_HEADER_TEXTO    = (255, 255, 255)   # Texto sobre ese fondo oscuro

COLOR_SECCION_FONDO   = (210, 224, 248)   # Banda de título de cada Trayecto
COLOR_SECCION_TEXTO   = (10,  40, 100)

COLOR_TABLA_CAB_FONDO = (35,  75, 155)    # Cabecera de la tabla de notas
COLOR_TABLA_CAB_TEXTO = (255, 255, 255)

COLOR_FILA_PAR        = (240, 245, 255)   # Filas pares del cuerpo de tabla
COLOR_FILA_IMPAR      = (255, 255, 255)   # Filas impares

COLOR_BORDE           = (155, 175, 215)   # Bordes de tabla

# ── Tipografía ───────────────────────────────────────────────────────────────
# Fuentes disponibles sin instalación extra:
#   Helvetica  Helvetica-Bold  Helvetica-Oblique
#   Times-Roman  Times-Bold
#   Courier  Courier-Bold
FUENTE_NORMAL = "Helvetica"
FUENTE_BOLD   = "Helvetica-Bold"
FUENTE_MONO   = "Courier"

TAMANIO_NOMBRE_CORTO = 16   # "UNEXCA" en el encabezado
TAMANIO_INSTITUCION  = 9    # nombre largo de la institución
TAMANIO_TITULO       = 10   # "EXPEDIENTE ACADÉMICO"
TAMANIO_NIVEL        = 9    # "Técnico Superior Universitario  ·  en Informática"
TAMANIO_DATOS_EST    = 9    # filas de datos personales del alumno
TAMANIO_SECCION      = 9    # banda "TRAYECTO I", "TRAYECTO INICIAL"…
TAMANIO_TABLA_CAB    = 8    # cabecera de tabla de notas
TAMANIO_TABLA_CUERPO = 8    # filas de notas
TAMANIO_PIE          = 6    # pie de página

# ── Márgenes en puntos (72 pt ≈ 2.54 cm) ────────────────────────────────────
MARGEN_SUPERIOR  = 45
MARGEN_INFERIOR  = 45
MARGEN_IZQUIERDO = 48
MARGEN_DERECHO   = 48

# ── Anchos de columna en puntos ──────────────────────────────────────────────

# Trayecto inicial  (Código | Unidad Curricular | Nota)
TI_W_CODIGO  = 62
TI_W_MATERIA = 295
TI_W_NOTA    = 55

# Materias anuales  (Unidad Curricular | Sem. I | Sem. II | Definitiva)
AN_W_MATERIA    = 262
AN_W_MOD1       = 58
AN_W_MOD2       = 58
AN_W_DEFINITIVA = 62

# Materias semestrales  (Código | Unidad Curricular | Nota)
SEM_W_CODIGO  = 62
SEM_W_MATERIA = 252
SEM_W_NOTA    = 55

# ── Alturas de fila en puntos ────────────────────────────────────────────────
ALTO_CAB_TABLA  = 17
ALTO_FILA_TABLA = 15

# Espacio vertical entre secciones (puntos)
ESPACIO_SECCION = 8
