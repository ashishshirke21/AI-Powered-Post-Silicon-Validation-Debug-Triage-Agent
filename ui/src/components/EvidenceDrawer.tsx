import type { LogLine } from "../types";

interface Props {
  lines: LogLine[];
  highlighted: number[];
  onClose: () => void;
}

export function EvidenceDrawer({ lines, highlighted, onClose }: Props) {
  const highlightSet = new Set(highlighted);
  return (
    <aside className="drawer">
      <header>
        <h3>Evidence</h3>
        <button className="link" onClick={onClose}>
          close
        </button>
      </header>
      <pre className="loglines">
        {lines.map((line) => (
          <div
            key={line.line_no}
            className={highlightSet.has(line.line_no) ? "logline hit" : "logline"}
          >
            <span className="lno">L{line.line_no}</span>
            {line.raw}
          </div>
        ))}
      </pre>
    </aside>
  );
}
