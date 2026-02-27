# =========================================================
# DEBUG LOGGER BONITO
# =========================================================
import time

def log_step(step, data=None):
    print("\n" + "="*60)
    print(f"🚀 STEP: {step}")
    if data is not None:
        print("📦 DATA:")
        try:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(data)
    print("="*60 + "\n")

from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv
from flask import Flask, render_template, send_from_directory
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.tools import tool
import sqlite3
import os
import json
import uuid
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import datetime
import secrets


# =========================================================
# Inicialização
# =========================================================
load_dotenv()

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)

# 🔥 SECRET_KEY dinâmica → limpa sessão a cada restart
app.secret_key = secrets.token_hex(32)


app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('../db', exist_ok=True)

# =========================================================
# Modelo LLM
# =========================================================
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2
)
# =========================================================
# Banco de Dados
# =========================================================
DB_PATH = '../db/curriculos.db'
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 🔹 Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT,
            bio TEXT,
            data_criacao TEXT
        )
    ''')

    # 🔹 Tabela de análises
    c.execute('''
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
    ''')

    conn.commit()
    conn.close()
    
init_db()

# =========================================================
# TOOL ÚNICA DE ANÁLISE
# =========================================================
@tool
def analisar_curriculo(texto: str) -> str:
    """
    Analisa currículo de forma criteriosa e retorna JSON estruturado.
    """

    log_step("TOOL iniciou")

    # =========================
    # SANITIZAÇÃO
    # =========================
    if not texto or len(texto.strip()) < 50:
        log_step("TOOL texto insuficiente")
        return json.dumps({
            "erro": "Texto do currículo insuficiente"
        })

    texto = texto[:15000]

    log_step("TOOL texto truncado", {
        "tamanho_texto": len(texto)
    })

    # =========================
    # PROMPT ULTRA CRITERIOSO
    # =========================
    prompt = f"""
Você é um ESPECIALISTA SÊNIOR em recrutamento técnico e análise de currículos.

Sua tarefa é fazer uma análise EXTREMAMENTE criteriosa.

================================
🎯 OBJETIVO
================================
Extrair informações REAIS do currículo e avaliar a qualidade profissional.

⚠️ REGRAS CRÍTICAS:

- NÃO invente informações
- NÃO deduza dados não explícitos
- Se não encontrar → use null
- Seja rigoroso na pontuação
- Penalize currículos vagos
- Penalize falta de métricas
- Penalize falta de experiência
- Penalize formatação pobre

================================
📊 CRITÉRIOS DE SCORE (0–100)
================================

Baseie-se em:

1. Clareza e organização (0–20)
2. Experiência relevante (0–25)
3. Uso de métricas e resultados (0–15)
4. Habilidades técnicas (0–15)
5. Formação acadêmica (0–10)
6. Profissionalismo do texto (0–10)
7. Diferenciais (certificações, projetos etc.) (0–5)

Seja CRITERIOSO. Não dê nota alta facilmente.

================================
📦 FORMATO DE SAÍDA (OBRIGATÓRIO)
================================

Retorne APENAS JSON válido:

{{
  "nome": string | null,
  "email": string | null,
  "telefone": string | null,
  "experiencia": [string],
  "educacao/formação": [string],
  "habilidades": [string],
  "idiomas": [string],
  "score": number,
  "justificativa_score": string,
  "nivel_curriculo": "fraco" | "medio" | "forte",
  "pontos_fortes": [string],
  "pontos_fracos": [string],
  "sugestoes": [string]
}}

⚠️ PROIBIDO:
- texto fora do JSON


================================
📄 CURRÍCULO
================================
{texto}
"""

    # =========================
    # CHAMADA DO MODELO
    # =========================
    log_step("TOOL chamando LLM")

    try:
        response = model.invoke(prompt)
        content = response.content.strip()

        log_step("TOOL resposta bruta", content[:800])

        # =========================
        # LIMPEZA FORTE
        # =========================
        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "").strip()

        # =========================
        # VALIDA JSON
        # =========================
        parsed = json.loads(content)

        log_step("TOOL JSON válido")

        return json.dumps(parsed, ensure_ascii=False)

    except Exception as e:
        log_step("TOOL ERRO", str(e))

        # 🔥 FALLBACK SE O MODELO VIAJAR
        return json.dumps({
            "erro": "Falha ao analisar currículo",
            "detalhe": str(e)
        }, ensure_ascii=False)

tools = [analisar_curriculo]

# =========================================================
# SYSTEM PROMPT DO AGENTE
# =========================================================
system_prompt = """
Você é um especialista em currículos e carreira.

REGRAS IMPORTANTES:

- Você NÃO deve usar ferramentas automaticamente.
- Só use a ferramenta analisar_curriculo quando o usuário
  pedir explicitamente para analisar um currículo.
- Se for conversa normal, responda de forma natural e útil.
- Se não houver currículo disponível, apenas converse.

COMPORTAMENTO:

REGRAS DE FORMATAÇÃO:
- Use Markdown estruturado.
- Use **negrito** para termos importantes.
- Para listas, use bullet points (*) com uma linha em branco entre os itens.
- Se for criar tabelas, use a sintaxe padrão de Markdown.
- IMPORTANTE: Sempre pule uma linha dupla entre parágrafos para garantir a legibilidade.


MODO CONVERSA:
- Respostas naturais
- Sugestões de carreira
- Dicas de currículo
- Tom amigável

MODO ANÁLISE (quando solicitado):
- Use a ferramenta analisar_curriculo
- Retorne JSON válido

================================
📌 REGRAS PARA SUGESTÕES
================================

- Cada sugestão deve ser específica ao conteúdo real do currículo.
- NÃO use sugestões genéricas.
- NÃO repita padrões como:
  "Adicionar métricas"
  "Melhorar formatação"
  "Adicionar mais detalhes"

- Se sugerir melhoria, cite exatamente onde e por quê./

==================================================
📦 FORMATO DE SAÍDA (OBRIGATÓRIO)
==================================================

Retorne APENAS JSON válido:

{
  "nome": string | null,
  "email": string | null,
  "telefone": string | null,
  "experiencia": [string],
  "educacao/formação": [string],
  "habilidades": [string],
  "idiomas": [string],
  "score": number,
  "justificativa_score": string,
  "nivel_curriculo": "fraco" | "medio" | "forte",
  "pontos_fortes": [string],
  "pontos_fracos": [string],
  "sugestoes": [string]
}

⚠️ PROIBIDO:

- texto fora do JSON

Se não tiver certeza, NÃO use a ferramenta.
"""

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt
)

# =========================================================
# ROTAS DE PÁGINAS (MULTIPAGE)
# =========================================================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    user = session.get("user")
    if not user:
        return redirect(url_for("home"))
    return render_template("dashboard.html", user=user)

@app.route("/settings")
def settings_page():
    user = session.get("user")
    if "user" not in session:
        return redirect(url_for("home"))
    return render_template("settings.html")


# =========================================================
# UPLOAD E ANÁLISE
# =========================================================
# =========================================================
# =========================================================
@app.route('/upload_curriculo', methods=['POST'])
def upload_curriculo():
    log_step("UPLOAD iniciado")

    if 'file' not in request.files:
        log_step("UPLOAD erro", "arquivo não enviado")
        return jsonify({'error': 'Arquivo não enviado'}), 400

    file = request.files['file']

    log_step("UPLOAD arquivo recebido", {"filename": file.filename})

    if file.filename == '':
        log_step("UPLOAD erro", "filename vazio")
        return jsonify({'error': 'Arquivo inválido'}), 400

    if not file.filename.lower().endswith('.pdf'):
        log_step("UPLOAD erro", "não é PDF")
        return jsonify({'error': 'Apenas PDF permitido'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    log_step("UPLOAD arquivo salvo", filepath)

    # =========================
    # EXTRAÇÃO PDF
    # =========================
    reader = PdfReader(filepath)
    texto = ""
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        texto += page_text
        log_step(f"PDF página {i+1} extraída", {"chars": len(page_text)})

    log_step("PDF texto total", {"chars_total": len(texto)})

    # =========================
    # CHAMADA DO AGENTE (USANDO TOOL)
    # =========================
    try:
        log_step("Chamando agente para analisar currículo")
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Analise este currículo e retorne JSON válido:\n\n{texto}"
                }
            ]
        })

        resposta_final = result["messages"][-1].content
        log_step("Resposta final do agente", resposta_final[:3000])

        # =========================
        # Limpeza da resposta JSON
        # =========================
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

        resposta_limpa = limpar_json_response(resposta_final)
        analise_json = json.loads(resposta_limpa)
        log_step("JSON parseado com sucesso", analise_json)

    except Exception as e:
        log_step("ERRO na análise", str(e))
        return jsonify({'error': 'Erro ao processar currículo'}), 500

    # =========================
    # SESSION
    # =========================
    session["curriculo"] = analise_json
    log_step("Currículo salvo na sessão")

    # =========================
    # BANCO DE DADOS
    # =========================
    user = session.get("user")
    if not user or not user.get("id"):
        return jsonify({'error': 'Usuário não logado'}), 403

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    analise_id = str(uuid.uuid4())

    c.execute('''
        INSERT INTO analises (
            id, user_id, nome, email, telefone, score, sugestoes, data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        analise_id,
        user["id"],
        analise_json.get('nome'),
        analise_json.get('email'),
        analise_json.get('telefone'),
        analise_json.get('score', 0),
        '; '.join(analise_json.get('sugestoes', [])),
        datetime.datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    log_step("Registro salvo no banco", {
        "id": analise_id,
        "user_id": user["id"],
        "score": analise_json.get('score')
    })

    return jsonify({
        'id': analise_id,
        'info': analise_json,
        'score': analise_json.get('score', 0),
        'sugestoes': analise_json.get('sugestoes', [])
    })
# =========================================================
# CHAT CONTEXTUAL
# =========================================================

@app.route("/chat")
def chat_page():
    # Pega o usuário logado na sessão
    user = session.get("user")
    if not user:
        return redirect(url_for("home"))

    # Não precisa buscar no banco, já temos o user
    return render_template("chat.html", user=user)

@app.post("/chat")
def chat():
    log_step("RAW request.json", request.json)
    log_step("CHAT iniciado")

    user_msg = request.json.get("msg", "")
    log_step("Mensagem do usuário", user_msg)

    curriculo = session.get("curriculo")

    if curriculo:
        log_step("CHAT com contexto de currículo")

        contexto = f"""
Currículo atual do usuário:
{json.dumps(curriculo, ensure_ascii=False)}

Pergunta do usuário:
{user_msg}
"""
    else:
        log_step("CHAT sem currículo na sessão")
        contexto = user_msg

    log_step("Invocando agente")

    result = agent.invoke({
        "messages": [{"role": "user", "content": contexto}]
    })

    resposta = result["messages"][-1].content

    log_step("Resposta do agente", resposta)

    return jsonify({
        "response": resposta
    })

# =========================================================
# PÁGINA DE PERFIL - GET E POST
# =========================================================

from flask import redirect, url_for

# ======================================
# LOGIN / LOGOUT
# ======================================
@app.route("/login", methods=["POST"])
def login():
    nome = request.form.get("nome")
    email = request.form.get("email")

    if not nome or not email:
        return "Nome e e-mail obrigatórios", 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 🔹 Verifica se usuário já existe
    c.execute("SELECT id, nome, email, telefone, bio FROM usuarios WHERE email=?", (email,))
    row = c.fetchone()

    if row:
        user_id, nome_db, email_db, telefone, bio = row
    else:
        user_id = str(uuid.uuid4())
        telefone = ""
        bio = ""
        c.execute("""
            INSERT INTO usuarios (id, nome, email, telefone, bio, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, nome, email, telefone, bio, datetime.datetime.now().isoformat()))
        conn.commit()

    conn.close()

    # 🔹 Salva dados do usuário na sessão
    session["user"] = {
        "id": user_id,
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "bio": bio
    }

    session["curriculo"] = None  # resetar currículo atual

    return redirect(url_for("chat"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

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

# =========================================================
# HISTÓRICO API
# =========================================================
@app.route('/historico', methods=['GET'])
def historico():
    user_id = session.get("user", {}).get("id")
    if not user_id:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, score, sugestoes, data FROM analises WHERE user_id=? ORDER BY data DESC', (user_id,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {
            'id': row[0],
            'score': row[1],
            'sugestoes': row[2],
            'data': row[3]
        }
        for row in rows
    ])

# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app.run(port=5000, debug=True)