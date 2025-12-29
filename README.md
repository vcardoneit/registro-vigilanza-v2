# 🛡 Registro Vigilanza

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-darkgreen?logo=django&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-336791?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Enabled-DC382D?logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-GPLv3-blue.svg)

Il progetto "Registro Vigilanza" è una piattaforma web progettata per la digitalizzazione e la gestione centralizzata delle attività di vigilanza presso il Radiotelescopio di Noto. Il sistema sostituisce i tradizionali registri cartacei con una soluzione digitale che offre tracciabilità in tempo reale, integrazione con i sistemi di identità aziendali (LDAP) e generazione automatizzata di reportistica.

## 📋 Caratteristiche

- **Dashboard in tempo reale** con WebSocket (Channels + Redis)
- **Area riservata** per utenti autenticati
- **Gestione registro** completa con generazione PDF
- **Autenticazione LDAP** integrata
- **Architettura Docker** pronta per la produzione
- **Database PostgreSQL** per affidabilità e scalabilità
- **Interfaccia responsive** con template moderni

## ⭐ Funzionalità

### Autenticazione e Accesso
- **Login LDAP INAF**: autenticazione integrata con il server LDAP INAF
- **Login vigilanti**: autenticazione standard per il personale di vigilanza
- **Accesso centrale operativa**: account dedicato per visualizzazione documenti
- **Cambio password**: funzionalità per aggiornamento credenziali dei vigilanti
- **Gestione turni automatica**: all'accesso/logout dei vigilanti viene creato/chiuso automaticamente un turno

### Registro Giornaliero
- **Creazione automatica**: registro giornaliero creato automaticamente
- **Gestione presenze personale INAF**: tracciamento del personale INAF presente nella struttura
- **Registrazione accessi esterni**: inserimento di visitatori e ditte esterne con nominativi multipli
- **Gestione orari**: registrazione orari di ingresso e uscita per ogni accesso
- **Note giornaliere**: campo note per annotazioni sulla giornata
- **Marcature**: sistema di marcatura oraria per i vigilanti

### Dashboard Amministrativa (Staff)
- **Visualizzazione registro**: consultazione del registro giornaliero per data selezionata
- **Lista accessi**: visualizzazione di tutti gli accessi esterni con dettagli ditta, nominativi e orari
- **Lista turni**: monitoraggio dei turni di vigilanza con orari inizio/fine
- **Presenze personale INAF**: elenco del personale presente/uscito nella giornata
- **Note della giornata**: visualizzazione delle note del registro

### Gestione Utenti
- **Personale INAF**: 
  - Aggiunta, modifica ed eliminazione del personale interno
  - Associazione nominativo con username LDAP
  - Solo il personale con username associato può autenticarsi via LDAP
- **Vigilanti**:
  - Creazione utenti vigilanti con username e password
  - Modifica dati anagrafici (nome, cognome, username, password)
  - Eliminazione vigilanti

### Gestione Accessi
- **Registrazione multipla**: inserimento di più nominativi contemporaneamente
- **Modifica accessi**: aggiornamento dati di accessi già registrati
- **Registrazione uscite**: inserimento dell'orario di uscita per gli accessi ancora in corso
- **Eliminazione accessi**: rimozione di accessi errati
- **Associazione turno**: ogni accesso è collegato al turno del vigilante che lo ha registrato

### Generazione Report PDF
- **Report giornalieri**: 
  - PDF con carta intestata INAF-IRA
  - Include personale esterno (accessi), lista turni, note e personale INAF presente
  - Generazione automatica e salvataggio nel database
- **Report mensili**: 
  - Unione di tutti i report giornalieri del mese selezionato
  - Generazione automatica in un unico file PDF
- **Report ricerca personalizzata**:
  - Filtri per intervallo di date
  - Filtro per singolo vigilante o tutti
  - Selezione tra turni, accessi o entrambi
  - Generazione PDF on-demand

### Ricerca Avanzata
- **Filtri temporali**: ricerca per intervallo di date
- **Filtro per vigilante**: ricerca per custode specifico o tutti
- **Tipologia dati**: selezione tra turni, accessi o entrambi
- **Risultati interattivi**: visualizzazione dei risultati filtrati
- **Esportazione PDF**: generazione immediata di report personalizzati

### Gestione Documenti
- **Upload fatture**: caricamento fatture con data di riferimento e descrizione
- **Upload programmazione turni**: caricamento pianificazioni turni
- **Archiviazione automatica**: organizzazione file per anno/mese
- **Consultazione documenti**: accesso a tutti i report, fatture e programmazioni turni
- **Accesso centrale operativa**: visualizzazione dedicata per account "centrale_operativa"

### Logs e Audit Trail
- **Log completo**: registrazione di tutte le operazioni degli utenti
- **Timestamp**: data e ora precisa di ogni azione
- **Dettagli azione**: descrizione completa dell'operazione eseguita
- **Esportazione CSV**: download logs per intervallo temporale e/o utente specifico
- **Filtri**: visualizzazione logs per utente e periodo

### Impostazioni Sistema
- **Configurazione Telegram**:
  - Token del bot Telegram
  - Chat ID per invio notifiche
- **Notifiche automatiche**: invio messaggi Telegram per eventi importanti
- **Webhook Telegram**: ricezione e gestione comandi dal bot

### Integrazione Telegram
- **Invio messaggi**: funzionalità per inviare notifiche dalla piattaforma
- **Messaggi da vigilanti**: i vigilanti possono inviare messaggi al personale INAF tramite l'interfaccia
- **Comando !send**: il bot può inoltrare messaggi al vigilante attualmente in turno

### Funzionalità WebSocket Real-time
- **Consumer dedicato**: canale WebSocket per ogni utente autenticato
- **Messaggi istantanei**: ricezione in tempo reale di notifiche dal personale INAF via Telegram
- **Integrazione Redis**: gestione dei canali WebSocket tramite Redis

### Homepage Vigilanti
- **Registro in tempo reale**: visualizzazione del registro giornaliero corrente
- **Lista accessi**: accessi registrati nella giornata con stato (presente/uscito)
- **Turno attivo**: informazioni sul proprio turno in corso
- **Gestione presenze INAF**: aggiornamento presenze del personale interno
- **Invio messaggi Telegram**: comunicazione con il personale INAF
- **Ricerca storico**: consultazione registri di date precedenti
- **Sistema marcature**: registrazione marcatura oraria

## 🛠️ Tecnologie

- **Backend**: Django
- **WebSocket**: Django Channels + Redis
- **Database**: PostgreSQL
- **Server ASGI**: Uvicorn
- **PDF Generation**: ReportLab + pypdf
- **Authentication**: LDAP3
- **Containerization**: Docker + Docker Compose

## 📦 Requisiti

- Docker e Docker Compose
- Python 3 (per sviluppo locale)
- PostgreSQL (già incluso in Docker)
- Redis (già incluso in Docker)

## 🚀 Installazione

### Con Docker (Raccomandato)

1. **Clona il repository**
```bash
git clone https://github.com/vcardoneit/registro-vigilanza-v2.git
cd registro-vigilanza-v2
```

2. **Configura le variabili d'ambiente**
```bash
cp example.env .env
```

Modifica il file `.env` con i tuoi parametri:
```env
DJANGO_SECRET_KEY="secret-key"
DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1,dominio.it"
DATABASE_ENGINE=postgresql_psycopg2
DATABASE_NAME=registro_vigilanza
DATABASE_USERNAME=dbuser
DATABASE_PASSWORD=password
```

3. **Avvia i container**
```bash
docker-compose up -d
```

4. **Crea un superuser**
```bash
docker exec -it rgv-app python manage.py createsuperuser
```

L'applicazione sarà disponibile su `http://localhost:8000`

## 🏗️ Struttura del Progetto

```
registro-vigilanza-v2/
├── registro/           # Configurazione principale Django
│   ├── settings.py    # Impostazioni del progetto
│   ├── urls.py        # URL routing principale
│   ├── asgi.py        # Configurazione ASGI per WebSocket
│   └── wsgi.py        # Configurazione WSGI
├── homepage/          # App homepage pubblica
├── areariservata/     # App area riservata
├── core/              # App core con utilities comuni
│   ├── consumers.py   # WebSocket consumers
│   ├── middleware.py  # Custom middleware
│   └── routing.py     # WebSocket routing
├── templates/         # Template HTML globali
├── static/            # File statici (CSS, JS, immagini)
├── media/             # File media (Report, Fatture, Programmazione turni)
├── requirements.txt   # Dipendenze Python
├── Dockerfile         # Configurazione Docker
├── compose.yaml       # Docker Compose setup
└── entrypoint.sh      # Script di avvio container
```

## ⚙️ Configurazione

### Variabili d'Ambiente

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Chiave segreta Django | - |
| `DJANGO_ALLOWED_HOSTS` | Host consentiti (separati da virgola) | - |
| `DATABASE_ENGINE` | Engine database | `postgresql_psycopg2` |
| `DATABASE_NAME` | Nome database | - |
| `DATABASE_USERNAME` | Username database | - |
| `DATABASE_PASSWORD` | Password database | - |
| `DATABASE_HOST` | Host database | `db` |
| `DATABASE_PORT` | Porta database | `5432` |
| `REDIS_HOST` | Host Redis | `redis` |
| `DEBUG` | Modalità debug | `False` |
| `TZ` | Timezone | `Europe/Rome` |

## ⏰ Operazioni Pianificate (Crontab)

Per il corretto funzionamento della generazione dei report e la gestione automatica dei turni, è necessario configurare le seguenti operazioni pianificate nel crontab del server ospitante.

```bash
# Aggiornamento turni (es. ogni giorno alle 01:00)
0 1 * * * docker exec rgv-app python manage.py aggiornaTurni >> /var/log/aggiornaTurni.log 2>&1

# Generazione report PDF (es. ogni giorno alle 03:00)
0 3 * * * docker exec rgv-app python manage.py generaReport >> /var/log/generaReport.log 2>&1
```

## 🔧 Comandi Utili

### Docker

```bash
# Avvia i container
docker-compose up -d

# Ferma i container
docker-compose down

# Visualizza i log
docker-compose logs -f

# Accedi al container app
docker exec -it rgv-app bash

# Crea superuser
docker exec -it rgv-app python manage.py createsuperuser
```

## 🔒 Sicurezza

- Usa sempre HTTPS in produzione
- Genera una `DJANGO_SECRET_KEY` sicura e unica
- Configura correttamente `ALLOWED_HOSTS`
- Mantieni aggiornate le dipendenze
- Usa password robuste per database e utenti

## 📝 License

Questo progetto è distribuito sotto licenza GNU General Public License v3.0. Vedi il file [LICENSE](LICENSE) per maggiori dettagli.

## 👤 Autore

**Vincenzo Cardone**

- Email: [vincenzo.cardone2@inaf.it](mailto:vincenzo.cardone2@inaf.it)
