# backend/db.py
import sys
import os
import sqlite3
import datetime

# 🔹 adiciona a raiz do projeto no path para imports funcionarem
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# agora podemos importar do backend sem erro
from backend.config import DB_PATH

def init_db():
    # cria pasta db se não existir
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabela usuários
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT,
            bio TEXT,
            data_criacao TEXT
        )
    """)

    # Tabela análises de currículos
    c.execute("""
        CREATE TABLE IF NOT EXISTS analises (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            nome TEXT,
            email TEXT,
            telefone TEXT,
            score REAL,
            sugestoes TEXT,
            data TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

if __name__ == "__main__":
    init_db()