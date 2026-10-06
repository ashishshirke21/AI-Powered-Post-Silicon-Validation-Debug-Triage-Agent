from __future__ import annotations

from datetime import datetime

from app.db.models import RunRow
from app.db.session import session_scope
from app.models.schemas import Run, RunStatus, TriageReport


def create_run(run: Run, raw_log: str) -> None:
    with session_scope() as session:
        session.add(
            RunRow(
                id=run.id,
                created_at=run.created_at,
                source=run.source,
                status=run.status.value,
                filename=run.filename,
                line_count=run.line_count,
                raw_log=raw_log,
            )
        )


def get_run(run_id: str) -> Run | None:
    with session_scope() as session:
        row = session.get(RunRow, run_id)
        if row is None:
            return None
        return _row_to_run(row)


def get_raw_log(run_id: str) -> str | None:
    with session_scope() as session:
        row = session.get(RunRow, run_id)
        return row.raw_log if row else None


def update_status(run_id: str, status: RunStatus) -> None:
    with session_scope() as session:
        row = session.get(RunRow, run_id)
        if row is not None:
            row.status = status.value


def save_report(run_id: str, report: TriageReport) -> None:
    with session_scope() as session:
        row = session.get(RunRow, run_id)
        if row is not None:
            row.report_json = report.model_dump_json()
            row.status = RunStatus.COMPLETE.value


def get_report(run_id: str) -> TriageReport | None:
    with session_scope() as session:
        row = session.get(RunRow, run_id)
        if row is None or row.report_json is None:
            return None
        return TriageReport.model_validate_json(row.report_json)


def list_runs() -> list[Run]:
    with session_scope() as session:
        rows = session.query(RunRow).order_by(RunRow.created_at.desc()).all()
        return [_row_to_run(r) for r in rows]


def _row_to_run(row: RunRow) -> Run:
    return Run(
        id=row.id,
        created_at=row.created_at if isinstance(row.created_at, datetime) else datetime.now(),
        source=row.source,
        status=RunStatus(row.status),
        filename=row.filename,
        line_count=row.line_count,
    )
