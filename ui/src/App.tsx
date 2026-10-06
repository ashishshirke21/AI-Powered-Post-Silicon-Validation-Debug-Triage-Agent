import { useState } from "react";
import { analyzeRun, getLines, getReportMarkdown } from "./api";
import { EvidenceDrawer } from "./components/EvidenceDrawer";
import { FailuresTable } from "./components/FailuresTable";
import { HypothesisCard } from "./components/HypothesisCard";
import { LogSourcePanel } from "./components/LogSourcePanel";
import type { LogLine, RunCreated, TriageReport } from "./types";
import "./styles.css";

export default function App() {
  const [runId, setRunId] = useState<string | null>(null);
  const [report, setReport] = useState<TriageReport | null>(null);
  const [lines, setLines] = useState<LogLine[]>([]);
  const [highlighted, setHighlighted] = useState<number[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function handleRunCreated(run: RunCreated) {
    setError(null);
    setBusy(true);
    setReport(null);
    setHighlighted(null);
    setRunId(run.run_id);
    setNote(
      run.injected_scenarios.length
        ? `Generated run ${run.run_id} (injected: ${run.injected_scenarios.join(", ")})`
        : `Created run ${run.run_id}`,
    );
    try {
      const [rep, ln] = await Promise.all([
        analyzeRun(run.run_id),
        getLines(run.run_id),
      ]);
      setReport(rep);
      setLines(ln);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function handleExport() {
    if (!runId) return;
    try {
      const md = await getReportMarkdown(runId);
      const blob = new Blob([md], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `triage-${runId}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Post-Silicon Validation &amp; Debug Triage Agent</h1>
        <span className="tag">assisted · evidence-traceable</span>
      </header>

      <div className="layout">
        <div className="left">
          <LogSourcePanel busy={busy} onRunCreated={handleRunCreated} onError={setError} />

          {note && <p className="note">{note}</p>}
          {error && <p className="error">{error}</p>}
          {busy && <p className="muted">Running triage pipeline…</p>}

          {report && (
            <>
              <section className="panel">
                <h2>2 · Experiment Summary</h2>
                <p>{report.experiment_summary}</p>
                <button className="secondary" onClick={handleExport}>
                  Export report (.md)
                </button>
              </section>

              <section className="panel">
                <h2>3 · Detected Failures</h2>
                <FailuresTable
                  failures={report.failures}
                  onCite={(refs) => setHighlighted(refs)}
                />
              </section>

              <section className="panel">
                <h2>4 · Root-Cause Hypotheses</h2>
                {report.hypotheses.length === 0 ? (
                  <p className="muted">No evidence-backed hypotheses were generated.</p>
                ) : (
                  report.hypotheses.map((h) => (
                    <HypothesisCard
                      key={h.id}
                      hypothesis={h}
                      recommendations={report.recommendations}
                      onCite={(refs) => setHighlighted(refs)}
                    />
                  ))
                )}
              </section>
            </>
          )}
        </div>

        <div className="right">
          {highlighted ? (
            <EvidenceDrawer
              lines={lines}
              highlighted={highlighted}
              onClose={() => setHighlighted(null)}
            />
          ) : (
            <aside className="drawer empty">
              <p className="muted">
                Click an evidence reference (e.g. <code>L12</code>) to trace a claim
                back to the exact log lines.
              </p>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
