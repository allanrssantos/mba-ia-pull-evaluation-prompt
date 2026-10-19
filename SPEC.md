# SPEC — Pull, Otimização e Avaliação de Prompts (LangSmith Prompt Hub)

## 1. Visão geral
Software em Python que automatiza o ciclo de vida de um prompt no LangSmith Prompt Hub: faz pull de um prompt original (v1) de baixa qualidade, gera uma versão otimizada (v2) aplicando técnicas de Prompt Engineering, publica o v2 no Hub e avalia ambos contra um dataset fixo de 15 exemplos, exigindo nota mínima de 0.9 em cinco métricas. O alvo é o prompt `leonanluppi/bug_to_user_story_v1`, que converte descrições de bugs em user stories.

## 2. Objetivos e não-objetivos

### Objetivos
- Pull idempotente do prompt `leonanluppi/bug_to_user_story_v1` para `prompts/bug_to_user_story_v1.yml`.
- Produzir `prompts/bug_to_user_story_v2.yml` com Few-shot obrigatório + 1 técnica avançada (CoT, ToT, Skeleton-of-Thought, ReAct ou Role Prompting).
- Push público do v2 como `{username}/bug_to_user_story_v2` no LangSmith Hub.
- Pipeline de avaliação que reporta Helpfulness, Correctness, F1-Score, Clarity, Precision com status APROVADO/REPROVADO.
- Suite pytest validando estrutura/qualidade do prompt v2.
- Iterar 3 a 5 ciclos até todas as métricas ficarem ≥ 0.9.

### Não-objetivos
- NÃO há ingestão de PDF, RAG, banco vetorial nem pgVector.
- NÃO há Docker nem docker-compose — execução local em venv.
- NÃO há chat CLI interativo nem servidor web.
- NÃO alterar `datasets/bug_to_user_story.jsonl` (15 exemplos imutáveis).
- NÃO criar novos datasets nem novos prompts além do v1/v2.

## 3. Personas / Usuários
- **Aluno/Engenheiro de Prompt:** executa o pipeline para entregar o desafio do MBA. Conhecimento Python intermediário, familiaridade com LangChain/LangSmith.
- **Avaliador (professor):** clona o repositório, configura `.env`, roda os comandos descritos no README e verifica que todas as métricas atingem ≥ 0.9.

## 4. Requisitos funcionais (RF)

- **RF-01 — Pull do prompt v1:** `python src/pull_prompts.py` faz `hub.pull("leonanluppi/bug_to_user_story_v1")` e serializa em `prompts/bug_to_user_story_v1.yml`. Idempotente: rodar duas vezes não duplica conteúdo.
- **RF-02 — Otimização v2:** `prompts/bug_to_user_story_v2.yml` deve conter system prompt explícito, role definida, formato de saída exigido, ao menos 2 exemplos few-shot, tratamento de edge cases, separação correta de mensagens System/User e ao menos uma técnica avançada além do Few-shot.
- **RF-03 — Push do v2:** `python src/push_prompts.py` lê `prompts/bug_to_user_story_v2.yml` e executa `hub.push("{username}/bug_to_user_story_v2", prompt, public=True)`. Idempotente: novas execuções geram nova versão pública sem erro.
- **RF-04 — Avaliação:** `python src/evaluate.py` executa avaliação no LangSmith contra `datasets/bug_to_user_story.jsonl` (15 exemplos) e produz no stdout, para v1 e v2: Helpfulness, Correctness, F1-Score, Clarity, Precision e STATUS (APROVADO se todas ≥ 0.9; REPROVADO caso contrário).
- **RF-05 — Métricas customizadas:** implementadas em `src/metrics.py` (LLM-as-judge para Helpfulness/Correctness/Clarity/Precision; F1-Score textual entre saída e referência).
- **RF-06 — Testes pytest:** `tests/test_prompts.py` valida no v2: existência de system prompt, role definida, formato exigido especificado, presença de few-shot (≥ 2 exemplos), ausência de "TODO"/"FIXME", uso de pelo menos 2 técnicas (Few-shot + 1 avançada).
- **RF-07 — Utilitários:** `src/utils.py` centraliza carregamento de `.env`, leitura/escrita YAML, instanciação de `Client` LangSmith e do LLM (OpenAI ou Gemini conforme env).
- **RF-08 — Iteração:** o aluno deve registrar evoluções entre v2 (ciclos 1..N) editando manualmente `prompts/bug_to_user_story_v2.yml` e re-executando push + evaluate até atingir o target.

## 5. Requisitos não-funcionais (RNF)

- **RNF-01 — Stack:** Python 3.9+, LangChain 0.3.x, LangSmith 0.2.x, `langchain-openai` ou `langchain-google-genai`, PyYAML, pytest. Sem Docker.
- **RNF-02 — Métricas alvo:** todas as 5 métricas no v2 devem atingir ≥ 0.9 sobre os 15 exemplos do dataset.
- **RNF-03 — Idempotência:** pull e push podem ser repetidos sem corrupção de estado local nem efeito colateral inesperado.
- **RNF-04 — Observabilidade:** runs e experimentos visíveis no LangSmith UI com `experiment_prefix="bug_to_user_story_v1"` e `..._v2`; tracing habilitado via `LANGSMITH_TRACING=true`.
- **RNF-05 — Segurança:** chaves de API somente em `.env` (gitignored). `.env.example` documenta variáveis sem valores reais.
- **RNF-06 — Custo:** modelo de resposta default `gpt-4o-mini` (ou `gemini-2.5-flash`); modelo de avaliação `gpt-4o` (ou `gemini-2.5-flash`). Avaliação completa do dataset (15 exemplos) deve caber em poucos dólares.
- **RNF-07 — Determinismo de testes:** `pytest tests/` deve rodar offline (apenas leitura do YAML) e terminar em segundos.

## 6. Stack obrigatória
- Python 3.9+
- LangChain 0.3.x (`langchain`, `langchain-core`, `langchain-openai` e/ou `langchain-google-genai`)
- LangSmith 0.2.x (`langsmith`)
- PyYAML
- pytest
- python-dotenv

Provedor LLM: OpenAI (`gpt-4o-mini` resposta / `gpt-4o` avaliação) **ou** Google Gemini (`gemini-2.5-flash` em ambos).

## 7. Contratos e interfaces

### 7.1 Comandos CLI
| Comando | Entrada | Saída esperada |
|---|---|---|
| `python src/pull_prompts.py` | env vars | cria/atualiza `prompts/bug_to_user_story_v1.yml`; loga "Pull OK: leonanluppi/bug_to_user_story_v1" |
| `python src/push_prompts.py` | `prompts/bug_to_user_story_v2.yml` | cria nova versão pública `{username}/bug_to_user_story_v2`; loga URL pública |
| `python src/evaluate.py` | dataset + ambos os prompts | imprime tabela de métricas v1 e v2 com STATUS APROVADO/REPROVADO |
| `pytest tests/` | YAMLs em `prompts/` | 6 testes verdes |

### 7.2 Variáveis de ambiente (`.env.example`)
```
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=bug_to_user_story
LANGSMITH_USERNAME=

# Provider: openai | gemini
LLM_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=
OPENAI_RESPONSE_MODEL=gpt-4o-mini
OPENAI_EVAL_MODEL=gpt-4o

# Gemini
GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
```

### 7.3 Schemas
- **`prompts/bug_to_user_story_v*.yml`:** YAML com mensagens (`system`, `user`) compatíveis com `ChatPromptTemplate`.
- **`datasets/bug_to_user_story.jsonl`:** 15 linhas, cada uma com `{ "input": {"bug": "..."}, "output": {"user_story": "..."} }` (NÃO alterar).

### 7.4 Prompt-alvo do pull
Literal: `leonanluppi/bug_to_user_story_v1`.

### 7.5 Métricas
- **Helpfulness, Correctness, Clarity, Precision:** LLM-as-judge, retornam float em [0,1].
- **F1-Score:** F1 a nível de tokens entre saída do modelo e referência do dataset.

## 8. Estrutura de arquivos esperada
```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── SPEC.md
├── prompts/
│   ├── bug_to_user_story_v1.yml
│   └── bug_to_user_story_v2.yml
├── datasets/
│   └── bug_to_user_story.jsonl
├── src/
│   ├── pull_prompts.py
│   ├── push_prompts.py
│   ├── evaluate.py
│   ├── metrics.py
│   └── utils.py
├── tests/
│   └── test_prompts.py
└── docs/
    ├── user-stories.md
    └── references/
        └── langsmith-overview.md
```

## 9. Critérios de aceite globais

1. `pip install -r requirements.txt` instala sem erros em Python 3.9+.
2. `python src/pull_prompts.py` cria `prompts/bug_to_user_story_v1.yml` válido (parseável por PyYAML).
3. `prompts/bug_to_user_story_v2.yml` existe, contém ≥ 2 exemplos few-shot, role explícita, formato de saída e nenhuma string `TODO`/`FIXME`.
4. `python src/push_prompts.py` retorna sem exceção e o prompt fica acessível publicamente em `https://smith.langchain.com/hub/{username}/bug_to_user_story_v2`.
5. `python src/evaluate.py` imprime as 5 métricas para v2 e todas são ≥ 0.9, com STATUS final `APROVADO`.
6. `pytest tests/` retorna 6 testes passando.
7. README documenta técnicas aplicadas, comparação v1 vs v2 e link público do prompt v2.

## 10. Riscos e premissas

### Riscos
- **R-01:** Indisponibilidade ou rate limit da API LangSmith/OpenAI/Gemini durante avaliação.
- **R-02:** Custo da avaliação com `gpt-4o` se executada muitas vezes; mitigar reusando experimentos.
- **R-03:** Não atingir 0.9 em todas as métricas em apenas 3 ciclos — orçamento permite até 5 iterações.
- **R-04:** Métricas LLM-as-judge não-determinísticas; usar `temperature=0` no avaliador.
- **R-05:** Mudança/remoção do prompt fonte `leonanluppi/bug_to_user_story_v1` no Hub.

### Premissas
- O usuário possui conta LangSmith ativa com `LANGSMITH_USERNAME` válido e permissão de push público.
- O dataset `bug_to_user_story.jsonl` (15 exemplos) já existe no repositório e não será alterado.
- Há ao menos uma chave válida (OpenAI **ou** Google) configurada no `.env`.

## 11. Roadmap de execução

1. **solution-architect** → `ARCHITECTURE.md` (módulos, fluxos pull/push/evaluate, contratos internos).
2. **devops-engineer** → `requirements.txt`, `.env.example`, `.gitignore` (sem Docker).
3. **python-developer** → `src/{pull_prompts,push_prompts,evaluate,metrics,utils}.py`, prompt v2 inicial.
4. **qa-engineer** → `tests/test_prompts.py` e ciclo de iteração de métricas até ≥ 0.9.
5. **technical-writer** → `README.md` final com técnicas, prints, link público do v2 e instruções de execução.
