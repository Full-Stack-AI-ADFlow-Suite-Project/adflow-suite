"""
Test per la coda dei job (core/coda.py).
"""

import pytest
from unittest.mock import patch, MagicMock
from app.core.coda import accoda, JOB_GENERA_CAMPAGNA, JOB_TICK_PUBBLICAZIONE


def test_accoda_job_valido():
    """Test accoda con un nome job valido."""
    with patch("app.core.coda.app") as mock_app:
        mock_job = MagicMock()
        mock_job.defer.return_value = MagicMock(id=123)
        mock_app.configure_job.return_value = mock_job

        job_id = accoda(JOB_GENERA_CAMPAGNA, campagna_id=123)
        assert job_id == 123
        mock_app.configure_job.assert_called_once_with(name=JOB_GENERA_CAMPAGNA)
        mock_job.defer.assert_called_once_with(campagna_id=123)


def test_accoda_job_con_più_argomenti():
    """Test accoda con più argomenti."""
    with patch("app.core.coda.app") as mock_app:
        mock_job = MagicMock()
        mock_job.defer.return_value = MagicMock(id=456)
        mock_app.configure_job.return_value = mock_job

        job_id = accoda(JOB_GENERA_CAMPAGNA, campagna_id=456, extra="test")
        assert job_id == 456
        mock_job.defer.assert_called_once_with(campagna_id=456, extra="test")


def test_accoda_nome_non_valido():
    """Test accoda con nome non valido genera ValueError."""
    with pytest.raises(ValueError, match="Nome job non valido"):
        accoda("job_inesistente", campagna_id=123)


def test_nomi_job_costanti_definite():
    """Test che tutte le costanti JOB_* siano definite."""
    nomi_attesi = {
        "genera_campagna",
        "tick_pubblicazione",
        "rigenera_post",
        "invia_notifica",
        "ritocca_foto",
        "promemoria",
        "raccogli_metriche",
        "report_settimanale",
    }

    from app.core.coda import (
        JOB_GENERA_CAMPAGNA,
        JOB_TICK_PUBBLICAZIONE,
        JOB_RIGENERA_POST,
        JOB_INVIA_NOTIFICA,
        JOB_RITOCCA_FOTO,
        JOB_PROMEMORIA,
        JOB_RACCOGLI_METRICHE,
        JOB_REPORT_SETTIMANALE,
    )

    costanti = {
        JOB_GENERA_CAMPAGNA,
        JOB_TICK_PUBBLICAZIONE,
        JOB_RIGENERA_POST,
        JOB_INVIA_NOTIFICA,
        JOB_RITOCCA_FOTO,
        JOB_PROMEMORIA,
        JOB_RACCOGLI_METRICHE,
        JOB_REPORT_SETTIMANALE,
    }

    assert costanti == nomi_attesi
