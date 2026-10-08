import { api } from "../api";
import { Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function Datasets() {
  const d = useLoad(api.datasets);
  return (
    <>
      <header className="page-head"><div><h1>Data sources and provenance</h1><p className="muted">What this build actually uses, and which public 2024–2026 sources are registered for later ingestion.</p></div></header>
      <Card>
        <ErrorBox error={d.error} onRetry={d.reload} />
        {d.loading && !d.data ? <Loading /> : (
          <table>
            <thead><tr><th>Source</th><th>Publisher</th><th>Year</th><th>Purpose</th><th>Status</th></tr></thead>
            <tbody>{d.data?.map((s) => (
              <tr key={s.name}>
                <td>{s.url.startsWith("http") ? <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : <>{s.name}<div className="mono small muted">{s.url}</div></>}</td>
                <td>{s.publisher}</td><td>{s.year}</td><td>{s.purpose}</td>
                <td><span className={`badge ${s.status.startsWith("IN USE") ? "green" : "gray"}`}>{s.status}</span></td>
              </tr>))}</tbody>
          </table>)}
      </Card>
    </>
  );
}
