# Bank of Belgium — Secure Online Banking Application & Security Platform

A modern, full-featured Flask web application implementing retail banking services alongside security monitoring (SOC) and honeypot deception capabilities (ARGUS).

## 🚀 Features

- **Retail Banking Portal**: User registration, authentication (MFA/OTP support), account dashboard, funds transfer, deposits, transaction history, and beneficiary management.
- **Security & Protection**:
  - Flask-Talisman CSP header management & nonce-based script execution.
  - Flask-WTF CSRF protection.
  - Flask-Limiter rate limiting.
  - XSS injection detection and audit logging.
- **Security Operations Center (SOC)**: Real-time security event dashboard (`/soc`) for monitoring suspicious activities, brute force attempts, and IDOR events.
- **ARGUS Honeypot Deception Architecture**: Embedded CTF deception subsystem and honeypot database (`bank_archive_2025.sqlite3`).

---

## 🛠️ Project Structure

```text
BankofBelgium/
├── banking_app/           # Main Flask application package
│   ├── routes/            # Blueprint routes (auth, account, banking, admin, soc, argus, support)
│   ├── static/            # CSS styles and JavaScript assets
│   ├── templates/         # HTML Jinja templates
│   ├── app.py             # Application factory & boot script
│   ├── db.py              # SQLite database layer & schema definitions
│   └── create_honey_database.py # Honeypot database seeder
├── nginx/                 # Nginx reverse proxy configuration & certs directory
├── tests/                 # Unit & integration test suite
├── .env.example           # Example environment configuration template
├── docker-compose.yml     # Multi-container orchestration
├── Dockerfile             # Docker container definition
├── requirements.txt       # Python dependencies
└── run.ps1                # PowerShell launcher script
```

---

## 💻 Getting Started Locally

### Prerequisites

- Python 3.10+
- Git

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/UmrahJaved/BankofBelgium.git
   cd BankofBelgium
   ```

2. **Set up Virtual Environment**:
   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   ```powershell
   Copy-Item .env.example .env
   ```

4. **Run the Application**:
   ```powershell
   python -m banking_app.app
   ```
   Open your browser at **`http://localhost:5000`**.

---

## 🐳 Running with Docker

```bash
cp .env.example .env
docker compose up --build
```

The application will be accessible via Nginx.

---

## 🧪 Running Tests

To run the unit test suite:
```powershell
python -m unittest discover tests
```

---

## 📄 License

This project is licensed under the MIT License.
