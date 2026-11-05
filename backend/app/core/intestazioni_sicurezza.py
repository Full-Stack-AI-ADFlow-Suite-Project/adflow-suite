"""Intestazioni di sicurezza sulle risposte dell'API (RL-015, R-01).

Le cinque intestazioni di base di OWASP ASVS V3 — CSP, HSTS, ``nosniff``,
``Referrer-Policy`` e ``X-Frame-Options`` — su ogni risposta il cui percorso
comincia con ``/api``, errori compresi. La CSP ``default-src 'none'``
romperebbe ``/docs`` e ``/openapi.json``: fuori dall'API non si manda. Le
stesse intestazioni le ridice anche il proxy per il solo percorso ``/api``
(``backend/README.md``, In produzione); la CSP di una risposta d'immagine non tocca
la pagina che la incorpora: le foto restano visibili nel frontend.
"""

# Il prefisso dei router dell'API in ``main.py``; rientrano anche le foto
# servite da ``/api/foto/…``.
PREFISSO_API = "/api"

INTESTAZIONI = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Strict-Transport-Security": "max-age=31536000",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
}


class IntestazioniSicurezza:
    """Le intestazioni di sicurezza su ``/api`` e solo lì.

    In ``main.py`` va aggiunto per ultimo, così è il più esterno e le porta
    anche le risposte fatte dai middleware interni o dal routing (403, 404,
    413). Un'intestazione già presente con lo stesso nome si sostituisce.
    """

    def __init__(self, app, prefisso: str = PREFISSO_API):
        self.app = app
        self.prefisso = prefisso

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope.get("path", "").startswith(
            self.prefisso
        ):
            return await self.app(scope, receive, send)

        aggiunte = {
            nome.lower().encode(): valore.encode()
            for nome, valore in INTESTAZIONI.items()
        }

        async def invia(messaggio):
            if messaggio["type"] == "http.response.start":
                messaggio["headers"] = [
                    (chiave, valore)
                    for chiave, valore in messaggio["headers"]
                    if chiave.lower() not in aggiunte
                ] + list(aggiunte.items())
            await send(messaggio)

        await self.app(scope, receive, invia)
