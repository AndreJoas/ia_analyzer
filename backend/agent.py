# llm.py
import json
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langchain.tools import tool
from backend.logger import log_step

# ============================
# Modelo LLM
# ============================
model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2
)
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
  "educacao/formacao": [string],
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
  "educacao/formacao": [string],
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
