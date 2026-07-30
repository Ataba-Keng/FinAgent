"""
FinAgent : agent orienté tâche pour l'analyse de documents financiers.

Principe de conception (à documenter tel quel dans les entretiens FDE) :
- L'agent ne répond JAMAIS sans passer par l'outil `search_documents`.
- Le prompt système impose un refus explicite si le contexte récupéré
  ne contient pas la réponse ("grounding strict"), plutôt que de laisser
  le modèle combler avec ses connaissances générales.
- Chaque appel outil est journalisé (source, score) pour être rejouable
  dans le harness d'Evals (evals/evaluate.py).
"""
import os
import time
from dataclasses import dataclass, field
from typing import List

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from rag_pipeline import FinancialRAGPipeline

GROQ_MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = """Tu es un assistant d'analyse financière pour un usage professionnel.

Règles strictes :
1. Utilise toujours l'outil search_documents avant de répondre à une question sur des chiffres ou des faits financiers.
2. Si le contexte récupéré ne contient pas l'information demandée, réponds EXACTEMENT, mot pour mot, sans reformuler :
   "Je ne trouve pas cette information dans les documents fournis."
   N'utilise aucune autre formulation de refus. Si le contexte contient l'information demandée, même formulée différemment de la question, réponds-y directement en citant la source ; ne refuse jamais par excès de prudence quand l'information est présente. Ne complète jamais une réponse avec des connaissances générales absentes du contexte.
3. Pour tout calcul, utilise l'outil calculate plutôt que de calculer mentalement.
4. Cite systématiquement la source (nom de document) de chaque affirmation factuelle.
"""

_pipeline = FinancialRAGPipeline()


@dataclass
class ToolCallLog:
    tool_name: str
    input: str
    output: str
    latency_s: float


call_log: List[ToolCallLog] = field(default_factory=list) if False else []


@tool
def search_documents(query: str) -> str:
    """Recherche dans les documents financiers indexés et retourne les passages pertinents avec leur source."""
    t0 = time.time()
    chunks = _pipeline.retrieve(query, k=2)
    if not chunks:
        result = "Aucun passage pertinent trouvé."
    else:
        result = "\n---\n".join(f"[Source: {c.source}] {c.text}" for c in chunks)
    call_log.append(ToolCallLog("search_documents", query, result, time.time() - t0))
    return result


@tool
def calculate(expression: str) -> str:
    """Évalue une expression arithmétique simple (ex: '(120000 - 95000) / 95000 * 100')."""
    t0 = time.time()
    try:
        allowed = set("0123456789.+-*/() ")
        if not set(expression) <= allowed:
            raise ValueError("expression non autorisée")
        result = str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        result = f"Erreur de calcul : {e}"
    call_log.append(ToolCallLog("calculate", expression, result, time.time() - t0))
    return result


def build_agent() -> AgentExecutor:
    llm = ChatGroq(model=GROQ_MODEL, temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    tools = [search_documents, calculate]
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)


def ask(question: str) -> dict:
    """Point d'entrée utilisé par l'app et par le harness d'Evals."""
    call_log.clear()
    executor = build_agent()
    t0 = time.time()
    result = executor.invoke({"input": question})
    return {
        "question": question,
        "answer": result["output"],
        "tool_calls": [c.__dict__ for c in call_log],
        "latency_s": time.time() - t0,
    }