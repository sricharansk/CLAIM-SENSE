import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, AnalysisResult, ClaimDetail as Detail, api, inr, when, words } from "../api";
import { useSession } from "../components/session";
import { Badge, Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function ClaimDetail() {
  const { claimNumber = "" } = useParams();
  const { user } = useSession();
  const claim = useLoad(() => api.claim(claimNumber), [claimNumber]);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [doc, setDoc] = useState<{ filename: string; text: string } | null>(null);

  if (claim.loading && !claim.data) return <Loading />;
  if (!claim.data) return <ErrorBox error={claim.error} onRetry={claim.reload} />;
  const c = claim.data;
  const r = c.analysis?.result ?? null;
  const closed = c.status === "APPROVED" || c.status === "REJECTED" || !user.can_write;

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label); setError(null);
    try { await fn(); claim.reload(); } catch (e) { setError(e as ApiError); } finally { setBusy(""); }
  };

  return (
    <>
      <header className="page-head">
        <div>
          <Link to="/claims" className="muted">← Claims</Link>
          <h1>{c.claim_number} <Badge value={c.status} /></h1>
          <p className="muted">{words(c.claim_type)} claim · {c.claimant_name} · policy <span className="mono">{c.policy_number}</span> · incident {c.incident_date ?? "unknown"} · claimed {inr(c.claimed_amount)}</p>
        </div>
        <div className="row">
          {!closed && <label className="btn">Upload documents
            <input hidden type="file" multiple accept=".pdf,.txt,.md" onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              if (files.length) run("Uploading…", () => api.upload(c.claim_number, files));
            }} />
          </label>}
          {!closed && <button className="btn primary" disabled={!!busy || !c.documents.length}
            onClick={() => run("Running agents…", () => api.analyze(c.claim_number))}>
            {c.analysis ? "Re-run analysis" : "Run AI analysis"}</button>}
        </div>
      </header>
      {busy && <div className="notice">{busy}</div>}
      <ErrorBox error={error} />
      {c.analysis?.status === "FAILED" && <div className="error">Analysis stopped safely: {c.analysis.error}</div>}

      {r && <Recommendation r={r} />}
      {r && <ReviewPanel claim={c} r={r} disabled={closed} onDone={claim.reload} />}

      <div className="grid2">
        {c.analysis && <Card title={`Agent pipeline · run ${c.analysis.run_id}`} actions={<span className="mono muted small">{c.analysis.correlation_id}</span>}>
          <ol className="pipeline">
            {c.analysis.agents.map((a, i) => (
              <li key={i}>
                <div className="row between"><strong>{a.agent}</strong><span><Badge value={a.status} /> <span className="muted small">{a.duration_ms} ms</span></span></div>
                <div>{a.summary}</div>
                {a.tool_calls.length > 0 && <details><summary className="muted small">{a.tool_calls.length} tool call(s)</summary>
                  <ul className="small mono">{a.tool_calls.map((t, j) => <li key={j}>{t.tool}({JSON.stringify(t.args)}) → {t.result}</li>)}</ul></details>}
              </li>
            ))}
          </ol>
        </Card>}
        <Card title="Documents">
          <table>
            <thead><tr><th>File</th><th>Type</th><th>Pages</th><th>Uploaded</th></tr></thead>
            <tbody>{c.documents.map((d) => (
              <tr key={d.id}>
                <td><button className="link" onClick={async () => setDoc(await api.document(c.claim_number, d.id))}>{d.filename}</button></td>
                <td><Badge value={d.doc_type} /></td><td>{d.pages}</td><td>{when(d.uploaded_at)}</td>
              </tr>))}
              {!c.documents.length && <tr><td colSpan={4} className="muted">No documents yet. Upload the claim form and bill or estimate.</td></tr>}
            </tbody>
          </table>
          {doc && <div className="doc-view"><div className="row between"><strong>{doc.filename}</strong><button className="btn small" onClick={() => setDoc(null)}>Close</button></div><pre>{doc.text}</pre></div>}
        </Card>
      </div>

      {r && <>
        <div className="grid2">
          <Card title={<>Coverage <Badge value={r.coverage.status} /></>}>
            <p className="muted small">{r.policy.product_name} v{r.policy.version} (in force {r.policy.effective_from} to {r.policy.effective_to}) · sum insured {inr(r.policy.sum_insured)} · cover since {r.policy.start_date}</p>
            <ul className="checks">{r.coverage.findings.map((f, i) => (
              <li key={i}><Badge value={f.outcome} /> <strong>{words(f.code)}</strong>: {f.message}
                {f.citation && <Cite c={f.citation} />}</li>))}
            </ul>
          </Card>
          <Card title={<>Risk <Badge value={r.risk.level} /> <span className="muted small">score {r.risk.score}/100</span></>}>
            {r.risk.signals.length ? <ul className="checks">{r.risk.signals.map((s) => <li key={s.code}><span className="badge gray">+{s.weight}</span> <strong>{words(s.code)}</strong>: {s.message}</li>)}</ul>
              : <p className="muted">No risk signals fired.</p>}
            <p className="muted small">{r.risk.rules_version}. A risk score never decides a claim on its own.</p>
          </Card>
        </div>
        <Card title="Adjudication waterfall" actions={<span className="muted small">{r.adjudication.rules_version} · deterministic, no LLM arithmetic</span>}>
          <table>
            <thead><tr><th>Rule</th><th>Step</th><th className="num">Adjustment</th><th className="num">Running total</th><th>Clause</th><th>Detail</th></tr></thead>
            <tbody>{r.adjudication.waterfall.map((s, i) => (
              <tr key={i} className={Number(s.adjustment) < 0 ? "neg" : ""}>
                <td className="mono small">{s.rule_id}</td><td>{s.label}</td>
                <td className="num">{i === 0 ? inr(s.adjustment) : Number(s.adjustment) === 0 ? "—" : inr(s.adjustment)}</td>
                <td className="num">{inr(s.running_total)}</td><td>{s.clause_ref ? `§${s.clause_ref}` : "—"}</td><td className="muted small">{s.detail}</td>
              </tr>))}
              <tr className="total"><td /><td>Payable amount</td><td /><td className="num">{inr(r.adjudication.payable_amount)}</td><td /><td /></tr>
            </tbody>
          </table>
        </Card>
        <div className="grid2">
          <Card title="Extracted claim facts">
            <table>
              <thead><tr><th>Fact</th><th>Value</th><th>Source</th></tr></thead>
              <tbody>{Object.entries(r.facts).filter(([k]) => k !== "distinct_names").map(([k, v]) => {
                const f = c.facts.find((x) => x.name === k);
                const d = f && c.documents.find((x) => x.id === f.document_id);
                return <tr key={k}><td>{words(k)}</td><td>{String(v)}</td><td className="muted small">{d ? `${d.filename} line ${f!.line} · ${(f!.confidence * 100).toFixed(0)}%` : "claim header"}</td></tr>;
              })}</tbody>
            </table>
          </Card>
          <Card title="Line items">
            <table>
              <thead><tr><th>Item</th><th>Category</th><th className="num">Amount</th></tr></thead>
              <tbody>{r.line_items.map((li, i) => <tr key={i}><td>{li.description}<div className="muted small">{li.source.document_type} line {li.source.line}</div></td><td><Badge value={li.category} /></td><td className="num">{inr(li.amount)}</td></tr>)}</tbody>
            </table>
          </Card>
        </div>
        <Card title={`Evidence package (${r.evidence.length})`}>
          <ul className="evidence">{r.evidence.map((e, i) => (
            <li key={i}><Badge value={e.kind} /> <strong>{words(e.used_for)}</strong>: {e.finding}
              {e.kind !== "claim_fact" ? <Cite c={e as never} /> : <div className="muted small">{String(e.text)} ({String(e.document_type)} line {String(e.line)})</div>}
            </li>))}
          </ul>
        </Card>
      </>}

      <div className="grid2">
        <Card title="Decisions">
          {c.decisions.length ? <ul className="timeline">{c.decisions.map((d) => (
            <li key={d.id}><Badge value={d.decision} /> <strong>{d.source === "AI" ? "AI recommendation" : `Reviewer ${d.actor}`}</strong> · {inr(d.payable_amount)} · <span className="muted small">{when(d.created_at)}</span>
              {d.notes && <div className="small">{d.notes}</div>}</li>))}</ul> : <p className="muted">No decisions yet.</p>}
          {c.workflow_task && <p className="small">Workflow: <Badge value={c.workflow_task.queue} /> {c.workflow_task.priority} priority · {words(c.workflow_task.status)}{c.workflow_task.assignee ? ` · ${c.workflow_task.assignee}` : ""}</p>}
        </Card>
        <Card title="Audit trail">
          <ul className="timeline">{c.audit.map((e) => (
            <li key={e.id}><strong>{words(e.event_type)}</strong> · {e.actor} · <span className="muted small">{when(e.created_at)}</span>
              <div className="muted small mono">{JSON.stringify(e.details)}</div></li>))}</ul>
        </Card>
      </div>
    </>
  );
}

function Recommendation({ r }: { r: AnalysisResult }) {
  const rec = r.recommendation;
  return (
    <section className={`card recommendation ${rec.decision}`}>
      <div className="rec-main">
        <div>
          <span className="muted small">AI recommendation · requires human review</span>
          <h2><Badge value={rec.decision} /> {rec.label}</h2>
          <p>{rec.summary}</p>
          <ul>{rec.reasons.map((x, i) => <li key={i}>{x}</li>)}</ul>
        </div>
        <div className="amounts">
          <div><span>Claimed</span><strong>{inr(r.adjudication.claimed_amount)}</strong></div>
          <div><span>Billed</span><strong>{inr(r.adjudication.gross_billed)}</strong></div>
          <div className="pay"><span>Payable</span><strong>{inr(r.adjudication.payable_amount)}</strong></div>
        </div>
      </div>
    </section>
  );
}

const ACTIONS = [["APPROVE", "Approve"], ["REJECT", "Reject"], ["REQUEST_INFO", "Request info"], ["INVESTIGATE", "Investigate"], ["ESCALATE", "Escalate"]];

function ReviewPanel({ claim, r, disabled, onDone }: { claim: Detail; r: AnalysisResult; disabled: boolean; onDone: () => void }) {
  const { user } = useSession();
  const [notes, setNotes] = useState("");
  const [amount, setAmount] = useState(r.adjudication.payable_amount);
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  if (disabled) return null;
  const overLimit = user.approval_limit !== null && Number(amount) > Number(user.approval_limit);
  const escalated = claim.status === "ESCALATED" && !user.is_supervisor;
  const act = async (action: string) => {
    setBusy(true); setError(null);
    try {
      await api.review(claim.claim_number, { action, notes, ...(action === "APPROVE" ? { payable_amount: amount } : {}) });
      setNotes(""); onDone();
    } catch (e) { setError(e as ApiError); } finally { setBusy(false); }
  };
  return (
    <Card title="Human review">
      <div className="form">
        <label>Reviewer<input value={`${user.display_name} (${user.role.toLowerCase()})`} disabled /></label>
        <label>Approved amount (₹)<input type="number" min={0} step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} /></label>
        <label className="wide">Notes (required to reject, investigate or escalate)<textarea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} /></label>
        {escalated && <div className="wide notice">This claim is escalated. A supervisor must decide it.</div>}
        {!escalated && overLimit && <div className="wide notice">₹{Number(amount).toLocaleString("en-IN")} is above your approval limit of ₹{Number(user.approval_limit).toLocaleString("en-IN")}. Escalate it to a supervisor, with a note.</div>}
        <div className="wide row">{ACTIONS.map(([a, label]) => <button key={a} className={`btn ${a === "APPROVE" ? "primary" : a === "REJECT" ? "danger" : ""}`}
          disabled={busy || escalated || (a === "APPROVE" && overLimit)} onClick={() => act(a)}>{label}</button>)}</div>
        <ErrorBox error={error} />
      </div>
    </Card>
  );
}

function Cite({ c }: { c: { product_code: string; version: string; clause_ref: string; page: number; title: string; text: string; document: string } }) {
  return (
    <details className="cite">
      <summary>{c.product_code} v{c.version} §{c.clause_ref} “{c.title}”, p.{c.page}</summary>
      <blockquote>{c.text}<footer className="muted small">{c.document}</footer></blockquote>
    </details>
  );
}
