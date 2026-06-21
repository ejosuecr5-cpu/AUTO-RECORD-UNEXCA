import hashlib
import os

def calcular_firma(ruta_pdf):
    """
    Calcula el SHA-256 del PDF y guarda el hash en un archivo .sha.
    Retorna el hash calculado como string hexadecimal.
    Lanza FileNotFoundError si el PDF no existe.
    """
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_pdf}")

    with open(ruta_pdf, "rb") as f:
        hash_checksum = hashlib.sha256(f.read()).hexdigest()

    ruta_sha = ruta_pdf.replace(".pdf", ".sha")
    with open(ruta_sha, "w") as f_sha:
        f_sha.write(hash_checksum)

    return hash_checksum

def verificar_integridad(ruta_pdf):
    """
    Compara el SHA-256 actual del PDF contra el hash guardado en el .sha.
    Retorna True si el documento es íntegro, False si fue alterado.
    Lanza FileNotFoundError si el PDF o el .sha no existen.
    """
    if not os.path.exists(ruta_pdf):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_pdf}")

    ruta_sha = ruta_pdf.replace(".pdf", ".sha")
    if not os.path.exists(ruta_sha):
        raise FileNotFoundError(f"No se encontró el archivo de firma: {ruta_sha}")

    with open(ruta_pdf, "rb") as f:
        hash_actual = hashlib.sha256(f.read()).hexdigest()

    with open(ruta_sha, "r") as f_sha:
        hash_guardado = f_sha.read().strip()

    return hash_actual == hash_guardado
