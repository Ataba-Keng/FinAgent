"""
Harness d'Evals pour FinAgent.

Métriques, choisies pour être défendables en entretien FDE (chacune répond
à une question business précise, pas une métrique ML générique) :

1. Groundedness (faithfulness) — LLM-as-judge : l'affirmation est-elle
   entièrement supportée par le contexte récupéré, sans ajout hors-source ?
   -> Répond à : "le système invente-t-il des chiffres ?"
2. Correct refusal rate — sur les questions hors-contexte du golden set,
   le système refuse-t-il explicitement plutôt que d'halluciner ?
   -> Répond à : "le système sait-il dire qu'il ne sait pas ?"
3. Source attribution rate — la source citée correspond-elle à la source
   attendue quand une réponse est donnée ?
   -> Répond à : "peut-on auditer chaque réponse ?"
4. Latence p50 / p95 — répond à : "le système est-il déployable en prod
   avec un SLA raisonnable ?"

Usage :
    python evaluate.py --dataset golden_dataset.jsonl --out report.json
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent / "agent"))

from groq import Groq
from agent import ask  # noqa: E402

JUDGE_MODEL = "llama-3.1-8b-instant"
_client = Groq()


def llm_judge_groundedness(question: str, answer: str, tool_calls: list) -> dict:
    """LLM-as-judge : score 0/1 de groundedness + justification courte."""
    if "ne trouve pas" in answer.lower():
        return {"grounded": True, "reason": "Réponse de refus, aucune affirmation factuelle à vérifier."}
    context = "\n".join(
        c["output"] for c in tool_calls if c["tool_name"] == "search_documents"
    )
    judge_prompt = f"""Tu évalues si une réponse est strictement fondée sur un contexte donné.

Contexte récupéré :
{context or "(aucun contexte récupéré)"}

Question : {question}
Réponse du système : {answer}

Réponds UNIQUEMENT en JSON strict : {{"grounded": true|false, "reason": "..."}}
- grounded=true si chaque affirmation factuelle de la réponse est supportée par le contexte,
  OU si le système a correctement refusé faute de contexte suffisant.
- grounded=false si la réponse contient une information non présente dans le contexte."""

    resp = _client.chat.completions.create(
        model=JUDGE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": judge_prompt}],
    )
    raw = resp.choices[0].message.content.strip()
    # Le modèle enveloppe parfois sa réponse dans un bloc markdown ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`").removeprefix("json").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"grounded": False, "reason": f"réponse juge non parsable : {raw[:120]}"} 


def run_eval(dataset_path: str) -> dict:
    dataset = [json.loads(l) for l in Path(dataset_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    results = []

    for item in dataset:
        run = ask(item["question"])
        judged = llm_judge_groundedness(item["question"], run["answer"], run["tool_calls"])

        is_refusal_expected = item["expected_source"] is None
        refused = "ne trouve pas" in run["answer"].lower()
        correct_refusal = (is_refusal_expected and refused) or (not is_refusal_expected and not refused)

        cited_sources = {
            c["output"].split("Source: ")[1].split("]")[0]
            for c in run["tool_calls"]
            if c["tool_name"] == "search_documents" and "Source: " in c["output"]
        }
        source_ok = (
            item["expected_source"] in cited_sources
            if item["expected_source"]
            else True
        )

        results.append({
            "id": item["id"],
            "category": item["category"],
            "question": item["question"],
            "answer": run["answer"],
            "grounded": judged["grounded"],
            "grounded_reason": judged["reason"],
            "correct_refusal": correct_refusal,
            "source_attribution_ok": source_ok,
            "latency_s": round(run["latency_s"], 2),
        })

    n = len(results)
    latencies = sorted(r["latency_s"] for r in results)
    summary = {
        "n_examples": n,
        "groundedness_rate": round(sum(r["grounded"] for r in results) / n, 3),
        "correct_refusal_rate": round(sum(r["correct_refusal"] for r in results) / n, 3),
        "source_attribution_rate": round(sum(r["source_attribution_ok"] for r in results) / n, 3),
        "latency_p50_s": round(statistics.median(latencies), 2),
        "latency_p95_s": round(latencies[min(int(n * 0.95), n - 1)], 2),
    }
    return {"summary": summary, "results": results}


def write_markdown_report(report: dict, path: str) -> None:
    s = report["summary"]
    lines = [
        "# Rapport d'Evals — FinAgent",
        "",
        f"- Exemples évalués : {s['n_examples']}",
        f"- Groundedness (LLM-judge) : {s['groundedness_rate']*100:.1f}%",
        f"- Taux de refus correct (hors-contexte) : {s['correct_refusal_rate']*100:.1f}%",
        f"- Attribution de source correcte : {s['source_attribution_rate']*100:.1f}%",
        f"- Latence p50 : {s['latency_p50_s']}s, p95 : {s['latency_p95_s']}s",
        "",
        "## Détail par exemple",
        "",
        "| ID | Catégorie | Grounded | Refus correct | Source OK | Latence (s) |",
        "|---|---|---|---|---|---|",
    ]
    for r in report["results"]:
        lines.append(
            f"| {r['id']} | {r['category']} | {'✅' if r['grounded'] else '❌'} "
            f"| {'✅' if r['correct_refusal'] else '❌'} | {'✅' if r['source_attribution_ok'] else '❌'} "
            f"| {r['latency_s']} |"
        )
    Path(path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="golden_dataset.jsonl")
    parser.add_argument("--out", default="report.json")
    parser.add_argument("--fail-under", type=float, default=0.85,
                         help="Seuil minimum de groundedness_rate pour que le CI passe (gate).")
    args = parser.parse_args()

    report = run_eval(args.dataset)
    Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown_report(report, Path(args.out).with_suffix(".md"))

    rate = report["summary"]["groundedness_rate"]
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    if rate < args.fail_under:
        print(f"\nÉCHEC : groundedness_rate {rate} < seuil {args.fail_under}", file=sys.stderr)
        sys.exit(1)