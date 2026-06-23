# Auto-Record UNEXCA

Auto-Record UNEXCA es una solución sociotecnológica diseñada para automatizar, centralizar y asegurar la compilación de historiales académicos dentro de la institución. El sistema unifica los registros estudiantiles en un documento digital único en formato PDF, implementando mecanismos de seguridad criptográfica para garantizar la inmutabilidad de la información y prevenir la alteración ilícita de calificaciones.

## Características Principales

* **Interfaz Gráfica Moderna (Presentación):** Desarrollada con CustomTkinter para ofrecer un entorno visual intuitivo, amigable y accesible que optimiza la carga de datos y disminuye el error humano.
* **Persistencia Relacional (Datos):** Sustitución de archivos planos (JSON) por un motor de base de datos robusto con SQLite (`sqlite3`), estructurando esquemas eficientes para estudiantes, materias y trayectos académicos (PNF).
* **Motor de Renderizado Dinámico:** Compilación en tiempo real de los datos del alumno y sus unidades curriculares para exportarlos formalmente mediante ReportLab.
* **Seguridad Criptográfica:** Implementación de firmas digitales mediante Checksum (SHA-256) a través de la librería `hashlib` para blindar los expedientes contra manipulaciones externas.

---

## Arquitectura y Estructura del Sistema

El proyecto aplica una arquitectura modular que separa estrictamente las responsabilidades del software para facilitar su mantenimiento y escalabilidad:

1.  **`interfaz.py` (Capa de Presentación):** Gestiona las ventanas, la navegación por roles y la captura de datos en los formularios visuales.
2.  **`database.py` (Capa de Datos):** Administra la conexión a `unexca.db`, la ejecución de sentencias SQL, las restricciones de llaves foráneas y el control exhaustivo de excepciones.
3.  **Seguridad:** Módulo encargado de procesar la información estructurada y generar la huella digital única de 64 caracteres (Hash) que valida el documento.

---

## Control de Requerimientos (Metodología Ágil)

La planificación y priorización del desarrollo se gestionaron mediante Historias de Usuario organizadas en el tablero de GitHub Projects:

### Épica 1: Consolidación y Generación de Expedientes
* **US2.1 (Perspectiva del Estudiante):** Como estudiante, quiero exportar mi expediente académico en formato PDF, para presentarlo ante entidades externas de manera rápida y confiable.
* **US2.2 (Perspectiva del Sistema):** Como sistema, quiero compilar el historial de notas, datos personales y periodos cursados en un solo documento estructurado, para evitar la dispersión de información y asegurar la coherencia de los datos.

---

## Manual de Operación y Flujo de Módulos

El sistema cuenta con un control de acceso diferenciado según el rol del operador:

* **Módulo Estudiante (Acceso por Cédula):** Permite el ingreso simplificado para consultar el estado académico, revisar el historial, generar el expediente digital y validar la integridad criptográfica de sus documentos.
* **Módulo Administrativo / Control de Estudios (Acceso Restringido):** Panel con credenciales de seguridad que permite la gestión de registros filiatorios, la carga/modificación de unidades curriculares y la importación masiva de datos a la base de datos a través de archivos estructurados CSV.

---

## Control de Calidad y Pruebas (QA)

El ciclo de vida del software concluyó con una fase rigurosa de validación registrada directamente en las tareas técnicas del repositorio:

* **Pruebas Unitarias:** Verificación de la integridad de datos en SQLite, asegurando que las excepciones (como la ausencia de columnas o datos nulos) sean interceptadas de forma controlada mediante el manejo de excepciones de Python sin afectar la estabilidad del programa.
* **Pruebas de Integración:** Evaluación del flujo dinámico de la GUI y la correcta vinculación de los componentes visuales con los datos en producción del PNF.
* **Pruebas de Seguridad:** Simulación de vulneraciones y edición externa de los expedientes PDFs generados para validar que el sistema quiebre la coincidencia del hash y detecte con éxito cualquier intento de fraude académico.

---

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.14+
* **Interfaz Gráfica:** CustomTkinter / Tkinter
* **Base de Datos:** SQLite3
* **Criptografía:** Hashlib (SHA-256)
* **Generación de Reportes:** ReportLab
* **Gestión de Rutas:** OS (Operating System)

---

## Integrantes (Los Baby Yoda)

* Daniel Bravo – C.I 26.745.209
* Ernesto Cedeño – C.I 27.788.854
* Keybert Herrera – C.I 30.264.679
* Efren Machado – C.I 30.815.535
