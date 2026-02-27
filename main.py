import os
import sys
from dotenv import load_dotenv

# 🔥 CARREGA O .env
load_dotenv()

# Garante que o Python encontre a pasta 'backend'
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))



from backend.config import app

# 🔥🔥🔥 CRÍTICO — inicializa banco no boot
from backend.db import init_db
init_db()

# 🔥 IMPORTANTE: Importar as rotas para o Flask registrá-las
try:
    import backend.profile
    import backend.upload
    import backend.auth
    import backend.pages
    import backend.chat
    import backend.historico
    print("Módulos de backend carregados com sucesso!")
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")

# O Hugging Face exige a porta 7860
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860, debug=False)