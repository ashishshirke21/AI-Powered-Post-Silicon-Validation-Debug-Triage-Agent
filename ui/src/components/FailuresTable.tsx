import type { FailureEvent } from "../types";

interface Props {
  failures: FailureEvent[];
  onCite: (lineRefs: number[]) => void;
}

export function FailuresTable({ failures, onCite }: Props) {
  if (failures.length === 0) {
    return <p className="muted">No failures detected in this log.</p>;
  }
  return (
    <table className="failures">
      <thead>
        <tr>
          <th>Severity</th>
          <th>Category</th>
          <th>Summary</th>
          <th>Signature</th>
          <th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        {failures.map((f) => (
          <tr key={f.id}>
            <td>
              <span className={`sev sev-${f.severity}`}>{f.severity}</span>
            </td>
            <td>{f.category}</td>
            <td>{f.summary}</td>
            <td>
              <code>{f.signature_id}</code>
            </td>
            <td>
              <button className="link" onClick={() => onCite(f.line_refs)}>
                {f.line_refs.length} line(s)
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
