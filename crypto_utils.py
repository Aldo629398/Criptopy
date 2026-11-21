import os
import secrets
import string
from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Parámetros estándar para Argon2id
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_LEN = 32  # 256 bits para AES-256

def generate_strong_password(length: int = 20) -> str:
    """Genera una contraseña segura combinando letras, números y símbolos."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        # Garantizar al menos una mayúscula, minúscula, dígito y símbolo
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in "!@#$%^&*()-_=+" for c in password)):
            return password

def derive_key(password: str, salt: bytes) -> bytes:
    """Deriva una llave de 256 bits usando Argon2id."""
    return hash_secret_raw(
        secret=password.encode('utf-8'),
        salt=salt,
        time_cost=3,         # Iteraciones
        memory_cost=65536,   # 64 MB de RAM
        parallelism=4,
        hash_len=KEY_LEN,
        type=Type.ID
    )

def encrypt_bytes(data: bytes, password: str) -> bytes:
    """Cifra bytes con AES-256-GCM. Formato: [SALT (16B)] + [NONCE (12B)] + [CIPHERTEXT + TAG]."""
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return salt + nonce + ciphertext

def decrypt_bytes(encrypted_data: bytes, password: str) -> bytes:
    """Descifra bytes verificando autenticidad e integridad."""
    if len(encrypted_data) < SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Archivo corrupto o demasiado corto.")
        
    salt = encrypted_data[:SALT_SIZE]
    nonce = encrypted_data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = encrypted_data[SALT_SIZE + NONCE_SIZE:]
    
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    # Si la contraseña es incorrecta o el archivo fue alterado, lanzará InvalidTag
    return aesgcm.decrypt(nonce, ciphertext, None)