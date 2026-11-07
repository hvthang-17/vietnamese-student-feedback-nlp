import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.preprocessing import normalize_text


def test_normalize_whitespace_preserves_vietnamese():
    assert normalize_text("  giảng   viên  nhiệt tình ") == "giảng viên nhiệt tình"


def test_normalize_rejects_empty():
    try:
        normalize_text(" \n ")
    except ValueError:
        return
    assert False, "expected empty text rejection"
