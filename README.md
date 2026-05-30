# AUTO-RECORD-UNEXCA
#2 Auto-Record UNEXCA: Generador de expedientes académicos con firma digital (checksum) para evitar alteración de datos.

import json
import hashlib

def generar_expediente(estudiante):
    # Estructura del expediente
    expediente = {
        "nombre": estudiante["nombre"],
        "cedula": estudiante["cedula"],
        "carrera": estudiante["carrera"],
        "materias": estudiante["materias"]
    }
    # Serializar datos (formato canónico)
    expediente_json = json.dumps(expediente, sort_keys=True)
    # Crear firma digital usando SHA-256
    checksum = hashlib.sha256(expediente_json.encode('utf-8')).hexdigest()
    resultado = {
        "expediente": expediente,
        "firma_digital": checksum
    }
    return resultado

def validar_expediente(expediente_con_firma):
    # Serializar datos
    expediente_json = json.dumps(expediente_con_firma["expediente"], sort_keys=True)
    # Recalcular checksum
    checksum = hashlib.sha256(expediente_json.encode('utf-8')).hexdigest()
    # Verificar integridad
    return checksum == expediente_con_firma["firma_digital"]

# Ejemplo de uso
estudiante = {
    "nombre": "Ana Pérez",
    "cedula": "12345678",
    "carrera": "Ingeniería Informática",
    "materias": [
        {"nombre": "Matemática I", "nota": 18},
        {"nombre": "Física I", "nota": 15}
    ]
}

expediente = generar_expediente(estudiante)
print("Expediente firmado:")
print(json.dumps(expediente, indent=4, ensure_ascii=False))

es_valido = validar_expediente(expediente)
print("\n¿El expediente es válido?", es_valido)