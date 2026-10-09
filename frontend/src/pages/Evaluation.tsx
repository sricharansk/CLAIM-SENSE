import { Fragment, useState } from "react";
import { Link } from "react-router-dom";
import { EvalCheck, api, inr, words } from "../api";
import { Badge, Card, ErrorBox, Loading, useLoad } from "../components/ui";

const pct = (v: number | null | undefined) => (v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`);
const show = (v: unknown) => (typeof v === "string" ? v : JSON.stringify(v));

function Checks({ checks }: { checks: EvalCheck[] }) {
  return (
    <table className="checks">
      <thead><tr><th>Dimension</th><th>Check</th><th>Expected</th><th>Actual</th><th></th></tr></thead>
      <tbody>{checks.map((c, i) => (
        <tr key={i}>
          <td>{words(c.dimension)}</td><td>{c.check}</td>
          <td className="mono small details">{show(c.expected)}</td><td className="mono small details">{show(c.actual)}</td>
          <td><Badge value={c.passed ? "PASS" : "FAIL"} /></td>
        </tr>))}</tbody>
    </table>
  );
}

export default function EvaluationPage() {
  const r = useLoad(api.evaluation);
  const [open, setOpen] = useState<string | null>(null);
  const e = r.data;
  const toggle = (id: string) => setOpen(open === id ? null : id);
  return (
    <>
      <header className="page-head"><div><h1>Golden evaluation</h1>
        <p className="muted">Hand-worked expected outcomes compared with what the running system produces. Regenerate with <span className="mono">python scripts/evaluate.py</span>; CI fails if any check fails.</p></div></header>
      <ErrorBox error={r.error} onRetry={r.reload} />
      {r.loading && !e ? <Loading /> : e && (
        <>
          <div className="kpis">
            <div className={`kpi ${e.summary.all_passed ? "" : "red"}`}><span>Checks passed</span><strong>{e.summary.checks_passed} / {e.summary.checks}</strong></div>
            <div className="kpi"><span>Claim cases</span><strong>{e.summary.claim_cases_passed} / {e.summary.claim_cases}</strong></div>
            <div className="kpi"><span>Policy questions</span><strong>{e.summary.questions_passed} / {e.summary.questions}</strong></div>
            <div className="kpi"><span>Retrieval hit@1</span><strong>{pct(e.summary.retrieval_hit_at_1)}</strong></div>
            <div className="kpi"><span>Mean reciprocal rank</span><strong>{e.summary.mean_reciprocal_rank.toFixed(2)}</strong></div>
            <div className="kpi"><span>Correct refusals</span><strong>{pct(e.summary.refusal_accuracy)}</strong></div>
          </div>
          <div className="grid2">
            <Card title="Scorecard by dimension">
              <div className="bars">{Object.entries(e.dimensions).map(([k, d]) => (
                <div key={k} className="bar-row">
                  <span className="bar-label">{d.label}</span>
                  <span className="bar-track"><span className="bar-fill" style={{ width: `${(d.score ?? 0) * 100}%` }} /></span>
                  <span className="bar-value">{d.passed}/{d.total}</span>
                </div>))}</div>
              <p className="muted small">Run {new Date(e.generated_at).toLocaleString()} · {e.rules_version} · {e.risk_version} · LLM {e.llm} · {e.data}</p>
            </Card>
            <Card title="Required case types">
              <table><tbody>{Object.entries(e.categories).map(([k, ids]) => (
                <tr key={k}><td>{words(k)}</td><td>{ids.length ? ids.join(", ") : <Badge value="MISSING" />}</td></tr>))}</tbody></table>
            </Card>
          </div>
          <Card title="Claim cases">
            <table>
              <thead><tr><th>Case</th><th>Claim</th><th>What it tests</th><th>Recommendation</th><th>Payable (expected / actual)</th><th>Result</th></tr></thead>
              <tbody>{e.claims.map((c) => (
                <Fragment key={c.id}>
                  <tr>
                    <td><button className="link" onClick={() => toggle(c.id)}>{open === c.id ? "▾" : "▸"} {c.id}</button></td>
                    <td>{c.source === "seeded scenario" ? <Link to={`/claims/${c.claim_number}`}>{c.claim_number}</Link> : <>{c.packet}<div className="muted small">fresh packet, created by the run</div></>}</td>
                    <td>{c.title}<div className="muted small">{c.categories.map(words).join(" · ")}</div></td>
                    <td><Badge value={c.actual.recommendation} /></td>
                    <td>{inr(c.expected.payable_amount)} / {inr(c.actual.payable_amount)}</td>
                    <td><Badge value={c.passed ? "PASS" : "FAIL"} /></td>
                  </tr>
                  {open === c.id && <tr><td colSpan={6}>
                    {c.working && <p className="small"><strong>Worked by hand:</strong> {c.working}</p>}
                    <Checks checks={c.checks} />
                  </td></tr>}
                </Fragment>))}</tbody>
            </table>
          </Card>
          <Card title="Policy assistant questions">
            <table>
              <thead><tr><th>Q</th><th>Kind</th><th>Question</th><th>Scope</th><th>Expected / cited</th><th>Result</th></tr></thead>
              <tbody>{e.questions.map((q) => (
                <Fragment key={q.id}>
                  <tr>
                    <td><button className="link" onClick={() => toggle(q.id)}>{open === q.id ? "▾" : "▸"} {q.id}</button></td>
                    <td>{words(q.kind)}</td><td>{q.question}</td><td className="small">{q.scope}</td>
                    <td className="mono small">{q.expected_clause ? `§${q.expected_clause} / §${q.top_citation ?? "—"}` : `refusal / ${q.mode}`}</td>
                    <td><Badge value={q.passed ? "PASS" : "FAIL"} /></td>
                  </tr>
                  {open === q.id && <tr><td colSpan={6}><Checks checks={q.checks} /></td></tr>}
                </Fragment>))}</tbody>
            </table>
          </Card>
        </>
      )}
    </>
  );
}
