# Contributing

Thank you for improving Fund Workbench. Contributions should preserve the project’s evidence-first behavior.

## Start here

1. Open an issue describing the workflow problem.
2. Use synthetic or public data in examples and tests.
3. Keep changes narrow and add a behavioral test for changed logic.
4. Run `uv run ruff check .` and `uv run pytest`.
5. Explain privacy and failure-mode changes in the pull request.

## Product rules

- Do not label company-controlled evidence independently verified.
- Do not add autonomous investment recommendations.
- Preserve source IDs through every transformation.
- Treat model output as untrusted until application validation completes.
- Make missing information visible.
- Avoid model-provider coupling in the core schemas.
- Do not add telemetry or persistence without an explicit design and documentation update.

## Development

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run streamlit run app.py
```

Use small commits and write plain-language commit messages. Never include real confidential decks, call notes, API keys, or personal information.
