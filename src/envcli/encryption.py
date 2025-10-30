import os
from pathlib import Path
from cryptography.fernet import Fernet
from .config import CONFIG_DIR

KEY_FILE = CONFIG_DIR / "key"

def get_or_create_key() -> bytes:
    """Get existing key or create a new one."""
    CONFIG_DIR.mkdir(exist_ok=True)
    if KEY_FILE.exists():
        with open(KEY_FILE, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)
        return key

def encrypt_file(file_path: str):
    """Encrypt a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    key = get_or_create_key()
    fernet = Fernet(key)

    with open(path, 'rb') as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(path, 'wb') as f:
        f.write(encrypted)

def decrypt_file(file_path: str):
    """Decrypt a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File {file_path} not found")

    key = get_or_create_key()
    fernet = Fernet(key)

    with open(path, 'rb') as f:
        data = f.read()

    try:
        decrypted = fernet.decrypt(data)
    except Exception:
        raise ValueError("Failed to decrypt file. Wrong key or not encrypted.")

    with open(path, 'wb') as f:
        f.write(decrypted)
