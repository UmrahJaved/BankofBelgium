# 🏦 Bank of Belgium — Secure Online Banking & Cyber Security Deception Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask--3.1-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

## 📌 Project Overview

**Bank of Belgium** is a full-featured, secure online retail banking web application integrated with an enterprise Security Operations Center (SOC) dashboard and an advanced CTF Deception engine (**ARGUS**). 

The application serves a dual purpose:
1. **Retail Banking Services**: Offers customers modern digital banking features such as account management (Current & Savings), real-time peer-to-peer transfers, funds deposit, transaction histories, credit card tracking, multi-factor authentication (MFA/OTP), and profile management.
2. **Cyber Security & Honeypot Architecture (ARGUS & SOC)**: Built-in defensive security mechanisms to monitor, log, and alert on potential security events (such as XSS script injections, brute force logins, IDOR attempts, and unauthorized access) alongside a deception honeypot database (`bank_archive_2025.sqlite3`).

---

## ✨ Key Features

### 💳 Retail Banking Operations
- **Account Management**: Create and manage Savings and Current accounts with automated IBAN generation.
- **Transfers & Deposits**: Transfer funds between accounts with per-user daily limits, balance checks, and recipient verification.
- **Transaction History**: Exportable statement logs and real-time transaction activity tracking.
- **Card Services**: Encrypted card number storage and credit limit monitoring.
- **Multi-Factor Authentication**: Email & TOTP/QR code verification during login and sensitive transactions.

### 🛡️ Defensive Security & SOC Monitoring
- **Content Security Policy (CSP)**: Nonce-based script execution enforced via `Flask-Talisman`.
- **CSRF Protection**: Form token validation using `Flask-WTF`.
- **Rate Limiting**: Endpoint throttling powered by `Flask-Limiter`.
- **Security Operations Center (SOC)**: Interactive dashboard (`/soc`) for security personnel to review real-time security alerts and audit logs.
- **ARGUS Honeypot Subsystem**: CTF deception subsystem (`/argus`) designed to detect and log unauthorized reconnaissance and intrusion attempts into decoy endpoints.

---

## 📁 Repository Structure

```text
BankofBelgium/
├── banking_app/                # Main Flask application core
│   ├── routes/                 # Modular Blueprint routes
│   │   ├── account.py          # Account overview, transfers, deposits
│   │   ├── admin.py            # Admin authentication & panel
│   │   ├── argus.py            # ARGUS honeypot deception routes
│   │   ├── auth.py             # Login, registration, MFA/OTP logic
│   │   ├── banking.py          # Products overview (loans, investments)
│   │   ├── main.py             # Landing page, terms, security policy
│   │   ├── soc.py              # SOC security monitoring dashboard
│   │   └── support.py          # Customer support contact system
│   ├── honeypot_seed/          # Seed database schema for CTF honeypot
│   ├── static/                 # Stylesheets (CSS), images, and JavaScript
│   ├── templates/              # Jinja2 HTML templates
│   ├── app.py                  # Application factory & entry point
│   ├── config.py               # Environment configuration loader
│   ├── create_admin.py         # CLI utility for creating admin accounts
│   ├── create_honey_database.py# Honeypot database generator script
│   ├── db.py                   # SQLite connection, schema, and queries
│   ├── email_utils.py          # SMTP & email alert handler
│   ├── extentions.py           # Flask extensions (Login, Limiter, Talisman, CSRF)
│                 
├── nginx/                      # Nginx reverse proxy configuration & TLS certs
├── tests/                      # Unit & integration test suite
├── .env.example                # Environment configuration template
├── docker-compose.yml          # Multi-container orchestration config
├── Dockerfile                  # Container build instructions
├── requirements.txt            # Python package dependencies
└── run.ps1                     # PowerShell launch helper script
```

---

## 📋 Prerequisites

Before running the application locally, ensure you have the following installed on your machine:

- **Python**: Version `3.10` or higher (Python `3.12+` recommended).
- **Git**: Version `2.x` or higher.
- **PowerShell** (Windows) or **Bash** (Linux / macOS).
- *(Optional)* **Docker Desktop**: If running via container orchestration.

---

## 🚀 How to Run Locally

Follow these step-by-step instructions to set up and run the project locally.

### Step 1: Clone the Repository

```bash
git clone https://github.com/UmrahJaved/BankofBelgium.git
cd BankofBelgium
```

### Step 2: Create a Virtual Environment

It is recommended to use a isolated virtual environment for Python packages.

- **Windows (PowerShell)**:
  ```powershell
  py -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

- **Linux / macOS (Bash)**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Dependencies

Upgrade `pip` and install all required Python packages from `requirements.txt`:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Copy the provided `.env.example` file to create your local `.env` configuration file:

- **Windows (PowerShell)**:
  ```powershell
  Copy-Item .env.example .env
  ```

- **Linux / macOS**:
  ```bash
  cp .env.example .env
  ```

> 💡 **Note**: For local testing over HTTP (`http://localhost:5000`), keep `SESSION_COOKIE_SECURE=false` in `.env`.

### Step 5: (Optional) Create an Admin User

To create an administrator account capable of accessing the SOC dashboard (`/soc`):

```bash
python -m banking_app.create_admin --email admin@bank.com --password "AdminPass123!" --first-name Ada --last-name Admin
```

### Step 6: Start the Application

Run the application factory directly with Python or use the included PowerShell script:

- **Using Python**:
  ```bash
  python -m banking_app.app
  ```

- **Using PowerShell (Windows)**:
  ```powershell
  .\run.ps1
  ```

Once started, the application auto-seeds the SQLite databases (`instance/banking.sqlite3` and `instance/bank_archive_2025.sqlite3`) and serves the site at:

🌐 **[http://localhost:5000](http://localhost:5000)** (or `http://127.0.0.1:5000`)

---

## 🐳 Running with Docker

To run the application using Docker and Nginx reverse proxy:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Start containers with Docker Compose:
   ```bash
   docker compose up --build
   ```

---

## 🧪 Running Unit Tests

Execute the automated unittest suite to verify route handlers and redirect logic:

```bash
python -m unittest discover tests
```

---

## 🌐 Application Endpoints Overview

| Route | Description | Access Level |
|---|---|---|
| `/` | Bank of Belgium Home Page | Public |
| `/login` | User Login with MFA/OTP verification | Public |
| `/register` | Customer Registration | Public |
| `/dashboard` | Main Retail Banking Dashboard | Authenticated User |
| `/transfer` | Send Money / Internal & External Transfers | Authenticated User |
| `/deposit` | Deposit Funds into Bank Account | Authenticated User |
| `/soc` | Security Operations Center Monitoring Dashboard | Admin User |
| `/argus` | CTF Deception & Honeypot Subsystem | Honeypot / Public |

---

## 📄 License

This project is licensed under the **MIT License**.
