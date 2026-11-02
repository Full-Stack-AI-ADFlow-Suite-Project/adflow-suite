"""T3-927: la demo di converge §4 con l'AI vera e Facebook vero, automatica.

Da lanciare a mano, mai da pytest (nei test nessuna chiamata reale, AGENTS.md)::

    uv run python qa/corsia9/T3-927/demo_reale.py --foto CARTELLA --si-spendo

CARTELLA ha almeno 3 foto vere (lato corto da 1080 px in su): due vanno nella
campagna, la terza è quella che l'artigiano carica rispondendo all'operatore.

Il database `adflow_demo` si crea da zero (si rifiuta di partire se esiste);
`backend/.env` non si tocca: provider e indirizzi passano come variabili
d'ambiente ai processi figli. API e worker veri; l'AI è quella di `.env`
(`litellm`), il social è Meta sulla Pagina di prova, solo Facebook (decisione
del 29/10/2026: Instagram resta simulato, D1). Costo atteso: circa 0,1-0,6 $.

I passi sono quelli 1-7 di converge §4. La pubblicazione si fa con il worker
vero e l'orologio avanti: si riavviano API e worker con
`OROLOGIO_GIORNI_AVANTI`. A fine corsa il rapporto è in
`qa/corsia9/T3-927/demo-reale-rapporto.md`. Nessun segreto in output.
"""

import argparse
import io
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

RADICE = Path(__file__).resolve().parents[3]
BACKEND = RADICE / "backend"
RAPPORTO = Path(__file__).with_name("demo-reale-rapporto.md")
NOME_DB = "adflow_demo"
PORTA = 8020
BASE = f"http://127.0.0.1:{PORTA}/api"
ATTESA_AI = 12 * 60  # secondi: generazione vera di una campagna piccola
ATTESA_PUBBLICAZIONE = 5 * 60
COSTO_MASSIMO = 2.0  # dollari: oltre, la prova è fuori scala

sys.path.insert(0, str(BACKEND))

righe_rapporto: list[str] = []


def passo(testo: str) -> None:
    print(f"\n== {testo}", flush=True)
    righe_rapporto.append(f"\n### {testo}\n")


def nota(testo: str) -> None:
    print(f"   {testo}", flush=True)
    righe_rapporto.append(f"- {testo}")


class ProvaFallita(AssertionError):
    pass


def verifica(condizione: object, messaggio: str) -> None:
    if not condizione:
        raise ProvaFallita(messaggio)
    nota(f"ok · {messaggio}")


def _url_db(base: str, nome: str) -> str:
    return base.rsplit("/", 1)[0] + "/" + nome


class Servizi:
    """API e worker veri come processi figli, con l'ambiente della demo."""

    def __init__(self, url_db: str, cartella_log: Path) -> None:
        self.url_db = url_db
        self.log = cartella_log
        self.processi: list[subprocess.Popen] = []

    def avvia(self, giorni_avanti: int) -> None:
        ambiente = {
            **os.environ,
            "DATABASE_URL": self.url_db,
            "AI_PROVIDER": "litellm",
            "SOCIAL_PROVIDER": "meta",
            "META_INSTAGRAM_ID": "",  # solo Facebook
            "OROLOGIO_GIORNI_AVANTI": str(giorni_avanti),
        }
        comandi = [
            ("api", ["uvicorn", "app.main:app", "--port", str(PORTA)]),
            (
                "worker",
                [
                    "procrastinate",
                    "-a",
                    "app.worker.app",
                    "worker",
                    "--concurrency",
                    "1",
                ],
            ),
        ]
        for nome, argomenti in comandi:
            file_log = open(self.log / f"{nome}.log", "ab")
            self.processi.append(
                subprocess.Popen(
                    [sys.executable, "-m", *argomenti],
                    cwd=BACKEND,
                    env=ambiente,
                    stdout=file_log,
                    stderr=subprocess.STDOUT,
                )
            )
        import httpx

        for _ in range(60):
            try:
                if httpx.get(f"{BASE}/health", timeout=2).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(1)
        raise ProvaFallita("l'API non è partita: vedi i log")

    def ferma(self) -> None:
        for processo in self.processi:
            processo.terminate()
        for processo in self.processi:
            try:
                processo.wait(timeout=15)
            except subprocess.TimeoutExpired:
                processo.kill()
        self.processi = []


class Cliente:
    """Una sessione HTTP con il suo utente."""

    def __init__(self, email: str, password: str) -> None:
        import httpx

        self.email = email
        self.password = password
        self.http = httpx.Client(
            base_url=BASE, headers={"Origin": f"http://127.0.0.1:{PORTA}"}, timeout=60
        )
        self.entra()

    def entra(self) -> None:
        r = self.http.post(
            "/auth/login", json={"email": self.email, "password": self.password}
        )
        if r.status_code != 200:
            raise ProvaFallita(f"accesso di {self.email}: {r.status_code}")

    def __call__(self, metodo: str, percorso: str, **kw):
        return self.http.request(metodo, percorso, **kw)

    def ok(self, metodo: str, percorso: str, codice: int = 200, **kw):
        r = self(metodo, percorso, **kw)
        if r.status_code != codice:
            raise ProvaFallita(
                f"{metodo} {percorso}: atteso {codice}, ricevuto {r.status_code} {r.text[:200]}"
            )
        return r.json() if r.content else None


def _vedi(c: Cliente, campagna: int) -> dict:
    return c.ok("GET", f"/campagne/{campagna}/post")


def _post(vista: dict) -> list[dict]:
    return [p for u in vista["uscite"] for p in u["post"]]


def _foto(post: dict) -> list[int]:
    return [f["foto_id"] for f in post["versione_corrente"]["foto"]]


def _attendi(descrizione: str, condizione, secondi: int, ogni: float = 5.0):
    fine = time.time() + secondi
    while time.time() < fine:
        risultato = condizione()
        if risultato:
            return risultato
        time.sleep(ogni)
    raise ProvaFallita(f"tempo scaduto: {descrizione}")


def prepara_foto(sorgente: Path, destinazione: Path) -> Path:
    """Copia 2 foto per la campagna (+ demo.json, solo Facebook) e tiene la terza."""
    foto = sorted(
        p
        for p in sorgente.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"} and p.is_file()
    )
    if len(foto) < 3:
        raise SystemExit("Servono almeno 3 foto nella cartella.")
    campagna = destinazione / "campagna"
    campagna.mkdir()
    for p in foto[:2]:
        shutil.copy(p, campagna / p.name)
    (campagna / "demo.json").write_text(
        json.dumps({"campagna": {"canali": ["facebook"]}}), encoding="utf-8"
    )
    extra = destinazione / ("artigiano" + foto[2].suffix.lower())
    shutil.copy(foto[2], extra)
    return extra


def graph_get(impostazioni, id_esterno: str, campi: str) -> dict:
    import httpx

    r = httpx.get(
        f"https://graph.facebook.com/{impostazioni.meta_graph_versione.strip('/')}/{id_esterno}",
        params={"fields": campi},
        headers={"Authorization": f"Bearer {impostazioni.meta_token_pagina}"},
        timeout=30,
    )
    if r.status_code != 200:
        raise ProvaFallita(f"Graph {id_esterno}: {r.status_code} {r.text[:120]}")
    return r.json()


def esegui(foto_sorgente: Path) -> None:
    os.chdir(BACKEND)  # backend/.env si legge da qui
    archivio = Path(tempfile.mkdtemp(prefix="demo_reale_archivio_"))
    os.environ["ARCHIVIO_FOTO_DIR"] = str(
        archivio
    )  # niente foto nell'archivio di sviluppo
    import sqlalchemy as sa

    from app.core.config import leggi_impostazioni

    base = leggi_impostazioni().database_url
    amministrativo = sa.create_engine(
        _url_db(base, "postgres"), isolation_level="AUTOCOMMIT"
    )
    with amministrativo.connect() as c:
        esiste = c.execute(
            sa.text("select 1 from pg_database where datname=:n"), {"n": NOME_DB}
        ).first()
        if esiste:
            raise SystemExit(
                f"Il database {NOME_DB} esiste già: eliminalo o scegline un altro."
            )
        c.execute(sa.text(f'create database "{NOME_DB}"'))
    url_db = _url_db(base, NOME_DB)
    os.environ["DATABASE_URL"] = url_db  # per le importazioni di `app` qui sotto

    cartella = Path(tempfile.mkdtemp(prefix="demo_reale_"))
    servizi = Servizi(url_db, cartella)
    password = secrets.token_urlsafe(18) + "aA1!"
    try:
        _corsa(servizi, foto_sorgente, cartella, url_db, password)
    finally:
        servizi.ferma()
        RAPPORTO.write_text(
            "# T3-927 · Demo con AI vera e Facebook vero (rapporto automatico)\n"
            + "\n".join(righe_rapporto)
            + "\n",
            encoding="utf-8",
        )
        print(f"\nRapporto: {RAPPORTO}  ·  log di API e worker: {cartella}")


def _corsa(servizi, foto_sorgente, cartella, url_db, password):
    import httpx
    import sqlalchemy as sa
    from PIL import ExifTags, Image

    from app import cli
    from app.core.config import leggi_impostazioni
    from sqlalchemy.orm import Session

    impostazioni = leggi_impostazioni()
    verifica(
        impostazioni.meta_pagina_id and impostazioni.meta_token_pagina,
        "Pagina e token Meta configurati",
    )
    foto_artigiano = prepara_foto(foto_sorgente, cartella)

    passo("0 · Database nuovo, migrazioni, dati della demo (T3-06)")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        env={**os.environ, "DATABASE_URL": url_db},
        check=True,
        capture_output=True,
    )
    motore = sa.create_engine(url_db)
    with Session(motore) as db:
        esito = cli.esegui_demo(
            db, password, cartella / "campagna", 0, datetime.now(timezone.utc)
        )
        db.commit()
    campagna = esito.campagna_id
    verifica(
        len(esito.caricate) == 2 and not esito.scartate,
        "2 foto vere caricate, nessuna scartata",
    )
    nota(f"post chiesti per canale: {esito.post_per_canale}; inizio {esito.inizio}")
    chiesti = esito.post_per_canale
    verifica(chiesti > 2, "le foto sono meno dei post chiesti (ci sarà un'immagine AI)")
    oggi = datetime.now(timezone.utc)

    servizi.avvia(0)
    artigiano = Cliente(cli.DEMO_EMAIL, password)
    operatore = Cliente("operatore@example.com", password)

    passo("1 · Operatore: artigiano nuovo con password provvisoria (CA-79)")
    creato = operatore.ok(
        "POST",
        "/artigiani",
        codice=201,
        json={"email": "nuovo.demo@example.com", "nome": "Nuova Bottega Prova"},
    )
    provvisoria = creato["password_provvisoria"]
    verifica(provvisoria, "la password provvisoria si vede alla creazione")
    doppio = operatore(
        "POST", "/artigiani", json={"email": "nuovo.demo@example.com", "nome": "Altra"}
    )
    verifica(doppio.status_code == 409, "la stessa email: 409")
    nuovo = Cliente("nuovo.demo@example.com", provvisoria)
    verifica(nuovo("GET", "/auth/me").status_code == 200, "il nuovo artigiano entra")
    nuovo.http.close()

    passo("2 · Artigiano: campagna di 7 giorni solo su Facebook, invio (CA-14, CA-54)")
    dettaglio = artigiano.ok("GET", f"/campagne/{campagna}")
    verifica(dettaglio["stato"] == "bozza", "la campagna è in bozza")
    verifica(dettaglio["canali"] == ["facebook"], "solo Facebook")
    verifica(
        "foto_poche" in dettaglio["avvisi"],
        "passo 12: avviso «foto poche» (immagini AI)",
    )
    senza = artigiano(
        "POST", f"/campagne/{campagna}/invia", json={"dichiarazione": False}
    )
    verifica(senza.status_code == 422, "invio senza dichiarazione rifiutato (422)")
    artigiano.ok("POST", f"/campagne/{campagna}/invia", json={"dichiarazione": True})
    verifica(
        artigiano.ok("GET", f"/campagne/{campagna}")["stato"] == "inviata",
        "con la dichiarazione: inviata",
    )

    passo(
        "3 · Generazione vera: post per canale, immagine AI, costo (CA-17, CA-57, CA-80, CA-82)"
    )
    inizio_gen = time.time()

    def pronta():
        stato = operatore.ok("GET", f"/campagne/{campagna}")["stato"]
        if stato in ("in_revisione", "generazione_fallita"):
            return stato

    stato = _attendi("generazione della campagna", pronta, ATTESA_AI)
    if stato != "in_revisione":
        errore = _vedi(operatore, campagna).get("ultimo_errore")
        raise ProvaFallita(f"generazione fallita: {errore}")
    nota(f"generazione in {time.time() - inizio_gen:.0f} s")
    vista = _vedi(operatore, campagna)
    post = _post(vista)
    verifica(
        len(post) == chiesti and {p["canale"] for p in post} == {"facebook"},
        f"{chiesti} post, tutti Facebook",
    )
    ai = [p for p in post if p["riempitivo"] == "immagine_ai"]
    con_foto = [p for p in post if p["riempitivo"] != "immagine_ai"]
    verifica(
        len(ai) == chiesti - 2 and len(con_foto) == 2,
        "i post scoperti hanno un'immagine AI, gli altri una foto vera",
    )
    verifica(
        all(
            p["versione_corrente"]["testo"].endswith("Immagine creata con AI")
            for p in ai
        ),
        "dicitura «Immagine creata con AI» sui post con immagine AI (CA-80)",
    )
    verifica(
        not any(
            "Immagine creata con AI" in p["versione_corrente"]["testo"]
            for p in con_foto
        ),
        "nessuna dicitura sui post con foto vera",
    )
    costo = float(vista["costo_ai"])
    verifica(
        0 < costo < COSTO_MASSIMO, f"costo AI della campagna {costo:.4f} $ (CA-82)"
    )
    righe_rapporto.append(f"- costo AI della campagna: **{costo:.4f} $**")

    passo(
        "4 · Operatore: modifica, rigenera, richiesta all'artigiano, cambia foto, approva (CA-71, CA-86..90, CA-56)"
    )
    uno, due = con_foto
    testo_uno = uno["versione_corrente"]["testo"]
    operatore.ok(
        "POST",
        f"/post/{uno['post_id']}/modifica",
        json={"testo": testo_uno + " Passate a trovarci in bottega."},
    )
    nota("modifica a mano del primo post: 200")
    operatore.ok(
        "POST",
        f"/post/{due['post_id']}/rigenera",
        json={"modalita": "totale", "nota": "Un tono più caldo."},
    )

    def rigenerato():
        p = next(
            x
            for x in _post(_vedi(operatore, campagna))
            if x["post_id"] == due["post_id"]
        )
        if p["intervento_in_corso"] is None and p["versione_corrente"][
            "tipo_intervento"
        ].startswith("rigenera"):
            return p

    rifatto = _attendi("rigenerazione del testo", rigenerato, 5 * 60)
    verifica(
        rifatto["versione_corrente"]["testo"] != due["versione_corrente"]["testo"],
        "testo rigenerato con l'AI vera",
    )
    vecchia_foto = _foto(rifatto)[0]
    operatore.ok(
        "POST",
        f"/campagne/{campagna}/richiesta",
        codice=201,
        json={
            "domanda": "Puoi mandarmi una foto più luminosa di questo pezzo?",
            "foto": [vecchia_foto],
        },
    )
    nota("richiesta all'artigiano con una foto segnata (CA-86)")
    visto = artigiano.ok("GET", f"/campagne/{campagna}")
    verifica(
        visto.get("richiesta") is not None, "l'artigiano vede la richiesta (CA-87)"
    )
    verifica(
        artigiano("GET", f"/campagne/{campagna}/post").status_code == 403,
        "l'artigiano non legge i post (403)",
    )
    estensione = foto_artigiano.suffix.lower()
    mime = "image/png" if estensione == ".png" else "image/jpeg"
    nuova = artigiano.ok(
        "POST",
        f"/campagne/{campagna}/richiesta/foto",
        codice=201,
        files={"file": (foto_artigiano.name, foto_artigiano.read_bytes(), mime)},
        data={"foto_id": str(vecchia_foto), "dichiarazione": "true"},
    )
    artigiano.ok(
        "POST",
        f"/campagne/{campagna}/richiesta/invia",
        json={"risposta": "Ecco la foto con più luce."},
    )
    nota("l'artigiano ha caricato la foto con la dichiarazione e risposto (CA-88)")
    possibili = operatore.ok("GET", f"/post/{due['post_id']}/foto-possibili")
    verifica(
        any(f["foto_id"] == nuova["id"] for f in possibili),
        "la foto nuova è tra le foto possibili del post",
    )
    operatore.ok(
        "POST",
        f"/post/{due['post_id']}/cambia-foto",
        json={"foto_id": nuova["id"], "riscrivi_testo": False},
    )
    p_due = next(
        x for x in _post(_vedi(operatore, campagna)) if x["post_id"] == due["post_id"]
    )
    verifica(_foto(p_due) == [nuova["id"]], "foto nuova in uso (CA-71)")
    verifica(
        operatore.ok("POST", f"/campagne/{campagna}/approva") == {"stato": "attiva"},
        "campagna approvata",
    )
    cal = operatore.ok("GET", f"/campagne/{campagna}/calendario")
    verifica(cal, "calendario della campagna per giorno (CA-56)")

    passo(
        "6 · Dopo l'approvazione: modifica, sposta, annulla, sospendi, riattiva (CA-84, CA-72, CA-85, CA-32)"
    )
    vista = _vedi(operatore, campagna)
    per_id = {p["post_id"]: p for p in _post(vista)}
    operatore.ok(
        "POST",
        f"/post/{uno['post_id']}/modifica",
        json={
            "testo": per_id[uno["post_id"]]["versione_corrente"]["testo"]
            + " Vi aspettiamo."
        },
    )
    nota("modifica a mano dopo l'approvazione (esce tra più di 15 minuti)")
    data_due = datetime.fromisoformat(per_id[due["post_id"]]["data_ora"])
    nuova_data = data_due + timedelta(hours=2)
    operatore.ok(
        "POST",
        f"/post/{due['post_id']}/sposta",
        json={"data_ora": nuova_data.isoformat()},
    )
    nota("post spostato di 2 ore")
    for a in ai[:1]:
        operatore.ok(
            "POST",
            f"/post/{a['post_id']}/annulla",
            json={"nota": "Meglio non uscire con questo."},
        )
    operatore.ok(
        "POST",
        f"/campagne/{campagna}/sospendi",
        json={"nota": "Nota interna di prova."},
    )
    sospesa = artigiano.ok("GET", f"/campagne/{campagna}")
    verifica(
        sospesa["stato"] == "sospesa", "campagna sospesa: l'artigiano la vede ferma"
    )
    verifica(
        "Nota interna di prova" not in json.dumps(sospesa),
        "l'artigiano non legge la nota interna",
    )
    operatore.ok("POST", f"/campagne/{campagna}/riattiva", json={})
    verifica(
        operatore.ok("GET", f"/campagne/{campagna}")["stato"] == "attiva",
        "campagna riattivata",
    )
    attivi = [p for p in _post(_vedi(operatore, campagna)) if p["stato"] == "approvato"]
    verifica(
        len(attivi) == chiesti - 1,
        f"{len(attivi)} post approvati da pubblicare (uno annullato)",
    )

    passo("5 · Pubblicazione vera su Facebook, con l'orologio avanti (CA-81, CA-83)")
    ultima = max(datetime.fromisoformat(p["data_ora"]) for p in attivi)
    giorni = (ultima.date() - oggi.date()).days + 1
    nota(f"orologio di API e worker avanti di {giorni} giorni")
    servizi.ferma()
    servizi.avvia(giorni)
    artigiano = Cliente(cli.DEMO_EMAIL, password)
    operatore = Cliente("operatore@example.com", password)

    def pubblicati():
        stati = {p["post_id"]: p["stato"] for p in _post(_vedi(operatore, campagna))}
        if any(s == "fallito" for s in stati.values()):
            raise ProvaFallita(f"pubblicazione fallita: {stati}")
        if all(stati[p["post_id"]] == "pubblicato" for p in attivi):
            return stati

    _attendi("pubblicazione dei post", pubblicati, ATTESA_PUBBLICAZIONE, ogni=10)
    verifica(True, f"{len(attivi)} post pubblicati dal worker")
    testi_pubblicati = {
        p["post_id"]: p["versione_corrente"]["testo"]
        for p in _post(_vedi(operatore, campagna))
    }
    with sa.create_engine(url_db).connect() as c:
        pubblicazioni = c.execute(
            sa.text(
                "select post_id,id_esterno from pubblicazione "
                "where stato='ok' and post_id = any(:ids) order by post_id"
            ),
            {"ids": [p["post_id"] for p in attivi]},
        ).all()
    verifica(
        len(pubblicazioni) == len(attivi) and all(i for _, i in pubblicazioni),
        "un solo tentativo ok per post, con l'id di Facebook (idempotenza)",
    )
    for post_id, id_esterno in pubblicazioni:
        dati = graph_get(
            impostazioni, id_esterno, "id,created_time,message,full_picture"
        )
        creato = datetime.fromisoformat(dati["created_time"].replace("Z", "+00:00"))
        verifica(
            datetime.now(timezone.utc) - creato < timedelta(hours=1),
            f"post {post_id} presente su Facebook (id {id_esterno}), creato ora",
        )
        verifica(
            testi_pubblicati[post_id][:40] in dati["message"],
            f"post {post_id}: il testo su Facebook è quello approvato",
        )
        im = Image.open(io.BytesIO(httpx.get(dati["full_picture"], timeout=30).content))
        exif = im.getexif()
        verifica(
            not exif.get_ifd(ExifTags.IFD.GPSInfo) and exif.get(0x0112, 1) == 1,
            f"foto del post {post_id}: senza GPS e dritta",
        )
        larghezza, altezza = im.size
        verifica(
            0.8 <= larghezza / altezza <= 1.91,
            f"foto del post {post_id}: {larghezza}x{altezza}, nel formato del canale",
        )
        righe_rapporto.append(
            f"- post {post_id} su Facebook: id `{id_esterno}`, creato {dati['created_time']}"
        )

    def conclusa():
        return operatore.ok("GET", f"/campagne/{campagna}")["stato"] == "conclusa"

    _attendi("conclusione della campagna", conclusa, 3 * 60, ogni=10)
    verifica(True, "la campagna si conclude dopo l'ultimo post")
    righe_rapporto.append(f"\nDatabase `{NOME_DB}`, campagna {campagna}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--foto", required=True, type=Path)
    parser.add_argument(
        "--si-spendo",
        action="store_true",
        help="conferma che la prova costa (AI vera) e pubblica sulla Pagina di prova",
    )
    argomenti = parser.parse_args()
    if not argomenti.si_spendo:
        raise SystemExit(
            "Aggiungi --si-spendo: la prova usa l'AI vera e pubblica su Facebook."
        )
    try:
        esegui(argomenti.foto.resolve())
    except ProvaFallita as errore:
        print(f"\nPROVA FALLITA: {errore}", file=sys.stderr)
        righe_rapporto.append(f"\n**PROVA FALLITA:** {errore}")
        RAPPORTO.write_text(
            "# T3-927 · Demo con AI vera e Facebook vero (rapporto automatico)\n"
            + "\n".join(righe_rapporto)
            + "\n",
            encoding="utf-8",
        )
        sys.exit(1)
    print("\nPROVA SUPERATA")
