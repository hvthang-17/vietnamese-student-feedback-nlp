"""Explicit dotenv loading without database/model startup."""
import sys

from backend.app.__main__ import main


def test_explicit_env_file_preserves_process_precedence(tmp_path, monkeypatch):
    import uvicorn
    config = tmp_path / "demo.env"
    config.write_text("HOST=127.0.0.2\nPORT=8123\n", encoding="utf-8")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.setattr(sys, "argv", ["backend", "serve", "--env-file", str(config)])
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    main()
    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == 8123
