"""
Funzioni di sicurezza: hash password, token sessione, cifratura.

TODO: Implementare completamente in T1-06
"""

import hashlib
from typing import Optional


def hash_password(password: str) -> str:
    """
    Hash di una password con scrypt.

    Args:
        password: Password in chiaro

    Returns:
        Hash della password

    TODO: Implementare in T1-06
    """
    # Placeholder: usare scrypt in T1-06
    return hashlib.sha256(password.encode()).hexdigest()


def verifica_password(password: str, password_hash: str) -> bool:
    """
    Verifica che una password corrisponda all'hash.

    Args:
        password: Password in chiaro
        password_hash: Hash salvato nel database

    Returns:
        True se la password è corretta

    TODO: Implementare in T1-06
    """
    # Placeholder: usare scrypt in T1-06
    return hash_password(password) == password_hash


def crea_token_sessione() -> str:
    """
    Crea un token di sessione casuale.

    Returns:
        Token di sessione

    TODO: Implementare in T1-06
    """
    # Placeholder: generare token sicuro in T1-06
    import secrets
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """
    Hash di un token (per salvare nel database).

    Args:
        token: Token in chiaro

    Returns:
        Hash del token (sha256)

    TODO: Implementare in T1-06
    """
    return hashlib.sha256(token.encode()).hexdigest()


def cifra_permesso(permesso: str) -> str:
    """
    Cifra un permesso social per salvare nel database.

    Args:
        permesso: Permesso in chiaro

    Returns:
        Permesso cifrato

    TODO: Implementare in T1-06
    """
    # Placeholder: usare Fernet in T1-06
    return permesso


def decifra_permesso(permesso_cifrato: str) -> str:
    """
    Decifra un permesso social dal database.

    Args:
        permesso_cifrato: Permesso cifrato

    Returns:
        Permesso in chiaro

    TODO: Implementare in T1-06
    """
    # Placeholder: usare Fernet in T1-06
    return permesso_cifrato
