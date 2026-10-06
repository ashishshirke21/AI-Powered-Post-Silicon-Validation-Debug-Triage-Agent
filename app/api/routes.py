from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import get_settings
from app.db import repository
from app.detection.catalog import load_signatures
from app.llm.provider import get_llm
from app.models.schemas import LogLine, Run, RunStatus, Signature, TriageReport
from app.parsing.parser import parse_log
from app.pipeline.graph import run_pipeline
from app.reporting.renderer import render_markdown
from app.synthetic.generator import generate_log

router = APIRouter()


class GenerateRequest(BaseModel):
    scenarios: list[str] | None = None
    noise_lines: int = 10
    seed: int | None = None


class RunCreated(BaseModel):
    run_id: str
    injected_scenarios: list[str] = []


def _new_run_id() -> str:
    return f"run_{uuid.uuid4().hex[:12]}"


def _persist_new_run(source: str, raw_log: str, filename: str | None) -> Run:
    run = Run(
        id=_new_run_id(),
        created_at=datetime.now(),
        source=source,
        status=RunStatus.PARSED,
        filename=filename,
        line_count=sum(1 for line in raw_log.splitlines() if line.strip()),
    )
    repository.create_run(run, raw_log)
    return run


@router.get("/signatures", response_model=list[Signature])
def get_signatures() -> list[Signature]:
    return list(load_signatures())


@router.get("/runs", response_model=list[Run])
def list_runs() -> list[Run]:
    return repository.list_runs()


@router.post("/logs/generate", response_model=RunCreated)
def generate(req: GenerateRequest) -> RunCreated:
    generated = generate_log(
        scenarios=req.scenarios, noise_lines=req.noise_lines, seed=req.seed
    )
    run = _persist_new_run("synthetic", generated.text, None)
    return RunCreated(run_id=run.id, injected_scenarios=generated.injected_scenarios)


@router.post("/runs", response_model=RunCreated)
async def upload_log(file: UploadFile = File(...)) -> RunCreated:  # noqa: B008
    content = (await file.read()).decode("utf-8", errors="replace")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Uploaded log is empty.")
    run = _persist_new_run("upload", content, file.filename)
    return RunCreated(run_id=run.id)


@router.get("/runs/{run_id}", response_model=Run)
def get_run(run_id: str) -> Run:
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


@router.post("/runs/{run_id}/analyze", response_model=TriageReport)
def analyze(run_id: str) -> TriageReport:
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    raw_log = repository.get_raw_log(run_id) or ""

    settings = get_settings()
    repository.update_status(run_id, RunStatus.ANALYZING)
    report = run_pipeline(
        run_id,
        run.source,
        raw_log,
        llm=get_llm(settings),
        min_confidence=settings.min_hypothesis_confidence,
        llm_weight=settings.confidence_llm_weight,
    )
    repository.save_report(run_id, report)
    return report


@router.get("/runs/{run_id}/report", response_model=TriageReport)
def get_report(run_id: str) -> TriageReport:
    report = repository.get_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No report; run analyze first.")
    return report


@router.get("/runs/{run_id}/report.md")
def get_report_markdown(run_id: str) -> dict:
    report = repository.get_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No report; run analyze first.")
    raw_log = repository.get_raw_log(run_id)
    return {"markdown": render_markdown(report, raw_log)}


@router.get("/runs/{run_id}/lines", response_model=list[LogLine])
def get_lines(run_id: str) -> list[LogLine]:
    raw_log = repository.get_raw_log(run_id)
    if raw_log is None:
        raise HTTPException(status_code=404, detail="Run not found.")
    return parse_log(raw_log)
