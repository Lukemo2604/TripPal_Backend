# src/utils/hash.py
import bcrypt

def hash_password(plain_text_password: str) -> bytes:
    """Generate a bcrypt hash for the given plain text password."""
    return bcrypt.hashpw(plain_text_password.encode('utf-8'), bcrypt.gensalt())

def check_password(plain_text_password: str, hashed_password: bytes) -> bool:
    """Check a plain text password against the stored bcrypt hashed password."""
    return bcrypt.checkpw(plain_text_password.encode('utf-8'), hashed_password)
