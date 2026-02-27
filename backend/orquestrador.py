from typing import TypedDict, List, Optional

# llm.py
import json
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.tools import tool
from backend.logger import log_step
  


from backend.softAgent import softskills_agent
from backend.SimulatorAgent import entrevistador_agent
from backend.convAgent import conversacional_agent
from backend.agent import agent


curriculo_agent = agent

# ============================
# Modelo LLM
# ============================
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2
)


class MultiAgentState(TypedDict, total=False):
    user_input: str
    intent: str

    # currículo
    curriculo_texto: str
    curriculo_json: dict

    # soft skills
    softskills_input: str
    softskills_feedback: str

    # entrevista
    vaga_alvo: str
    perguntas_entrevista: List[str]
    resposta_usuario: str
    feedback_entrevista: str

    final_output: str



# ============================
# Funções de chamada dos agentes
# ============================
def call_curriculo_agent(state: MultiAgentState):
    print("\n=== CALL CURRICULO AGENT ===")
    print("Entrada:", state["curriculo_texto"][:200], "...")  # mostra só os primeiros 200 caracteres
    out = curriculo_agent.invoke({
        "messages": [
            {"role": "user", "content": state["curriculo_texto"]}
        ]
    })
    content = out["messages"][-1].content
    print("Saída bruta do agente:", content[:500], "...")  # preview de 500 chars
    curriculo_json = json.loads(content)
    print("JSON parseado:", curriculo_json)
    return {
        "curriculo_json": curriculo_json,
        "final_output": curriculo_json
    }


def call_softskills_agent(state: MultiAgentState):
    print("\n=== CALL SOFTSKILLS AGENT ===")
    print("Entrada:", state["softskills_input"])
    out = softskills_agent.invoke({
        "messages": [
            {"role": "user", "content": state["softskills_input"]}
        ]
    })
    content = out["messages"][-1].content
    print("Saída do agente:", content)
    return {
        "softskills_feedback": content,
        "final_output": content
    }
def call_entrevistador(state: MultiAgentState):
    print("\n=== CALL ENTREVISTADOR AGENT ===")
    
    # Pega a vaga do estado; se não houver, usa fallback
    vaga_alvo = state.get("vaga_alvo", "Engenheiro(a)")
    nivel_vaga = state.get("nivel_vaga")  # nível informado pelo usuário, se houver
    
    # Cria prompt dinâmico com a vaga real
    if nivel_vaga:
        print(f"Iniciando entrevista direto para {vaga_alvo} ({nivel_vaga})")
        prompt = f"Inicie a entrevista para a vaga '{vaga_alvo}' ({nivel_vaga}). Faça perguntas técnicas e comportamentais relevantes, uma por vez, em JSON com key 'perguntas'."
    else:
        # Caso contrário, pergunta o nível
        prompt = f"Vaga alvo: '{vaga_alvo}'. Qual o nível de senioridade (junior, pleno, senior)?"

    # Invoca o agente
    out = entrevistador_agent.invoke({
        "messages": [{"role": "user", "content": prompt}]
    })

    content = out["messages"][-1].content
    print("Saída do agente (texto):", content[:500], "...")

    # Tenta extrair JSON
    perguntas = []
    try:
        perguntas = json.loads(content).get("perguntas", [])
        print("Perguntas parseadas:", perguntas)
    except Exception as e:
        print("⚠️ Conteúdo não está em JSON, fallback para texto:", e)
        perguntas = [content]

    return {
        "perguntas_entrevista": perguntas,
        "final_output": content
    }

# ============================
# Função de chamada do agente conversacional
# ============================
def call_conversacional_agent(state: MultiAgentState):
    print("\n=== CALL CONVERSACIONAL AGENT ===")
    user_input = state.get("user_input", "")
    print("Entrada do usuário:", user_input[:200], "...")

    out = conversacional_agent.invoke({
        "messages": [
            {"role": "user", "content": user_input}
        ]
    })

    content = out["messages"][-1].content
    print("Saída do agente:", content[:500], "...")

    return {
        "final_output": content
    }

# ============================
# Roteamento
# ============================
def route_intent(state: MultiAgentState):
    text = state.get("user_input", "").lower()
    print("\n=== ROUTE INTENT ===")
    print("User input:", text)

    if any(k in text for k in ["soft skill", "comportamental",  "softskill", "trabalhei em equipe", "perfil"]):
        print("Intent detectada: softskills")
        if "softskills_input" in state:
            return "softskills"
        else:
            print("⚠️ sem softskills_input, fallback para conversacional")
            return "conversacional"

    if any(k in text for k in ["entrevista", "simular entrevista", "mock interview"]):
        print("Intent detectada: entrevistador")
        return "entrevistador"

    if any(k in text for k in ["analisar currículo", "currículo", "cv", "resume"]):
        print("Intent detectada: curriculo")
        return "curriculo"

    # Pergunta genérica sobre o sistema → agente conversacional
    if any(k in text for k in ["como usar", "ajuda", "o que posso fazer", "boa tarde",'bom dia', 'ola','boa tarde',"como funciona"]):
        print("Intent detectada: conversacional")
        return "conversacional"

    # Fallback final
    print("Intent fallback: conversacional")
    return "conversacional"


# ============================
# Orquestrador com prints
# ============================
from langgraph.graph import StateGraph, START, END

builder = StateGraph(MultiAgentState)

builder.add_node("softskills", call_softskills_agent)
builder.add_node("entrevistador", call_entrevistador)
builder.add_node("curriculo", call_curriculo_agent)
builder.add_node("conversacional", call_conversacional_agent)

builder.add_conditional_edges(
    START,
    route_intent,
    {
        "softskills": "softskills",
        "entrevistador": "entrevistador",
        "curriculo": "curriculo",
        "conversacional": "conversacional"
    }
)

builder.add_edge("softskills", END)
builder.add_edge("entrevistador", END)
builder.add_edge("curriculo", END)
builder.add_edge("conversacional", END)

multiagent_graph = builder.compile()

print("\n=== MULTIAGENT GRAPH COMPILADO COM SUCESSO ===")