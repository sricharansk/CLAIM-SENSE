import { Link } from "react-router-dom";
import { api, inr } from "../api";
import { useSession } from "../components/session";
import { Badge, Bars, Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function Dashboard() {
  const { user } = useSession();
  const a = useLoad(api.analytics);
  const claims = useLoad(() => api.claims());
  if (a.loading && !a.data) return <Loading />;
  if (!a.data) return <ErrorBox error={a.error} onRetry={a.reload} />;
  const { totals, portfolio, human_vs_ai: h } = a.data;
  return (
    <>
      <header className="page-head">
        <div>
          <h1>Claims intelligence dashboard</h1>
          <p className="muted">Claim Sense: RAG-Based Insurance Claims Adjudication &amp; Policy Knowledge Assistant</p>
        </div>
        {user.can_write && <Link className="btn primary" to="/claims/new">New claim</Link>}
      </header>
      <div className="kpis">
        <Kpi label="Claims" value={totals.claims} />
        <Kpi label="Pending human review" value={totals.pending_review} />
        <Kpi label="High risk" value={totals.high_risk} tone="red" />
        <Kpi label="Decided by reviewers" value={totals.decided} />
        <Kpi label="Claimed" value={inr(totals.claimed_amount)} />
        <Kpi label="AI-recommended payable" value={inr(totals.recommended_payable)} />
        <Kpi label="Avg. analysis time" value={totals.avg_analysis_ms !== null ? `${totals.avg_analysis_ms} ms` : "—"} />
        <Kpi label="Override rate (reviewer vs AI)" value={rate(h.override_rate, h.overridden, h.decided)} />
        <Kpi label="Escalation rate" value={rate(h.escalation_rate, h.escalated, h.reviewed)} />
        <Kpi label="Settlement overdue / breached" value={totals.overdue} tone={totals.overdue ? "red" : undefined} />
      </div>
      <div className="grid3">
        <Card title="AI recommendations"><Bars data={a.data.by_recommendation} />
          <h4>Reviewer actions</h4><Bars data={a.data.human_outcomes} />
          {h.amount_overridden > 0 && <p className="muted small">{h.amount_overridden} approval{h.amount_overridden === 1 ? "" : "s"} at an amount other than the AI's.</p>}
        </Card>
        <Card title="Risk levels"><Bars data={a.data.by_risk} /></Card>
        <Card title="Claim status"><Bars data={a.data.by_status} /><h4>Settlement clock</h4><Bars data={a.data.settlement} /></Card>
      </div>
      <div className="grid2">
        <Card title="Recent claims" actions={<Link to="/claims">All claims</Link>}>
          <table>
            <thead><tr><th>Claim</th><th>Claimant</th><th>Claimed</th><th>Recommendation</th><th>Risk</th></tr></thead>
            <tbody>
              {(claims.data ?? []).slice(0, 8).map((c) => (
                <tr key={c.claim_number}>
                  <td><Link to={`/claims/${c.claim_number}`}>{c.claim_number}</Link></td>
                  <td>{c.claimant_name}</td><td>{inr(c.claimed_amount)}</td>
                  <td><Badge value={c.recommendation} /></td><td><Badge value={c.risk_level} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
        <Card title="Synthetic portfolio: risk rules vs injected anomalies">
          {portfolio ? (
            <>
              <div className="kpis small">
                <Kpi label="Portfolio claims" value={portfolio.claims} />
                <Kpi label="Injected anomalies" value={portfolio.injected_anomalies} />
                <Kpi label="Precision" value={`${(portfolio.precision * 100).toFixed(1)}%`} />
                <Kpi label="Recall" value={`${(portfolio.recall * 100).toFixed(1)}%`} />
              </div>
              <Bars data={portfolio.by_risk} />
              <p className="muted small">{portfolio.note} Confusion: TP {portfolio.confusion.tp}, FP {portfolio.confusion.fp}, FN {portfolio.confusion.fn}, TN {portfolio.confusion.tn}.</p>
            </>
          ) : <p className="muted">Portfolio file not found.</p>}
        </Card>
      </div>
    </>
  );
}

const rate = (r: number | null, n: number, d: number) => (r === null ? "—" : `${Math.round(r * 100)}% (${n}/${d})`);

function Kpi({ label, value, tone }: { label: string; value: string | number; tone?: string }) {
  return <div className={`kpi ${tone ?? ""}`}><span>{label}</span><strong>{value}</strong></div>;
}
