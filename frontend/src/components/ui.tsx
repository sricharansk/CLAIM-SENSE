import { ReactNode, useEffect, useState } from "react";
import { Link } from "react-router-dom";
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

export function Due({ s }: { s: { due_date: string; days_left: number | null; state: string } | null | undefined }) {
  if (!s) return <span className="muted">—</span>;
  const label = s.days_left === null ? s.state.toLowerCase() : s.days_left < 0 ? `${-s.days_left}d overdue` : `${s.days_left}d left`;
  return <span title={`Settle by ${s.due_date}`}><Badge value={s.state} /> <span className="muted small">{label}</span></span>;
}

export const Loading = () => <div className="loading">Loading…</div>;

const TONE: Record<string, string> = {
  HIGH: "red", MEDIUM: "amber", LOW: "green", APPROVE: "green", APPROVED: "green", PARTIAL_APPROVAL: "teal",
  RECOMMEND_REJECT: "red", REJECTED: "red", REJECT: "red", INVESTIGATE: "red", UNDER_INVESTIGATION: "red",
  REQUEST_INFO: "amber", INFO_REQUESTED: "amber", PENDING_REVIEW: "blue", ESCALATED: "purple", ESCALATE: "purple",
  COVERED: "green", NOT_COVERED: "red", UNCERTAIN: "amber", PASS: "green", FAIL: "red", MISSING: "amber",
  ON_TRACK: "green", DUE_SOON: "amber", OVERDUE: "red", MET: "green", BREACHED: "red", FINAL: "green", DRAFT: "amber",
  READY: "green", UPLOADED: "gray", VALIDATING: "blue", EXTRACTING: "blue", INDEXING: "blue",
  SUCCEEDED: "green", FAILED: "red", NEEDS_ATTENTION: "red", DOCUMENTS_RECEIVED: "gray", SUBMITTED: "gray",
  CORRECTED: "purple", IN_USE: "green", REGISTERED: "gray", VERIFIED: "green", COMPLETE: "blue", CHECK_SOURCE: "amber",
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

/** Horizontal bars. With `link`, each row opens the matching list (dashboard drill-down). */
export function Bars({ data, total, link, keepOrder, plain }: { data: Record<string, number>; total?: number;
  link?: (key: string) => string; keepOrder?: boolean; plain?: boolean }) {
  const sum = total ?? Object.values(data).reduce((a, b) => a + b, 0);
  const entries = keepOrder ? Object.entries(data) : Object.entries(data).sort((a, b) => b[1] - a[1]);
  if (!entries.length || !sum) return <p className="muted">No data for this selection.</p>;
  return (
    <div className="bars">
      {entries.map(([k, v]) => {
        const body = (
          <>
            <span className="bar-label">{plain ? <span className="small">{k}</span> : <Badge value={k} />}</span>
            <span className="bar-track"><span className="bar-fill" style={{ width: `${(v / Math.max(sum, 1)) * 100}%` }} /></span>
            <span className="bar-value">{v}</span>
          </>
        );
        return link && v > 0
          ? <Link key={k} className="bar-row link-row" to={link(k)} title={`Show these ${v} claims`}>{body}</Link>
          : <div key={k} className="bar-row">{body}</div>;
      })}
    </div>
  );
}

export function Kpi({ label, value, tone, to, hint }: { label: string; value: string | number; tone?: string; to?: string; hint?: string }) {
  const body = <><span>{label}</span><strong>{value}</strong>{hint && <small className="muted">{hint}</small>}</>;
  return to ? <Link className={`kpi link-kpi ${tone ?? ""}`} to={to} title="Show these claims">{body}</Link>
    : <div className={`kpi ${tone ?? ""}`}>{body}</div>;
}

/** A row of mutually exclusive choices (filters). */
export function Segmented({ label, options, value, onChange }: { label: string; options: [string, string][]; value: string;
  onChange: (v: string) => void }) {
  return (
    <div className="segmented" role="group" aria-label={label}>
      {options.map(([v, text]) => (
        <button key={v} type="button" className={v === value ? "active" : ""} aria-pressed={v === value} onClick={() => onChange(v)}>{text}</button>
      ))}
    </div>
  );
}
