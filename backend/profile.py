# routes_profile.py
import sqlite3
import uuid
import datetime
import json
from flask import Blueprint, request, session, render_template
from backend.config import app
from backend.config import app, DB_PATH


@app.route("/profile", methods=["GET", "POST"])
def profile_page():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 🔹 Pega o usuário logado na sessão
    user = session.get("user", None)

    if user:
        # 🔹 Tenta carregar dados adicionais do banco (bio, telefone, id)
        c.execute(
            "SELECT id, sugestoes FROM analises WHERE email=? ORDER BY data DESC LIMIT 1",
            (user["email"],)
        )
        row = c.fetchone()
        if row:
            user["id"] = row[0]
            user["bio"] = row[1]
            user["telefone"] = user.get("telefone", "")
        else:
            # Caso não exista ainda no banco
            user["id"] = None
            user["bio"] = ""
            user["telefone"] = ""

    if request.method == "POST":
        # 🔹 Pega dados do formulário
        nome = request.form.get("nome")
        email = request.form.get("email")
        bio = request.form.get("bio")
        telefone = request.form.get("telefone")

        if user and user.get("id"):
            # 🔹 Atualiza registro existente
            c.execute("""
                UPDATE analises
                SET nome = ?, email = ?, sugestoes = ?
                WHERE id = ?
            """, (nome, email, bio, user["id"]))
        else:
            # 🔹 Cria novo registro
            new_id = str(uuid.uuid4())
            c.execute("""
                INSERT INTO analises (id, nome, email, score, sugestoes, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, nome, email, 0, bio, datetime.datetime.now().isoformat()))
            user["id"] = new_id

        # 🔹 Atualiza sessão com possíveis mudanças
        session["user"]["nome"] = nome
        session["user"]["email"] = email
        user["nome"] = nome
        user["email"] = email
        user["bio"] = bio
        user["telefone"] = telefone

        conn.commit()

    conn.close()

    # 🔹 Renderiza template passando o usuário logado (nome sempre da sessão)
    return render_template("profile.html", user=user)