from __future__ import annotations

import json
import re
from typing import Protocol

from app.config import Settings, get_settings


class TriageLLM(Protocol):
    """Minimal interface the triage node depends on."""

    def triage(self, prompt: str) -> dict:
        """Return a dict with keys ``hypotheses`` and ``recommendations``."""
        ...


class MockLLM:
    """Deterministic, offline provider used for tests and demos without a key.

    It derives hypotheses directly from the evidence block embedded in the
    prompt, only ever citing line IDs that actually appear there. This keeps the
    whole pipeline runnable (and the guardrail testable) without network access.
    """

    def triage(self, prompt: str) -> dict:
        evidence_ids = [int(n) for n in re.findall(r"L(\d+):", prompt)]
        failure_match = re.search(r"FAILURE_ID:\s*(\S+)", prompt)
        failure_id = failure_match.group(1) if failure_match else "UNKNOWN"
        category_match = re.search(r"CATEGORY:\s*(\S+)", prompt)
        category = category_match.group(1) if category_match else "unknown"

        top_refs = evidence_ids[:3]
        hyp_id = f"HYP_{failure_id}"
        return {
            "hypotheses": [
                {
                    "id": hyp_id,
                    "failure_id": failure_id,
                    "statement": (
                        f"The {category} failure is most consistent with the symptoms "
                        f"recorded in the cited evidence lines."
                    ),
                    "category": category,
                    "confidence": 0.7 if top_refs else 0.2,
                    "evidence_refs": top_refs,
                }
            ],
            "recommendations": [
                {
                    "id": f"REC_{failure_id}",
                    "hypothesis_id": hyp_id,
                    "action": (
                        f"Re-run the {category} test with verbose logging and "
                        f"capture rail/thermal telemetry."
                    ),
                    "rationale": "Confirm reproducibility and isolate the failing component.",
                }
            ],
        }


class OpenAILLM:
    """OpenAI / Azure OpenAI provider via langchain-openai."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = self._build_client(settings)

    @staticmethod
    def _build_client(settings: Settings):
        if settings.llm_provider == "azure":
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                api_key=settings.azure_openai_api_key,
                azure_endpoint=settings.azure_openai_endpoint,
                azure_deployment=settings.azure_openai_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=0,
            )

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0,
        )

    def triage(self, prompt: str) -> dict:
        response = self._client.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        return _parse_json_block(content)


def _parse_json_block(text: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    brace = re.search(r"\{.*\}", candidate, re.DOTALL)
    if brace:
        candidate = brace.group(0)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {"hypotheses": [], "recommendations": []}


def get_llm(settings: Settings | None = None) -> TriageLLM:
    settings = settings or get_settings()
    if settings.llm_provider in ("openai", "azure"):
        return OpenAILLM(settings)
    return MockLLM()
