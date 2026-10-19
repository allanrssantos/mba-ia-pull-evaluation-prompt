"""
Funções auxiliares para o projeto de otimização de prompts.
"""

import os
import sys
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Os logs usam emojis (✓ ✗ ❌). No Windows o console padrão é cp1252 e
# `print` lança UnicodeEncodeError; forçamos UTF-8 em stdout/stderr.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def load_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Carrega arquivo YAML.

    Args:
        file_path: Caminho do arquivo YAML

    Returns:
        Dicionário com conteúdo do YAML ou None se erro
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data
    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {file_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Erro ao parsear YAML: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao carregar arquivo: {e}")
        return None


def save_yaml(data: Dict[str, Any], file_path: str) -> bool:
    """
    Salva dados em arquivo YAML.

    Args:
        data: Dados para salvar
        file_path: Caminho do arquivo de saída

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        output_file = Path(file_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, indent=2)

        return True
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return False


def check_env_vars(required_vars: list) -> bool:
    """
    Verifica se variáveis de ambiente obrigatórias estão configuradas.

    Args:
        required_vars: Lista de variáveis obrigatórias

    Returns:
        True se todas configuradas, False caso contrário
    """
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Variáveis de ambiente faltando:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nConfigure-as no arquivo .env antes de continuar.")
        return False

    return True


def format_score(score: float, threshold: float = 0.9) -> str:
    """
    Formata score com indicador visual de aprovação.

    Args:
        score: Score entre 0.0 e 1.0
        threshold: Limite mínimo para aprovação

    Returns:
        String formatada com score e símbolo
    """
    symbol = "✓" if score >= threshold else "✗"
    return f"{score:.2f} {symbol}"


def print_section_header(title: str, char: str = "=", width: int = 50):
    """
    Imprime cabeçalho de seção formatado.

    Args:
        title: Título da seção
        char: Caractere para a linha
        width: Largura da linha
    """
    print("\n" + char * width)
    print(title)
    print(char * width + "\n")


def validate_prompt_structure(prompt_data: Dict[str, Any]) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt.

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    required_fields = ['description', 'system_prompt', 'version']
    for field in required_fields:
        if field not in prompt_data:
            errors.append(f"Campo obrigatório faltando: {field}")

    system_prompt = prompt_data.get('system_prompt', '').strip()
    if not system_prompt:
        errors.append("system_prompt está vazio")

    if 'TODO' in system_prompt:
        errors.append("system_prompt ainda contém TODOs")

    techniques = prompt_data.get('techniques_applied', [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Extrai JSON de uma resposta de LLM que pode conter texto adicional.

    Args:
        response_text: Texto da resposta do LLM

    Returns:
        Dicionário extraído ou None se não encontrar JSON válido
    """
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1

        if start != -1 and end > start:
            try:
                json_str = response_text[start:end]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

    return None


def env_first(*names: str, default: str = "") -> str:
    """
    Retorna o valor da primeira variável de ambiente preenchida dentre `names`.

    Permite aceitar tanto os nomes do scaffold do curso (LLM_MODEL, EVAL_MODEL,
    USERNAME_LANGSMITH_HUB) quanto os aliases do SPEC (OPENAI_RESPONSE_MODEL,
    OPENAI_EVAL_MODEL, GEMINI_MODEL, LANGSMITH_USERNAME).
    """
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return default


def get_provider() -> str:
    """
    Retorna o provider normalizado: 'openai' ou 'google' ('gemini' é aceito como alias).
    """
    provider = (os.getenv('LLM_PROVIDER') or 'openai').strip().lower()
    return 'google' if provider in ('google', 'gemini') else provider


def get_response_model() -> str:
    """
    Modelo de resposta (geração das user stories), conforme o desafio:
    OpenAI -> gpt-4o-mini | Gemini -> gemini-2.5-flash.
    """
    if get_provider() == 'google':
        return env_first('LLM_MODEL', 'GEMINI_MODEL', default='gemini-2.5-flash')
    return env_first('LLM_MODEL', 'OPENAI_RESPONSE_MODEL', default='gpt-4o-mini')


def get_eval_model() -> str:
    """
    Modelo avaliador (LLM-as-judge), conforme o desafio:
    OpenAI -> gpt-4o | Gemini -> gemini-2.5-flash.
    """
    if get_provider() == 'google':
        return env_first('EVAL_MODEL', 'GEMINI_MODEL', default='gemini-2.5-flash')
    return env_first('EVAL_MODEL', 'OPENAI_EVAL_MODEL', default='gpt-4o')


def get_hub_username() -> str:
    """
    Username do LangSmith Hub usado em `{username}/bug_to_user_story_v2`.
    Aceita USERNAME_LANGSMITH_HUB (scaffold) ou LANGSMITH_USERNAME (SPEC).
    """
    return env_first('USERNAME_LANGSMITH_HUB', 'LANGSMITH_USERNAME')


_RATE_LIMITER = None


def get_rate_limiter():
    """
    Rate limiter compartilhado por todas as instâncias de LLM do processo.

    A avaliação dispara ~180 chamadas (15 exemplos x (1 resposta + 5 juízes) x 2 prompts).
    O plano gratuito do Gemini limita gemini-2.5-flash a 5 req/min, então sem
    limitação o run falha com HTTP 429. Controle via LLM_REQUESTS_PER_MINUTE
    (default: 4.5 no Google, 60 na OpenAI). Use 0 para desativar.
    """
    global _RATE_LIMITER
    if _RATE_LIMITER is None:
        from langchain_core.rate_limiters import InMemoryRateLimiter

        default_rpm = '4.5' if get_provider() == 'google' else '60'
        rpm = float(os.getenv('LLM_REQUESTS_PER_MINUTE', default_rpm))
        if rpm <= 0:
            _RATE_LIMITER = False
        else:
            _RATE_LIMITER = InMemoryRateLimiter(
                requests_per_second=rpm / 60.0,
                check_every_n_seconds=0.5,
                max_bucket_size=1,
            )
    return _RATE_LIMITER or None


def get_llm(model: Optional[str] = None, temperature: float = 0.0):
    """
    Retorna uma instância de LLM configurada baseada no provider.

    Args:
        model: Nome do modelo (opcional, usa get_response_model() por padrão)
        temperature: Temperatura para geração (padrão: 0.0 para determinístico)

    Returns:
        Instância de ChatOpenAI ou ChatGoogleGenerativeAI

    Raises:
        ValueError: Se provider não for suportado ou API key não configurada
    """
    provider = get_provider()
    model_name = model or get_response_model()
    rate_limiter = get_rate_limiter()
    max_retries = int(os.getenv('LLM_MAX_RETRIES', '6'))

    if provider == 'openai':
        from langchain_openai import ChatOpenAI

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY não configurada no .env\n"
                "Obtenha uma chave em: https://platform.openai.com/api-keys"
            )

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=api_key,
            max_retries=max_retries,
            rate_limiter=rate_limiter,
        )

    elif provider == 'google':
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY não configurada no .env\n"
                "Obtenha uma chave em: https://aistudio.google.com/app/apikey"
            )

        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=api_key,
            max_retries=max_retries,
            rate_limiter=rate_limiter,
        )

    else:
        raise ValueError(
            f"Provider '{provider}' não suportado.\n"
            f"Use 'openai' ou 'google' na variável LLM_PROVIDER do .env"
        )


def get_eval_llm(temperature: float = 0.0):
    """
    Retorna LLM configurado especificamente para avaliação (usa get_eval_model()).

    Args:
        temperature: Temperatura para geração

    Returns:
        Instância de LLM configurada para avaliação
    """
    return get_llm(model=get_eval_model(), temperature=temperature)
