# FinAgent — Agent RAG financier, Evals formalisées, déploiement Kubernetes multi-cloud

Projet portfolio construit pour combler deux exigences concrètes des postes
Forward Deployed AI Engineer : l'évaluation rigoureuse d'un système GenAI, et
son déploiement en environnement conteneurisé portable entre clouds.

## Ce que fait le système

Un agent (LangChain + Claude) répond à des questions sur des documents
financiers, avec deux règles non négociables :
- il ne répond jamais sans passer par l'outil `search_documents` (grounding strict) ;
- il refuse explicitement quand le contexte récupéré ne contient pas la réponse,
  plutôt que de compléter avec des connaissances générales.

## Evals

`evals/evaluate.py` fait tourner l'agent sur un golden dataset de 12 questions
(`evals/golden_dataset.jsonl`) mêlant questions factuelles présentes dans les
documents, questions hors-contexte (pour tester le refus), et questions de calcul.

Quatre métriques, choisies pour répondre chacune à une question business, pas
juste "faire un score" :

| Métrique | Question à laquelle elle répond |
|---|---|
| Groundedness (LLM-as-judge) | Le système invente-t-il des chiffres ? |
| Correct refusal rate | Sait-il dire qu'il ne sait pas ? |
| Source attribution rate | Peut-on auditer chaque réponse ? |
| Latence p50/p95 | Le système tient-il un SLA raisonnable ? |

Le seuil de groundedness (`--fail-under 0.85`) est un gate CI : en dessous,
le pipeline échoue et bloque le déploiement.

## Résultats des Evals et itérations

Les métriques ci-dessous ne sont pas le premier run, elles sont le résultat
de plusieurs itérations de debug, documentées ici parce qu'elles disent
autant sur le système que le chiffre final.

### Résultat final (llama-3.1-8b-instant, Groq, free tier)

| Métrique | Valeur |
|---|---|
| Groundedness (LLM-judge) | 91,7% |
| Taux de refus correct | 75% |
| Attribution de source correcte | 91,7% |
| Latence p50 / p95 | 15,9s / 27,2s |

### Ce qui a été corrigé en cours de route

1. **Embedding par défaut inadapté au français.** Le modèle d'embedding par
   défaut de ChromaDB (`all-MiniLM-L6-v2`) est entraîné presque exclusivement
   en anglais. Sur des documents français, les scores de similarité tombaient
   à ~0,09 (quasi aléatoire) et le retrieval renvoyait des passages sans
   rapport avec la question. Passage à un modèle multilingue
   (`paraphrase-multilingual-MiniLM-L12-v2`) : scores remontés à ~0,7,
   retrieval pertinent.

2. **Taille de chunk contrainte par le quota API du free tier.** Groq limite
   `llama-3.1-8b-instant` à 6000 tokens/minute sur le tier gratuit. Des chunks
   de 1000 caractères avec k=4 dépassaient cette limite. Réduit à 500
   caractères et k=2, un compromis assumé entre coût (gratuit) et richesse du
   contexte par requête.

3. **Refus non standardisé, invisible à la mesure automatique.** Le prompt
   système initial laissait le modèle reformuler librement son refus
   ("je ne trouve pas...", "aucune mention de..."), rendant la détection par
   correspondance de texte peu fiable. Le prompt impose maintenant une phrase
   de refus invariante, ce qui rend `correct_refusal_rate` mesurable sans
   ambiguïté.

### Comparaison de modèles pour l'agent (tool-calling)

| Modèle | Résultat |
|---|---|
| `llama-3.3-70b-versatile` | Rejeté : erreur `Failed to call a function` reproductible sur des appels d'outils simples (2 outils, schéma basique), indépendamment des autres fixes (embedding, taille de chunk, prompt). Instabilité propre au modèle sur ce cas d'usage précis. |
| `llama-3.1-8b-instant` | Retenu : stable sur le tool-calling, mais tendance à la sur-prudence sur des questions formulées avec un acronyme entre parenthèses (ex: "outil abrégé en RIBAT"), refusant parfois même quand le contexte récupéré contient explicitement la réponse. |

### Limite connue, assumée

Le taux de refus correct (75%) reflète une vraie limite du modèle gratuit
choisi, pas un bug du système : sur 3 des 12 questions du golden set,
l'agent refuse par excès de prudence malgré un contexte pertinent et
explicite. Documenté plutôt que masqué, ce point serait la première chose à
traiter avec un budget de calcul plus important (modèle plus grand et plus
fiable, type Claude ou GPT-4, sur lequel ce même harnais tournerait sans
modification).

## Déploiement

- `Dockerfile` + `agent/api.py` : l'agent exposé en API FastAPI avec probes
  liveness/readiness, prêt pour Kubernetes.
- `k8s/` : manifests bruts (Deployment, Service, HPA) pour un déploiement
  direct, cloud-agnostique.
- `helm/finagent/` : même chart, `values-aws.yaml` et `values-gcp.yaml`
  isolent uniquement ce qui change réellement d'un cloud à l'autre (registre
  d'images, classe de stockage, annotations du Load Balancer).
- `terraform/aws/` : module EKS, sur le même modèle que le data lake Terraform
  déjà en production dans mon activité freelance.
- `terraform/gcp/` : module GKE équivalent, écrit sur la même structure —
  **non déployé faute de compte GCP facturable**, à valider par `terraform plan`
  avant tout usage réel.
- `.github/workflows/ci-cd.yaml` : build → Evals (gate) → push image → `helm upgrade`.

## Limites assumées 

- Le module GCP est un pattern de portabilité documenté, pas un déploiement
  testé en conditions réelles.
- Le golden dataset (12 questions) est un point de départ méthodologique,
  pas une couverture exhaustive ; en contexte client, il serait construit
  avec les experts métier du domaine.
- Pas de test de charge réel sur le HPA (les seuils sont des valeurs de
  départ raisonnables, pas des chiffres mesurés).

