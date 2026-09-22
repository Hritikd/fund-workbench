import pytest

from fund_workbench.io import read_document, slugify


def test_plain_text_reading() -> None:
    assert read_document("notes.md", b"  Hello evidence  ") == "Hello evidence"


def test_unsupported_document_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        read_document("deck.pptx", b"not a deck")


def test_slugify_is_stable() -> None:
    assert slugify("Founder Call #2") == "founder-call-2"
