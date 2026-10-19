"""
Testes offline (RNF-07) que validam a estrutura/qualidade do prompt v2
lendo apenas o YAML local. Nao requer chaves de API.
"""
from pathlib import Path

import pytest
import yaml

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"

KNOWN_TECHNIQUES = {
    "few-shot": ["few-shot", "few shot", "fewshot"],
    "chain-of-thought": ["chain of thought", "chain-of-thought", "cot"],
    "role-prompting": ["role prompting", "role-prompting", "role"],
    "tree-of-thought": ["tree of thought", "tot"],
    "skeleton-of-thought": ["skeleton of thought", "sot"],
    "react": ["react"],
}


@pytest.fixture(scope="module")
def prompt_data():
    assert PROMPT_PATH.exists(), f"Prompt v2 nao encontrado em {PROMPT_PATH}"
    with open(PROMPT_PATH, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), "YAML invalido."
    assert PROMPT_KEY in data, f"Chave raiz '{PROMPT_KEY}' ausente."
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        system_prompt = (prompt_data.get("system_prompt") or "").strip()
        assert system_prompt, "system_prompt vazio."
        assert len(system_prompt) > 200, "system_prompt parece curto demais."

    def test_prompt_has_role_definition(self, prompt_data):
        haystack = (prompt_data.get("system_prompt", "") + " " + (prompt_data.get("role") or "")).lower()
        role_markers = ["voce e um", "voce é um", "product owner", "role", "persona", "especialista"]
        assert any(marker in haystack for marker in role_markers), (
            "Nenhum marcador de role/persona encontrado no system_prompt."
        )

    def test_prompt_mentions_format(self, prompt_data):
        haystack = (prompt_data.get("system_prompt", "") + " " + (prompt_data.get("format") or "")).lower()
        assert "como" in haystack and "eu quero" in haystack and "para que" in haystack, (
            "Formato 'Como X, eu quero Y, para que Z' nao foi exigido explicitamente."
        )
        assert "criterios de aceitacao" in haystack or "criterios de aceitação" in haystack or "given-when-then" in haystack, (
            "Criterios de aceitacao / Given-When-Then nao mencionados."
        )

    def test_prompt_has_few_shot_examples(self, prompt_data):
        system_prompt = prompt_data.get("system_prompt", "")
        lower = system_prompt.lower()
        explicit_examples = lower.count("exemplo ")
        story_blocks = lower.count("user story:")
        assert explicit_examples >= 2 or story_blocks >= 2, (
            f"Esperado >= 2 exemplos few-shot; encontrado exemplos={explicit_examples}, blocos user story={story_blocks}."
        )

    def test_prompt_no_todos(self, prompt_data):
        haystack = (
            (prompt_data.get("system_prompt") or "")
            + (prompt_data.get("user_prompt") or "")
        )
        for marker in ("TODO", "FIXME", "[TODO]", "[FIXME]"):
            assert marker not in haystack, f"Marcador proibido '{marker}' encontrado."

    def test_minimum_techniques(self, prompt_data):
        techniques_meta = [t.lower() for t in (prompt_data.get("techniques_applied") or [])]
        haystack = (prompt_data.get("system_prompt") or "").lower()

        detected = set()
        for tech, aliases in KNOWN_TECHNIQUES.items():
            if any(alias in t for t in techniques_meta for alias in aliases):
                detected.add(tech)
            elif any(alias in haystack for alias in aliases):
                detected.add(tech)

        assert len(detected) >= 2, (
            f"Esperado >= 2 tecnicas detectadas; encontradas: {sorted(detected)}."
        )
        assert "few-shot" in detected, "Tecnica obrigatoria Few-shot nao detectada."

    def test_prompt_only_expects_bug_report_variable(self, prompt_data):
        """Chaves literais no texto viram variaveis e quebram o evaluate."""
        from langchain_core.prompts import ChatPromptTemplate

        template = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_data.get("system_prompt") or ""),
                ("user", prompt_data.get("user_prompt") or ""),
            ]
        )
        assert set(template.input_variables) == {"bug_report"}, (
            f"Variaveis inesperadas no prompt: {sorted(set(template.input_variables) - {'bug_report'})}. "
            "Escape chaves literais com {{ }}."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
