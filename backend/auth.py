from flask import Blueprint, request, session, redirect, url_for
import sqlite3, uuid, datetime
from backend.config import DB_PATH  # <- use o DB_PATH do config
from backend.config import app



@app.route("/login", methods=["POST"])
def login():
    nome = request.form.get("nome")
    email = request.form.get("email")
    print("SESSION SETADA:", session.get("user"))
    print("SECRET EM LOGIN:", app.secret_key)
    if not nome or not email:
        return "Nome e e-mail obrigatórios", 400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, nome, email, telefone, bio FROM usuarios WHERE email=?", (email,))
    row = c.fetchone()
    if row:
        user_id, nome_db, email_db, telefone, bio = row
    else:
        user_id = str(uuid.uuid4())
        telefone, bio = "", ""
        c.execute("""
            INSERT INTO usuarios (id, nome, email, telefone, bio, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, nome, email, telefone, bio, datetime.datetime.now().isoformat()))
        conn.commit()
    conn.close()
    session.permanent = True  # 🔥 ADICIONE ESTA LINHA
    session["user"] = {"id": user_id, "nome": nome, "email": email, "telefone": telefone, "bio": bio}
    session["curriculo"] = None
    print("SESSION SETADA:", session.get("user"))
    return redirect(url_for("chat_page")) 

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home")) 