import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Analytics, api, inr, words } from "../api";
import { useSession } from "../components/session";
import { Badge, Bars, Card, Due, ErrorBox, Kpi, Loading, Segmented, useLoad } from "../components/ui";

const LINES: [string, string][] = [["", "All lines"], ["health", "Health"], ["motor", "Motor"]];
const PERIODS: [string, string][] = [["", "All time"], ["7", "Last 7 days"], ["30", "Last 30 days"], ["90", "Last 90 days"]];
const OPEN = "PENDING_REVIEW,ESCALATED";
const INTRO_KEY = "claimsense.intro-dismissed";

export default function Dashboard() {
  const { user } = useSession();
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const line = params.get("line") ?? "";
  const days = params.get("days") ?? "";
  const a = useLoad(() => api.analytics({ line, days }), [line, days]);
  const recent = useLoad(() => api.claims({ claim_type: line, days }), [line, days]);
  const [intro, setIntro] = useState(() => { try { return !localStorage.getItem(INTRO_KEY); } catch { return true; } });
  const set = (k: string, v: string) => {
    const p = new URLSearchParams(params);
    if (v) p.set(k, v); else p.delete(k);
    setParams(p, { replace: true });
  };
  // drill-downs keep the dashboard's line and period
  const claimsLink = (extra: Record<string, string>) =>
    `/claims?${new URLSearchParams({ ...(line && { claim_type: line }), ...(days && { days }), ...extra })}`;
  const dismiss = () => { setIntro(false); try { localStorage.setItem(INTRO_KEY, "1"); } catch { /* storage unavailable */ } };

  return (
    <>
      <header className="page-head">
        <div>
          <h1>Claims intelligence dashboard</h1>
          <p className="muted">Claim Sense: RAG-Based Insurance Claims Adjudication &amp; Policy Knowledge Assistant</p>
        </div>
        <div className="row">
          <Link className="btn" to="/guide">How to use</Link>
          {user.can_write && <Link className="btn primary" to="/claims/new">New claim</Link>}
        </div>
      </header>
      {intro && (
        <div className="notice row between">
          <span>New here? The <Link to="/guide">guide</Link> walks through a claim from upload to decision in about ten minutes.
            Click any tile or bar below to open the claims behind it.</span>
          <button className="btn small" onClick={dismiss}>Dismiss</button>
        </div>
      )}
      <div className="toolbar">
        <Segmented label="Line of business" options={LINES} value={line} onChange={(v) => set("line", v)} />
        <Segmented label="Filed in" options={PERIODS} value={days} onChange={(v) => set("days", v)} />
        {a.data && <span className="muted small">{a.data.totals.claims} claims{line ? ` · ${line}` : ""}{days ? ` · filed in the last ${days} days` : ""}</span>}
      </div>
      {a.loading && !a.data ? <Loading /> : !a.data ? <ErrorBox error={a.error} onRetry={a.reload} /> : (
        <Body a={a.data} claimsLink={claimsLink} />
      )}
      <Card title="Recent claims" actions={<Link to={claimsLink({})}>All matching claims</Link>}>
        <table className="clickable">
          <thead><tr><th>Claim</th><th>Line</th><th>Claimant</th><th className="num">Claimed</th><th className="num">AI payable</th><th>Recommendation</th><th>Risk</th><th>Status</th><th>Settlement</th></tr></thead>
          <tbody>
            {(recent.data ?? []).slice(0, 8).map((c) => (
              <tr key={c.claim_number} onClick={() => nav(`/claims/${c.claim_number}`)}>
                <td className="nowrap"><Link to={`/claims/${c.claim_number}`}>{c.claim_number}</Link></td>
                <td>{c.claim_type}</td><td>{c.claimant_name}</td><td className="num">{inr(c.claimed_amount)}</td><td className="num">{inr(c.recommended_payable)}</td>
                <td><Badge value={c.recommendation} /></td><td><Badge value={c.risk_level} /></td><td><Badge value={c.status} /></td><td><Due s={c.settlement} /></td>
              </tr>
            ))}
            {recent.data?.length === 0 && <tr><td colSpan={9} className="muted">No claims in this selection.</td></tr>}
          </tbody>
        </table>
      </Card>
      <Portfolio p={a.data?.portfolio ?? null} />
    </>
  );
}

function Body({ a, claimsLink }: { a: Analytics; claimsLink: (extra: Record<string, string>) => string }) {
  const { totals, human_vs_ai: h } = a;
  return (
    <>
      <div className="kpis">
        <Kpi label="Claims" value={totals.claims} to={claimsLink({})} />
        <Kpi label="Pending human review" value={totals.pending_review} to={claimsLink({ status: OPEN })} />
        <Kpi label="High risk" value={totals.high_risk} tone="red" to={claimsLink({ risk: "HIGH" })} />
        <Kpi label="Settlement overdue / breached" value={totals.overdue} tone={totals.overdue ? "red" : undefined}
          to={claimsLink({ settlement: "OVERDUE,BREACHED" })} />
        <Kpi label="Decided by reviewers" value={totals.decided} to={claimsLink({ status: "APPROVED,REJECTED" })} />
        <Kpi label="Claimed" value={inr(totals.claimed_amount)} />
        <Kpi label="AI-recommended payable" value={inr(totals.recommended_payable)} />
        <Kpi label="Approved by reviewers" value={inr(totals.approved_amount)} tone="green" />
        <Kpi label="Avg. days to decision" value={totals.avg_days_to_decision ?? "—"} />
        <Kpi label="Avg. analysis time" value={totals.avg_analysis_ms !== null ? `${totals.avg_analysis_ms} ms` : "—"} />
        <Kpi label="Override rate (reviewer vs AI)" value={rate(h.override_rate, h.overridden, h.decided)} />
        <Kpi label="Escalation rate" value={rate(h.escalation_rate, h.escalated, h.reviewed)} />
      </div>
      <div className="grid2 wide-left">
        <Card title="Weekly activity" actions={<span className="legend"><i className="filed" /> Filed <i className="decided" /> Decided</span>}>
          <Trend weeks={a.trend} />
        </Card>
        <Card title="Needs attention" actions={<Link to="/reviews">Go to tasks</Link>}>
          {a.attention.length === 0 ? <p className="muted">Nothing overdue, escalated or high risk in this selection.</p> : (
            <ul className="attention">
              {a.attention.map((r) => (
                <li key={r.claim_number}>
                  <Link to={`/claims/${r.claim_number}`}><strong>{r.claim_number}</strong></Link>
                  <span className="muted small"> {r.claimant_name} · {r.claim_type} · {inr(r.claimed_amount)} · filed {r.age_days}d ago</span>
                  <div className="chips">{r.reasons.map((x) => <span key={x} className={`tag ${x.startsWith("High") || x.includes("overdue") ? "red" : "amber"}`}>{x}</span>)}</div>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
      <div className="grid3">
        <Card title="AI recommendations">
          <Bars data={a.by_recommendation} link={(k) => claimsLink({ recommendation: k })} />
          <h4>Reviewer actions</h4><Bars data={a.human_outcomes} />
          {h.amount_overridden > 0 && <p className="muted small">{h.amount_overridden} approval{h.amount_overridden === 1 ? "" : "s"} at an amount other than the AI's.</p>}
        </Card>
        <Card title="Risk levels">
          <Bars data={a.by_risk} link={(k) => claimsLink({ risk: k })} />
          <h4>Most common risk signals</h4><Bars data={a.risk_signals} />
        </Card>
        <Card title="Claim status">
          <Bars data={a.by_status} link={(k) => claimsLink({ status: k })} />
          <h4>Settlement clock</h4><Bars data={a.settlement} link={(k) => claimsLink({ settlement: k })} />
        </Card>
      </div>
      <div className="grid3">
        <Card title="Open claims by age"><Bars data={a.ageing} keepOrder plain /></Card>
        <Card title="Why claims are declined or held">
          {a.top_reasons.length === 0 ? <p className="muted">No failing or missing checks in this selection.</p> : (
            <table>
              <tbody>
                {a.top_reasons.map((r) => (
                  <tr key={r.code}><td>{reason(r.code)}</td><td>{r.clause_ref ? <span className="mono small">§{r.clause_ref}</span> : "—"}</td><td className="num">{r.count}</td></tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
        <Card title="Work queues" actions={<Link to="/reviews">Open queue</Link>}>
          <Bars data={a.queues} />
          <h4>Open tasks by assignee</h4><Bars data={a.workload} plain />
        </Card>
      </div>
      <Card title="Amounts by line of business">
        <table>
          <thead><tr><th>Line</th><th className="num">Claims</th><th className="num">Claimed</th><th className="num">AI-recommended payable</th><th className="num">Approved by reviewers</th></tr></thead>
          <tbody>
            {Object.entries(a.by_line_amounts).filter(([, v]) => v.claims > 0).map(([k, v]) => (
              <tr key={k}><td><Link to={`/claims?claim_type=${k}`}>{words(k)}</Link></td><td className="num">{v.claims}</td>
                <td className="num">{inr(v.claimed)}</td><td className="num">{inr(v.ai_payable)}</td><td className="num">{inr(v.approved)}</td></tr>
            ))}
          </tbody>
        </table>
      </Card>
    </>
  );
}

function Trend({ weeks }: { weeks: Analytics["trend"] }) {
  const top = Math.max(1, ...weeks.flatMap((w) => [w.filed, w.decided]));
  const max = Math.ceil(top / 2) * 2; // even, so the middle gridline is a whole number
  const W = 560, H = 190, pad = 26, slot = (W - pad) / weeks.length, bar = Math.min(18, slot / 3);
  const y = (v: number) => H - 22 - (v / max) * (H - 40);
  const label = (d: string) => new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
  return (
    <svg className="trend" viewBox={`0 0 ${W} ${H}`} role="img"
      aria-label={`Claims filed and decided per week: ${weeks.map((w) => `${label(w.week)} ${w.filed} filed, ${w.decided} decided`).join("; ")}`}>
      {[0, 0.5, 1].map((f) => (
        <g key={f}><line x1={pad} x2={W} y1={y(max * f)} y2={y(max * f)} className="grid" />
          <text x={pad - 6} y={y(max * f) + 4} textAnchor="end" className="axis">{Math.round(max * f)}</text></g>
      ))}
      {weeks.map((w, i) => {
        const x = pad + i * slot + slot / 2;
        return (
          <g key={w.week}>
            <rect x={x - bar - 1} y={y(w.filed)} width={bar} height={H - 22 - y(w.filed)} className="filed" rx={3}>
              <title>{`Week of ${label(w.week)}: ${w.filed} filed (${inr(w.claimed)} claimed)`}</title></rect>
            <rect x={x + 1} y={y(w.decided)} width={bar} height={H - 22 - y(w.decided)} className="decided" rx={3}>
              <title>{`Week of ${label(w.week)}: ${w.decided} decided (${inr(w.approved)} approved)`}</title></rect>
            <text x={x} y={H - 6} textAnchor="middle" className="axis">{label(w.week)}</text>
          </g>
        );
      })}
    </svg>
  );
}

function Portfolio({ p }: { p: Analytics["portfolio"] }) {
  return (
    <Card title="Synthetic portfolio: risk rules vs injected anomalies">
      {p ? (
        <>
          <div className="kpis small">
            <Kpi label="Portfolio claims" value={p.claims} />
            <Kpi label="Injected anomalies" value={p.injected_anomalies} />
            <Kpi label="Precision" value={`${(p.precision * 100).toFixed(1)}%`} />
            <Kpi label="Recall" value={`${(p.recall * 100).toFixed(1)}%`} />
          </div>
          <Bars data={p.by_risk} />
          <p className="muted small">{p.note} Confusion: TP {p.confusion.tp}, FP {p.confusion.fp}, FN {p.confusion.fn}, TN {p.confusion.tn}.</p>
        </>
      ) : <p className="muted">Portfolio file not found.</p>}
    </Card>
  );
}

// EXCL_DUI -> "Exclusion: DUI", EXCL_COSMETIC -> "Exclusion: cosmetic"
const reason = (code: string) => {
  if (!code.startsWith("EXCL_")) return words(code);
  const what = code.slice(5).replace(/_/g, " ");
  return `Exclusion: ${what.length <= 3 ? what : what.toLowerCase()}`;
};

const rate = (r: number | null, n: number, d: number) => (r === null ? "—" : `${Math.round(r * 100)}% (${n}/${d})`);
