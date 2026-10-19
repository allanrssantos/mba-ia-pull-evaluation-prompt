# User Stories — Pull, Otimização e Avaliação de Prompts

## US-01: Pull do prompt v1 do LangSmith Hub
**Como** engenheiro de prompt
**Quero** baixar o prompt `leonanluppi/bug_to_user_story_v1` do LangSmith Hub para um arquivo YAML local
**Para** ter um baseline versionado e comparável com a versão otimizada

### Critérios de aceite
```gherkin
Cenário: Pull bem-sucedido
  Dado que LANGSMITH_API_KEY está configurada no .env
  E o prompt "leonanluppi/bug_to_user_story_v1" existe no Hub
  Quando executo "python src/pull_prompts.py"
  Então o arquivo prompts/bug_to_user_story_v1.yml é criado
  E o YAML é parseável e contém mensagens system/user
  E o stdout exibe "Pull OK: leonanluppi/bug_to_user_story_v1"

Cenário: Idempotência do pull
  Dado que prompts/bug_to_user_story_v1.yml já existe
  Quando executo "python src/pull_prompts.py" novamente
  Então o comando termina com exit code 0
  E o conteúdo do arquivo permanece equivalente ao do Hub
```

---

## US-02: Otimização do prompt para v2
**Como** engenheiro de prompt
**Quero** criar uma versão otimizada `prompts/bug_to_user_story_v2.yml` com Few-shot e 1 técnica avançada
**Para** elevar a qualidade das user stories geradas a partir de bugs

### Critérios de aceite
```gherkin
Cenário: Estrutura mínima do v2
  Dado o arquivo prompts/bug_to_user_story_v2.yml
  Quando inspeciono o conteúdo
  Então existe uma mensagem system com role definida
  E existem ao menos 2 exemplos few-shot
  E há especificação explícita do formato de saída
  E há ao menos uma técnica avançada (CoT, ToT, Skeleton-of-Thought, ReAct ou Role Prompting)
  E não existem strings "TODO" nem "FIXME"
```

---

## US-03: Push público do v2 para o Hub
**Como** engenheiro de prompt
**Quero** publicar `{username}/bug_to_user_story_v2` como prompt público no LangSmith
**Para** permitir que avaliadores e a comunidade acessem a versão otimizada

### Critérios de aceite
```gherkin
Cenário: Push bem-sucedido e público
  Dado LANGSMITH_API_KEY e LANGSMITH_USERNAME configurados
  E prompts/bug_to_user_story_v2.yml válido
  Quando executo "python src/push_prompts.py"
  Então uma nova versão é criada em {username}/bug_to_user_story_v2
  E o prompt é acessível publicamente em https://smith.langchain.com/hub/{username}/bug_to_user_story_v2
  E o stdout exibe a URL pública

Cenário: Re-push gera nova versão sem erro
  Dado que já existe versão prévia do prompt no Hub
  Quando executo "python src/push_prompts.py" novamente
  Então uma nova versão é criada sem exceção
```

---

## US-04: Avaliação com 5 métricas
**Como** avaliador
**Quero** rodar uma avaliação automatizada que reporte Helpfulness, Correctness, F1-Score, Clarity e Precision
**Para** confirmar que o v2 atinge ≥ 0.9 em todas as métricas

### Critérios de aceite
```gherkin
Cenário: Avaliação aprovada
  Dado que prompts/bug_to_user_story_v2.yml está publicado
  E datasets/bug_to_user_story.jsonl tem 15 exemplos
  Quando executo "python src/evaluate.py"
  Então o stdout exibe Helpfulness, Correctness, F1-Score, Clarity, Precision para v1 e v2
  E todas as métricas do v2 são ≥ 0.9
  E o STATUS final do v2 é "APROVADO"
  E o experimento aparece no LangSmith UI com prefixo "bug_to_user_story_v2"

Cenário: Avaliação reprovada
  Dado que ao menos uma métrica do v2 < 0.9
  Quando executo "python src/evaluate.py"
  Então o STATUS final do v2 é "REPROVADO"
  E o exit code é diferente de 0
```

---

## US-05: Suíte pytest validando o prompt v2
**Como** mantenedor
**Quero** uma suite de testes pytest que valide a estrutura do prompt v2 sem chamadas externas
**Para** detectar regressões rapidamente em CI/local

### Critérios de aceite
```gherkin
Cenário: Todos os testes passam
  Dado prompts/bug_to_user_story_v2.yml válido
  Quando executo "pytest tests/"
  Então 6 testes passam:
    | system prompt existe                |
    | role definida                       |
    | formato exigido                     |
    | few-shot presente (>= 2 exemplos)   |
    | sem TODO nem FIXME                  |
    | mínimo de 2 técnicas aplicadas      |
  E o tempo de execução é inferior a 10 segundos
```

---

## US-06: Iteração até atingir o target
**Como** engenheiro de prompt
**Quero** iterar de 3 a 5 ciclos editando o v2, dando push e re-avaliando
**Para** convergir todas as métricas para ≥ 0.9

### Critérios de aceite
```gherkin
Cenário: Ciclo de iteração
  Dado que uma execução de evaluate retornou REPROVADO
  Quando edito prompts/bug_to_user_story_v2.yml
  E executo "python src/push_prompts.py"
  E executo "python src/evaluate.py"
  Então uma nova versão pública é registrada
  E uma nova rodada de métricas é exibida
  E após no máximo 5 ciclos o STATUS final é APROVADO
```

---

## US-07: Configuração de ambiente reproduzível
**Como** avaliador externo
**Quero** clonar o repositório, criar venv, instalar dependências e configurar `.env`
**Para** rodar todo o pipeline localmente sem Docker

### Critérios de aceite
```gherkin
Cenário: Setup limpo
  Dado um clone fresco do repositório
  Quando crio venv com Python 3.9+
  E executo "pip install -r requirements.txt"
  E copio .env.example para .env e preencho as chaves
  Então consigo executar pull_prompts.py, push_prompts.py, evaluate.py e pytest sem erros de import nem de configuração
```

---

## US-08: Seleção de provedor LLM
**Como** engenheiro de prompt
**Quero** alternar entre OpenAI e Gemini via variável `LLM_PROVIDER`
**Para** escolher o provedor disponível sem alterar código

### Critérios de aceite
```gherkin
Cenário: Provedor OpenAI
  Dado LLM_PROVIDER=openai e OPENAI_API_KEY configurada
  Quando executo evaluate.py
  Então as respostas usam gpt-4o-mini e a avaliação usa gpt-4o

Cenário: Provedor Gemini
  Dado LLM_PROVIDER=gemini e GOOGLE_API_KEY configurada
  Quando executo evaluate.py
  Então respostas e avaliação usam gemini-2.5-flash
```
