"""SAST leggero e senza dipendenze esterne per primitive ad alto rischio."""

import ast
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Impostazioni

APP = Path(__file__).resolve().parents[1] / "app"


def _nome_chiamata(nodo: ast.AST) -> str:
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return f"{_nome_chiamata(nodo.value)}.{nodo.attr}"
    return ""


def _problemi_sast(sorgente: str) -> list[str]:
    albero = ast.parse(sorgente)
    problemi: list[str] = []

    for nodo in ast.walk(albero):
        if not isinstance(nodo, ast.Call):
            continue

        chiamata = _nome_chiamata(nodo.func)
        foglia = chiamata.rsplit(".", 1)[-1]
        if foglia in {"eval", "exec"} or chiamata in {"os.system", "os.popen"}:
            problemi.append("dynamic-code-or-shell")
        if chiamata in {"pickle.load", "pickle.loads", "_pickle.load", "_pickle.loads"}:
            problemi.append("unsafe-deserialization")
        if chiamata in {"text", "sqlalchemy.text"} and nodo.args:
            query = nodo.args[0]
            if isinstance(query, (ast.JoinedStr, ast.BinOp)) or (
                isinstance(query, ast.Call)
                and _nome_chiamata(query.func).endswith(".format")
            ):
                problemi.append("interpolated-sql")

        for keyword in nodo.keywords:
            if (
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                problemi.append("shell-true")
            if (
                keyword.arg == "verify"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
            ):
                problemi.append("tls-verification-disabled")

    return problemi


def test_sorgenti_backend_senza_primitive_ad_alto_rischio() -> None:
    problemi: list[str] = []
    for percorso in APP.rglob("*.py"):
        sorgente = percorso.read_text(encoding="utf-8")
        for regola in _problemi_sast(sorgente):
            problemi.append(f"{percorso.relative_to(APP)}: {regola}")

    assert not problemi, "\n".join(problemi)


@pytest.mark.parametrize(
    ("sorgente", "regola"),
    [
        ("eval(payload)", "dynamic-code-or-shell"),
        ("os.system(command)", "dynamic-code-or-shell"),
        ("pickle.loads(payload)", "unsafe-deserialization"),
        ('text(f"SELECT * FROM utenti WHERE id={user_id}")', "interpolated-sql"),
        (
            'text("SELECT * FROM utenti WHERE id={}".format(user_id))',
            "interpolated-sql",
        ),
        ("subprocess.run(command, shell=True)", "shell-true"),
        ("httpx.get(url, verify=False)", "tls-verification-disabled"),
    ],
)
def test_regole_sast_rilevano_pattern_pericolosi(sorgente: str, regola: str) -> None:
    assert regola in _problemi_sast(sorgente)


def _impostazioni_produzione(**extra) -> Impostazioni:
    return Impostazioni(
        _env_file=None,
        database_url="postgresql+psycopg://app:pass@db/app",
        database_url_test="postgresql+psycopg://app:pass@db/app_test",
        ambiente="produzione",
        login_limite_segreto="segreto-casuale-di-test-lungo-32-caratteri",
        **extra,
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://media.example.test",
        "https:///senza-host",
        "https://utente:password@media.example.test",
        "https://media.example.test/?token=non-ammesso",
        "https://media.example.test/#fragment",
        "https://media.example.test:99999",
    ],
)
def test_config_produzione_rifiuta_url_foto_non_sicuri_o_malformati(
    url: str,
) -> None:
    with pytest.raises(ValidationError):
        _impostazioni_produzione(foto_url_pubblico=url)


def test_instagram_meta_in_produzione_richiede_url_foto_https() -> None:
    with pytest.raises(ValidationError):
        _impostazioni_produzione(
            social_provider="meta",
            meta_instagram_id="123456",
        )


def test_config_produzione_accetta_url_foto_https_valido() -> None:
    impostazioni = _impostazioni_produzione(
        foto_url_pubblico="https://media.example.test/adflow"
    )
    assert impostazioni.foto_url_pubblico == "https://media.example.test/adflow"
