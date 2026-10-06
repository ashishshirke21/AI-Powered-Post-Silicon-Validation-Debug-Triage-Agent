import { useEffect, useRef, useState } from "react";
import { generateLog, getSignatures, uploadLog } from "../api";
import type { RunCreated, Signature } from "../types";

interface Props {
  busy: boolean;
  onRunCreated: (run: RunCreated) => void;
  onError: (message: string) => void;
}

// Derive selectable scenario categories from the signature catalog.
const SCENARIOS = [
  { id: "boot_hang", label: "Boot hang" },
  { id: "thermal_trip", label: "Thermal trip" },
  { id: "memory_ecc", label: "Memory ECC (UE)" },
  { id: "pcie_link", label: "PCIe link failure" },
  { id: "power_rail", label: "Power rail fault" },
  { id: "pattern_mismatch", label: "Test pattern mismatch" },
];

export function LogSourcePanel({ busy, onRunCreated, onError }: Props) {
  const [selected, setSelected] = useState<string[]>(["thermal_trip"]);
  const [seed, setSeed] = useState<string>("");
  const [signatureCount, setSignatureCount] = useState<number>(0);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    getSignatures()
      .then((s: Signature[]) => setSignatureCount(s.length))
      .catch(() => setSignatureCount(0));
  }, []);

  function toggle(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function handleGenerate() {
    try {
      const parsedSeed = seed.trim() === "" ? null : Number(seed);
      const run = await generateLog(selected.length ? selected : null, parsedSeed);
      onRunCreated(run);
    } catch (e) {
      onError(String(e));
    }
  }

  async function handleUpload() {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      onError("Choose a log file first.");
      return;
    }
    try {
      onRunCreated(await uploadLog(file));
    } catch (e) {
      onError(String(e));
    }
  }

  return (
    <section className="panel">
      <h2>1 · Log Source</h2>
      <p className="muted">{signatureCount} failure signatures loaded.</p>

      <div className="block">
        <h3>Generate synthetic log</h3>
        <div className="chips">
          {SCENARIOS.map((s) => (
            <label key={s.id} className={selected.includes(s.id) ? "chip on" : "chip"}>
              <input
                type="checkbox"
                checked={selected.includes(s.id)}
                onChange={() => toggle(s.id)}
              />
              {s.label}
            </label>
          ))}
        </div>
        <div className="row">
          <input
            className="seed"
            placeholder="seed (optional)"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
          />
          <button disabled={busy} onClick={handleGenerate}>
            Generate
          </button>
        </div>
      </div>

      <div className="block">
        <h3>Or upload a log file</h3>
        <div className="row">
          <input type="file" ref={fileRef} accept=".log,.txt" />
          <button disabled={busy} onClick={handleUpload}>
            Upload
          </button>
        </div>
      </div>
    </section>
  );
}
