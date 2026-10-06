import type { Hypothesis, Recommendation } from "../types";

interface Props {
  hypothesis: Hypothesis;
  recommendations: Recommendation[];
  onCite: (lineRefs: number[]) => void;
}

function confidenceClass(c: number): string {
  if (c >= 0.66) return "conf high";
  if (c >= 0.33) return "conf med";
  return "conf low";
}

export function HypothesisCard({ hypothesis, recommendations, onCite }: Props) {
  const recs = recommendations.filter((r) => r.hypothesis_id === hypothesis.id);
  return (
    <article className="hypothesis">
      <header>
        <code>{hypothesis.id}</code>
        <span
          className={confidenceClass(hypothesis.confidence)}
          title={`LLM self-confidence ${hypothesis.llm_confidence.toFixed(
            2,
          )}, blended with signature severity`}
        >
          confidence {hypothesis.confidence.toFixed(2)}
        </span>
      </header>
      <p>{hypothesis.statement}</p>

      {hypothesis.flagged && (
        <p className="flag">⚠ {hypothesis.flag_reason}</p>
      )}

      <div className="evidence-row">
        <strong>Cited evidence:</strong>
        {hypothesis.evidence_refs.length === 0 ? (
          <span className="muted"> none</span>
        ) : (
          hypothesis.evidence_refs.map((ref) => (
            <button key={ref} className="evref" onClick={() => onCite([ref])}>
              L{ref}
            </button>
          ))
        )}
      </div>

      {recs.length > 0 && (
        <div className="recs">
          <strong>Recommended next steps:</strong>
          <ul>
            {recs.map((r) => (
              <li key={r.id}>
                {r.action}
                {r.rationale && <span className="muted"> — {r.rationale}</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}
