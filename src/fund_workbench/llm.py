from __future__ import annotations

import os

from openai import OpenAI

from .models import ClaimExtraction, Source

SYSTEM_PROMPT = """You extract auditable claims for an opportunity-evaluation workflow.
Return only claims supported by the supplied sources. Preserve the supplied source_id.
The quote must be an exact, contiguous excerpt from that source.
Use verified only for an independent source. Use company_reported for company material,
reported for call notes/internal records, inferred only for an explicitly labelled inference,
and unknown only when the source explicitly states that information is unknown.
Do not make an investment recommendation. Prefer material claims about team, product,
market, traction, funding, economics, or risk. Limit the result to 40 claims."""


def has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def extract_claims_ai(sources: list[Source]) -> list:
    if not has_api_key():
        raise RuntimeError("OPENAI_API_KEY is not set. Use deterministic mode or provide a key.")
    client = OpenAI()
    source_text = "\n\n".join(
        "\n".join(
            [
                f"SOURCE_ID: {source.id}",
                f"SOURCE_TYPE: {source.source_type.value}",
                f"TITLE: {source.title}",
                f"CONTENT:\n{source.content[:30000]}",
            ]
        )
        for source in sources
    )
    response = client.responses.parse(
        model=os.getenv("OPENAI_MODEL", "gpt-6-astra"),
        instructions=SYSTEM_PROMPT,
        input=source_text,
        text_format=ClaimExtraction,
        store=False,
    )
    if response.output_parsed is None:
        raise RuntimeError("The model returned no structured claim extraction.")
    return response.output_parsed.claims
