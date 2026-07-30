# Rapport d'Evals — FinAgent

- Exemples évalués : 12
- Groundedness (LLM-judge) : 91.7%
- Taux de refus correct (hors-contexte) : 75.0%
- Attribution de source correcte : 91.7%
- Latence p50 : 15.86s, p95 : 27.19s

## Détail par exemple

| ID | Catégorie | Grounded | Refus correct | Source OK | Latence (s) |
|---|---|---|---|---|---|
| q01 | factuel_present | ✅ | ✅ | ✅ | 1.03 |
| q02 | factuel_present | ❌ | ✅ | ✅ | 0.82 |
| q03 | hors_contexte | ✅ | ✅ | ✅ | 1.84 |
| q04 | factuel_present | ✅ | ✅ | ❌ | 27.19 |
| q05 | hors_contexte | ✅ | ✅ | ✅ | 17.31 |
| q06 | factuel_present | ✅ | ❌ | ✅ | 15.08 |
| q07 | factuel_present | ✅ | ❌ | ✅ | 22.24 |
| q08 | factuel_present | ✅ | ✅ | ✅ | 15.04 |
| q09 | hors_contexte | ✅ | ✅ | ✅ | 16.45 |
| q10 | factuel_present | ✅ | ❌ | ✅ | 16.08 |
| q11 | factuel_present | ✅ | ✅ | ✅ | 15.63 |
| q12 | factuel_present | ✅ | ✅ | ✅ | 16.23 |