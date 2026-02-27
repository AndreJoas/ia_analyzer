# backend/upload.py
import os
import uuid
import datetime
import json
import sqlite3
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from backend.logger import log_step
from backend.agent import agent  # assume agent e tools/model já definidos
from backend.config import DB_PATH
from flask import current_app
from backend.config import app

@app.route("/upload_curriculo", methods=["POST"])
def upload_curriculo():
    print("UPLOAD_FOLDER:", current_app.config['UPLOAD_FOLDER'])
    print("DB_PATH:", DB_PATH)
    print("USER SESSION:", session.get("user"))
    log_step("UPLOAD iniciado")

    if "file" not in request.files:
        log_step("UPLOAD erro", "arquivo não enviado")
        return jsonify({"error": "Arquivo não enviado"}), 400

    file = request.files["file"]

    log_step("UPLOAD arquivo recebido", {"filename": file.filename})

    if file.filename == "":
        log_step("UPLOAD erro", "filename vazio")
        return jsonify({"error": "Arquivo inválido"}), 400

    if not file.filename.lower().endswith(".pdf"):
        log_step("UPLOAD erro", "não é PDF")
        return jsonify({"error": "Apenas PDF permitido"}), 400

    # 🔹 Usa UPLOAD_FOLDER do app.config
    filename = secure_filename(file.filename)
   

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    log_step("UPLOAD arquivo salvo", filepath)

    # 🔹 Extrai texto do PDF
    reader = PdfReader(filepath)
    texto = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        texto += page_text
        log_step(f"PDF página {i+1} extraída", {"chars": len(page_text)})

    log_step("PDF texto total", {"chars_total": len(texto)})

    # 🔹 Chama agente
    try:
        log_step("Chamando agente para analisar currículo")
        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Analise este currículo e retorne JSON válido:\n\n{texto}"}]
        })

        resposta_final = result["messages"][-1].content
        log_step("Resposta final do agente", resposta_final[:3000])

        def limpar_json_response(texto: str) -> str:
            if not texto:
                raise ValueError("Resposta vazia do modelo")
            texto = texto.strip()
            if "```" in texto:
                texto = texto.replace("```json", "").replace("```", "")
            inicio = texto.find("{")
            fim = texto.rfind("}")
            if inicio != -1 and fim != -1:
                texto = texto[inicio:fim+1]
            return texto.strip()

        analise_json = json.loads(limpar_json_response(resposta_final))
        log_step("JSON parseado com sucesso", analise_json)

    except Exception as e:
        log_step("ERRO na análise", str(e))
        return jsonify({"error": "Erro ao processar currículo"}), 500

    # 🔹 Salva na sessão
    session["curriculo"] = analise_json
    log_step("Currículo salvo na sessão")

    # 🔹 Salva no banco
    user = session.get("user")
    if not user or not user.get("id"):
        return jsonify({"error": "Usuário não logado"}), 403

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    analise_id = str(uuid.uuid4())
    c.execute(
        """
        INSERT INTO analises (id, user_id, nome, email, telefone, score, sugestoes, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            analise_id,
            user["id"],
            analise_json.get("nome"),
            analise_json.get("email"),
            analise_json.get("telefone"),
            analise_json.get("score", 0),
            "; ".join(analise_json.get("sugestoes", [])),
            datetime.datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()
    log_step("Registro salvo no banco", {"id": analise_id, "user_id": user["id"], "score": analise_json.get("score")})

    return jsonify({"id": analise_id, "info": analise_json, "score": analise_json.get("score", 0), "sugestoes": analise_json.get("sugestoes", [])})