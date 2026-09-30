# AdFlow Suite

Repository ufficiale per il progetto di fine tirocinio Full Stack AI.

## 📁 Struttura del Progetto
- `backend/`: API FastAPI e Worker Procrastinate (Python)
- `frontend/`: Interfaccia utente (React + TypeScript + Mantine)
- `docs/`: Documentazione tecnica del progetto (vedi sotto)

## 📚 Documentazione

Prima di scrivere codice, leggere:
- [`docs/ADR.md`](docs/ADR.md): registro delle decisioni architetturali (una riga per decisione, mai cancellata)
- [`docs/SPEC-CODICE.md`](docs/SPEC-CODICE.md): regole tecniche vincolanti, struttura del repo, modello dati, contratto API, sprint corrente
- [`docs/architettura/`](docs/architettura/AdFlow-flusso-architettura-v4.md): flusso e architettura dettagliati (v4.6), diagrammi, schede statiche (scheda bottega, pagina operatore) e script per rigenerarli

## 🚀 Setup Iniziale (Fase 1 - Locale)

### 1. Backend & Worker
1. Entra nella cartella: `cd backend`
2. Crea l'ambiente virtuale: `python -m venv venv`
3. Attivalo:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Installa le dipendenze: `pip install -r requirements.txt`
5. **Importante**: Installa i pre-commit hook (una volta sola): `pre-commit install`
6. Copia `.env.example` in `.env` e inserisci le tue credenziali locali.
7. Assicurati che PostgreSQL sia in esecuzione e crea i DB `adflow` e `adflow_test`.
8. Avvia il server: `uvicorn main:app --reload`

### 2. Frontend
1. Entra nella cartella: `cd frontend`
2. Installa le dipendenze: `npm install`
3. Copia `.env.example` in `.env`.
4. Avvia il server di sviluppo: `npm run dev`

## 🔧 Regole di Git (Leggere attentamente!)
1. **NON** lavorare mai direttamente sul branch `main`.
2. Prima di iniziare un task, crea un branch: `git checkout -b feature/nome-task`
3. Prima di fare `git commit`, assicurati di aver lanciato `pre-commit install` al primo setup. Questo formatterà automaticamente il tuo codice.
4. Quando hai finito, pusha il branch e apri una **Pull Request** su GitHub. L'admin farà la review e il merge.
