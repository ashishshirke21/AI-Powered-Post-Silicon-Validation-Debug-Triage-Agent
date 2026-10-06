from __future__ import annotations

import re

from app.detection.catalog import load_signatures
from app.models.schemas import FailureEvent, LogLine, Signature


def _matches(pattern: re.Pattern[str], line: LogLine) -> bool:
    return bool(pattern.search(line.raw))


def detect_failures(
    lines: list[LogLine], signatures: tuple[Signature, ...] | None = None
) -> list[FailureEvent]:
    """Apply the signature catalog to parsed lines.

    One FailureEvent is produced per signature that matches, aggregating every
    line that triggered it so each failure remains traceable to its evidence.
    """
    catalog = signatures if signatures is not None else load_signatures()
    failures: list[FailureEvent] = []

    for signature in catalog:
        pattern = re.compile(signature.pattern, re.IGNORECASE)
        matched = [line for line in lines if _matches(pattern, line)]
        if not matched:
            continue

        line_refs = [line.line_no for line in matched]
        components = sorted({line.component for line in matched if line.component})
        comp_hint = f" on {', '.join(components)}" if components else ""
        failures.append(
            FailureEvent(
                id=f"FAIL_{signature.id}",
                signature_id=signature.id,
                category=signature.category,
                severity=signature.severity,
                summary=f"{signature.name}{comp_hint} ({len(matched)} line(s))",
                line_refs=line_refs,
            )
        )

    return failures
