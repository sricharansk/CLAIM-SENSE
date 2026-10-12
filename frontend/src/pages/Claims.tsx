import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, inr } from "../api";
import { useSession } from "../components/session";
import { Badge, Card, Due, ErrorBox, Loading, useLoad } from "../components/ui";

const STATUSES = ["", "PENDING_REVIEW", "DOCUMENTS_RECEIVED", "SUBMITTED", "APPROVED", "REJECTED", "INFO_REQUESTED", "UNDER_INVESTIGATION", "ESCALATED", "NEEDS_ATTENTION"];

export default function Claims() {
  const { user } = useSession();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState("");
  const status = params.get("status") ?? "";
  const filters = (["type", "recommendation", "risk"] as const).map((k) => [k, params.get(k) ?? ""] as const).filter(([, v]) => v);
  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };
  const list = useLoad(() => api.claims(q, status), [q, status]);
  const field = { type: "claim_type", recommendation: "recommendation", risk: "risk_level" } as const;
  const rows = (list.data ?? []).filter((c) => filters.every(([k, v]) => String(c[field[k]] ?? "") === v));
  return (
    <>
      <header className="page-head">
        <h1>Claims</h1>
        <div className="row">
          <button className="btn" onClick={() => api.exportCsv().catch((e) => alert(e.message))}>Export CSV</button>
          {user.can_write && <Link className="btn primary" to="/claims/new">New claim</Link>}
        </div>
      </header>
      <Card>
        <div className="filters">
          <input placeholder="Search claim, claimant or policy number" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={status} onChange={(e) => set("status", e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replace(/_/g, " ").toLowerCase() : "All statuses"}</option>)}
          </select>
        </div>
        {filters.length > 0 && list.data && (
          <p className="row small">
            Showing {rows.length} of {list.data?.length ?? 0} claims where
            {filters.map(([k, v]) => <button key={k} className="chip" onClick={() => set(k, "")} title="Remove this filter">{k} = {v.replace(/_/g, " ").toLowerCase()} ×</button>)}
          </p>
        )}
        <ErrorBox error={list.error} onRetry={list.reload} />
        {list.loading && !list.data ? <Loading /> : (
          <table>
            <thead><tr><th>Claim</th><th>Type</th><th>Claimant</th><th>Policy</th><th>Incident</th><th>Claimed</th><th>AI payable</th><th>Recommendation</th><th>Risk</th><th>Status</th><th>Settlement</th></tr></thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.claim_number}>
                  <td><Link to={`/claims/${c.claim_number}`}>{c.claim_number}</Link></td>
                  <td>{c.claim_type}</td><td>{c.claimant_name}</td><td className="mono">{c.policy_number}</td>
                  <td>{c.incident_date ?? "—"}</td><td>{inr(c.claimed_amount)}</td><td>{inr(c.recommended_payable)}</td>
                  <td><Badge value={c.recommendation} /></td><td><Badge value={c.risk_level} /></td><td><Badge value={c.status} /></td><td><Due s={c.settlement} /></td>
                </tr>
              ))}
              {list.data && rows.length === 0 && <tr><td colSpan={11} className="muted">No claims match.</td></tr>}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
