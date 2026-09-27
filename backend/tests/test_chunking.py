import pytest

from app.services.chunking import chunk_pages


def test_chunks_never_cross_pages() -> None:
    chunks = chunk_pages(["First page text.", "", "Third page text."], size=100, overlap=10)
    assert [(c.page, c.text) for c in chunks] == [(1, "First page text."), (3, "Third page text.")]
    assert [c.index for c in chunks] == [0, 1]


def test_long_pages_are_split_with_overlap() -> None:
    sentences = " ".join(f"Sentence number {i} has some words." for i in range(40))
    chunks = chunk_pages([sentences], size=200, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.text) <= 200 for c in chunks)
    # The start of each chunk repeats the end of the previous one.
    for previous, current in zip(chunks, chunks[1:], strict=False):
        assert current.text.split(" ")[0] in previous.text


def test_very_long_sentences_are_hard_split() -> None:
    chunks = chunk_pages(["x" * 1000], size=300, overlap=50)
    assert all(len(c.text) <= 300 for c in chunks)
    assert len(chunks) >= 4


def test_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        chunk_pages(["text"], size=100, overlap=100)
