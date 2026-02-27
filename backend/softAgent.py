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

    #AGENTE AVALIADOR DE SOFT SKILLS

softskills_prompt = """
Você é um especialista em avaliação de soft skills e feedback de desempenho.

OBJETIVO:

1. Identificar soft skills implícitas na frase do candidato.
2. Avaliar a força e clareza da frase.
3. Reescrever a frase de forma mensurável e concreta.
4. Sugerir melhorias específicas para aumentar o impacto da resposta.

REQUISITOS:

- Seja direto e conciso.
- Use uma linguagem profissional.
- Produza a saída sempre no formato JSON:

{
  "soft_skill": "<nome da soft skill detectada>",
  "frase_original": "<entrada do candidato>",
  "frase_mensuravel": "<versão mensurável da frase>",
  "sugestao_melhoria": "<recomendações para melhorar a frase>"
}

EXEMPLO:

Entrada:
"Trabalhei em equipe"

Saída esperada:
{
  "soft_skill": "Trabalho em equipe",
  "frase_original": "Trabalhei em equipe",
  "frase_mensuravel": "Conduzi um projeto em equipe de 5 pessoas e atingimos 100% das metas estabelecidas.",
  "sugestao_melhoria": "Inclua resultados concretos e números para demonstrar impacto."
}
"""

from langchain.agents import create_agent

softskills_agent = create_agent(
    model=model,
    tools=[],
    system_prompt=softskills_prompt
)

