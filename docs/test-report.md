# Test Report — Pull, Otimizacao e Avaliacao de Prompts (LangSmith Prompt Hub)

**Data:** 2026-05-05  
**Ambiente:** Python 3.12.10, Windows 11 Pro 10.0.26200, pytest 8.3.4  
**Diretorio:** `C:\Users\allan.santos\Documents\MBA\mba-langchain-langsmith\mba-ia-pull-evaluation-prompt`  
**Executado por:** QA Engineer (Claude)

---

## 1. Tabela de Criterios de Aceite

| # | Criterio | Comando | Esperado | Obtido | Status |
|---|---|---|---|---|---|
| A-01 | Setup venv — criacao do ambiente virtual | `python -m venv venv` | Diretorio `venv/` criado com `Scripts/python.exe` | Diretorio criado com sucesso; `Scripts/python.exe` presente | PASS |
| A-02 | Setup deps — `pip install -r requirements.txt` sem erros | `venv/Scripts/python.exe -m pip install -r requirements.txt` | Saida termina com `Successfully installed ...`; exit code 0 | `Successfully installed langchain-0.3.13 ... pytest-8.3.4 ...`; exit code 0 | PASS |
| A-03 | Pytest — 6 testes PASS | `venv/Scripts/python.exe -m pytest tests/test_prompts.py -v` | `6 passed` em < 10 s | `6 passed in 0.21s` | PASS |
| A-04 | Pytest — test_prompt_has_system_prompt | (subitem A-03) | PASSED | PASSED | PASS |
| A-05 | Pytest — test_prompt_has_role_definition | (subitem A-03) | PASSED | PASSED | PASS |
| A-06 | Pytest — test_prompt_mentions_format | (subitem A-03) | PASSED | PASSED | PASS |
| A-07 | Pytest — test_prompt_has_few_shot_examples | (subitem A-03) | PASSED | PASSED | PASS |
| A-08 | Pytest — test_prompt_no_todos | (subitem A-03) | PASSED | PASSED | PASS |
| A-09 | Pytest — test_minimum_techniques | (subitem A-03) | PASSED | PASSED | PASS |
| A-10 | Arquivo `prompts/bug_to_user_story_v1.yml` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-11 | Arquivo `prompts/bug_to_user_story_v2.yml` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-12 | `bug_to_user_story_v2.yml` contem >= 2 exemplos few-shot | inspecao manual YAML | >= 2 blocos de exemplo | 3 exemplos (Exemplo 1, 2, 3) em `system_prompt` | PASS |
| A-13 | `bug_to_user_story_v2.yml` contem role explicita | inspecao manual YAML | campo `role` e/ou marcador no `system_prompt` | `role: "Product Owner senior..."` e `# ROLE` no system_prompt | PASS |
| A-14 | `bug_to_user_story_v2.yml` contem formato de saida | inspecao manual YAML | formato "Como X, eu quero Y, para que Z" especificado | presente em `format` e em `system_prompt` (regras obrigatorias) | PASS |
| A-15 | `bug_to_user_story_v2.yml` sem strings TODO/FIXME | inspecao manual YAML | nenhuma ocorrencia | nenhuma ocorrencia encontrada | PASS |
| A-16 | `bug_to_user_story_v2.yml` contem >= 2 tecnicas | inspecao manual YAML `techniques_applied` | >= 2 tecnicas listadas | `Few-shot Learning`, `Role Prompting`, `Chain of Thought` (3 tecnicas) | PASS |
| A-17 | `datasets/bug_to_user_story.jsonl` tem 15 linhas | `wc -l datasets/bug_to_user_story.jsonl` | 15 | `15` | PASS |
| A-18 | `src/pull_prompts.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-19 | `src/push_prompts.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-20 | `src/evaluate.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-21 | `src/metrics.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-22 | `src/utils.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-23 | `tests/test_prompts.py` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-24 | `requirements.txt` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-25 | `.env.example` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-26 | `.gitignore` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-27 | `SPEC.md` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-28 | `docs/ARCHITECTURE.md` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-29 | `docs/user-stories.md` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-30 | `docs/SETUP.md` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-31 | `README.md` existe | Glob | arquivo presente | arquivo presente | PASS |
| A-32 | README documenta tecnicas aplicadas, comparacao v1 vs v2 e link publico do v2 | inspecao manual `README.md` | secoes "Tecnicas Aplicadas", resultados com link publico e comparacao v1 vs v2 | README e o template original do curso; nao contem secao "Tecnicas Aplicadas (Fase 2)", nao ha resultados reais, sem link publico do prompt v2, sem tabela comparativa v1 vs v2 | FAIL |
| C-01 | Smoke sintaxe: `src/utils.py` | `python -m py_compile src/utils.py` | exit code 0, sem saida | `utils.py: OK` (exit code 0) | PASS |
| C-02 | Smoke sintaxe: `src/pull_prompts.py` | `python -m py_compile src/pull_prompts.py` | exit code 0, sem saida | `pull_prompts.py: OK` (exit code 0) | PASS |
| C-03 | Smoke sintaxe: `src/push_prompts.py` | `python -m py_compile src/push_prompts.py` | exit code 0, sem saida | `push_prompts.py: OK` (exit code 0) | PASS |
| C-04 | Smoke sintaxe: `src/metrics.py` | `python -m py_compile src/metrics.py` | exit code 0, sem saida | `metrics.py: OK` (exit code 0) | PASS |
| C-05 | Smoke sintaxe: `src/evaluate.py` | `python -m py_compile src/evaluate.py` | exit code 0, sem saida | `evaluate.py: OK` (exit code 0) | PASS |
| A-33 | `.env` presente com chaves preenchidas (pre-condicao para Bloco B) | Glob `.env` | arquivo `.env` com chaves preenchidas | `.env` AUSENTE no diretorio | N/A (dispara SKIP no Bloco B) |
| B-01 | `python src/pull_prompts.py` cria `prompts/bug_to_user_story_v1.yml` idempotente | `python src/pull_prompts.py` | exit code 0; stdout "Pull OK: leonanluppi/bug_to_user_story_v1"; arquivo atualizado | SKIP — `.env` ausente; `LANGSMITH_API_KEY` nao configurada | SKIP |
| B-02 | `python src/push_prompts.py` publica v2 publicamente | `python src/push_prompts.py` | exit code 0; stdout com URL publica `https://smith.langchain.com/hub/{username}/bug_to_user_story_v2` | SKIP — `.env` ausente; `LANGSMITH_API_KEY` e `USERNAME_LANGSMITH_HUB` nao configuradas | SKIP |
| B-03 | `python src/evaluate.py` reporta 5 metricas v2 >= 0.9 e STATUS APROVADO | `python src/evaluate.py` | exit code 0; stdout com tabela de metricas; todas >= 0.9; "STATUS APROVADO" | SKIP — `.env` ausente; credenciais nao configuradas | SKIP |

---

## 2. Cobertura por User Story

| US | Descricao | Testes que cobrem | Resultado |
|---|---|---|---|
| US-01 | Pull do prompt v1 do LangSmith Hub | B-01 | SKIP (sem credenciais) |
| US-02 | Otimizacao do prompt para v2 | A-11 a A-16 | PASS (todos estruturais) |
| US-03 | Push publico do v2 para o Hub | B-02 | SKIP (sem credenciais) |
| US-04 | Avaliacao com 5 metricas | B-03 | SKIP (sem credenciais) |
| US-05 | Suite pytest validando o prompt v2 | A-03 a A-09 | PASS (6/6 testes) |
| US-06 | Iteracao ate atingir o target | B-03 (indireto) | SKIP (sem credenciais) |
| US-07 | Configuracao de ambiente reproduzivel | A-01, A-02 | PASS |
| US-08 | Selecao de provedor LLM | C-01 a C-05 (sintaxe), B-03 (execucao) | Sintaxe PASS; execucao SKIP |

---

## 3. Saida crua do pytest

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.4, pluggy-1.6.0 -- C:\Users\allan.santos\Documents\MBA\mba-langchain-langsmith\mba-ia-pull-evaluation-prompt\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\allan.santos\Documents\MBA\mba-langchain-langsmith\mba-ia-pull-evaluation-prompt
plugins: anyio-4.13.0, cov-6.0.0
collecting ... collected 6 items

tests/test_prompts.py::TestPrompts::test_prompt_has_system_prompt PASSED [ 16%]
tests/test_prompts.py::TestPrompts::test_prompt_has_role_definition PASSED [ 33%]
tests/test_prompts.py::TestPrompts::test_prompt_mentions_format PASSED   [ 50%]
tests/test_prompts.py::TestPrompts::test_prompt_has_few_shot_examples PASSED [ 66%]
tests/test_prompts.py::TestPrompts::test_prompt_no_todos PASSED          [ 83%]
tests/test_prompts.py::TestPrompts::test_minimum_techniques PASSED       [100%]

============================== 6 passed in 0.21s ==============================
```

---

## 4. Saida crua dos py_compile (Bloco C)

```
utils.py: OK        (exit code 0)
pull_prompts.py: OK (exit code 0)
push_prompts.py: OK (exit code 0)
metrics.py: OK      (exit code 0)
evaluate.py: OK     (exit code 0)
```

---

## 5. Observacoes tecnicas adicionais

### 5.1 Divergencia de nomes de variaveis de ambiente

O SPEC (secao 7.2) define `LANGSMITH_USERNAME` como nome canonico para o username do Hub.
O codigo em `src/push_prompts.py` (linha 79, 94) e `src/evaluate.py` (linha 334, 336) usa `USERNAME_LANGSMITH_HUB`.
O `.env.example` tambem usa `USERNAME_LANGSMITH_HUB`.
A `ARCHITECTURE.md` (secao 5) documenta e aceita essa divergencia, recomendando o uso de `USERNAME_LANGSMITH_HUB` como alias para manter retrocompatibilidade com o boilerplate do curso.
Este item nao e um FAIL isolado — e uma inconsistencia documentada e aceita na arquitetura.

### 5.2 README nao atualizado (FAIL A-32)

O `README.md` presente e o template original do curso (boilerplate), nao a documentacao final do aluno.
O SPEC (criterio 9.7) exige que o README documente:
- Quais tecnicas foram aplicadas
- Comparacao v1 vs v2
- Link publico do prompt v2

Nenhum desses tres itens esta presente. O README existente descreve o que o aluno "deve fazer" (instrucoes do professor), nao o que foi feito.

### 5.3 Arquivo .env ausente

Nao existe `.env` no diretorio do projeto. Todos os testes do Bloco B requerem credenciais validas e foram marcados SKIP conforme a regra definida. Nao sao FAIL.

### 5.4 `prompts/bug_to_user_story_v1.yml` presente sem pull online

O arquivo `prompts/bug_to_user_story_v1.yml` esta presente no repositorio como artifact estatico (boilerplate do curso, conteudo de baixa qualidade intencional). Nao foi gerado pelo `pull_prompts.py`. Isso e esperado no contexto de repositorio sem credenciais.

---

## 6. Conclusao

| Categoria | PASS | FAIL | SKIP |
|---|---|---|---|
| Bloco A — Validacoes Offline | 31 | 1 | 0 |
| Bloco B — Validacoes Online | 0 | 0 | 3 |
| Bloco C — Smoke sintaxe | 5 | 0 | 0 |
| **TOTAL** | **36** | **1** | **3** |

**Veredicto geral: CONDICIONAL**

Todos os testes executaveis (offline e sintaxe) passaram. O unico FAIL e estrutural/documental: o `README.md` nao foi preenchido com as informacoes requeridas pelo SPEC (tecnicas aplicadas, comparacao v1 vs v2, link publico do prompt v2). Os 3 SKIPs sao por ausencia de credenciais de API e nao representam deficiencias de codigo.

---

## 7. Correcoes recomendadas

### FAIL A-32 — README incompleto
- **Agente responsavel:** `technical-writer` (ou o proprio aluno/engenheiro de prompt)
- **Acao:** Substituir o conteudo atual do `README.md` pelo relatorio final do processo de otimizacao, incluindo:
  1. Secao "Tecnicas Aplicadas" — descricao de Few-shot, Role Prompting e Chain of Thought com justificativa
  2. Secao "Resultados Finais" — tabela comparativa v1 vs v2 com as 5 metricas, screenshots do LangSmith, link publico do prompt `{username}/bug_to_user_story_v2`
  3. Secao "Como Executar" — instrucoes de setup, configuracao do `.env` e ordem de execucao dos scripts

### SKIPs B-01, B-02, B-03 — Requerem credenciais
- **Agente responsavel:** o proprio usuario/aluno
- **Acao:** Configurar `.env` copiando `.env.example` e preenchendo `LANGSMITH_API_KEY`, `USERNAME_LANGSMITH_HUB` e `GOOGLE_API_KEY` (ou `OPENAI_API_KEY`), entao re-executar os testes do Bloco B.
