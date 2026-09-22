from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from .analysis import build_screening_memo, memo_to_markdown
from .evidence import build_ledger
from .io import dump_json, load_json, source_from_file
from .models import EvidenceLedger, PortfolioUpdate, SourceType, Thesis
from .samples import sample_sources, sample_thesis, sample_updates
from .updates import compare_updates, comparison_to_markdown

app = typer.Typer(help="Evidence-first workflow tools for investors and operators.")


@app.command()
def demo(
    output: Annotated[Path, typer.Option(help="Directory for generated demo artifacts")] = Path("demo-output"),
) -> None:
    """Run all tools on synthetic sample data without an API key."""
    output.mkdir(parents=True, exist_ok=True)
    ledger = build_ledger("Northstar Robotics", sample_sources())
    memo = build_screening_memo(ledger, sample_thesis())
    previous, current = sample_updates()
    comparison = compare_updates(previous, current)
    (output / "evidence-ledger.json").write_text(dump_json(ledger), encoding="utf-8")
    (output / "screening-brief.md").write_text(memo_to_markdown(memo), encoding="utf-8")
    (output / "portfolio-comparison.md").write_text(comparison_to_markdown(comparison), encoding="utf-8")
    typer.echo(f"Generated three artifacts in {output.resolve()}")


@app.command()
def evidence(
    company: Annotated[str, typer.Option(help="Company or opportunity name")],
    files: Annotated[list[Path], typer.Argument(help="Text, Markdown, PDF, or DOCX sources")],
    output: Annotated[Path, typer.Option(help="Output JSON path")] = Path("evidence-ledger.json"),
    source_type: Annotated[SourceType, typer.Option(help="Type applied to all input files")] = SourceType.COMPANY,
    ai: Annotated[bool, typer.Option(help="Use OpenAI Structured Outputs; requires OPENAI_API_KEY")] = False,
) -> None:
    """Create an evidence ledger from one or more documents."""
    sources = [source_from_file(path.name, path.read_bytes(), source_type) for path in files]
    ledger = build_ledger(company, sources, ai=ai)
    output.write_text(dump_json(ledger), encoding="utf-8")
    typer.echo(f"Wrote {len(ledger.claims)} claims to {output}")


@app.command()
def memo(
    ledger_path: Annotated[Path, typer.Argument(help="Evidence ledger JSON")],
    thesis_path: Annotated[Path, typer.Argument(help="Thesis JSON")],
    output: Annotated[Path, typer.Option(help="Output Markdown path")] = Path("screening-brief.md"),
) -> None:
    """Build a screening brief from a ledger and explicit thesis."""
    ledger = EvidenceLedger.model_validate(load_json(ledger_path))
    thesis = Thesis.model_validate(load_json(thesis_path))
    result = build_screening_memo(ledger, thesis)
    output.write_text(memo_to_markdown(result), encoding="utf-8")
    typer.echo(f"Wrote screening brief to {output}")


@app.command("compare-updates")
def compare_update_files(
    previous_path: Annotated[Path, typer.Argument(help="Previous PortfolioUpdate JSON")],
    current_path: Annotated[Path, typer.Argument(help="Current PortfolioUpdate JSON")],
    output: Annotated[Path, typer.Option(help="Output Markdown path")] = Path("update-comparison.md"),
) -> None:
    """Compare two normalized portfolio updates."""
    previous = PortfolioUpdate.model_validate(json.loads(previous_path.read_text(encoding="utf-8")))
    current = PortfolioUpdate.model_validate(json.loads(current_path.read_text(encoding="utf-8")))
    result = compare_updates(previous, current)
    output.write_text(comparison_to_markdown(result), encoding="utf-8")
    typer.echo(f"Wrote update comparison to {output}")


if __name__ == "__main__":
    app()
