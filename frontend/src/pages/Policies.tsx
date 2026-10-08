import { FormEvent, useState } from "react";
import { ApiError, api } from "../api";
import { useSession } from "../components/session";
import { Card, ErrorBox, Loading, useLoad } from "../components/ui";

export default function Policies() {
  const { user } = useSession();
  const list = useLoad(api.policies);
  const [code, setCode] = useState("");
  const selected = code || list.data?.[0]?.product_code || "";
  const versions = useLoad(() => (selected ? api.versions(selected) : Promise.resolve([])), [selected]);
  const [vid, setVid] = useState<number | null>(null);
  const version = versions.data?.find((v) => v.id === vid) ?? versions.data?.[versions.data.length - 1];
  const [filter, setFilter] = useState("");
  const [files, setFiles] = useState<{ wording?: File; terms?: File }>({});
  const [msg, setMsg] = useState("");
  const [error, setError] = useState<ApiError | null>(null);

  const upload = async (e: FormEvent) => {
    e.preventDefault();
    if (!files.wording || !files.terms) return;
    setError(null);
    try {
      const r = await api.uploadPolicy(files.wording, files.terms);
      setMsg(`Ingested ${r.product_code} v${r.version}: ${r.clauses} clauses indexed.`);
      list.reload();
    } catch (err) { setError(err as ApiError); }
  };

  if (list.loading && !list.data) return <Loading />;
  return (
    <>
      <header className="page-head"><h1>Policy library</h1></header>
      <ErrorBox error={list.error} onRetry={list.reload} />
      <div className="grid3">
        {list.data?.map((p) => (
          <button key={p.product_code} className={`card select ${p.product_code === selected ? "active" : ""}`} onClick={() => { setCode(p.product_code); setVid(null); }}>
            <strong>{p.name}</strong>
            <span className="muted small">{p.product_code} · {p.line_of_business} · {p.insurer}</span>
            <span className="small">{p.versions.map((v) => `v${v.version} (${v.effective_from} → ${v.effective_to}, ${v.clauses} clauses)`).join(" · ")}</span>
          </button>
        ))}
      </div>
      {version && (
        <Card title={`${selected} wording`} actions={
          <div className="row">
            <select value={version.id} onChange={(e) => setVid(Number(e.target.value))}>
              {versions.data?.map((v) => <option key={v.id} value={v.id}>v{v.version}</option>)}
            </select>
            <input placeholder="Filter clauses" value={filter} onChange={(e) => setFilter(e.target.value)} />
          </div>}>
          <div className="clauses">
            {version.clauses.filter((c) => !filter || `${c.title} ${c.text}`.toLowerCase().includes(filter.toLowerCase())).map((c) => (
              <article key={c.id}><h4>§{c.clause_ref} {c.title} <span className="muted small">· {c.section} · page {c.page}</span></h4><p>{c.text}</p></article>
            ))}
          </div>
          <details><summary className="muted">Structured terms used by the rules engine</summary><pre>{JSON.stringify(version.terms, null, 2)}</pre></details>
        </Card>
      )}
      {user.is_supervisor ? <Card title="Ingest a policy wording">
        <form className="form" onSubmit={upload}>
          <label>Wording (.md with “## N. Section” and “### N.M Clause” headings)<input type="file" accept=".md,.txt" onChange={(e) => setFiles({ ...files, wording: e.target.files?.[0] })} /></label>
          <label>Structured terms (.json)<input type="file" accept=".json" onChange={(e) => setFiles({ ...files, terms: e.target.files?.[0] })} /></label>
          <div className="wide row"><button className="btn primary" disabled={!files.wording || !files.terms}>Ingest and index</button>{msg && <span className="ok-text">{msg}</span>}</div>
          <ErrorBox error={error} />
        </form>
      </Card> : <p className="muted small">Supervisors can ingest new policy wordings.</p>}
    </>
  );
}
