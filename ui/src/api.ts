import type { RunCreated, LogLine, Signature, TriageReport } from "./types";

const BASE = "/api";

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function getSignatures(): Promise<Signature[]> {
  return handle(await fetch(`${BASE}/signatures`));
}

export async function generateLog(
  scenarios: string[] | null,
  seed: number | null,
): Promise<RunCreated> {
  return handle(
    await fetch(`${BASE}/logs/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenarios, seed }),
    }),
  );
}

export async function uploadLog(file: File): Promise<RunCreated> {
  const form = new FormData();
  form.append("file", file);
  return handle(await fetch(`${BASE}/runs`, { method: "POST", body: form }));
}

export async function analyzeRun(runId: string): Promise<TriageReport> {
  return handle(await fetch(`${BASE}/runs/${runId}/analyze`, { method: "POST" }));
}

export async function getLines(runId: string): Promise<LogLine[]> {
  return handle(await fetch(`${BASE}/runs/${runId}/lines`));
}

export async function getReportMarkdown(runId: string): Promise<string> {
  const data = await handle<{ markdown: string }>(
    await fetch(`${BASE}/runs/${runId}/report.md`),
  );
  return data.markdown;
}
