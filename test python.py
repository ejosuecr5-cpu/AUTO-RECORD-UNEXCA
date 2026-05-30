import json
import hashlib
from datetime import datetime

def validar_datos_estudiante(estudiante):
    """
    Valida que el diccionario 'estudiante' tenga los campos requeridos y tipos válidos.
    Lanza ValueError si se detecta un problema.
    """
    campos_obligatorios = {
        "nombre": str,
        "cedula": str,
        "carrera": str,
        "materias": list
    }
    for campo, tipo in campos_obligatorios.items():
        if campo not in estudiante:
            raise ValueError(f"Falta el campo obligatorio: {campo}")
        if not isinstance(estudiante[campo], tipo):
            raise ValueError(f"El campo '{campo}' debe ser de tipo {tipo.__name__}")

    # Validar el contenido de la lista de materias
    for i, materia in enumerate(estudiante["materias"]):
        if not isinstance(materia, dict):
            raise ValueError(f"La materia #{i+1} no es un diccionario válido.")
        if "nombre" not in materia or "nota" not in materia:
            raise ValueError(f"A la materia #{i+1} le falta 'nombre' o 'nota'.")
        if not isinstance(materia["nombre"], str):
            raise ValueError(f"El nombre de la materia #{i+1} debe ser texto.")
        if not isinstance(materia["nota"], (int, float)):
            raise ValueError(f"La nota de la materia #{i+1} debe ser numérica.")

def generar_expediente(estudiante):
    """
    Genera un expediente firmado digitalmente (checksum SHA-256).
    Añade la fecha y hora (timestamp).
    """
    validar_datos_estudiante(estudiante)
    expediente = {
        "nombre": estudiante["nombre"],
        "cedula": estudiante["cedula"],
        "carrera": estudiante["carrera"],
        "materias": estudiante["materias"],
        "creado_en": datetime.now().isoformat(timespec='seconds')
    }
    expediente_json = json.dumps(expediente, sort_keys=True, ensure_ascii=False)
    checksum = hashlib.sha256(expediente_json.encode('utf-8')).hexdigest()
    return {
        "expediente": expediente,
        "firma_digital": checksum
    }

def validar_expediente(expediente_con_firma):
    """
    Valida la integridad de un expediente firmado.
    """
    expediente_json = json.dumps(expediente_con_firma["expediente"], sort_keys=True, ensure_ascii=False)
    checksum = hashlib.sha256(expediente_json.encode('utf-8')).hexdigest()
    return checksum == expediente_con_firma["firma_digital"]

# Ejemplo de uso
if __name__ == "__main__":
    estudiante = {
        "nombre": "Ana Pérez",
        "cedula": "12345678",
        "carrera": "Ingeniería Informática",
        "materias": [
            {"nombre": "Matemática I", "nota": 18},
            {"nombre": "Física I", "nota": 15}
        ]
    }
    try:
        expediente = generar_expediente(estudiante)
        print("Expediente firmado:")
        print(json.dumps(expediente, indent=4, ensure_ascii=False))

        es_valido = validar_expediente(expediente)
        print("\n¿El expediente es válido?", es_valido)
    except ValueError as e: 
        print("Error al generar expediente:", e)
