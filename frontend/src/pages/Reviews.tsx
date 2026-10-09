import { useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, ReviewTask, api, inr, words } from "../api";
import { useSession } from "../components/session";
import { Badge, Card, Due, ErrorBox, Loading, useLoad } from "../components/ui";

const age = (h: number) => (h < 1 ? `${Math.max(1, Math.round(h * 60))} min` : h < 48 ? `${Math.round(h)} h` : `${Math.round(h / 24)} d`);
type View = "all" | "mine" | "unassigned";

export default function Reviews() {
  const { user } = useSession();
  const q = useLoad(api.reviews);
  const people = useLoad(api.reviewers);
  const [view, setView] = useState<View>("all");
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const tasks = q.data ?? [];
  const views: Record<View, ReviewTask[]> = {
    all: tasks, mine: tasks.filter((t) => t.assignee === user.display_name), unassigned: tasks.filter((t) => !t.assignee),
  };

  const assign = async (t: ReviewTask, username: string | null) => {
    setBusy(t.task_id); setError(null);
    try { await api.assign(t.task_id, username); q.reload(); } catch (e) { setError(e as ApiError); } finally { setBusy(null); }
  };

  const owner = (t: ReviewTask) => {
    const mine = t.assignee === user.display_name;
    const canTake = user.can_write && !t.assignee && (t.queue !== "SUPERVISOR_REVIEW" || user.is_supervisor);
    if (user.is_supervisor && people.data) {
      const current = people.data.find((p) => p.display_name === t.assignee)?.username ?? "";
      return (
        <select aria-label={`Assign ${t.claim_number}`} value={current} disabled={busy === t.task_id}
          onChange={(e) => assign(t, e.target.value || null)}>
          <option value="">Unassigned</option>
          {people.data.map((p) => <option key={p.username} value={p.username}>{p.display_name}</option>)}
        </select>
      );
    }
    return (
      <>
        {t.assignee ?? <span className="muted">Unassigned</span>}{" "}
        {canTake && <button className="btn small" disabled={busy === t.task_id} onClick={() => assign(t, user.username)}>Take</button>}
        {mine && user.can_write && <button className="btn small" disabled={busy === t.task_id} onClick={() => assign(t, null)}>Release</button>}
      </>
    );
  };

  return (
    <>
      <header className="page-head"><div><h1>Review queue</h1>
        <p className="muted">Every AI recommendation waits here for a person. Take a task to work it; a supervisor can reassign.</p></div></header>
      <Card title="Open tasks, highest priority first, oldest first within a priority">
        <nav className="tabs">{(Object.keys(views) as View[]).map((v) => (
          <button key={v} className={view === v ? "active" : ""} onClick={() => setView(v)}>
            {v === "all" ? "All open" : v === "mine" ? "Assigned to me" : "Unassigned"}<span className="count">{views[v].length}</span>
          </button>))}</nav>
        <ErrorBox error={q.error ?? error} onRetry={q.error ? q.reload : undefined} />
        {q.loading && !q.data ? <Loading /> : (
          <table>
            <thead><tr><th>Priority</th><th>Queue</th><th>Claim</th><th>Status</th><th>Risk</th><th>AI recommendation</th><th>AI payable</th><th>Settlement due</th><th>Age</th><th>Assignee</th></tr></thead>
            <tbody>{views[view].map((t) => (
              <tr key={t.task_id}>
                <td><Badge value={t.priority === "NORMAL" ? "LOW" : t.priority} /></td><td>{words(t.queue)}</td>
                <td><Link to={`/claims/${t.claim_number}#review`}>{t.claim_number}</Link><div className="muted small">{t.claimant_name} · {inr(t.claimed_amount)}</div></td>
                <td><Badge value={t.status} /></td><td><Badge value={t.risk_level} /></td>
                <td><Badge value={t.recommendation} /></td><td>{inr(t.recommended_payable)}</td>
                <td><Due s={t.settlement} /> <div className="muted small">{t.settlement.due_date}</div></td>
                <td className="nowrap" title={new Date(t.created_at).toLocaleString()}>{age(t.age_hours)}</td>
                <td className="nowrap">{owner(t)}</td>
              </tr>))}
              {views[view].length === 0 && <tr><td colSpan={10} className="muted">Nothing here.</td></tr>}
            </tbody>
          </table>)}
      </Card>
    </>
  );
}
