# routes_chat.py
from flask import Blueprint, request, jsonify, session, json
from backend.SimulatorAgent import avaliar_resposta_entrevista, estruturar_pergunta
from backend.logger import log_step
from backend.agent import agent
from backend.config import app


from backend.orquestrador import multiagent_graph
from backend.orquestrador import entrevistador_agent





import re




@app.route("/chat_orquestrador", methods=["POST"])
def chat():
    log_step("RAW request.json", request.json)
    log_step("CHAT iniciado")

    # Captura a mensagem do usuário
    user_msg = request.json.get("msg", "")
    log_step("Mensagem do usuário", user_msg)

    # Obtém currículo da sessão (se houver)
    curriculo = session.get("curriculo")

    # =========================
    # Cria estado inicial
    # =========================
    state = {
        "user_input": user_msg
    }

    if curriculo:
        log_step("CHAT com contexto de currículo")
        state["curriculo_json"] = curriculo
    else:
        log_step("CHAT sem currículo na sessão")

    # =========================
    # Extrai vaga do texto do usuário
    # =========================
    vaga_alvo = None
    match = re.search(r'vaga\s+(?:de\s+)?([a-zA-ZÀ-ú ]+)', user_msg, re.IGNORECASE)
    if match:
        vaga_alvo = match.group(1).strip()
        log_step("Vaga detectada pelo usuário", vaga_alvo)
        state["vaga_alvo"] = vaga_alvo

    # =========================
    # Fluxo principal
    # =========================
    user_msg_lower = user_msg.lower()

    # Se o usuário informou o nível da vaga, inicia diretamente o entrevistador
    if user_msg_lower in ["junior", "pleno", "sênior"]:
        log_step("Nivel da vaga detectado", user_msg_lower)
        state["nivel_vaga"] = user_msg_lower
        
        # Chama a versão "safe" do entrevistador
        result = call_entrevistador_safe(state)

    else:
        # Caso normal, passa pelo orquestrador multiagente
        log_step("Invocando ORQUESTRADOR")
        result = multiagent_graph.invoke(state)

    # =========================
    # Resposta final
    # =========================
    resposta = result.get("final_output", "Não consegui processar.")
    log_step("Resposta final", resposta)

    return jsonify({"response": resposta})

def call_entrevistador_safe(state):
    from backend.orquestrador import entrevistador_agent
    import json

    print("\n=== CALL ENTREVISTADOR AGENT (SAFE) ===")

    # Pega do estado: se não houver, cai no default
    vaga_alvo = state.get("vaga_alvo", "Engenheiro(a)")
    nivel_vaga = state.get("nivel_vaga", "junior")

    # Mensagem dinâmica, incluindo a vaga real do usuário
    user_prompt = f"""
    Gere uma pergunta técnica e comportamental para a vaga '{vaga_alvo}' ({nivel_vaga}).
    A pergunta deve ser realista, alinhada à vaga e retornar JSON com a key 'perguntas'.
    """

    # ⚠️ Evita tool call validation, forçando uso da ferramenta interna do agente
    out = entrevistador_agent.invoke({
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "tools": [estruturar_pergunta, avaliar_resposta_entrevista]
  # evita erros de validação
    })

    # Extrai o conteúdo do agente
    content = out["messages"][-1].content
    perguntas = []

    try:
        perguntas = json.loads(content).get("perguntas", [])
    except Exception as e:
        print("⚠️ Falha ao parsear JSON:", e)
        # fallback: retorna o texto bruto do agente
        perguntas = [content]

    return {
        "perguntas_entrevista": perguntas,
        "final_output": content
    }












@app.route("/chat", methods=["POST"])
def chat2():
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

    return jsonify({"response": resposta})