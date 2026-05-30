# Auto-Record UNEXCA 🎓⚙️

Sistema automatizado para la consolidación, generación y verificación de expedientes académicos con integridad criptográfica, desarrollado para la comunidad universitaria de la UNEXCA.

## 🚀 Descripción del Proyecto
Auto-Record UNEXCA es una aplicación de escritorio diseñada para compilar el historial de notas, datos personales y periodos cursados por los estudiantes en un formato estructurado. Para evitar la alteración de los documentos emitidos y garantizar su validez ante entidades externas, el sistema genera automáticamente un **checksum digital (SHA-256)** embebido en cada expediente PDF.

---

## 🛠️ Tecnologías Utilizadas
* **Lenguaje:** Python 3.x
* **Interfaz Gráfica (GUI):** Tkinter
* **Generación de Documentos:** ReportLab (u otra librería de PDF que utilicen)
* **Seguridad y Criptografía:** `hashlib` (SHA-256)
* **Persistencia de Datos:** Archivos estructurados (`.json` / `.txt`)

---

## 🎯 Planificación del Desarrollo (Épicas e Historias de Usuario)

### Épica 1: Consolidación y Generación de Expedientes
* **US2.1 - Exportación de Expediente en PDF:** Permite al estudiante exportar su historial académico en un formato PDF estandarizado y formal.
* **US2.2 - Compilación de Datos Estructurados:** El sistema extrae y organiza automáticamente la información de las materias, periodos y calificaciones desde el almacenamiento local.
* **US2.3 - Integridad Criptográfica (Checksum):** Implementación de la firma digital mediante SHA-256 en el pie de página del documento para evitar fraudes o modificaciones secundarias.


* **Institución:** Universidad Nacional Experimental de la Gran Caracas (UNEXCA)
* **Asignatura / Proyecto:** PROGRAMACION I 
