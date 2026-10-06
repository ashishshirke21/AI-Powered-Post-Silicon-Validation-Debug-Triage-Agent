export type Severity = "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface LogLine {
  line_no: number;
  raw: string;
  timestamp: string | null;
  severity: Severity;
  component: string | null;
  message: string;
}

export interface Signature {
  id: string;
  name: string;
  category: string;
  pattern: string;
  severity: Severity;
  description: string;
}

export interface FailureEvent {
  id: string;
  signature_id: string;
  category: string;
  severity: Severity;
  summary: string;
  line_refs: number[];
}

export interface Hypothesis {
  id: string;
  failure_id: string;
  statement: string;
  category: string;
  confidence: number;
  llm_confidence: number;
  evidence_refs: number[];
  flagged: boolean;
  flag_reason: string | null;
}

export interface Recommendation {
  id: string;
  hypothesis_id: string;
  action: string;
  rationale: string;
}

export interface TriageReport {
  run_id: string;
  created_at: string;
  source: string;
  experiment_summary: string;
  failures: FailureEvent[];
  hypotheses: Hypothesis[];
  recommendations: Recommendation[];
}

export interface RunCreated {
  run_id: string;
  injected_scenarios: string[];
}
