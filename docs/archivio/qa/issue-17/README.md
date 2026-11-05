# Rapporto QA · Follow-up #17 (Configurazione proxy/cookie con TLS locale)

**Data:** 30 ottobre 2026
**Ambito:** verifica locale end-to-end della catena HTTPS → reverse proxy TLS → processo Uvicorn separato (`backend/tests/moduli/accesso/test_proxy_http_reale.py`) e documentazione operativa in `docs/sicurezza-accesso.md` e `docs/valutazione-sicurezza.md`.

## 1. Catena provata in locale

1. **Certificato TLS temporaneo verificato**: generazione a runtime di chiave RSA 2048 bit e certificato X.509 con `SubjectAlternativeName: IPAddress(127.0.0.1)`, verificato dal client HTTPS tramite `ssl.create_default_context(cafile=...)` (nessun `CERT_NONE`).
2. **Reverse proxy TLS**: `ThreadingHTTPServer` avvolto in `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` che termina HTTPS e inoltra a Uvicorn su HTTP locale (`127.0.0.1`), sovrascrivendo `X-Forwarded-Proto: https` e `X-Forwarded-For` con l'indirizzo reale del client.
3. **Processo Uvicorn reale separato**: avviato con `proxy_headers=True`, `forwarded_allow_ips=127.0.0.1`, `access_log=False`, `log_level="critical"`, collegato esclusivamente al database isolato `adflow_test` (`SELECT current_database() == 'adflow_test'`).

## 2. Controlli verificati (senza credenziali o chiavi nell'evidenza)

| Controllo | Caso `fidato=127.0.0.1, via_proxy=True` | Caso `fidato=192.0.2.1, via_proxy=False` | Esito |
|---|---|---|---|
| `POST /api/auth/login` e `POST /api/auth/logout` | `200 OK` / `204 No Content` via HTTPS | `200 OK` / `204 No Content` diretto | PASS |
| Attributo `Secure` su `Set-Cookie` (`adflow_sessione`) | Presente (`; Secure`) | Assente (header `X-Forwarded-Proto: https` ignorato perché il mittente non è nel `forwarded_allow_ips`) | PASS |
| Attributi `HttpOnly`, `SameSite=lax`, `Path=/` | Presenti al login e al logout | Presenti al login e al logout | PASS |
| Assenza attributo `Domain=` | Verificata (`"domain=" not in cookie.lower()`) | Verificata (`"domain=" not in cookie.lower()`) | PASS |
| Sovrascrittura header contraffatti (`X-Forwarded-Proto: http`, `X-Forwarded-For: 203.0.113.99`, `X-Request-ID: 000...`) | Proxy impone `X-Forwarded-Proto: https`; backend rigenera `X-Request-ID` a 32 caratteri esadecimali | Backend ignora `X-Forwarded-Proto: https` e rigenera `X-Request-ID` | PASS |

## 3. Esecuzione dei test

```text
$ uv run pytest tests/moduli/accesso/test_proxy_http_reale.py -v
tests/moduli/accesso/test_proxy_http_reale.py::test_catena_https_e_proxy_non_fidato[127.0.0.1-True-True] PASSED
tests/moduli/accesso/test_proxy_http_reale.py::test_catena_https_e_proxy_non_fidato[192.0.2.1-False-False] PASSED
2 passed in 4.16s

$ uv run python scripts/esegui_valutazione_sicurezza.py --security-only
34 passed in 0.44s
```
