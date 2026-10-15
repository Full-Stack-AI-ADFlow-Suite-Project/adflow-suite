"""Prova una tantum: pubblica un post vero su Facebook e Instagram.

Non cambia l'adattatore social: serve per l'evidenza di staging di una
pubblicazione reale, con il flusso che un futuro adattatore Meta seguirà.

Configurazione in ``backend/.env`` (o variabili d'ambiente, che hanno
precedenza)::

    META_TOKEN_PAGINA=<page access token>
    META_PAGINA_ID=<id della pagina Facebook>
    META_INSTAGRAM_ID=<id dell'account Instagram business collegato>
    META_GRAPH_VERSIONE=v26.0  # facoltativo

Esempi::

    # solo Facebook: le foto si caricano come file, niente URL pubblici
    uv run python scripts/pubblica_reale.py --confermo \
        --testo "Prova di pubblicazione" --hashtag adflow prova \
        --foto archivio_foto/una.jpg archivio_foto/due.jpg --canali facebook

    # Instagram: serve un URL pubblico per ogni foto. Lo script espone i file
    # su localhost:8787; in un altro terminale un tunnel, per esempio
    #   cloudflared tunnel --url http://localhost:8787
    # e si passa l'URL https che stampa:
    uv run python scripts/pubblica_reale.py --confermo \
        --testo "Prova" --foto una.jpg \
        --public-base https://xxx-yyy.trycloudflare.com

    # oppure con URL già pubblici (uno per foto, nello stesso ordine):
    uv run python scripts/pubblica_reale.py --confermo \
        --testo "Prova" --foto una.jpg \
        --ig-image-url https://staging.example.com/media/una.jpg

Il token non viene mai stampato. ``--confermo`` è obbligatorio: ricorda che
il post esce davvero sulla pagina e sull'account collegati.
"""

import argparse
import mimetypes
import os
import sys
import tempfile
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx

GRAPH = "https://graph.facebook.com"
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def carica_env() -> None:
    """Legge backend/.env e mette le variabili in os.environ, senza sovrascrivere."""
    if not ENV_FILE.exists():
        return
    for riga in ENV_FILE.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga:
            continue
        chiave, _, valore = riga.partition("=")
        os.environ.setdefault(chiave.strip(), valore.strip())


def _errore_meta(risposta: httpx.Response) -> str:
    try:
        err = risposta.json().get("error", {})
        return f"{risposta.status_code}: {err.get('message', risposta.text)}"
    except ValueError:
        return f"{risposta.status_code}: {risposta.text}"


def _graph_post(percorso: str, **parametri) -> dict:
    url = f"{GRAPH}/{VERSION}/{percorso.lstrip('/')}"
    file_payload = parametri.pop("_files", None)
    risposta = httpx.post(url, data=parametri, files=file_payload, timeout=120)
    if risposta.status_code >= 400:
        raise SystemExit(f"Errore Meta su {percorso}: {_errore_meta(risposta)}")
    return risposta.json()


def _graph_get(percorso: str, **parametri) -> dict:
    url = f"{GRAPH}/{VERSION}/{percorso.lstrip('/')}"
    risposta = httpx.get(url, params=parametri, timeout=30)
    if risposta.status_code >= 400:
        raise SystemExit(f"Errore Meta su {percorso}: {_errore_meta(risposta)}")
    return risposta.json()


def pubblica_facebook(page_id: str, token: str, testo: str, foto: list[Path]) -> str:
    """Post con foto sulla pagina; restituisce il permalink.

    Una foto: upload diretto su ``/photos`` pubblicato con il testo.
    Più foto: upload non pubblicato di ognuna, poi ``/feed`` con
    ``attached_media``.
    """
    if len(foto) == 1:
        mime = mimetypes.guess_type(foto[0].name)[0] or "image/jpeg"
        esito = _graph_post(
            f"{page_id}/photos",
            caption=testo,
            access_token=token,
            _files={"source": (foto[0].name, foto[0].read_bytes(), mime)},
        )
        post_id = esito.get("post_id") or esito.get("id")
    else:
        media_ids = []
        for una in foto:
            mime = mimetypes.guess_type(una.name)[0] or "image/jpeg"
            esito = _graph_post(
                f"{page_id}/photos",
                published="false",
                access_token=token,
                _files={"source": (una.name, una.read_bytes(), mime)},
            )
            media_ids.append(esito["id"])
        import json

        parametri = {
            f"attached_media[{i}]": json.dumps({"media_fbid": mid})
            for i, mid in enumerate(media_ids)
        }
        esito = _graph_post(
            f"{page_id}/feed", message=testo, access_token=token, **parametri
        )
        post_id = esito["id"]
    permalink = _graph_get(post_id, fields="permalink_url", access_token=token)
    return permalink.get("permalink_url", f"post {post_id}")


def _contenitore_ig(ig_id: str, token: str, **parametri) -> str:
    esito = _graph_post(f"{ig_id}/media", access_token=token, **parametri)
    return esito["id"]


def _attendi_contenitore(contenitore_id: str, token: str) -> None:
    """Aspetta che il contenitore IG sia FINISHED (la media publish lo richiede)."""
    for _ in range(30):
        stato = _graph_get(
            contenitore_id, fields="status_code", access_token=token
        ).get("status_code")
        if stato == "FINISHED":
            return
        if stato == "ERROR":
            raise SystemExit(f"Contenitore IG {contenitore_id} in errore.")
        time.sleep(2)
    raise SystemExit(f"Contenitore IG {contenitore_id} mai pronto (timeout).")


def pubblica_instagram(ig_id: str, token: str, testo: str, urls: list[str]) -> str:
    """Post con immagine (o carosello) sull'account IG business.

    Ogni immagine deve avere un ``image_url`` pubblicamente raggiungibile:
    è un vincolo dell'API di Instagram, i byte locali non bastano.
    """
    if len(urls) == 1:
        contenitore = _contenitore_ig(ig_id, token, image_url=urls[0], caption=testo)
    else:
        figli = []
        for url in urls:
            figlio = _contenitore_ig(
                ig_id, token, image_url=url, is_carousel_item="true"
            )
            _attendi_contenitore(figlio, token)
            figli.append(figlio)
        contenitore = _contenitore_ig(
            ig_id, token, media_type="CAROUSEL", children=",".join(figli), caption=testo
        )
    _attendi_contenitore(contenitore, token)
    media = _graph_post(
        f"{ig_id}/media_publish", creation_id=contenitore, access_token=token
    )
    permalink = _graph_get(media["id"], fields="permalink", access_token=token)
    return permalink.get("permalink", f"media {media['id']}")


def _server_foto(
    foto: list[Path], porta: int
) -> tuple[ThreadingHTTPServer, dict[str, str]]:
    """Copia le foto in una cartella temporanea e la serve su localhost.

    Restituisce il server e la mappa nome file → percorso URL.
    """
    cartella = Path(tempfile.mkdtemp(prefix="adflow_pub_"))
    nomi = {}
    for i, una in enumerate(foto):
        nome = f"foto_{i}{una.suffix.lower() or '.jpg'}"
        (cartella / nome).write_bytes(una.read_bytes())
        nomi[una.name] = nome
    handler = partial(SimpleHTTPRequestHandler, directory=str(cartella))
    server = ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, nomi


def main() -> None:
    carica_env()
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--confermo", action="store_true", help="obbligatorio: il post esce davvero"
    )
    parser.add_argument("--testo", required=True, help="testo del post")
    parser.add_argument(
        "--hashtag", nargs="*", default=[], help="hashtag senza il simbolo #"
    )
    parser.add_argument(
        "--foto", nargs="+", required=True, type=Path, help="file delle foto"
    )
    parser.add_argument(
        "--canali", choices=["entrambi", "facebook", "instagram"], default="entrambi"
    )
    parser.add_argument(
        "--ig-image-url",
        nargs="*",
        default=None,
        help="URL pubblico per ogni foto, stesso ordine",
    )
    parser.add_argument(
        "--public-base",
        default=None,
        help="URL pubblico del server locale avviato dallo script",
    )
    parser.add_argument("--porta", type=int, default=8787)
    args = parser.parse_args()

    if not args.confermo:
        raise SystemExit(
            "Manca --confermo: questo comando pubblica davvero sui social."
        )

    token = os.environ.get("META_TOKEN_PAGINA")
    page_id = os.environ.get("META_PAGINA_ID")
    ig_id = os.environ.get("META_INSTAGRAM_ID")
    if not token:
        raise SystemExit("META_TOKEN_PAGINA mancante (backend/.env o ambiente).")
    for una in args.foto:
        if not una.is_file():
            raise SystemExit(f"File non trovato: {una}")

    testo = args.testo
    if args.hashtag:
        testo += "\n\n" + " ".join(f"#{h.lstrip('#')}" for h in args.hashtag)

    if args.canali in ("entrambi", "facebook"):
        if not page_id:
            raise SystemExit("META_PAGINA_ID mancante.")
        print("Pubblicazione su Facebook…")
        print(f"  Facebook: {pubblica_facebook(page_id, token, testo, args.foto)}")

    if args.canali in ("entrambi", "instagram"):
        if not ig_id:
            raise SystemExit("META_INSTAGRAM_ID mancante.")
        urls = list(args.ig_image_url or [])
        server = None
        if not urls:
            if not args.public_base:
                raise SystemExit(
                    "Per Instagram serve --ig-image-url per ogni foto, oppure "
                    "--public-base con l'URL pubblico del server locale."
                )
            server, nomi = _server_foto(args.foto, args.porta)
            urls = [
                f"{args.public_base.rstrip('/')}/{nomi[una.name]}" for una in args.foto
            ]
            print(f"Foto esposte su :{args.porta} tramite {args.public_base}")
        elif len(urls) != len(args.foto):
            raise SystemExit(
                "--ig-image-url: un URL per ogni foto, nello stesso ordine."
            )
        try:
            print("Pubblicazione su Instagram…")
            print(f"  Instagram: {pubblica_instagram(ig_id, token, testo, urls)}")
        finally:
            if server:
                server.shutdown()


if __name__ == "__main__":
    VERSION = os.environ.get("META_GRAPH_VERSIONE", "v26.0")
    sys.exit(main())
