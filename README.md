# 🤖 FinAgent — Agent RAG financier (Evals rigoureux + déploiement multi-cloud)

Agent de question-réponse **RAG** sur documents financiers, bâti pour répondre aux exigences concrètes du poste de **Forward Deployed AI Engineer** : évaluation rigoureuse d'un système GenAI, et déploiement conteneurisé portable entre cloud.

---

## 🇫🇷 Français

### 🎯 Objectif
Répondre à des questions sur des **documents financiers** avec deux règles non négociables :
- ne **jamais répondre** sans passer par l'outil `search_documents` (grounding strict) ;
- **refuser explicitement** quand le contexte récupéré ne contient pas la réponse (pas de complétion par connaissance générale).

### 🏗️ Démarche
1. **Agent RAG** — LangChain + LLM (Llama-3.1-8B via Groq) + ChromaDB (embeddings multilingues) sur documents financiers.
2. **Evals formalisées** — golden dataset de **12 questions** (factuelles, hors-contexte, calcul) ; **4 métriques orientées business** : groundedness (LLM-as-judge), taux de refus correct, attribution de source, latence p50/p95.
3. **Gate CI** — seuil `--fail-under 0.85` sur la groundedness : en dessous, le pipeline échoue et bloque le déploiement.
4. **Itérations documentées** — correction de l'embedding (anglais → multilingue : scores 0,09 → ~0,7), gestion du quota API du free tier.
5. **Déploiement** — Docker, **Kubernetes multi-cloud** (Helm, Terraform) et GitHub Actions.

### 🛠️ Technologies
Python · LangChain · ChromaDB · sentence-transformers · Groq API (Llama-3.1) · FastAPI · Docker · Kubernetes / Helm · Terraform · GitHub Actions

### 📊 Résultats (évaluation finale — Groq free tier)
| Métrique | Valeur |
|---|---|
| Groundedness (LLM-judge) | **91,7 %** |
| Taux de refus correct | **75 %** |
| Attribution de source | **91,7 %** |
| Latence p50 / p95 | **15,9 s / 27,2 s** |

---

## 🇬🇧 English

### 🎯 Objective
Answer questions over **financial documents** with two non-negotiable rules:
- **never answer** without calling the `search_documents` tool (strict grounding);
- **explicitly refuse** when the retrieved context does not contain the answer (no general-knowledge completion).

### 🏗️ Approach
1. **RAG agent** — LangChain + LLM (Llama-3.1-8B via Groq) + ChromaDB (multilingual embeddings) over financial documents.
2. **Formalised evals** — golden dataset of **12 questions** (factual, out-of-context, calculation); **4 business-driven metrics**: groundedness (LLM-as-judge), correct refusal rate, source attribution, p50/p95 latency.
3. **CI gate** — `--fail-under 0.85` on groundedness: below it, the pipeline fails and blocks deploys.
4. **Documented iterations** — embedding fix (English → multilingual: similarity 0.09 → ~0.7), free-tier API quota handling.
5. **Deployment** — Docker, **multi-cloud Kubernetes** (Helm, Terraform) and GitHub Actions.

### 🛠️ Tech Stack
Python · LangChain · ChromaDB · sentence-transformers · Groq API (Llama-3.1) · FastAPI · Docker · Kubernetes / Helm · Terraform · GitHub Actions

### 📊 Results (final evaluation — Groq free tier)
| Metric | Value |
|---|---|
| Groundedness (LLM-judge) | **91.7%** |
| Correct refusal rate | **75%** |
| Source attribution | **91.7%** |
| p50 / p95 latency | **15.9s / 27.2s** |

---

### 🗂️ Structure
`agent/` (logique RAG) · `evals/` (dataset + metrics) · `docs/` · `k8s/` · `helm/` · `terraform/` · `.github/` (CI gate)