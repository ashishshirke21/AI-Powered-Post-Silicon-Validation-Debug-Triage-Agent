from __future__ import annotations

import os
import tempfile

import pytest

# Use an isolated temp SQLite DB per test session.
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_signatures_endpoint(client):
    resp = client.get("/api/signatures")
    assert resp.status_code == 200
    assert len(resp.json()) > 0


def test_generate_analyze_report_flow(client):
    gen = client.post("/api/logs/generate", json={"scenarios": ["pcie_link"], "seed": 1})
    assert gen.status_code == 200
    run_id = gen.json()["run_id"]
    assert gen.json()["injected_scenarios"] == ["pcie_link"]

    analyze = client.post(f"/api/runs/{run_id}/analyze")
    assert analyze.status_code == 200
    report = analyze.json()
    assert any(f["category"] == "pcie" for f in report["failures"])

    md = client.get(f"/api/runs/{run_id}/report.md")
    assert md.status_code == 200
    assert "Triage Report" in md.json()["markdown"]


def test_upload_flow(client):
    log = "[2026-01-01T08:00:00.000] [CRITICAL] [THERMAL] thermal shutdown triggered\n"
    resp = client.post(
        "/api/runs",
        files={"file": ("test.log", log, "text/plain")},
    )
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    analyze = client.post(f"/api/runs/{run_id}/analyze")
    assert analyze.status_code == 200
    assert any(f["category"] == "thermal" for f in analyze.json()["failures"])


def test_missing_run_returns_404(client):
    assert client.get("/api/runs/nope").status_code == 404
