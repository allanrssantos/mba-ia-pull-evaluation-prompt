# Guia de Setup Local

Este documento descreve como configurar o ambiente de desenvolvimento para o projeto
**Pull, Otimizacao e Avaliacao de Prompts (LangSmith Prompt Hub)**.

---

## Pre-requisitos

| Requisito | Versao minima | Verificar |
|---|---|---|
| Python | 3.9+ | `python --version` |
| pip | qualquer recente | `pip --version` |
| Conta LangSmith | ativa (plano gratuito disponivel) | https://smith.langchain.com |
| Chave OpenAI OU Google AI Studio | qualquer | ver secao abaixo |

Nao ha Docker, banco de dados nem servico web. Tudo roda localmente em venv.

---

## 1. Clonar o repositorio

```bash
git clone <URL-DO-REPOSITORIO>
cd mba-ia-pull-evaluation-prompt
```

---

## 2. Criar o ambiente virtual (venv)

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a execucao de scripts, execute uma vez como administrador:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 3. Instalar dependencias

Com o venv ativo:

```bash
pip install -r requirements.txt
```

Tempo estimado: 1 a 3 minutos. Confirme sem erros ao final.

---

## 4. Configurar variaveis de ambiente

Copie o arquivo de exemplo e preencha com suas credenciais reais:

### Linux / macOS

```bash
cp .env.example .env
```

### Windows (PowerShell)

```powershell
Copy-Item .env.example .env
```

Abra `.env` em qualquer editor e preencha os campos obrigatorios descritos abaixo.

---

## 5. Variaveis de ambiente — como obter cada chave

### LANGSMITH_API_KEY

1. Acesse https://smith.langchain.com e faca login (ou crie conta gratuita).
2. Va em **Settings** > **API Keys**.
3. Clique em **Create API Key**, copie e cole em `LANGSMITH_API_KEY`.

### USERNAME_LANGSMITH_HUB

Este e o seu nome de usuario no LangSmith Hub, necessario para publicar o prompt v2.

**Como descobrir:**

1. No LangSmith UI, va em **Prompt Hub** > **New Prompt**.
2. Publique qualquer prompt temporario (pode apagar depois).
3. Abra o prompt publicado — a URL tera o formato:
   `https://smith.langchain.com/hub/<SEU-USERNAME>/nome-do-prompt`
4. Copie `<SEU-USERNAME>` e cole em `USERNAME_LANGSMITH_HUB`.

Alternativamente: no LangSmith UI, clique no seu avatar (canto superior direito) e veja o campo **Username**.

### OPENAI_API_KEY (se usar LLM_PROVIDER=openai)

1. Acesse https://platform.openai.com/api-keys.
2. Clique em **Create new secret key**, copie e cole em `OPENAI_API_KEY`.
3. Certifique-se de ter credito disponivel na conta (https://platform.openai.com/usage).

### GOOGLE_API_KEY (se usar LLM_PROVIDER=google — plano gratuito)

1. Acesse https://aistudio.google.com/app/apikey.
2. Clique em **Create API key**, selecione um projeto Google Cloud (ou crie um novo).
3. Copie a chave e cole em `GOOGLE_API_KEY`.

O Google AI Studio oferece cota gratuita generosa para `gemini-2.5-flash` — recomendado para o curso.

---

## 6. Exemplo de `.env` preenchido (Google Gemini)

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=ls__xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=bug_to_user_story
USERNAME_LANGSMITH_HUB=meu-usuario

LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
EVAL_MODEL=gemini-2.5-flash

OPENAI_API_KEY=
GOOGLE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 7. Smoke test — verificar conectividade com LangSmith

Com o venv ativo e `.env` preenchido, execute:

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); from langsmith import Client; print(Client().info)"
```

Saida esperada: dicionario com informacoes do servidor LangSmith (versao, status, etc.).
Se receber erro de autenticacao, verifique `LANGSMITH_API_KEY` no `.env`.

---

## 8. Executar os scripts do projeto

### 8.1 Pull do prompt v1 (do LangSmith Hub para arquivo local)

```bash
python src/pull_prompts.py
```

Cria `prompts/bug_to_user_story_v1.yml`.

### 8.2 Push do prompt v2 (do arquivo local para o LangSmith Hub)

```bash
python src/push_prompts.py
```

Requer que `prompts/bug_to_user_story_v2.yml` exista e `USERNAME_LANGSMITH_HUB` esteja configurado.

### 8.3 Avaliacao dos prompts v1 e v2

```bash
python src/evaluate.py
```

Imprime tabela com as 5 metricas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
e STATUS APROVADO/REPROVADO para cada prompt.

### 8.4 Suite de testes pytest (offline, segundos)

```bash
pytest tests/ -v
```

Deve retornar 6 testes verdes. Nao requer rede nem credenciais.

---

## 9. Ciclo de iteracao

O processo esperado para atingir STATUS APROVADO em todas as metricas:

```
1. Editar prompts/bug_to_user_story_v2.yml
2. python src/push_prompts.py
3. python src/evaluate.py
4. Se alguma metrica < 0.9 -> voltar ao passo 1
5. Quando todas >= 0.9 -> STATUS APROVADO -> commit
```

Preveja de 3 a 5 ciclos.

---

## 10. Troubleshooting

| Problema | Causa provavel | Solucao |
|---|---|---|
| `ModuleNotFoundError: langchain` | venv nao ativo ou deps nao instaladas | ativar venv + `pip install -r requirements.txt` |
| `AuthenticationError` LangSmith | `LANGSMITH_API_KEY` invalida ou ausente | verificar chave em https://smith.langchain.com/settings |
| `AuthenticationError` OpenAI | `OPENAI_API_KEY` invalida | verificar em https://platform.openai.com/api-keys |
| `400 Bad Request` Google | `GOOGLE_API_KEY` invalida ou projeto sem billing | verificar em https://aistudio.google.com/app/apikey |
| `PermissionError` ao ativar venv no PowerShell | politica de execucao de scripts bloqueada | executar `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Push falha com `username not found` | `USERNAME_LANGSMITH_HUB` incorreto | seguir instrucoes da secao 5 para descobrir o username correto |
