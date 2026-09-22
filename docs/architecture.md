# Architecture

Fund Workbench separates probabilistic extraction from deterministic workflow rules.

## Core modules

- `io.py` extracts text from supported documents and creates source records.
- `llm.py` optionally requests schema-constrained claim extraction.
- `evidence.py` provides the deterministic extractor and validates all claims.
- `analysis.py` performs transparent thesis routing, question generation, and memo rendering.
- `updates.py` compares recurring metrics, risks, and asks.
- `app.py` is the local Streamlit interface.
- `cli.py` exposes portable automation commands.

## Trust boundaries

Documents and model output are untrusted. The validator applies these rules:

1. Every attributed claim must reference a supplied source ID.
2. Every quote must appear verbatim in that source.
3. Company-controlled material cannot independently verify its own claim.
4. Duplicate source-and-statement pairs collapse to one claim.
5. Missing or invalid attribution becomes an explicit inference.

The tool does not verify whether an independent publication is truthful. It records the source relationship so a human can judge its quality.

## Extension points

Additional model providers should return the same Pydantic models and pass through `validate_claims`. CRM integrations should consume exported schemas or a future webhook adapter rather than importing Streamlit state.
