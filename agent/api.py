"""API minimale exposant FinAgent, pensée pour tourner derrière Kubernetes
(liveness/readiness probes incluses)."""
from fastapi import FastAPI
from pydantic import BaseModel

from agent import ask

app = FastAPI(title="FinAgent")


class Question(BaseModel):
    question: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # En prod : vérifier la connexion à ChromaDB / au vector store distant ici.
    return {"status": "ready"}


@app.post("/ask")
def ask_endpoint(q: Question):
    return ask(q.question)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
