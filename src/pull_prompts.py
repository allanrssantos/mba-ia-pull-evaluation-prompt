"""
Faz pull do prompt v1 do LangSmith Hub e salva em prompts/bug_to_user_story_v1.yml.

Idempotente: rodar duas vezes sobrescreve o arquivo com o conteudo canonico do Hub
sem duplicar nem corromper nada.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate

from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

PROMPT_NAME = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = "prompts/bug_to_user_story_v1.yml"


def _serialize_messages(prompt: ChatPromptTemplate) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = []
    for message in prompt.messages:
        # Templates (SystemMessagePromptTemplate etc.) nao expoem `.type`;
        # mensagens concretas (SystemMessage etc.) expoem "system"/"human"/"ai".
        class_name = message.__class__.__name__.lower()
        message_type = (getattr(message, "type", None) or "").lower()
        if class_name.startswith("system") or message_type == "system":
            role = "system"
        elif class_name.startswith(("human", "user")) or message_type in ("human", "user"):
            role = "user"
        elif class_name.startswith(("ai", "assistant")) or message_type in ("ai", "assistant"):
            role = "assistant"
        else:
            role = message_type or class_name

        template = getattr(message, "prompt", None)
        content = getattr(template, "template", None) if template else None
        if content is None:
            content = getattr(message, "content", "")

        messages.append({"role": role, "content": content})
    return messages


def _to_yaml_payload(prompt: ChatPromptTemplate) -> Dict[str, Any]:
    messages = _serialize_messages(prompt)

    system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
    user_prompt = next((m["content"] for m in messages if m["role"] == "user"), "")

    return {
        "bug_to_user_story_v1": {
            "description": "Prompt original (v1) puxado do LangSmith Hub para baseline de comparacao.",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "messages": messages,
            "version": "v1",
            "source": PROMPT_NAME,
            "tags": ["bug-analysis", "user-story", "baseline"],
        }
    }


def pull_prompt() -> bool:
    print_section_header(f"PULL: {PROMPT_NAME}")

    try:
        prompt = hub.pull(PROMPT_NAME)
    except Exception as exc:  # noqa: BLE001
        print(f"Falha ao executar hub.pull('{PROMPT_NAME}'): {exc}")
        print("Verifique LANGSMITH_API_KEY e conectividade com a API do LangSmith.")
        return False

    if not isinstance(prompt, ChatPromptTemplate):
        print("Prompt retornado nao e ChatPromptTemplate; abortando serializacao.")
        return False

    payload = _to_yaml_payload(prompt)

    output = Path(OUTPUT_PATH)
    if not save_yaml(payload, str(output)):
        return False

    print(f"Pull OK: {PROMPT_NAME}")
    print(f"Arquivo salvo em: {output.resolve()}")
    return True


def main() -> int:
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1
    return 0 if pull_prompt() else 1


if __name__ == "__main__":
    sys.exit(main())
