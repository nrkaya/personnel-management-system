# 🛡️ KAYA PTS — Enterprise Personnel Tracking and Management System

[🇹🇷 Türkçe](README.md) | [🇬🇧 English](README_EN.md)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Tests](https://github.com/nrkaya/personnel-management-system/actions/workflows/tests.yml/badge.svg)](https://github.com/nrkaya/personnel-management-system/actions/workflows/tests.yml)

**KAYA PTS (Kaya Personnel Tracking System)** is a modern enterprise web application designed for comprehensive human resources, employee lifecycle management, leave workflows, department analytics, and payroll management. It pairs top-tier enterprise security and a clean modular architecture with a dark Glassmorphism UI experience.

---

## 📸 Screenshots & UI Showcase

### ⚡ Executive Dashboard
![Executive Dashboard](images/dashboard.png)

<details>
  <summary><b>🔍 Click to View Additional Module Screenshots (Collapsible Menu)</b></summary>
  <br>

  #### 👥 1. Personnel Management (Live Filtering & Search)
  ![Personnel Management](images/personeller.png)

  #### 📅 2. Leave Management & Approval Workflows
  ![Leave Management](images/izinler.png)

  #### 🛡️ 3. User & 4-Tier Role Administration (RBAC)
  ![User Administration](images/kullanicilar.png)

  #### 🗑️ 4. Trash Bin & Archive Recovery
  ![Trash Bin](images/cop_kutusu.png)

  #### 📜 5. System Audit Logs & Activity Trails
  ![System Audit Logs](images/loglar.png)

</details>

---

## 🌟 Key Features

- 🏗️ **Modular Architecture (Flask Blueprints):** 7 decoupled business domain modules (`auth`, `dashboard`, `personel`, `izin`, `kullanici`, `logs`, `api`).
- 🔐 **Multi-Layer Enterprise Security:**
  - **CSRF Protection:** Token-based request validation across all forms via `Flask-WTF`.
  - **Brute-Force & Rate Limiting:** An account is **locked for 10 minutes** after 5 consecutive failures. An IP address is locked only after 20 failures across all accounts (`MAX_IP_LOGIN_ATTEMPTS`), so behind a shared office connection one person's typos do not lock out colleagues. Every failure shows the same message and unknown usernames cost the same hashing work, so attackers cannot tell which usernames exist.
  - **Strong Password Policy:** At least 12 characters with uppercase and lowercase letters, digits and a special character. Users can change their own password; admins can reset passwords.
  - **Secure Photo Uploads:** Images are verified and re-encoded with Pillow (EXIF/location data is dropped), stored under random UUID names in `uploads/` instead of the public `static` folder, and served only to logged-in users allowed to see that record.
  - **Secure Session Management:** `HttpOnly`, `SameSite=Lax`, 8-hour lifetime. Logout, password changes and deactivation revoke **every** session cookie of that user.
  - **Strict Content Security Policy:** No inline scripts; Lucide, Chart.js and the Inter font are served from `static/vendor`, so no visitor data reaches third-party CDNs.
  - **Comprehensive Audit Logging:** Logs capture user actions, event types, IP addresses and timestamps; `flask purge-logs` applies a retention period.
  - **Spreadsheet Formula Injection Protection:** Values starting with `=`, `+`, `-` or `@` are exported as plain text.
- 👥 **4-Tier Role-Based Access Control (RBAC):** `Admin`, `IK` (HR), `Mudur` (Manager), `Muhasebe` (Accounting).
- 📊 **Bento Grid Dashboard:** Chart.js department distribution charts, birthday reminders, and upcoming leave tracking widgets.
- 📱 **Mobile Friendly:** On phones the sidebar turns into a drawer opened from the menu button in the top bar.
- 💾 **Backups:** `backup_db.py` backs up SQLite or PostgreSQL together with personnel photos; the Docker Compose setup includes a daily automatic backup service.
- ✅ **Continuous Integration:** GitHub Actions runs the tests on every push and pull request and checks that migrations match the models on SQLite and PostgreSQL.
- ⚡ **High-Performance UI:** Paginated tables (10 records/page) and instantaneous client-side search and filtering.
- 📑 **Corporate Excel Reporting:** Styled and formatted `.xlsx` export engine powered by `openpyxl`.
- 🌐 **RESTful API v1:** Headless JSON API service secured with `X-API-KEY` authentication for third-party integrations.
- 🐳 **DevOps & Containerization:** Single-command setup via `Dockerfile` and `docker-compose.yml` with native PostgreSQL database support.

---

## 👥 4-Tier Role & Permission Matrix (RBAC)

| Feature / Action | 👑 Admin | 💼 IK (Human Resources) | 👔 Mudur (Manager) | 💰 Muhasebe (Accounting) |
| :--- | :---: | :---: | :---: | :---: |
| **Login & Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **View Personnel List** | ✅ | ✅ | 🔸 own department | ✅ |
| **Create / Edit Personnel** | ✅ | ✅ | ❌ | ❌ |
| **Delete Personnel & Trash Bin** | ✅ | ✅ | ❌ | ❌ |
| **Permanently Delete from Trash** | ✅ | ❌ | ❌ | ❌ |
| **View Salary Information** | ✅ | ✅ | ❌ | ✅ |
| **Birth Date & Dossier Notes** | ✅ | ✅ | ❌ | ❌ |
| **Request / Approve / Reject Leaves** | ✅ | ✅ | 🔸 own department | ❌ |
| **View Leave Reasons** | ✅ | ✅ | 🔸 own department | ❌ |
| **Delete Leave Records** | ✅ | ✅ | ❌ | ❌ |
| **Export Excel Reports** | ✅ | ✅ | 🔸 own department | ✅ |
| **User & Role Management** | ✅ | ❌ | ❌ | ❌ |
| **System Audit Logs** | ✅ | ❌ | ❌ | ❌ |

> Manager accounts are bound to a department (assigned in User Management); a manager without a department sees no personnel records. Permissions come from a single matrix (`ROLE_HIERARCHY` in `utils.py`) and buttons appear only when the action is allowed.

---

## 🚀 Installation and Setup

### Method 1: Local Setup (Development Mode - SQLite)

1. **Prerequisites:** Python 3.10+
2. **Prepare the environment and secrets:**
   ```powershell
   cd C:\Users\Muhammed\Desktop\personelsistemi
   Copy-Item .env.example .env
   # Replace the SECRET_KEY and API_KEY placeholders in .env with unique values.
   .\venv\Scripts\python -m pip install -r requirements.txt
   .\venv\Scripts\python -m flask --app app:create_app db upgrade
   .\venv\Scripts\python -m flask --app app:create_app create-admin
   .\venv\Scripts\python app.py
   ```
3. **Open in Browser:**
   👉 **`http://127.0.0.1:5000`**
4. The administrator account is created only through `create-admin`; no default credentials are embedded in the application.

> **Upgrade note:** this release adds a database migration — run `flask --app app:create_app db upgrade` after updating. Session cookies are now versioned, so every user signs in once more. Photos uploaded to `static/uploads/` by older versions move to `uploads/` automatically the first time they are opened.

---

### Method 2: Docker & PostgreSQL (Production Mode)

```bash
docker-compose up --build -d
```
> First copy `.env.example` to `.env` and replace all secret and PostgreSQL placeholders. PostgreSQL is not exposed to the host; the application listens on `127.0.0.1:5000` for a TLS reverse proxy. The image applies migrations on start (`flask db upgrade`). Behind a reverse proxy set `TRUSTED_PROXY_COUNT=1` in `.env`.

### Method 3: Render (or a similar PaaS)

The Dockerfile reads Render's `$PORT`, starts with `FLASK_ENV=production` and applies migrations on every deploy. Environment variables:

| Variable | Value |
| :--- | :--- |
| `SECRET_KEY`, `API_KEY` | Two different random values of at least 32 characters (`python -c "import secrets; print(secrets.token_urlsafe(48))"`). Keys that once appeared in the repository history are rejected. |
| `DATABASE_URL` | A Render PostgreSQL URL. **Do not use SQLite**: Render's filesystem is reset on every deploy. |
| `TRUSTED_PROXY_COUNT` | `1` — otherwise every visitor shares the proxy's IP and one person's failed logins lock everybody out. |
| `RATELIMIT_STORAGE_URI` | Preferably a Render Key Value (Redis) URL; `memory://` is not shared between workers. The required `redis` package is installed; Docker Compose uses its own Redis service. |

Attach a Render Persistent Disk at `/app/uploads` so personnel photos survive deploys, and create the first admin from the Render Shell with `flask --app app:create_app create-admin`.

### Maintenance: log retention

Audit logs contain names and IP addresses. Apply the retention period regularly (for example from a daily cron job):

```bash
flask --app app:create_app purge-logs            # logs older than LOG_RETENTION_DAYS (default 365)
flask --app app:create_app purge-logs --days 180 # a different period
```

### Backups

Each backup contains a copy of the database and an archive of personnel photos (`uploads/`). Photos are personal data and a database backup alone would not bring them back.

**Local (SQLite or PostgreSQL):**

```powershell
.\venv\Scripts\python.exe backup_db.py --keep 14   # back up into backups/, keep the 14 newest
.\venv\Scripts\python.exe backup_db.py --list      # list existing backups
```

SQLite backups are safe while the app is running. For PostgreSQL, `pg_dump` must be installed, at the server's major version or newer. Schedule the command daily with Windows Task Scheduler (or cron on Linux); `BACKUP_DIR` writes the backups to another disk.

**Docker Compose:** the `backup` service takes a daily database dump and photo archive and deletes those older than `BACKUP_KEEP_DAYS` (default 14). Copy them to the host with:

```bash
docker compose cp backup:/backups ./backups
```

**Render:** Render's free PostgreSQL plan has no backups and expires after a while; use a paid plan (automatic daily backups) for real data. You can also back up from your own computer with Render's *External Database URL*:

```powershell
$env:DATABASE_URL = "<Render External Database URL>"; .\venv\Scripts\python.exe backup_db.py --no-uploads
```

**Restore:**

| What | How |
| :--- | :--- |
| SQLite | Stop the app, copy `kaya_pts_<time>.db` over `database.db`. |
| PostgreSQL | `pg_restore --clean --if-exists --no-owner -d "<database URL>" kaya_pts_<time>.dump` |
| Photos | Extract `kaya_pts_<time>_uploads.zip` (`.tar.gz` under Docker) into `uploads/`. |

> Copy backups to another place regularly (external disk, cloud storage); a backup on the same server is lost with the server.

---

## 🌐 RESTful API v1 Documentation

All API endpoints are protected using `X-API-KEY` or `Authorization: Bearer`. Keys are defined only in `.env`; `API_KEYS_JSON` supports additional scoped integration keys.

| Scope | Grants |
| :--- | :--- |
| `personnel:read` | List and read personnel records |
| `personnel:write` | Create, update and archive personnel |
| `personnel:salary` | Read and write the `maas` (salary) field |
| `personnel:personal` | Read and write `dogum_tarihi` and `ek_bilgi` |
| `stats:read` | `/stats` and `/docs` |

A key without a scope does not see those fields in responses and gets `403` when writing them.

### 1. Retrieve Statistics
* **GET** `/api/v1/stats`
* **Headers:** `X-API-KEY: <API_KEY from .env>`
* **Response Sample:**
  ```json
  {
    "success": true,
    "data": {
      "toplam_aktif_personel": 45,
      "toplam_kullanici": 4,
      "aktif_izindekiler": 2
    }
  }
  ```

### 2. List Personnel
* **GET** `/api/v1/personeller?page=1&per_page=20&q=Ahmet&departman=Yazılım`
* **Headers:** `X-API-KEY: <API_KEY from .env>`

### 3. Create Personnel
* **POST** `/api/v1/personel`
* **Headers:** `X-API-KEY: <API_KEY from .env>`, `Content-Type: application/json`
* **Body (JSON):**
  ```json
  {
    "ad": "Mehmet",
    "soyad": "Kaya",
    "departman": "Yazılım",
    "pozisyon": "Senior Backend Developer",
    "telefon": "0555 123 4567",
    "email": "mehmet@kayapts.com",
    "maas": 95000
  }
  ```

### 4. Update Personnel
* **PUT** `/api/v1/personel/<id>`
* **Headers:** `X-API-KEY: <API_KEY from .env>`, `Content-Type: application/json`
* **Body (JSON):** `{"maas": 105000, "pozisyon": "Lead Developer"}`

### 5. Delete Personnel (Soft Delete)
* **DELETE** `/api/v1/personel/<id>`
* **Headers:** `X-API-KEY: <API_KEY from .env>`

---

## 🧪 Automated Testing

To run the complete automated test suite covering authentication, brute-force lockout, password policy, RBAC authorization, CRUD lifecycles, Excel export, and REST API:

```powershell
.\venv\Scripts\python -m unittest -v
```
> The suite includes RBAC denial, API validation limits, CRUD, leave, Excel, authentication and backup coverage. GitHub Actions runs it on every push and pull request (`.github/workflows/tests.yml`).

---

## 📁 Project Directory Structure

```
personelsistemi/
├── app.py                  # Application Factory (create_app)
├── config.py               # Development, Production, Testing configurations
├── database.py             # Shared SQLAlchemy and CSRFProtect instances
├── models.py               # Database Models (Kullanici, Personel, Izin, Log, LoginAttempt)
├── utils.py                # RBAC decorators, Rate Limiter, File & Password Validators
├── test_enterprise.py      # Automated enterprise test suite
├── test_security.py        # Security, privacy and role tests
├── test_backup.py          # Backup tests
├── backup_db.py            # Database + photo backups
├── clean_system.py         # System reset and database sanitation utility
├── routes/
│   ├── auth.py             # Login, Logout, Session Rate Limiting
│   ├── dashboard.py        # Bento Grid, Analytics & Statistics
│   ├── personel.py         # CRUD, Live Search, Pagination, Excel Export
│   ├── izin.py             # Leave Request Approval Workflow
│   ├── kullanici.py        # 4-Tier User & Role Administration
│   ├── logs.py             # System Audit Logs
│   └── api.py              # RESTful API v1 Endpoints
├── templates/              # Glassmorphism Jinja2 HTML Templates
├── static/
│   ├── css/style.css       # Enterprise Dark Theme & Bento Grid Layouts
│   ├── js/main.js          # Modals, confirmations, chart and live search (CSP-safe)
│   └── vendor/             # Self-hosted Lucide, Chart.js and Inter font
├── uploads/                # Personnel photos (not in git, not public)
├── migrations/             # Alembic database migrations
├── Dockerfile              # Production Docker Image Specification
├── docker-compose.yml      # Multi-container Compose for Web + PostgreSQL
├── requirements.txt        # Python package dependencies
├── README.md               # Turkish documentation
└── README_EN.md            # English documentation
```

---
*© 2026 KAYA PTS — Enterprise Personnel Tracking System. All Rights Reserved.*
