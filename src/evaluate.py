"""
Script COMPLETO para avaliar prompts otimizados.

Este script:
1. Carrega dataset de avaliação de arquivo .jsonl (datasets/bug_to_user_story.jsonl)
2. Cria/atualiza dataset no LangSmith (15 exemplos)
3. Puxa prompts do LangSmith Hub (fonte única de verdade): v1 original e v2 otimizado
4. Executa cada prompt contra o dataset via `langsmith.evaluation.evaluate`
5. Calcula 5 métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
6. Publica os experimentos (traces + scores por exemplo) no dashboard do LangSmith
7. Exibe resumo e comparação v1 vs v2 no terminal

Suporta múltiplos providers de LLM:
- OpenAI (gpt-4o-mini resposta / gpt-4o avaliação)
- Google Gemini (gemini-2.5-flash em ambos)

Configure o provider no arquivo .env através da variável LLM_PROVIDER.
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from langsmith.evaluation import evaluate

from metrics import (
    evaluate_clarity,
    evaluate_correctness,
    evaluate_f1_score,
    evaluate_helpfulness,
    evaluate_precision,
)
from utils import (
    check_env_vars,
    format_score,
    get_eval_model,
    get_hub_username,
    get_llm as get_configured_llm,
    get_provider,
    get_response_model,
    print_section_header,
)

load_dotenv()

THRESHOLD = 0.9
METRICS_ORDER = ["helpfulness", "correctness", "f1_score", "clarity", "precision"]
METRIC_LABELS = {
    "helpfulness": "Helpfulness",
    "correctness": "Correctness",
    "f1_score": "F1-Score",
    "clarity": "Clarity",
    "precision": "Precision",
}
METRIC_FUNCTIONS: Dict[str, Callable[[str, str, str], Dict[str, Any]]] = {
    "helpfulness": evaluate_helpfulness,
    "correctness": evaluate_correctness,
    "f1_score": evaluate_f1_score,
    "clarity": evaluate_clarity,
    "precision": evaluate_precision,
}
JSONL_PATH = "datasets/bug_to_user_story.jsonl"


def get_llm():
    return get_configured_llm(temperature=0)


def _empty_scores() -> Dict[str, float]:
    return {m: 0.0 for m in METRICS_ORDER}


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
def load_dataset_from_jsonl(jsonl_path: str) -> List[Dict[str, Any]]:
    examples = []

    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Ignorar linhas vazias
                    examples.append(json.loads(line))
        return examples

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {jsonl_path}")
        print("\nCertifique-se de que o arquivo datasets/bug_to_user_story.jsonl existe.")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao parsear JSONL: {e}")
        return []
    except Exception as e:
        print(f"❌ Erro ao carregar dataset: {e}")
        return []


def create_evaluation_dataset(client: Client, dataset_name: str, jsonl_path: str) -> bool:
    print(f"Criando dataset de avaliação: {dataset_name}...")

    examples = load_dataset_from_jsonl(jsonl_path)
    if not examples:
        print("❌ Nenhum exemplo carregado do arquivo .jsonl")
        return False

    print(f"   ✓ Carregados {len(examples)} exemplos do arquivo {jsonl_path}")

    try:
        existing = next(
            (ds for ds in client.list_datasets(dataset_name=dataset_name) if ds.name == dataset_name),
            None,
        )

        if existing:
            print(f"   ✓ Dataset '{dataset_name}' já existe, usando existente")
            return True

        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description="Bug reports -> User Stories (15 exemplos fixos do desafio).",
        )
        client.create_examples(
            dataset_id=dataset.id,
            inputs=[ex["inputs"] for ex in examples],
            outputs=[ex["outputs"] for ex in examples],
            metadata=[ex.get("metadata", {}) for ex in examples],
        )
        print(f"   ✓ Dataset criado com {len(examples)} exemplos")
        return True

    except Exception as e:
        print(f"   ❌ Erro ao criar dataset: {e}")
        return False


# ---------------------------------------------------------------------------
# Prompt (Hub)
# ---------------------------------------------------------------------------
def pull_prompt_from_langsmith(prompt_name: str) -> ChatPromptTemplate:
    try:
        print(f"   Puxando prompt do LangSmith Hub: {prompt_name}")
        prompt = hub.pull(prompt_name)
        print("   ✓ Prompt carregado com sucesso")
        return prompt

    except Exception as e:
        error_msg = str(e).lower()

        print(f"\n{'=' * 70}")
        print(f"❌ ERRO: Não foi possível carregar o prompt '{prompt_name}'")
        print(f"{'=' * 70}\n")

        if "not found" in error_msg or "404" in error_msg:
            print("⚠️  O prompt não foi encontrado no LangSmith Hub.\n")
            print("AÇÕES NECESSÁRIAS:")
            print("1. Verifique se você já fez push do prompt otimizado:")
            print("   python src/push_prompts.py")
            print()
            print("2. Confirme se o prompt foi publicado com sucesso em:")
            print("   https://smith.langchain.com/prompts")
            print()
            print(f"3. Certifique-se de que o nome do prompt está correto: '{prompt_name}'")
            print()
            print("4. Se você alterou o prompt no YAML, refaça o push:")
            print("   python src/push_prompts.py")
        else:
            print(f"Erro técnico: {e}\n")
            print("Verifique:")
            print("- LANGSMITH_API_KEY está configurada corretamente no .env")
            print("- Você tem acesso ao workspace do LangSmith")
            print("- Sua conexão com a internet está funcionando")

        print(f"\n{'=' * 70}\n")
        raise


# ---------------------------------------------------------------------------
# Target + evaluators para langsmith.evaluation.evaluate
# ---------------------------------------------------------------------------
def build_target(prompt_template: ChatPromptTemplate, llm: Any) -> Callable[[dict], dict]:
    """Função alvo executada pelo LangSmith para cada exemplo do dataset."""
    chain = prompt_template | llm

    def target(inputs: dict) -> dict:
        response = chain.invoke(inputs)
        content = getattr(response, "content", response)
        return {"answer": content if isinstance(content, str) else str(content)}

    return target


def _make_evaluator(metric_key: str) -> Callable[..., Dict[str, Any]]:
    """Adapta uma função de metrics.py para a assinatura (run, example) do LangSmith."""
    metric_fn = METRIC_FUNCTIONS[metric_key]

    def _evaluator(run, example) -> Dict[str, Any]:
        inputs = example.inputs or {}
        question = inputs.get("bug_report") or inputs.get("question") or "N/A"
        answer = (run.outputs or {}).get("answer", "")
        reference = (example.outputs or {}).get("reference", "")

        if not answer:
            return {"key": metric_key, "score": 0.0, "comment": "Resposta vazia."}

        result = metric_fn(question, answer, reference)
        return {
            "key": metric_key,
            "score": float(result.get("score", 0.0)),
            "comment": result.get("reasoning") or result.get("comment") or "",
        }

    _evaluator.__name__ = metric_key
    return _evaluator


EVALUATORS = [_make_evaluator(m) for m in METRICS_ORDER]


# ---------------------------------------------------------------------------
# Avaliação
# ---------------------------------------------------------------------------
def evaluate_prompt(label: str, prompt_name: str, dataset_name: str, client: Client) -> Dict[str, Any]:
    print(f"\n🔍 Avaliando: {prompt_name}")

    prompt_template = pull_prompt_from_langsmith(prompt_name)
    llm = get_llm()

    print("   Executando experimento no LangSmith (traces + 5 métricas por exemplo)...")
    results = evaluate(
        build_target(prompt_template, llm),
        data=dataset_name,
        evaluators=EVALUATORS,
        experiment_prefix=f"bug_to_user_story_{label}",
        description=f"Avaliação do prompt {prompt_name} com 5 métricas LLM-as-judge (threshold {THRESHOLD}).",
        metadata={
            "prompt": prompt_name,
            "version": label,
            "provider": get_provider(),
            "llm_model": get_response_model(),
            "eval_model": get_eval_model(),
        },
        max_concurrency=int(os.getenv("EVAL_MAX_CONCURRENCY", "1")),
        client=client,
    )

    per_metric: Dict[str, List[float]] = defaultdict(list)
    total = 0
    for i, row in enumerate(results, 1):
        total += 1
        row_scores: Dict[str, float] = {}
        for res in row["evaluation_results"]["results"]:
            score = float(res.score or 0.0)
            per_metric[res.key].append(score)
            row_scores[res.key] = score
        print(
            f"      [{i}] "
            f"H:{row_scores.get('helpfulness', 0):.2f} "
            f"C:{row_scores.get('correctness', 0):.2f} "
            f"F1:{row_scores.get('f1_score', 0):.2f} "
            f"Cl:{row_scores.get('clarity', 0):.2f} "
            f"P:{row_scores.get('precision', 0):.2f}"
        )

    print(f"   Dataset: {total} exemplos | Experimento: {results.experiment_name}")

    def _avg(values: List[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    scores = {m: round(_avg(per_metric.get(m, [])), 4) for m in METRICS_ORDER}
    return {"scores": scores, "experiment_name": results.experiment_name, "examples": total}


def display_results(prompt_name: str, scores: Dict[str, float]) -> bool:
    print("\n" + "=" * 50)
    print(f"Prompt: {prompt_name}")
    print("=" * 50)

    print("\nMétricas (LLM-as-judge dedicado, temperature=0):")
    for m in METRICS_ORDER:
        print(f"  - {METRIC_LABELS[m] + ':':<13}{format_score(scores[m], threshold=THRESHOLD)}")

    average_score = sum(scores.values()) / len(scores)

    print("\n" + "-" * 50)
    print(f"📊 MÉDIA GERAL: {average_score:.4f}")
    print("-" * 50)

    passed = all(score >= THRESHOLD for score in scores.values())

    if passed:
        print(f"\n✅ STATUS: APROVADO - Todas as métricas >= {THRESHOLD}")
    else:
        print("\n❌ STATUS: REPROVADO")
        failed_metrics = [METRIC_LABELS[m] for m in METRICS_ORDER if scores[m] < THRESHOLD]
        print(f"⚠️  Métricas abaixo de {THRESHOLD}: {', '.join(failed_metrics)}")

    return passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print_section_header("AVALIAÇÃO DE PROMPTS OTIMIZADOS")

    provider = get_provider()
    print(f"Provider: {provider}")
    print(f"Modelo Principal: {get_response_model()}")
    print(f"Modelo de Avaliação: {get_eval_model()}\n")

    required_vars = ["LANGSMITH_API_KEY"]
    if provider == "openai":
        required_vars.append("OPENAI_API_KEY")
    elif provider == "google":
        required_vars.append("GOOGLE_API_KEY")
    else:
        print(f"❌ LLM_PROVIDER='{provider}' inválido. Use 'openai' ou 'google'.")
        return 1

    if not check_env_vars(required_vars):
        return 1

    username = get_hub_username()
    if not username:
        print("❌ Username do LangSmith Hub não configurado.")
        print("   Defina USERNAME_LANGSMITH_HUB (ou LANGSMITH_USERNAME) no .env.")
        return 1

    if not Path(JSONL_PATH).exists():
        print(f"❌ Arquivo de dataset não encontrado: {JSONL_PATH}")
        print("\nCertifique-se de que o arquivo existe antes de continuar.")
        return 1

    client = Client()
    project_name = os.getenv("LANGSMITH_PROJECT", "bug_to_user_story")
    dataset_name = f"{project_name}-eval"

    if not create_evaluation_dataset(client, dataset_name, JSONL_PATH):
        return 1

    print("\n" + "=" * 70)
    print("PROMPTS PARA AVALIAR")
    print("=" * 70)
    print("\nEste script irá puxar prompts do LangSmith Hub.")
    print("Certifique-se de ter feito push do prompt v2 antes de avaliar:")
    print("  python src/push_prompts.py\n")

    prompts_to_evaluate = [
        ("v1", "leonanluppi/bug_to_user_story_v1"),
        ("v2", f"{username}/bug_to_user_story_v2"),
    ]

    results_summary: Dict[str, Dict[str, Any]] = {}

    for label, prompt_name in prompts_to_evaluate:
        try:
            outcome = evaluate_prompt(label, prompt_name, dataset_name, client)
            passed = display_results(prompt_name, outcome["scores"])
            results_summary[label] = {**outcome, "prompt": prompt_name, "passed": passed}
        except Exception as e:
            print(f"\n❌ Falha ao avaliar '{prompt_name}': {e}")
            results_summary[label] = {
                "prompt": prompt_name,
                "scores": _empty_scores(),
                "experiment_name": None,
                "examples": 0,
                "passed": False,
            }

    print("\n" + "=" * 70)
    print("COMPARAÇÃO LADO A LADO (v1 vs v2)")
    print("=" * 70)
    v1 = results_summary.get("v1", {"scores": _empty_scores()})
    v2 = results_summary.get("v2", {"scores": _empty_scores()})

    header = f"{'Métrica':<14} {'v1':>10} {'v2':>10} {'Delta':>10}"
    print(header)
    print("-" * len(header))
    for m in METRICS_ORDER:
        s1, s2 = v1["scores"][m], v2["scores"][m]
        print(f"{METRIC_LABELS[m]:<14} {s1:>10.4f} {s2:>10.4f} {s2 - s1:>+10.4f}")

    v2_passed = bool(v2.get("passed"))

    print("\n" + "=" * 70)
    print(f"STATUS FINAL (v2): {'APROVADO' if v2_passed else 'REPROVADO'}")
    print("=" * 70)

    print("\n✓ Evidências no LangSmith:")
    print(f"  Dataset: {dataset_name}")
    for label in ("v1", "v2"):
        exp = results_summary.get(label, {}).get("experiment_name")
        if exp:
            print(f"  Experimento {label}: {exp}")
    print("  https://smith.langchain.com/ -> Datasets & Experiments")

    if v2_passed:
        print("\n✅ O prompt v2 atingiu todas as métricas >= 0.9!")
        print("\nPróximos passos:")
        print("1. Documente o processo e os resultados no README.md")
        print("2. Capture screenshots das avaliações (docs/screenshots/)")
        print("3. Faça commit e push para o GitHub")
        return 0

    print("\n⚠️  O prompt v2 não atingiu todas as métricas >= 0.9")
    print("\nPróximos passos:")
    print("1. Refatore prompts/bug_to_user_story_v2.yml focando nas métricas baixas")
    print("2. Faça push novamente: python src/push_prompts.py")
    print("3. Execute: python src/evaluate.py novamente")
    return 1


if __name__ == "__main__":
    sys.exit(main())
