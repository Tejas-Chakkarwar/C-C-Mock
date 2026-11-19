from __future__ import annotations

from pathlib import Path

import pytest

from scripts.preprocess import parse_edges


def test_parse_edges_rejects_extra_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.edges"
    path.write_text("1 2 3\n", encoding="utf-8")

    with pytest.raises(ValueError, match="exactly two IDs"):
        parse_edges(path)


def test_processed_outputs_are_present() -> None:
    processed = Path("data/processed")
    expected = {"users.csv", "circles.csv", "memberships.csv", "follows.csv", "preprocess_log.json"}
    assert expected <= {path.name for path in processed.iterdir()}
