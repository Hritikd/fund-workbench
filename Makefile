.PHONY: install test lint app demo

install:
	uv sync --extra dev

test:
	uv run pytest

lint:
	uv run ruff check .

app:
	uv run streamlit run app.py

demo:
	uv run fund-workbench demo --output demo-output
