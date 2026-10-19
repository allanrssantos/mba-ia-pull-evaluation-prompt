"""
Push do prompt v2 (prompts/bug_to_user_story_v2.yml) para o LangSmith Hub
como `{username}/bug_to_user_story_v2` publico.
"""

import sys
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from utils import check_env_vars, get_hub_username, load_yaml, print_section_header

load_dotenv()

INPUT_PATH = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
FORBIDDEN_MARKERS = ("TODO", "FIXME", "[TODO]", "[FIXME]")


def validate_prompt(prompt_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    errors: List[str] = []

    body = prompt_data.get(PROMPT_KEY)
    if not isinstance(body, dict):
        errors.append(f"Chave raiz '{PROMPT_KEY}' ausente ou invalida.")
        return False, errors

    system_prompt = (body.get("system_prompt") or "").strip()
    user_prompt = (body.get("user_prompt") or "").strip()

    if not system_prompt:
        errors.append("system_prompt vazio.")
    if not user_prompt:
        errors.append("user_prompt vazio.")

    haystack = f"{system_prompt}\n{user_prompt}"
    for marker in FORBIDDEN_MARKERS:
        if marker in haystack:
            errors.append(f"Marcador proibido encontrado no prompt: {marker}.")

    techniques = body.get("techniques_applied") or []
    if len(techniques) < 2:
        errors.append("techniques_applied deve listar pelo menos 2 tecnicas.")

    # Chaves simples no texto ({algo}) viram variaveis do ChatPromptTemplate e
    # quebram a execucao no evaluate (missing variables). So {bug_report} e permitida.
    if system_prompt and user_prompt:
        try:
            variables = set(
                ChatPromptTemplate.from_messages(
                    [("system", system_prompt), ("user", user_prompt)]
                ).input_variables
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Prompt invalido como ChatPromptTemplate: {exc}")
        else:
            extra = variables - {"bug_report"}
            if extra:
                errors.append(
                    f"Variaveis inesperadas no prompt: {sorted(extra)}. "
                    "Escape chaves literais com {{ }} ou remova-as."
                )
            if "bug_report" not in variables:
                errors.append("Prompt nao usa a variavel {bug_report}.")

    return len(errors) == 0, errors


def build_chat_prompt(prompt_data: Dict[str, Any]) -> ChatPromptTemplate:
    body = prompt_data[PROMPT_KEY]
    return ChatPromptTemplate.from_messages(
        [
            ("system", body["system_prompt"]),
            ("user", body["user_prompt"]),
        ]
    )


def push_prompt(prompt_name: str, prompt: ChatPromptTemplate, body: Dict[str, Any]) -> bool:
    """
    Publica o prompt no LangSmith Hub como PUBLICO.

    Usa `Client.push_prompt(..., is_public=True)`: diferente de `hub.push`
    (cujo parametro `new_repo_is_public` so vale na criacao do repositorio),
    este metodo garante visibilidade publica tambem em repositorios ja existentes.
    """
    client = Client()
    try:
        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=body.get("description"),
            tags=list(body.get("tags") or []),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Falha em push_prompt('{prompt_name}'): {exc}")
        return False

    print(f"Push OK: {prompt_name}")
    if url:
        print(f"URL: {url}")
    return True


def main() -> int:
    print_section_header("PUSH: bug_to_user_story_v2")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    username = get_hub_username()
    if not username:
        print("❌ Username do LangSmith Hub nao configurado.")
        print("   Defina USERNAME_LANGSMITH_HUB (ou LANGSMITH_USERNAME) no .env.")
        return 1

    prompt_data = load_yaml(INPUT_PATH)
    if not prompt_data:
        print(f"Falha ao carregar {INPUT_PATH}.")
        return 1

    ok, errors = validate_prompt(prompt_data)
    if not ok:
        print("Validacao do prompt v2 falhou:")
        for err in errors:
            print(f" - {err}")
        return 1

    full_name = f"{username}/bug_to_user_story_v2"

    prompt = build_chat_prompt(prompt_data)
    return 0 if push_prompt(full_name, prompt, prompt_data[PROMPT_KEY]) else 1


if __name__ == "__main__":
    sys.exit(main())
