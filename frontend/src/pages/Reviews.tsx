import { Link } from "react-router-dom";
import { api, inr, when } from "../api";
import { Badge, Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function Reviews() {
  const q = useLoad(api.reviews);
  return (
    <>
      <header className="page-head"><h1>Review queue</h1></header>
      <Card title="Open tasks, highest priority first">
        <ErrorBox error={q.error} onRetry={q.reload} />
        {q.loading && !q.data ? <Loading /> : (
          <table>
            <thead><tr><th>Priority</th><th>Queue</th><th>Claim</th><th>Claimant</th><th>Claimed</th><th>AI recommendation</th><th>AI payable</th><th>Since</th></tr></thead>
            <tbody>{q.data?.map((t) => (
              <tr key={t.task_id}>
                <td><Badge value={t.priority === "NORMAL" ? "LOW" : t.priority} /></td><td>{t.queue.replace(/_/g, " ").toLowerCase()}</td>
                <td><Link to={`/claims/${t.claim_number}`}>{t.claim_number}</Link></td><td>{t.claimant_name}</td>
                <td>{inr(t.claimed_amount)}</td><td><Badge value={t.recommendation} /></td><td>{inr(t.recommended_payable)}</td><td>{when(t.created_at)}</td>
              </tr>))}
              {q.data?.length === 0 && <tr><td colSpan={8} className="muted">Queue is empty.</td></tr>}
            </tbody>
          </table>)}
      </Card>
    </>
  );
}
