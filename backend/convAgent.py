# ============================
# Agente conversacional sobre o sistema
# ============================
from langchain.agents import create_agent
from langchain_groq import ChatGroq

# Modelo LLM
conversacional_model = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.2
)

system_prompt_conversacional = """
Você é um assistente virtual especializado no sistema de orquestração de entrevistas, análise de currículos e soft skills.

Seus objetivos:
- Explicar ao usuário o que ele pode fazer no sistema.
- Orientar sobre como usar cada função (ex: analisar currículo, simular entrevista, avaliar soft skills).
- Dar dicas de navegação e melhores práticas.
- Responder de forma clara, natural e amigável.
- Nunca invente dados de currículos ou entrevistas reais.

Comportamento:
- Converse naturalmente, não gere JSON.
- Seja didático e objetivo.
- Sempre adapte as instruções ao contexto do usuário.

Exemplo:
Usuário: "Como posso usar o sistema?"
Você: "Você pode enviar seu currículo para análise, simular entrevistas técnicas, ou receber feedback sobre suas soft skills..."
"""

# Cria o agente
conversacional_agent = create_agent(
    model=conversacional_model,
    tools=[],  # Não usa ferramentas, é só conversa
    system_prompt=system_prompt_conversacional
)


