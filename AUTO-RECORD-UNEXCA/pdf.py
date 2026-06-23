"""
pdf.py — Motor de generación de expedientes académicos AUTO-RECORD UNEXCA.
Las constantes de diseño (colores, fuentes, márgenes, textos) están en
plantilla_expediente.py — edite ese archivo para personalizar la apariencia.
"""

import os
import hashlib
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import plantilla_expediente as P


# ── helpers internos ──────────────────────────────────────────────────────────

def _rgb(tupla):
    r, g, b = tupla
    return colors.Color(r / 255, g / 255, b / 255)


def _fmt(nota):
    """Formatea una nota numérica: sin decimales si es entero, con si no."""
    if nota is None:
        return "—"
    if isinstance(nota, float) and nota == int(nota):
        return str(int(nota))
    return f"{nota:.2f}".rstrip('0').rstrip('.')


def _romano(n):
    mapa = {0: '0', 1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
            6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X'}
    return mapa.get(n, str(n))


def _tabla_notas(datos, col_w):
    """
    Crea una tabla ReportLab con el estilo del expediente.
    La fila 0 se usa como cabecera.
    """
    t = Table(datos, colWidths=col_w)
    n = len(datos)
    st = [
        # ── cabecera ──────────────────────────────────────────────────────────
        ('BACKGROUND',    (0, 0), (-1, 0),  _rgb(P.COLOR_TABLA_CAB_FONDO)),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  _rgb(P.COLOR_TABLA_CAB_TEXTO)),
        ('FONTNAME',      (0, 0), (-1, 0),  P.FUENTE_BOLD),
        ('FONTSIZE',      (0, 0), (-1, 0),  P.TAMANIO_TABLA_CAB),
        ('ROWHEIGHT',     (0, 0), (0, 0),   P.ALTO_CAB_TABLA),
        # ── cuerpo ───────────────────────────────────────────────────────────
        ('FONTNAME',      (0, 1), (-1, -1), P.FUENTE_NORMAL),
        ('FONTSIZE',      (0, 1), (-1, -1), P.TAMANIO_TABLA_CUERPO),
        ('ROWHEIGHT',     (0, 1), (-1, -1), P.ALTO_FILA_TABLA),
        # ── bordes ───────────────────────────────────────────────────────────
        ('BOX',           (0, 0), (-1, -1), 0.5, _rgb(P.COLOR_BORDE)),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, _rgb(P.COLOR_BORDE)),
        # ── alineación y padding ─────────────────────────────────────────────
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]
    # Columnas numéricas (todas menos la primera): centradas
    for col in range(1, len(col_w)):
        st.append(('ALIGN', (col, 0), (col, -1), 'CENTER'))
    # Filas alternadas
    for i in range(1, n):
        bg = P.COLOR_FILA_PAR if i % 2 == 0 else P.COLOR_FILA_IMPAR
        st.append(('BACKGROUND', (0, i), (-1, i), _rgb(bg)))
    t.setStyle(TableStyle(st))
    return t


def _banda_seccion(texto, ancho, s_seccion):
    """Fila coloreada que encabeza cada sección (Trayecto I, Trayecto Inicial…)."""
    t = Table([[Paragraph(texto, s_seccion)]], colWidths=[ancho])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), _rgb(P.COLOR_SECCION_FONDO)),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t


# ── función principal ─────────────────────────────────────────────────────────

def generar_expediente(cedula, pnf_codigo, nivel, datos_est, notas):
    """
    Genera el PDF del expediente académico y devuelve (ruta_pdf, sha256).

    Parámetros
    ----------
    cedula      : str  — cédula del estudiante
    pnf_codigo  : str  — código del PNF
    nivel       : str  — 'TSU' | 'Licenciatura'
    datos_est   : dict — datos_personales (cedula, nombre, apellido,
                         fecha_nacimiento, lugar_residencia)
    notas       : dict — estructura retornada por
                         database.obtener_notas_para_expediente()
    """
    os.makedirs(P.DIRECTORIO_SALIDA, exist_ok=True)

    fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fecha_tag = fecha_str[:10].replace('-', '')
    nivel_tag = "TSU" if nivel == "TSU" else "LIC"
    filename  = f"expediente_{cedula}_{pnf_codigo}_{nivel_tag}_{fecha_tag}.pdf"
    ruta      = os.path.join(P.DIRECTORIO_SALIDA, filename)

    # Título del nivel
    pnf_nombre  = notas['pnf_nombre']
    nivel_sup   = notas.get('nivel_superior_label', 'Licenciatura')
    if nivel == "TSU":
        linea_nivel = f"{P.TITULO_TSU}  ·  en {pnf_nombre}"
    else:
        linea_nivel = P.TITULO_SUPERIOR.format(
            nivel_superior=nivel_sup, nombre_pnf=pnf_nombre
        )

    # ── Documento ─────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        ruta, pagesize=A4,
        topMargin=P.MARGEN_SUPERIOR, bottomMargin=P.MARGEN_INFERIOR,
        leftMargin=P.MARGEN_IZQUIERDO, rightMargin=P.MARGEN_DERECHO,
    )
    ancho = A4[0] - P.MARGEN_IZQUIERDO - P.MARGEN_DERECHO

    # ── Estilos ───────────────────────────────────────────────────────────────
    s_hdr_gde = ParagraphStyle('hdr_gde',
        fontName=P.FUENTE_BOLD,   fontSize=P.TAMANIO_NOMBRE_CORTO,
        textColor=_rgb(P.COLOR_HEADER_TEXTO), alignment=TA_CENTER)
    s_hdr_med = ParagraphStyle('hdr_med',
        fontName=P.FUENTE_BOLD,   fontSize=P.TAMANIO_INSTITUCION,
        textColor=_rgb(P.COLOR_HEADER_TEXTO), alignment=TA_CENTER)
    s_hdr_sml = ParagraphStyle('hdr_sml',
        fontName=P.FUENTE_NORMAL, fontSize=P.TAMANIO_NIVEL,
        textColor=_rgb(P.COLOR_HEADER_TEXTO), alignment=TA_CENTER)
    s_hdr_tit = ParagraphStyle('hdr_tit',
        fontName=P.FUENTE_BOLD,   fontSize=P.TAMANIO_TITULO,
        textColor=_rgb(P.COLOR_HEADER_TEXTO), alignment=TA_CENTER)
    s_dato_k  = ParagraphStyle('dato_k',
        fontName=P.FUENTE_BOLD,   fontSize=P.TAMANIO_DATOS_EST,
        textColor=colors.HexColor('#1e293b'))
    s_dato_v  = ParagraphStyle('dato_v',
        fontName=P.FUENTE_NORMAL, fontSize=P.TAMANIO_DATOS_EST,
        textColor=colors.HexColor('#1e293b'))
    s_seccion = ParagraphStyle('seccion',
        fontName=P.FUENTE_BOLD,   fontSize=P.TAMANIO_SECCION,
        textColor=_rgb(P.COLOR_SECCION_TEXTO))
    s_pie     = ParagraphStyle('pie',
        fontName=P.FUENTE_NORMAL, fontSize=P.TAMANIO_PIE,
        textColor=colors.grey, alignment=TA_CENTER)
    s_sha     = ParagraphStyle('sha',
        fontName=P.FUENTE_MONO, fontSize=6,
        textColor=colors.grey, alignment=TA_CENTER)

    story = []

    # ── Bloque institucional (encabezado oscuro) ──────────────────────────────
    hdr_rows = [
        [Paragraph(P.NOMBRE_CORTO, s_hdr_gde)],
        [Paragraph(P.NOMBRE_LARGO, s_hdr_med)],
        [Paragraph(P.TITULO_DOCUMENTO, s_hdr_tit)],
        [Paragraph(linea_nivel, s_hdr_sml)],
    ]
    hdr = Table(hdr_rows, colWidths=[ancho])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), _rgb(P.COLOR_HEADER_FONDO)),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 5))

    # ── Datos del estudiante ──────────────────────────────────────────────────
    pers           = datos_est
    nombre_completo = f"{pers.get('nombre', '')} {pers.get('apellido', '')}"
    w_k = ancho * 0.165
    w_v = ancho * 0.335

    est_rows = [
        [Paragraph('Cédula:',              s_dato_k), Paragraph(pers.get('cedula', ''),             s_dato_v),
         Paragraph('Fecha de nacimiento:', s_dato_k), Paragraph(pers.get('fecha_nacimiento', '—'),  s_dato_v)],
        [Paragraph('Nombre:',             s_dato_k), Paragraph(nombre_completo,                    s_dato_v),
         Paragraph('Lugar de residencia:',s_dato_k), Paragraph(pers.get('lugar_residencia', '—'), s_dato_v)],
        [Paragraph('Fecha de generación:',s_dato_k), Paragraph(fecha_str,                          s_dato_v),
         Paragraph('',                    s_dato_k), Paragraph('',                                 s_dato_v)],
    ]
    est_t = Table(est_rows, colWidths=[w_k, w_v, w_k, w_v])
    est_t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX',           (0, 0), (-1, -1), 0.5, _rgb(P.COLOR_BORDE)),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, _rgb(P.COLOR_BORDE)),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING',   (0, 0), (-1, -1), 6),
    ]))
    story.append(est_t)
    story.append(Spacer(1, 10))

    # ── Trayecto Inicial ──────────────────────────────────────────────────────
    inicial = notas.get('trayecto_inicial', [])
    if inicial:
        story.append(_banda_seccion(P.LABEL_TRAYECTO_INICIAL, ancho, s_seccion))
        story.append(Spacer(1, 2))
        filas_ti = [[P.LABEL_CODIGO, P.LABEL_UNIDAD_CURRICULAR, P.LABEL_NOTA]] + [
            [m['codigo'], m['nombre'], _fmt(m['nota'])] for m in inicial
        ]
        story.append(_tabla_notas(filas_ti, [P.TI_W_CODIGO, P.TI_W_MATERIA, P.TI_W_NOTA]))
        story.append(Spacer(1, P.ESPACIO_SECCION))

    # ── Trayectos 1, 2, 3… ───────────────────────────────────────────────────
    for tray_num, data in sorted(notas.get('trayectos', {}).items()):
        anuales     = data.get('anuales', [])
        semestrales = data.get('semestrales', [])
        if not anuales and not semestrales:
            continue

        etiq = P.LABEL_TRAYECTO.format(n=_romano(tray_num))
        story.append(_banda_seccion(etiq, ancho, s_seccion))
        story.append(Spacer(1, 2))

        # Primero las materias anuales (con Sem. I | Sem. II | Definitiva)
        if anuales:
            filas_an = [
                [P.LABEL_UNIDAD_CURRICULAR, P.LABEL_MOD1, P.LABEL_MOD2, P.LABEL_DEFINITIVA]
            ] + [
                [m['nombre'], _fmt(m['mod1']), _fmt(m['mod2']), _fmt(m['definitiva'])]
                for m in anuales
            ]
            story.append(_tabla_notas(
                filas_an,
                [P.AN_W_MATERIA, P.AN_W_MOD1, P.AN_W_MOD2, P.AN_W_DEFINITIVA]
            ))
            if semestrales:
                story.append(Spacer(1, 4))

        # Después las semestrales (Código | Unidad Curricular | Nota)
        if semestrales:
            filas_sem = [
                [P.LABEL_CODIGO, P.LABEL_UNIDAD_CURRICULAR, P.LABEL_NOTA]
            ] + [
                [m['codigo'], m['nombre'], _fmt(m['nota'])] for m in semestrales
            ]
            story.append(_tabla_notas(
                filas_sem,
                [P.SEM_W_CODIGO, P.SEM_W_MATERIA, P.SEM_W_NOTA]
            ))

        story.append(Spacer(1, P.ESPACIO_SECCION))

    # ── Pie de página ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width='100%', thickness=0.5, color=_rgb(P.COLOR_BORDE)))
    story.append(Spacer(1, 3))
    story.append(Paragraph(P.PIE_PAGINA, s_pie))
    story.append(Paragraph(f"Generado: {fecha_str}", s_pie))

    # Construir el PDF
    doc.build(story)

    # Calcular SHA-256 y guardar .sha
    with open(ruta, 'rb') as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    with open(ruta.replace('.pdf', '.sha'), 'w') as f:
        f.write(sha256)

    return ruta, sha256
