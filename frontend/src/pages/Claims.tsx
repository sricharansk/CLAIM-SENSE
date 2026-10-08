import { useState } from "react";
import { Link } from "react-router-dom";
import { api, inr } from "../api";
import { useSession } from "../components/session";
import { Badge, Card, ErrorBox, Loading, useLoad } from "../components/ui";

const STATUSES = ["", "PENDING_REVIEW", "DOCUMENTS_RECEIVED", "SUBMITTED", "APPROVED", "REJECTED", "INFO_REQUESTED", "UNDER_INVESTIGATION", "ESCALATED", "NEEDS_ATTENTION"];

export default function Claims() {
  const { user } = useSession();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const list = useLoad(() => api.claims(q, status), [q, status]);
  return (
    <>
      <header className="page-head">
        <h1>Claims</h1>
        {user.can_write && <Link className="btn primary" to="/claims/new">New claim</Link>}
      </header>
      <Card>
        <div className="filters">
          <input placeholder="Search claim, claimant or policy number" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {STATUSES.map((s) => <option key={s} value={s}>{s ? s.replace(/_/g, " ").toLowerCase() : "All statuses"}</option>)}
          </select>
        </div>
        <ErrorBox error={list.error} onRetry={list.reload} />
        {list.loading && !list.data ? <Loading /> : (
          <table>
            <thead><tr><th>Claim</th><th>Type</th><th>Claimant</th><th>Policy</th><th>Incident</th><th>Claimed</th><th>AI payable</th><th>Recommendation</th><th>Risk</th><th>Status</th></tr></thead>
            <tbody>
              {(list.data ?? []).map((c) => (
                <tr key={c.claim_number}>
                  <td><Link to={`/claims/${c.claim_number}`}>{c.claim_number}</Link></td>
                  <td>{c.claim_type}</td><td>{c.claimant_name}</td><td className="mono">{c.policy_number}</td>
                  <td>{c.incident_date ?? "—"}</td><td>{inr(c.claimed_amount)}</td><td>{inr(c.recommended_payable)}</td>
                  <td><Badge value={c.recommendation} /></td><td><Badge value={c.risk_level} /></td><td><Badge value={c.status} /></td>
                </tr>
              ))}
              {list.data?.length === 0 && <tr><td colSpan={10} className="muted">No claims match.</td></tr>}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
