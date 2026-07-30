FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent/ ./agent
COPY evals/ ./evals

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# En prod : servir agent.ask() derrière une API (FastAPI) plutôt qu'en CLI direct.
CMD ["python", "-m", "agent.api"]
