"""Il catalogo del ritocco è coerente (RT-12, ADR-124)."""

from dataclasses import fields

import pytest

from app.moduli.campagne import ritocco_catalogo as catalogo
from app.moduli.campagne.esecutore import VERSIONE_ESECUTORE


def test_ogni_codice_ha_un_significato_e_un_effetto_dichiarato():
    for tabella in (catalogo.NOTE, catalogo.RUOLI_ZONA):
        assert tabella
        for nome, codice in tabella.items():
            assert codice.significato.strip(), nome
            assert codice.effetto in catalogo.EFFETTI, nome


def test_ogni_effetto_dichiarato_e_usato():
    usati = {
        c.effetto for t in (catalogo.NOTE, catalogo.RUOLI_ZONA) for c in t.values()
    }
    assert usati <= catalogo.EFFETTI


def test_i_codici_attesi_dalla_nota():
    assert list(catalogo.NOTE) == [
        "lontana", "decentrata", "storta", "ambiente", "non_tagliare",
        "ruota_90", "ruota_180", "ruota_270",
        "scura", "chiara", "controluce", "flash",
        "calda", "fredda", "verde", "magenta",
        "riflessi_bordi", "riflessi_soggetto",
        "mossa_lieve", "mossa_forte", "foto_di_foto", "screenshot", "grafica",
        "marchi",
    ]  # fmt: skip
    assert list(catalogo.RUOLI_ZONA) == [
        "tieni", "togli", "neutro", "volto", "nome", "indirizzo", "targa", "dati",
    ]  # fmt: skip


def test_i_gruppi_derivati_usano_solo_codici_veri():
    for gruppo in catalogo.NOTE_IN_CONFLITTO:
        assert gruppo <= set(catalogo.NOTE)
        assert len(gruppo) == 2
    assert catalogo.NOTE_SOLO_ORIGINALE == {"screenshot", "grafica"}
    assert catalogo.NOTE_DOMINANTE <= set(catalogo.NOTE)
    assert set(catalogo.DOMINANTE_ASSI.values()) == catalogo.NOTE_DOMINANTE


@pytest.mark.parametrize("nome", sorted(catalogo.FASCE))
def test_le_soglie_sono_dentro_il_dominio_e_crescenti(nome):
    fascia = catalogo.FASCE[nome]
    minimo, massimo = fascia.dominio
    assert minimo < massimo
    assert len(fascia.soglie) == len(fascia.nomi) - 1
    assert list(fascia.soglie) == sorted(set(fascia.soglie))
    assert all(minimo < s < massimo for s in fascia.soglie)
    assert fascia.normali <= set(fascia.nomi)
    assert fascia.normali != set(
        fascia.nomi
    ), "se tutto è normale non si dice mai niente"


@pytest.mark.parametrize(
    ("misura", "valore", "atteso"),
    [
        ("nitidezza", 10.0, "bassa"),
        ("nitidezza", 30.0, "media"),
        ("nitidezza", 149.9, "media"),
        ("nitidezza", 500.0, "alta"),
        ("esposizione", 12.0, "scura"),
        ("esposizione", 50.0, "normale"),
        ("esposizione", 90.0, "chiara"),
        ("luci_bruciate", 0.0, "nessuna"),
        ("luci_bruciate", 1.0, "poche"),
        ("luci_bruciate", 8.0, "molte"),
        ("ombre_chiuse", 0.2, "nessuna"),
        ("ombre_chiuse", 2.0, "poche"),
        ("ombre_chiuse", 20.0, "molte"),
        ("compressione", 30.0, "forte"),
        ("compressione", 80.0, "lieve"),
        ("compressione", 95.0, "nessuna"),
    ],
)
def test_la_fascia_di_un_valore(misura, valore, atteso):
    assert catalogo.FASCE[misura].di(valore) == atteso


def test_la_dominante_ha_soglia_e_assi():
    minimo, massimo = catalogo.DOMINANTE_DOMINIO
    assert minimo < catalogo.DOMINANTE_SOGLIA < massimo
    assert set(catalogo.DOMINANTE_ASSI) == {"a+", "a-", "b+", "b-"}


def test_i_parametri_hanno_senso_dominio_e_un_valore_per_ogni_variante():
    nomi = {f.name for f in fields(catalogo.Parametri)}
    assert set(catalogo.SENSO) == nomi
    assert set(catalogo.DOMINIO_PARAMETRI) == nomi
    assert set(catalogo.SENSO.values()) == {"maggiore", "minore"}
    for variante, parametri in catalogo.PARAMETRI_VARIANTE.items():
        for nome in nomi:
            minimo, massimo = catalogo.DOMINIO_PARAMETRI[nome]
            valore = getattr(parametri, nome)
            assert minimo <= valore <= massimo, (variante, nome, valore)


@pytest.mark.parametrize("nome", [f.name for f in fields(catalogo.Parametri)])
def test_la_spinta_non_e_mai_piu_debole_della_standard(nome):
    standard = getattr(catalogo.STANDARD, nome)
    spinta = getattr(catalogo.SPINTA, nome)
    if catalogo.SENSO[nome] == "maggiore":
        assert spinta >= standard
    else:
        assert spinta <= standard


def test_la_spinta_cambia_qualcosa_per_ogni_parametro_tranne_nessuno():
    uguali = [
        f.name
        for f in fields(catalogo.Parametri)
        if getattr(catalogo.STANDARD, f.name) == getattr(catalogo.SPINTA, f.name)
    ]
    assert uguali == []


def test_la_standard_non_ingrandisce_e_non_corregge_il_bianco_senza_riferimento():
    assert catalogo.STANDARD.ingrandimento_max == 1.0
    assert catalogo.STANDARD.bianco_senza_neutro_tetto == 0.0
    assert catalogo.STANDARD.flash_dose == 0.0


def test_le_versioni():
    assert catalogo.VERSIONE_LOCALE == "locale-1"
    assert catalogo.VERSIONE_DIAGNOSI == "diagnosi-1"
    assert catalogo.VERSIONE_RITOCCO == "ritocco-1"
    assert catalogo.VERSIONE_RITOCCO == VERSIONE_ESECUTORE
    assert catalogo.VARIANTI == ("originale", "standard", "spinta")
