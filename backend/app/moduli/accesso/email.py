"""Validazione senza DNS e identificazione compatibile con gli account storici."""
from email_validator import EmailNotValidError, validate_email
from app.core.config import leggi_impostazioni
from app.core.errori import DatiNonValidi


def normalizza_email(email: str) -> str:
    try:
        return validate_email(
            email.strip(),
            check_deliverability=False,
            test_environment=leggi_impostazioni().email_test_environment,
        ).normalized.lower()
    except EmailNotValidError:
        raise DatiNonValidi("Indirizzo email non valido.") from None


def identita_login(email: str) -> str:
    # Non blocca account creati con la precedente politica (.test incluso).
    # Nuove creazioni usano sempre la politica rigorosa di normalizza_email.
    try:
        return normalizza_email(email)
    except DatiNonValidi:
        return email.strip().lower()


def candidati_login(email: str) -> set[str]:
    """Forme storiche, Unicode e IDNA dell'indirizzo, senza DNS."""
    candidati = {email.strip().lower(), identita_login(email)}
    try:
        validata = validate_email(
            email.strip(),
            check_deliverability=False,
            test_environment=leggi_impostazioni().email_test_environment,
        )
    except EmailNotValidError:
        return candidati
    if validata.ascii_email is not None:
        candidati.add(validata.ascii_email.lower())
    return candidati
