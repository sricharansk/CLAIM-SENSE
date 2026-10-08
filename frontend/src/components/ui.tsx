import { ReactNode, useEffect, useState } from "react";
import { ApiError, words } from "../api";

export function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(true);
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let live = true;
    setLoading(true);
    fn().then((d) => { if (live) { setData(d); setError(null); } })
      .catch((e) => live && setError(e instanceof ApiError ? e : new ApiError(String(e), 0)))
      .finally(() => live && setLoading(false));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  return { data, error, loading, reload: () => setTick((t) => t + 1) };
}

export function ErrorBox({ error, onRetry }: { error: ApiError | null; onRetry?: () => void }) {
  if (!error) return null;
  return (
    <div className="error" role="alert">
      <strong>{error.message}</strong>
      {error.correlationId && <span className="muted"> · correlation ID {error.correlationId}</span>}
      {onRetry && <button className="btn small" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export const Loading = () => <div className="loading">Loading…</div>;

const TONE: Record<string, string> = {
  HIGH: "red", MEDIUM: "amber", LOW: "green", APPROVE: "green", APPROVED: "green", PARTIAL_APPROVAL: "teal",
  RECOMMEND_REJECT: "red", REJECTED: "red", REJECT: "red", INVESTIGATE: "red", UNDER_INVESTIGATION: "red",
  REQUEST_INFO: "amber", INFO_REQUESTED: "amber", PENDING_REVIEW: "blue", ESCALATED: "purple", ESCALATE: "purple",
  COVERED: "green", NOT_COVERED: "red", UNCERTAIN: "amber", PASS: "green", FAIL: "red", MISSING: "amber",
  SUCCEEDED: "green", FAILED: "red", NEEDS_ATTENTION: "red", DOCUMENTS_RECEIVED: "gray", SUBMITTED: "gray",
};
export function Badge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="muted">—</span>;
  return <span className={`badge ${TONE[value] ?? "gray"}`}>{words(value)}</span>;
}

export function Card({ title, children, actions }: { title?: ReactNode; children: ReactNode; actions?: ReactNode }) {
  return (
    <section className="card">
      {(title || actions) && <div className="card-head"><h3>{title}</h3>{actions}</div>}
      {children}
    </section>
  );
}

export function Bars({ data, total }: { data: Record<string, number>; total?: number }) {
  const sum = total ?? Object.values(data).reduce((a, b) => a + b, 0);
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (!entries.length) return <p className="muted">No data yet.</p>;
  return (
    <div className="bars">
      {entries.map(([k, v]) => (
        <div key={k} className="bar-row">
          <span className="bar-label"><Badge value={k} /></span>
          <span className="bar-track"><span className="bar-fill" style={{ width: `${(v / Math.max(sum, 1)) * 100}%` }} /></span>
          <span className="bar-value">{v}</span>
        </div>
      ))}
    </div>
  );
}
