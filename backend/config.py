import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

# --------------------------
# BASE DIR
# --------------------------
BASE_DIR = os.getcwd()

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_DIR = os.path.join(BASE_DIR, "db")
DB_PATH = os.path.join(DB_DIR, "curriculos.db")

# --------------------------
# FLASK APP
# --------------------------
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static")
)

# =========================
# SECRET KEY ROBUSTA
# =========================
secret = os.environ.get("SECRET_KEY")

if not secret:
    print("⚠️ SECRET_KEY não encontrada — usando fallback (DEV)")
    secret = "dev-secret-key-fixa-2026"  # fallback estável

app.secret_key = secret

print("🔑 SECRET KEY carregada:", bool(secret))
# ==========================
# 🍪 CONFIGURAÇÃO DE SESSÃO (AUTO AMBIENTE)
# ==========================

is_production = os.environ.get("SPACE_ID") is not None
# HF sempre tem SPACE_ID

app.config.update(
    SESSION_COOKIE_NAME="cv_analyzer_session",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=is_production,  # 🔥 dinâmico
    SESSION_COOKIE_SAMESITE="None" if is_production else "Lax",
    PERMANENT_SESSION_LIFETIME=86400
)

print("🔐 Modo produção:", is_production)
# --------------------------
# PASTAS
# --------------------------
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DB_PATH'] = DB_PATH
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024