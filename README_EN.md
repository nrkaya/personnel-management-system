# 🛡️ KAYA PTS — Enterprise Personnel Tracking and Management System

[🇹🇷 Türkçe](README.md) | [🇬🇧 English](README_EN.md)

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

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
  - **Brute-Force & Rate Limiting:** Accounts and IP addresses are **automatically locked for 10 minutes** after 5 consecutive failed login attempts.
  - **Strong Password Policy:** Strict enforcement requiring a minimum of 8 characters, uppercase and lowercase letters, and digits.
  - **Secure File & Avatar Uploads:** Only validated MIME types (`image/png`, `image/jpeg`, `image/webp`) and safe extensions are permitted. Uploaded files are renamed using secure random UUIDs to prevent path traversal attacks.
  - **Secure Session Management:** `HttpOnly`, `SameSite=Lax`, and `PermanentSessionLifetime` (8 hours).
  - **Comprehensive Audit Logging:** Non-repudiable logs capture user actions, event types, IP addresses, and timestamps.
- 👥 **4-Tier Role-Based Access Control (RBAC):** `Admin`, `IK` (HR), `Mudur` (Manager), `Muhasebe` (Accounting).
- 📊 **Bento Grid Dashboard:** Chart.js department distribution charts, birthday reminders, and upcoming leave tracking widgets.
- ⚡ **High-Performance UI:** Paginated tables (10 records/page) and instantaneous client-side search and filtering.
- 📑 **Corporate Excel Reporting:** Styled and formatted `.xlsx` export engine powered by `openpyxl`.
- 🌐 **RESTful API v1:** Headless JSON API service secured with `X-API-KEY` authentication for third-party integrations.
- 🐳 **DevOps & Containerization:** Single-command setup via `Dockerfile` and `docker-compose.yml` with native PostgreSQL database support.

---

## 👥 4-Tier Role & Permission Matrix (RBAC)

| Feature / Action | 👑 Admin | 💼 IK (Human Resources) | 👔 Mudur (Manager) | 💰 Muhasebe (Accounting) |
| :--- | :---: | :---: | :---: | :---: |
| **Login & Dashboard** | ✅ | ✅ | ✅ | ✅ |
| **View Personnel List** | ✅ | ✅ | ✅ | ✅ |
| **Create / Edit Personnel** | ✅ | ✅ | ❌ | ❌ |
| **Delete Personnel & Trash Bin** | ✅ | ✅ | ❌ | ❌ |
| **View Salary Information** | ✅ | ✅ | ❌ | ✅ |
| **Approve / Reject Leaves** | ✅ | ✅ | ✅ | ❌ |
| **Export Excel Reports** | ✅ | ✅ | ✅ | ✅ |
| **User & Role Management** | ✅ | ❌ | ❌ | ❌ |
| **System Audit Logs** | ✅ | ❌ | ❌ | ❌ |

---

## 🚀 Installation and Setup

### Method 1: Local Setup (Development Mode - SQLite)

1. **Prerequisites:** Python 3.10+
2. **Navigate and Start the Virtual Environment:**
   ```powershell
   # Navigate to the project directory
   cd C:\Users\Muhammed\Desktop\personelsistemi

   # Launch the application
   .\venv\Scripts\python app.py
   ```
3. **Open in Browser:**
   👉 **`http://127.0.0.1:5000`**
4. **Default Administrator Credentials:**
   - **Username:** `admin`
   - **Password:** `Admin123!`

---

### Method 2: Docker & PostgreSQL (Production Mode)

```bash
docker-compose up --build -d
```
> Spawns both the web service and the PostgreSQL container ready at (`http://localhost:5000`).

---

## 🌐 RESTful API v1 Documentation

All API endpoints are protected using the `X-API-KEY` HTTP header.  
**Default API Key:** `kaya-pts-enterprise-api-key-2026`

### 1. Retrieve Statistics
* **GET** `/api/v1/stats`
* **Headers:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`
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
* **GET** `/api/v1/personeller?page=1&limit=20&search=Ahmet&dept=Yazılım`
* **Headers:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`

### 3. Create Personnel
* **POST** `/api/v1/personel`
* **Headers:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`, `Content-Type: application/json`
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
* **Headers:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`, `Content-Type: application/json`
* **Body (JSON):** `{"maas": 105000, "pozisyon": "Lead Developer"}`

### 5. Delete Personnel (Soft Delete)
* **DELETE** `/api/v1/personel/<id>`
* **Headers:** `X-API-KEY: kaya-pts-enterprise-api-key-2026`

---

## 🧪 Automated Testing

To run the complete automated test suite covering authentication, brute-force lockout, password policy, RBAC authorization, CRUD lifecycles, Excel export, and REST API:

```powershell
.\venv\Scripts\python -m unittest test_enterprise.py
```
> **Result:** `Ran 8 tests in ~3.2s -> OK (100% Passing)`

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
│   └── js/main.js          # Live Search Filtering, Toast Notifications
├── Dockerfile              # Production Docker Image Specification
├── docker-compose.yml      # Multi-container Compose for Web + PostgreSQL
├── requirements.txt        # Python package dependencies
├── README.md               # Turkish documentation
└── README_EN.md            # English documentation
```

---
*© 2026 KAYA PTS — Enterprise Personnel Tracking System. All Rights Reserved.*
