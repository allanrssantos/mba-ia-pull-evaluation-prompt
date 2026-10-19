# Pull, Otimização e Avaliação de Prompts — LangSmith Prompt Hub

Pipeline Python que automatiza o ciclo de vida de um prompt no LangSmith Prompt Hub: faz pull do prompt original `leonanluppi/bug_to_user_story_v1` (baixa qualidade intencional), gera uma versão otimizada `v2` aplicando técnicas de Prompt Engineering, publica o `v2` publicamente no Hub e avalia ambos contra um dataset fixo de 15 exemplos usando cinco métricas (Helpfulness, Correctness, F1-Score, Clarity, Precision), exigindo nota mínima de 0.9 em todas.

---

## Objetivo

- Praticar o ciclo completo de engenharia de prompts: pull → otimizar → push → avaliar → iterar.
- Aplicar técnicas avançadas (Few-shot Learning, Role Prompting, Chain of Thought) para elevar a qualidade de um prompt que converte relatos de bugs em user stories no padrão INVEST.
- Comparar quantitativamente o prompt v1 versus o v2 otimizado usando LLM-as-judge e F1-Score semântico.
- Atingir STATUS APROVADO (todas as 5 métricas ≥ 0.9) e publicar o prompt v2 para revisão do avaliador.

Para detalhes completos de requisitos, consulte [`SPEC.md`](SPEC.md).

---

## Stack tecnológica

- Python 3.9+
- LangChain 0.3.x (`langchain`, `langchain-core`, `langchain-openai`, `langchain-google-genai`)
- LangSmith 0.2.x (`langsmith`)
- PyYAML
- pytest
- python-dotenv
- Provedor LLM: OpenAI (`gpt-4o-mini` resposta / `gpt-4o` avaliação) **ou** Google Gemini (`gemini-2.5-flash` em ambos)

---

## Pré-requisitos

| Requisito | Versão mínima | Como verificar |
|---|---|---|
| Python | 3.9+ | `python --version` |
| Conta LangSmith | ativa (plano gratuito) | https://smith.langchain.com |
| Chave OpenAI **ou** Google AI Studio | qualquer | ver seção Variáveis de Ambiente |

Não há Docker, banco de dados nem servidor web. Tudo roda localmente em venv.

---

## Como executar

Para instruções detalhadas de setup (como obter cada chave de API, troubleshooting de PowerShell, smoke test de conectividade), consulte [`docs/SETUP.md`](docs/SETUP.md).

### 1. Clonar o repositório

```bash
git clone <URL-DO-REPOSITORIO>
cd mba-ia-pull-evaluation-prompt
```

### 2. Criar e ativar o ambiente virtual

**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> Se o PowerShell bloquear a execução de scripts, execute uma vez como administrador:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente

**Linux / macOS**
```bash
cp .env.example .env
```

**Windows (PowerShell)**
```powershell
Copy-Item .env.example .env
```

Abra `.env` em qualquer editor e preencha os campos obrigatórios (ver tabela abaixo).

### 5. Executar o pipeline

```bash
# Passo 1 — Baixa o prompt v1 do Hub para arquivo local
python src/pull_prompts.py

# Passo 2 — Publica o prompt v2 otimizado no Hub (requer USERNAME_LANGSMITH_HUB no .env)
python src/push_prompts.py

# Passo 3 — Avalia v1 e v2 contra o dataset de 15 exemplos
python src/evaluate.py

# Passo 4 — Valida a estrutura do prompt v2 (offline, sem credenciais)
pytest tests/test_prompts.py -v
```

### 6. Ciclo de iteração (até STATUS APROVADO)

```
1. Editar prompts/bug_to_user_story_v2.yml
2. python src/push_prompts.py
3. python src/evaluate.py
4. Se alguma métrica < 0.9 → voltar ao passo 1
5. Quando todas >= 0.9 → STATUS APROVADO → commit
```

Preveja de 3 a 5 ciclos.

---

## Técnicas aplicadas no prompt v2

O arquivo `prompts/bug_to_user_story_v2.yml` combina três técnicas:

### Few-shot Learning

**O que é:** fornecer ao modelo exemplos concretos de entrada e saída esperada antes de apresentar a tarefa real.

**Justificativa:** a tarefa de converter um relato de bug em uma user story INVEST exige que o modelo entenda sutilezas de persona, granularidade de critérios de aceitação e nível de detalhe técnico. Sem exemplos, o modelo tende a gerar user stories genéricas ou omite seções importantes. A descoberta central das iterações foi que o `gpt-4o-mini` **imita exemplos muito melhor do que segue regras escritas**: um checklist em texto com as mesmas boas práticas foi largamente ignorado, enquanto um exemplo da mesma categoria elevou o score do exemplo correspondente a 1.0. Por isso o v2 final traz **um exemplo por categoria de bug**, todos em domínios diferentes dos do dataset:

| Categoria | Exemplos | O que ensina |
|---|---|---|
| Simples (3) | Botão de favoritar, checkout em landscape, contagem no painel | Frase principal + exatamente 5 critérios; generalizar identificadores do relato (ID, "Cliente A"); nenhuma seção extra |
| Médio (7) | Webhook, busca lenta por CPF, endpoint sem autorização, cálculo de frete, histórico que trava no iOS, assento vendido duas vezes, modal atrás do cabeçalho | Quais seções extras cada natureza de bug pede: Contexto Técnico, Critérios Técnicos + Contexto do Bug, Critérios Adicionais + Contexto de Segurança (OWASP), Exemplo de Cálculo, Critérios de Prevenção, Critérios de Acessibilidade |
| Complexo (2) | Portal de agendamento (segurança, integração, concorrência, UX) e app de inspeções offline (conflitos, upload, memória, N+1, cache, exportação) | Formato em blocos `=== ... ===`: um bloco de critérios por problema, critérios técnicos nomeando técnicas concretas (SELECT FOR UPDATE, circuit breaker, CRDTs, chunked upload, materialized views), contexto com números do relato, tasks por fase e métricas de sucesso |

Os exemplos também fixam comportamentos que regras isoladas não conseguiram: ordem rígida Dado/Quando/Então/E, metas numéricas claramente melhores que o estado atual e nenhuma derivação de números que não estejam no relato.

---

### Role Prompting

**O que é:** atribuir ao modelo uma persona específica e detalhada antes de qualquer instrução de tarefa.

**Justificativa:** o prompt v1 não define persona alguma — o modelo responde como um assistente genérico. Ao instruir o modelo a se comportar como um **Product Owner sênior com 10+ anos em Scrum/Kanban/SAFe e domínio do padrão INVEST**, o tom, vocabulário e nível de exigência das respostas mudam radicalmente. O modelo passa a questionar ambiguidades (como um PO real faria), usar linguagem ágil correta e priorizar valor de negócio na cláusula "para que". A role foi escolhida em vez de "desenvolvedor" ou "analista" porque o PO é o papel que mais se beneficia de user stories de alta qualidade e que mais sofre com requisitos mal escritos.

---

### Chain of Thought (6 etapas internas)

**O que é:** instruir o modelo a percorrer um processo de raciocínio estruturado internamente antes de produzir a resposta final, sem expor esse raciocínio na saída.

**Justificativa:** bugs são frequentemente descritos de forma caótica (misturando sintoma, causa, impacto e contexto técnico). Sem um roteiro explícito de análise, o modelo pula etapas e produz user stories incompletas. As 6 etapas definidas no `# PROCESSO DE RACIOCÍNIO` garantem que o modelo passe por:

1. Identificar a **tela/funcionalidade** citada e **quem a usa** (persona por mapeamento explícito)
2. Identificar a **ação positiva** e o **valor de negócio**
3. Classificar a **categoria** (simples / médio de qual natureza / complexo), primeiro pelo tamanho e estrutura do relato
4. Escolher o **exemplo few-shot da mesma categoria** como molde de estrutura, seções e tamanho
5. Listar os **números, endpoints e nomes** do relato que devem aparecer literalmente
6. Definir os **critérios Given-When-Then** e os complementos que o exemplo da categoria inclui

O CoT é instruído como raciocínio interno (`NÃO EXIBIR`) para que a saída continue limpa e no formato exigido. A etapa 3 foi a que mais evoluiu entre os ciclos: classificar pelo tamanho do relato antes de olhar o tema evitou que bugs simples ganhassem seções técnicas e que bugs médios com bloco "Detalhes" fossem tratados como simples.

---

## Resultados finais

Avaliação executada em 19/10/2026 com `LLM_PROVIDER=openai`, `gpt-4o-mini` para gerar as user stories e `gpt-4o` como juiz (temperature 0), sobre o dataset `bug_to_user_story-eval` com 15 exemplos. Saída completa do terminal em [`docs/evaluate_output_final.txt`](docs/evaluate_output_final.txt).

### Tabela comparativa v1 vs v2

| Métrica | v1 (leonanluppi/bug_to_user_story_v1) | v2 (allansoares/bug_to_user_story_v2) | Delta | Target |
|---|---|---|---|---|
| Helpfulness | 0.79 ✗ | **0.91** ✓ | +0.12 | ≥ 0.9 |
| Correctness | 0.77 ✗ | **0.93** ✓ | +0.16 | ≥ 0.9 |
| F1-Score | 0.70 ✗ | **0.92** ✓ | +0.23 | ≥ 0.9 |
| Clarity | 0.84 ✗ | **0.95** ✓ | +0.10 | ≥ 0.9 |
| Precision | 0.83 ✗ | **0.93** ✓ | +0.10 | ≥ 0.9 |
| **Média geral** | 0.79 | **0.93** | +0.14 | — |
| **STATUS** | REPROVADO | **APROVADO** | | **APROVADO** |

Experimentos no LangSmith (Datasets & Experiments → `bug_to_user_story-eval`):

- v1: `bug_to_user_story_v1-c94ceff9`
- v2: `bug_to_user_story_v2-2fb71e76`

Cada experimento contém os 15 traces de geração e 75 feedbacks (5 métricas × 15 exemplos) com o raciocínio do juiz.

### Histórico de iteração (6 ciclos)

| Ciclo | Mudança principal no v2 | Help. | Corr. | F1 | Clar. | Prec. | Status |
|---|---|---|---|---|---|---|---|
| 1 | v2 inicial: Role + CoT + 3 exemplos genéricos | 0.85 | 0.83 | 0.78 | 0.89 | 0.87 | REPROVADO |
| 2 | Regras de persona e de não inventar números; 4 exemplos | 0.84 | 0.85 | 0.80 | 0.89 | 0.84 | REPROVADO |
| 3 | Checklist de boas práticas por categoria em texto | 0.85 | 0.88 | 0.82 | 0.89 | 0.85 | REPROVADO |
| 4 | Checklist substituído por 12 exemplos, um por categoria | 0.93 | 0.92 | 0.89 | 0.92 | 0.90 | REPROVADO (F1) |
| 5 | Classificação pelo tamanho do relato; generalização de IDs | 0.91 | 0.91 | 0.91 | 0.93 | 0.895 | REPROVADO (Precision) |
| 6 | Bloco rotulado no relato ⇒ médio; ordem rígida Dado/Quando/Então/E; seções obrigatórias por categoria | **0.91** | **0.93** | **0.92** | **0.95** | **0.93** | **APROVADO** |

Lições das iterações:

- Os ciclos 2 e 3 quase não moveram as métricas: o modelo ignorava boa parte das regras escritas. O salto veio no ciclo 4, ao trocar regras por exemplos.
- Os juízes comparam contra a referência, então o v2 precisa espelhar o **nível de detalhe** da referência: nem a mais (bugs simples com seções técnicas perdem Precision) nem a menos (bugs médios sem acessibilidade ou prevenção perdem F1).
- O exemplo mais simples do dataset (botão do carrinho) fica em Precision 0.67 mesmo com a story praticamente idêntica à referência, porque o juiz cobra "diagnóstico do bug". Os prompts dos juízes em `src/metrics.py` fazem parte do material base e não foram alterados.

### Link público do prompt v2 no LangSmith Hub

```
https://smith.langchain.com/hub/allansoares/bug_to_user_story_v2
```

Publicado com `is_public=True` via `Client.push_prompt`, com descrição e tags do YAML. Commit avaliado no ciclo 6: `da50cc70`.

### Evidências (screenshots)

Adicione os prints em `docs/screenshots/` (a pasta **não** é ignorada pelo git):

- `docs/screenshots/evaluate_resultado_final.png` — saída do terminal com as 5 métricas e STATUS APROVADO
- `docs/screenshots/langsmith_experiment_v2.png` — experimento `bug_to_user_story_v2-2fb71e76` no LangSmith UI
- `docs/screenshots/langsmith_hub_prompt_v2.png` — prompt v2 público no Hub

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example                        # Template de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── README.md
├── SPEC.md                             # Especificação completa do desafio
├── prompts/
│   ├── bug_to_user_story_v1.yml        # Prompt original (baixa qualidade)
│   └── bug_to_user_story_v2.yml        # Prompt otimizado (Few-shot + Role + CoT)
├── datasets/
│   └── bug_to_user_story.jsonl         # 15 exemplos imutáveis (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py                 # RF-01: pull do Hub para YAML local
│   ├── push_prompts.py                 # RF-03: push do YAML local para o Hub
│   ├── evaluate.py                     # RF-04: pipeline de avaliação com 5 métricas
│   ├── metrics.py                      # RF-05: evaluators LLM-as-judge
│   └── utils.py                        # RF-07: utilitários compartilhados
├── tests/
│   └── test_prompts.py                 # RF-06: 7 testes pytest offline
└── docs/
    ├── ARCHITECTURE.md
    ├── SETUP.md
    ├── test-report.md
    ├── user-stories.md
    ├── evaluate_output_final.txt       # Saída completa da avaliação aprovada
    └── screenshots/                    # Prints das evidências
```

---

## Variáveis de ambiente

Consulte `.env.example` para o template completo. As variáveis abaixo são lidas por `src/utils.py`.

| Variável | Descrição | Obrigatória? |
|---|---|---|
| `LANGSMITH_TRACING` | Habilita tracing automático no LangSmith (`true` recomendado) | Sim |
| `LANGSMITH_ENDPOINT` | Endpoint da API LangSmith (default: `https://api.smith.langchain.com`) | Sim |
| `LANGSMITH_API_KEY` | Chave de API do LangSmith (obter em Settings > API Keys) | Sim |
| `LANGSMITH_PROJECT` | Nome do projeto/experimento no LangSmith (ex: `bug_to_user_story`) | Sim |
| `USERNAME_LANGSMITH_HUB` | Seu username no LangSmith Hub (usado no push do v2). Alias aceito: `LANGSMITH_USERNAME` | Sim |
| `LLM_PROVIDER` | Provedor LLM: `openai` ou `google` (`gemini` é aceito como alias) | Sim |
| `LLM_MODEL` | Modelo de resposta (default: `gpt-4o-mini` na OpenAI, `gemini-2.5-flash` no Gemini). Aliases: `OPENAI_RESPONSE_MODEL`, `GEMINI_MODEL` | Não |
| `EVAL_MODEL` | Modelo do juiz (default: `gpt-4o` na OpenAI, `gemini-2.5-flash` no Gemini). Aliases: `OPENAI_EVAL_MODEL`, `GEMINI_MODEL` | Não |
| `OPENAI_API_KEY` | Chave de API da OpenAI | Se `LLM_PROVIDER=openai` |
| `GOOGLE_API_KEY` | Chave de API do Google AI Studio | Se `LLM_PROVIDER=google` |

> Os nomes do scaffold do curso (`LLM_MODEL`, `EVAL_MODEL`, `USERNAME_LANGSMITH_HUB`) têm prioridade; os aliases do `SPEC.md` são usados como fallback por `env_first()` em `src/utils.py`.

---

## Critérios de aceite atingidos

Estado em 19/10/2026, após a execução real do pipeline:

| Requisito do desafio | Evidência | Status |
|---|---|---|
| 1. Pull de `leonanluppi/bug_to_user_story_v1` para `prompts/bug_to_user_story_v1.yml` | Arquivo gerado pelo `pull_prompts.py` com `system_prompt`, `user_prompt` e `messages` do Hub | ✓ |
| 2. Prompt v2 com Few-shot + técnica avançada, regras explícitas, edge cases, System vs User | `prompts/bug_to_user_story_v2.yml`: 12 exemplos few-shot, Role Prompting, Chain of Thought, seção de edge cases, `system_prompt` e `user_prompt` separados | ✓ |
| 3. Push público como `{username}/bug_to_user_story_v2` | `allansoares/bug_to_user_story_v2`, `is_public=True` confirmado via API | ✓ |
| 4. Iteração de 3 a 5 ciclos até todas as métricas ≥ 0.9 | 6 ciclos; ciclo 6 APROVADO com todas as 5 métricas ≥ 0.9 | ✓ |
| 5. Testes pytest obrigatórios (system prompt, role, formato, few-shot, sem TODO, ≥ 2 técnicas) | `tests/test_prompts.py`: 7 testes passando (os 6 obrigatórios + 1 que garante que o template só espera `{bug_report}`) | ✓ |
| Evidências no LangSmith: dataset com 15 exemplos, execuções ≥ 0.9, tracing | Dataset `bug_to_user_story-eval`; experimentos `bug_to_user_story_v1-c94ceff9` e `bug_to_user_story_v2-2fb71e76` com 15 traces e 75 feedbacks cada | ✓ |
| README: técnicas, resultados, como executar | Este documento | ✓ (prints em `docs/screenshots/` a adicionar) |

O relatório de QA anterior, `docs/test-report.md`, foi executado em 05/05/2026 sem credenciais e registrou os itens online como SKIP; as execuções acima substituem esses SKIPs.

---

## Troubleshooting

| Problema | Causa provável | Solução |
|---|---|---|
| `ModuleNotFoundError: langchain` | venv não ativo ou dependências não instaladas | Ativar o venv e executar `pip install -r requirements.txt` |
| `AuthenticationError` LangSmith | `LANGSMITH_API_KEY` inválida ou ausente no `.env` | Verificar a chave em https://smith.langchain.com/settings |
| `AuthenticationError` OpenAI | `OPENAI_API_KEY` inválida | Verificar em https://platform.openai.com/api-keys e confirmar crédito disponível |
| `400 Bad Request` Google / `GOOGLE_API_KEY` inválida | Chave expirada ou projeto sem quota | Recriar a chave em https://aistudio.google.com/app/apikey |
| Push falha com `username not found` | `USERNAME_LANGSMITH_HUB` incorreto | No LangSmith UI, clicar no avatar (canto superior direito) e copiar o campo **Username** |
| `PermissionError` ao ativar venv no PowerShell | Política de execução de scripts bloqueada | Executar `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` como administrador |

Para troubleshooting detalhado (incluindo smoke test de conectividade), consulte [`docs/SETUP.md`](docs/SETUP.md).

---

## Documentação relacionada

| Documento | Conteúdo |
|---|---|
| [`SPEC.md`](SPEC.md) | Especificação completa: requisitos funcionais, não-funcionais, contratos de interface, critérios de aceite |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Diagrama de componentes, fluxos de dados, ADRs e mapeamento requisitos → código |
| [`docs/SETUP.md`](docs/SETUP.md) | Setup passo a passo, como obter cada chave de API, troubleshooting detalhado |
| [`docs/user-stories.md`](docs/user-stories.md) | User stories com critérios de aceite em Gherkin |
| [`docs/test-report.md`](docs/test-report.md) | Relatório completo do QA: resultados por critério, saída bruta do pytest, observações técnicas |
