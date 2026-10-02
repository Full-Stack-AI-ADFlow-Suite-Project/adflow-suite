"""Password con scrypt e token di sessione (constitution §3)."""

import hashlib
import hmac
import secrets

# Parametri di scrypt: restano scritti nell'hash, così si possono alzare
# senza invalidare le password già salvate.
_N = 16384
_R = 8
_P = 1
_BYTE_SALT = 16
_BYTE_DIGEST = 64
# Sopra il fabbisogno di scrypt (128 · n · r byte) con i parametri ammessi.
_MAXMEM = 64 * 1024 * 1024
_N_MASSIMO = 2**17


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int, dklen: int) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=dklen
    )


def hash_password(password: str) -> str:
    """Hash da salvare in ``utente.password_hash``: ``scrypt$n$r$p$salt$digest``."""
    salt = secrets.token_bytes(_BYTE_SALT)
    digest = _scrypt(password, salt, _N, _R, _P, _BYTE_DIGEST)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${digest.hex()}"


def verifica_password(password: str, password_hash: str) -> bool:
    """Vero se la password corrisponde all'hash; falso anche per un hash malformato."""
    try:
        schema, n, r, p, salt, digest = password_hash.split("$")
        if schema != "scrypt" or int(n) > _N_MASSIMO:
            return False
        atteso = bytes.fromhex(digest)
        calcolato = _scrypt(
            password, bytes.fromhex(salt), int(n), int(r), int(p), len(atteso)
        )
    except ValueError:
        return False
    return hmac.compare_digest(calcolato, atteso)


def genera_token() -> str:
    """Token di sessione casuale: va nel cookie ``adflow_sessione``, mai nel database."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """sha256 del token (64 caratteri): è ciò che si salva in ``sessione.token_hash``."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
