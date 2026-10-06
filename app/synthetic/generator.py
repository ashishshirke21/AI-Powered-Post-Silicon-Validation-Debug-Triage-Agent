from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class GeneratedLog:
    text: str
    # Scenario IDs injected into this log, for detection ground-truth testing.
    injected_scenarios: list[str] = field(default_factory=list)


# Each scenario yields a block of log lines modelling a real failure mode.
SCENARIOS: dict[str, list[tuple[str, str, str]]] = {
    # id -> list of (severity, component, message)
    "boot_hang": [
        ("INFO", "BIOS", "POST stage 3 memory training started"),
        ("WARNING", "BIOS", "CPU1 core sync taking longer than expected"),
        ("ERROR", "BIOS", "boot watchdog timeout waiting for AP core handoff"),
        ("CRITICAL", "BIOS", "system halted: boot sequence did not complete"),
    ],
    "thermal_trip": [
        ("INFO", "THERMAL", "package temperature 78C within limits"),
        ("WARNING", "THERMAL", "package temperature 97C approaching Tjmax"),
        ("ERROR", "THERMAL", "thermal threshold exceeded 105C PROCHOT asserted"),
        ("CRITICAL", "THERMAL", "thermal shutdown triggered to protect silicon"),
    ],
    "memory_ecc": [
        ("INFO", "MEM", "DIMM channel A training passed"),
        ("WARNING", "MEM", "correctable ECC error at rank 2 bank 5"),
        ("ERROR", "MEM", "uncorrectable ECC error DIMM_A1 address 0x3F8A0000"),
        ("CRITICAL", "MEM", "memory controller fenced channel A due to UE storm"),
    ],
    "pcie_link": [
        ("INFO", "PCIE", "link training port 0 negotiating Gen5"),
        ("WARNING", "PCIE", "port 0 downgraded to Gen3 after retrain"),
        ("ERROR", "PCIE", "link training failed port 0 stuck in polling LTSSM"),
        ("ERROR", "PCIE", "device enumeration failed on root port 0"),
    ],
    "power_rail": [
        ("INFO", "PWR", "VDDCR_CPU rail nominal at 0.95V"),
        ("WARNING", "PWR", "VDDCR_SOC droop detected 0.78V under load"),
        ("ERROR", "PWR", "power good deassert on VDDCR_SOC rail"),
        ("CRITICAL", "PWR", "VR fault shutdown: overcurrent on VDDCR_CPU"),
    ],
    "pattern_mismatch": [
        ("INFO", "ATE", "scan test pattern set 12 loaded"),
        ("WARNING", "ATE", "marginal timing on pattern 14 vector 2048"),
        ("ERROR", "ATE", "test pattern mismatch expected 0xA5 got 0xA1 vector 4096"),
        ("ERROR", "ATE", "logic BIST failure signature 0xDEADBEEF chain 7"),
    ],
}

_HEALTHY_NOISE: list[tuple[str, str, str]] = [
    ("INFO", "BIOS", "POST complete, handing off to bootloader"),
    ("INFO", "MEM", "all DIMM channels trained successfully"),
    ("INFO", "PCIE", "all root ports enumerated and linked at Gen5"),
    ("INFO", "THERMAL", "package temperature stable at 65C"),
    ("INFO", "PWR", "all rails within regulation tolerance"),
    ("INFO", "ATE", "functional test suite passed 1024 patterns"),
    ("INFO", "SMU", "clock domains locked at target frequencies"),
    ("INFO", "FABRIC", "data fabric links trained, bandwidth nominal"),
]


def _format(ts: datetime, severity: str, component: str, message: str) -> str:
    return f"[{ts.isoformat(timespec='milliseconds')}] [{severity}] [{component}] {message}"


def generate_log(
    scenarios: list[str] | None = None,
    *,
    noise_lines: int = 10,
    seed: int | None = None,
) -> GeneratedLog:
    """Generate a synthetic log.

    If ``scenarios`` is None, a random subset of failure scenarios is injected.
    Returns the log text and the list of scenario IDs actually injected.
    """
    rng = random.Random(seed)
    if scenarios is None:
        count = rng.randint(1, 3)
        scenarios = rng.sample(list(SCENARIOS), count)
    else:
        scenarios = [s for s in scenarios if s in SCENARIOS]

    ts = datetime(2026, 1, 1, 8, 0, 0)
    entries: list[str] = []

    def advance() -> datetime:
        nonlocal ts
        ts = ts + timedelta(milliseconds=rng.randint(5, 500))
        return ts

    for _ in range(noise_lines // 2):
        sev, comp, msg = rng.choice(_HEALTHY_NOISE)
        entries.append(_format(advance(), sev, comp, msg))

    for scenario in scenarios:
        for sev, comp, msg in SCENARIOS[scenario]:
            entries.append(_format(advance(), sev, comp, msg))
        for _ in range(rng.randint(0, 2)):
            sev, comp, msg = rng.choice(_HEALTHY_NOISE)
            entries.append(_format(advance(), sev, comp, msg))

    for _ in range(noise_lines - noise_lines // 2):
        sev, comp, msg = rng.choice(_HEALTHY_NOISE)
        entries.append(_format(advance(), sev, comp, msg))

    return GeneratedLog(text="\n".join(entries) + "\n", injected_scenarios=scenarios)
