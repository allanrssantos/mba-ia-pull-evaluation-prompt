# LangSmith — Referência Resumida

Fonte: https://docs.langchain.com/langsmith/home

## Conceitos-chave
- **Observability / Tracing:** rastreamento de cada etapa da aplicação para depuração e confiabilidade.
- **Evaluation:** medir e acompanhar qualidade ao longo do tempo via datasets + evaluators.
- **Deployment:** publicação de agentes como Agent Servers escaláveis.

## Funcionalidades usadas no desafio
- **Prompt Hub:** versionamento e colaboração de prompts (pull/push).
- **Datasets & Evaluators:** medir qualidade automatizadamente.
- **CLI LangSmith:** consulta de traces/datasets/experimentos.

## Imports/funções essenciais
```python
from langchain import hub
from langsmith import Client
from langsmith.evaluation import evaluate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Pull de prompt
prompt = hub.pull("leonanluppi/bug_to_user_story_v1")

# Push de prompt (público)
hub.push("<username>/bug_to_user_story_v2", prompt, public=True)

# Evaluate
client = Client()
results = evaluate(
    target_fn,
    data="<dataset_name>",
    evaluators=[evaluator_fn],
    experiment_prefix="bug_to_user_story_v2",
)
```

## Variáveis de ambiente
- `LANGSMITH_TRACING=true`
- `LANGSMITH_ENDPOINT=https://api.smith.langchain.com`
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`

## Referências adicionais
- Prompt Engineering Guide (PT-BR): https://www.promptingguide.ai/pt
- Repo base (clonado em `mba-ia-pull-evaluation-prompt/`).
