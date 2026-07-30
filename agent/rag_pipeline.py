"""
Pipeline RAG pour documents financiers.
Reprend l'architecture du projet "Assistant Financier IA" : parsing PDF,
vectorisation ChromaDB, retrieval contraint au contexte récupéré.
"""
from dataclasses import dataclass
from typing import List

import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path

DEFAULT_PERSIST_DIR = str(Path(__file__).resolve().parent / "chroma_store")

@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


class FinancialRAGPipeline:
    """
    Encapsule l'indexation et la récupération de contexte pour des
    documents comptables/financiers. Ne fait aucune génération elle-même :
    la génération et le grounding strict sont gérés par l'agent (agent.py),
    ce qui permet d'évaluer retrieval et génération séparément dans les Evals.
    """

    def __init__(self, collection_name: str = "financial_docs", persist_dir: str = None):
        persist_dir = persist_dir or DEFAULT_PERSIST_DIR
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedder = embedding_functions.SentenceTransformerEmbeddingFunction(
           model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedder
        )

    def index_documents(self, chunks: List[str], sources: List[str]) -> None:
        ids = [f"chunk-{i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, metadatas=[{"source": s} for s in sources], ids=ids)

    def retrieve(self, query: str, k: int = 2) -> List[RetrievedChunk]:
        results = self.collection.query(query_texts=[query], n_results=k)
        out = []
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            out.append(RetrievedChunk(text=doc, source=meta.get("source", "unknown"), score=1 - dist))
        return out
