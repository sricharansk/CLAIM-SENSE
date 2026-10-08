import { Link } from "react-router-dom";
import { api, when, words } from "../api";
import { Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function AuditLog() {
  const a = useLoad(() => api.audit());
  return (
    <>
      <header className="page-head"><h1>Audit trail</h1></header>
      <Card title="Latest 100 events (append-only)">
        <ErrorBox error={a.error} onRetry={a.reload} />
        {a.loading && !a.data ? <Loading /> : (
          <table>
            <thead><tr><th>When</th><th>Event</th><th>Claim</th><th>Actor</th><th>Details</th><th>Correlation</th></tr></thead>
            <tbody>{a.data?.map((e) => (
              <tr key={e.id}>
                <td className="small">{when(e.created_at)}</td><td>{words(e.event_type)}</td>
                <td>{e.claim_number ? <Link to={`/claims/${e.claim_number}`}>{e.claim_number}</Link> : "—"}</td>
                <td>{e.actor}</td><td className="mono small details">{JSON.stringify(e.details)}</td><td className="mono small">{e.correlation_id ?? "—"}</td>
              </tr>))}</tbody>
          </table>)}
      </Card>
    </>
  );
}
