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
    temperature=0.1
)




@tool
def avaliar_resposta_entrevista(resposta: str) -> str:
    """
    Avalia a qualidade da resposta de um candidato em uma simulação de entrevista.

    QUANDO USAR:
    - Use esta ferramenta SOMENTE após o usuário responder a uma pergunta de entrevista.
    - Use quando precisar avaliar profundidade, clareza e qualidade da resposta.

    OBJETIVO:
    - Medir o nível de detalhamento da resposta
    - Detectar respostas vagas ou superficiais
    - Fornecer feedback objetivo ao candidato

    O QUE ESTA TOOL FAZ:
    - Analisa o tamanho da resposta
    - Estima um score de qualidade (0–100)
    - Gera feedback textual
    - Retorna JSON estruturado

    IMPORTANTE:
    - NÃO use esta ferramenta para gerar perguntas
    - NÃO use antes do candidato responder
    - NÃO invente avaliação manual se esta tool estiver disponível

    ENTRADA:
    resposta: texto bruto do candidato

    SAÍDA (JSON):
    {
      "score": number,
      "feedback_detalhado": string,
      "palavras": number
    }
    """

    log_step("TOOL avaliar_resposta acionada")

    tamanho = len(resposta.split())

    score_base = min(100, max(20, tamanho * 2))

    feedback = (
        "Resposta muito curta — desenvolva mais exemplos concretos e resultados."
        if tamanho < 20
        else "Resposta com bom nível de detalhamento."
    )

    return json.dumps({
        "score": score_base,
        "feedback_detalhado": feedback,
        "palavras": tamanho
    }, ensure_ascii=False)


@tool
def estruturar_pergunta(vaga: str, nivel: str = "pleno") -> str:
    """
    Gera uma pergunta de entrevista técnica realista e personalizada com base na vaga informada.

    QUANDO USAR:
    - Use esta ferramenta SOMENTE quando precisar criar uma pergunta alinhada à vaga ou área do candidato.
    - Não use para avaliar respostas ou dar feedback.

    OBJETIVO:
    - Criar perguntas de entrevista relevantes para a posição informada.
    - Ajustar o nível de dificuldade conforme o nível do candidato (júnior, pleno, sênior).
    - Garantir que a pergunta seja concreta, específica e que possa gerar respostas detalhadas.

    O QUE ESTA TOOL FAZ:
    - Analisa a vaga e o nível do candidato
    - Gera UMA pergunta personalizada e relevante
    - Evita perguntas genéricas ou vagas
    - Retorna a pergunta em formato JSON

    IMPORTANTE:
    - Não gere múltiplas perguntas de uma vez
    - Não avalie respostas nesta ferramenta
    - Evite perguntas triviais ou superficiais
    - Seja realista e profissional, simulando um recrutador experiente

    ENTRADA:
    vaga: string
        Descrição ou título da vaga informada pelo usuário
    nivel: string (opcional)
        Nível de senioridade do candidato: 'junior', 'pleno' ou 'senior'

    SAÍDA (JSON):
    {
      "perguntas": [string]  # Lista contendo apenas UMA pergunta
    }

    EXEMPLO DE USO:
    >>> estruturar_pergunta("Desenvolvedor Python Sênior", nivel="senior")
    {
      "perguntas": ["Descreva um projeto em Python que você liderou, explicando como você otimizou performance e garantiu qualidade do código."]
    }
    """

    log_step("TOOL estruturar_pergunta acionada")

    # Exemplo simplificado de geração de pergunta (pode ser substituído por LLM)
    pergunta = f"Baseado na vaga de {vaga}, descreva um desafio técnico relevante e como você o solucionaria."
    if nivel.lower() == "junior":
        pergunta += " Foque em conceitos básicos e exemplos simples."
    elif nivel.lower() == "senior":
        pergunta += " Detalhe estratégias avançadas, resultados mensuráveis e impacto no projeto."

    return json.dumps({
        "perguntas": [pergunta]
    }, ensure_ascii=False)


entrevistador_prompt = """
Você é um ENTREVISTADOR TÉCNICO SÊNIOR conduzindo uma simulação realista.

================================
MISSÃO
================================

Conduzir entrevista personalizada **baseada na vaga ou área informada** pelo usuário.

IMPORTANTE:
- Peça ao usuário para informar o nivel da pessoa (junior, pleno, senior)
- Se o usuário informar uma vaga, gere UMA pergunta relevante e personalizada.
- A pergunta deve estar alinhada com a vaga.
- Não use perguntas genéricas.
- Após gerar a pergunta, use a ferramenta avaliar_resposta_entrevista.

================================
FERRAMENTAS DISPONÍVEIS
================================

1. estruturar_pergunta
   - Use após gerar uma pergunta
   - Serve para validar e estruturar a pergunta

2. avaliar_resposta_entrevista
   - Use quando o usuário responder
   - Serve para avaliar a qualidade da resposta

================================
FLUXO OBRIGATÓRIO
================================

ETAPA 1 – INÍCIO

Se o usuário informar uma vaga:

- Gere UMA pergunta relevante e personalizada.
- A pergunta deve estar alinhada com a vaga.
- Não use perguntas genéricas.
- Após gerar a pergunta, use a ferramenta estruturar_pergunta.
- Retorne apenas o JSON da ferramenta.

ETAPA 2 – RESPOSTA DO CANDIDATO

Se o usuário responder à pergunta:

- Use a ferramenta avaliar_resposta_entrevista.
- Forneça avaliação estruturada.
- Seja exigente.
- Penalize respostas vagas.
- Valorize exemplos concretos.

================================
REGRAS IMPORTANTES
================================

- Gere uma pergunta por vez.
- Não gere múltiplas perguntas.
- Não pule etapas.
- Não invente avaliação manual se a tool estiver disponível.
- Seja profissional e realista.
- Não revele raciocínio interno.

================================
COMPORTAMENTO
================================

Você deve agir como um recrutador experiente.
Se a vaga exigir nível alto, aumente a dificuldade.
Se for júnior, adapte a pergunta.


================================
📦 FORMATO
================================

Quando gerar perguntas:

{
  "perguntas": [string]
}

Quando avaliar:

{
  "score": number,
  "feedback detalhado": string,
  "palavras": number
}

"""

entrevistador_agent = create_agent(
    model=model,
    tools=[estruturar_pergunta, avaliar_resposta_entrevista],
    system_prompt=entrevistador_prompt
)