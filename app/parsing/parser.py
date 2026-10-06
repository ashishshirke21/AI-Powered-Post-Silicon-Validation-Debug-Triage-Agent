from __future__ import annotations

import re
from datetime import datetime

from app.models.schemas import LogLine, Severity

# Matches: [2026-09-30T12:00:01.123] [ERROR] [PCIE] link training failed
# Timestamp and component are optional; the whole prefix is best-effort.
_TIMESTAMP_RE = re.compile(
    r"^\s*[\[\(]?(?P<ts>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)[\]\)]?\s*"
)
_SEVERITY_RE = re.compile(
    r"[\[\(]?\b(?P<sev>CRITICAL|CRIT|FATAL|ERROR|ERR|WARNING|WARN|INFO|DEBUG)\b[\]\)]?",
    re.IGNORECASE,
)
_COMPONENT_RE = re.compile(r"[\[\(](?P<comp>[A-Za-z0-9_\-]{2,20})[\]\)]")

_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "CRIT": Severity.CRITICAL,
    "FATAL": Severity.CRITICAL,
    "ERROR": Severity.ERROR,
    "ERR": Severity.ERROR,
    "WARNING": Severity.WARNING,
    "WARN": Severity.WARNING,
    "INFO": Severity.INFO,
    "DEBUG": Severity.INFO,
}


def _parse_timestamp(value: str) -> datetime | None:
    normalized = value.replace(" ", "T")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def parse_line(line_no: int, raw: str) -> LogLine:
    text = raw.rstrip("\n")
    remainder = text
    timestamp: datetime | None = None
    severity = Severity.INFO
    component: str | None = None

    ts_match = _TIMESTAMP_RE.match(remainder)
    if ts_match:
        timestamp = _parse_timestamp(ts_match.group("ts"))
        remainder = remainder[ts_match.end() :]

    sev_match = _SEVERITY_RE.search(remainder)
    if sev_match:
        severity = _SEVERITY_MAP.get(sev_match.group("sev").upper(), Severity.INFO)
        remainder = remainder[: sev_match.start()] + remainder[sev_match.end() :]

    comp_match = _COMPONENT_RE.search(remainder)
    if comp_match:
        component = comp_match.group("comp").upper()
        remainder = remainder[: comp_match.start()] + remainder[comp_match.end() :]

    message = re.sub(r"\s{2,}", " ", remainder).strip(" :-\t")

    return LogLine(
        line_no=line_no,
        raw=text,
        timestamp=timestamp,
        severity=severity,
        component=component,
        message=message or text.strip(),
    )


def parse_log(raw_log: str) -> list[LogLine]:
    """Parse raw log text into structured lines. ``line_no`` starts at 1."""
    lines: list[LogLine] = []
    for idx, raw in enumerate(raw_log.splitlines(), start=1):
        if raw.strip() == "":
            continue
        lines.append(parse_line(idx, raw))
    return lines
