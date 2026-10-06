from __future__ import annotations

from app.parsing.parser import parse_log


def test_parses_timestamp_severity_component():
    raw = "[2026-01-01T08:00:01.123] [ERROR] [PCIE] link training failed port 0"
    lines = parse_log(raw)
    assert len(lines) == 1
    line = lines[0]
    assert line.line_no == 1
    assert line.severity.value == "ERROR"
    assert line.component == "PCIE"
    assert "link training failed" in line.message
    assert line.timestamp is not None


def test_blank_lines_skipped_but_line_numbers_track_source():
    raw = "line one\n\n[INFO] [MEM] trained"
    lines = parse_log(raw)
    assert [line.line_no for line in lines] == [1, 3]


def test_unstructured_line_defaults_to_info():
    lines = parse_log("just some free text")
    assert lines[0].severity.value == "INFO"
    assert lines[0].message == "just some free text"
