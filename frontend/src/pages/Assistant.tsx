import { FormEvent, useState } from "react";
import { ApiError, RagAnswer, api } from "../api";
import { Badge, Card, ErrorBox, useLoad } from "../components/ui";

const EXAMPLES = ["Is cataract surgery covered in the first year?", "What is the room rent limit per day?",
  "How much depreciation applies to plastic parts?", "Is drunk driving covered?", "What documents are needed for a hospital claim?"];

export default function Assistant() {
  const policies = useLoad(api.policies);
  const [q, setQ] = useState("");
  const [product, setProduct] = useState("");
  const [version, setVersion] = useState("");
  const [ans, setAns] = useState<RagAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const ask = async (question: string, e?: FormEvent) => {
    e?.preventDefault();
    setQ(question); setBusy(true); setError(null);
    try { setAns(await api.ask(question, product, version)); } catch (err) { setError(err as ApiError); } finally { setBusy(false); }
  };
  const versions = policies.data?.find((p) => p.product_code === product)?.versions ?? [];
  return (
    <>
      <header className="page-head"><div><h1>Policy knowledge assistant</h1><p className="muted">Hybrid retrieval (BM25 + n-gram vectors) over policy clauses. Answers quote the wording and cite clause and page, or refuse.</p></div></header>
      <Card>
        <form className="ask" onSubmit={(e) => ask(q, e)}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about coverage, exclusions, limits or claim procedure" />
          <select value={product} onChange={(e) => { setProduct(e.target.value); setVersion(""); }}>
            <option value="">All policies</option>{policies.data?.map((p) => <option key={p.product_code} value={p.product_code}>{p.product_code}</option>)}
          </select>
          <select value={version} onChange={(e) => setVersion(e.target.value)} disabled={!product}>
            <option value="">All versions</option>{versions.map((v) => <option key={v.id} value={v.version}>v{v.version}</option>)}
          </select>
          <button className="btn primary" disabled={busy || q.trim().length < 3}>{busy ? "Searching…" : "Ask"}</button>
        </form>
        <div className="chips">{EXAMPLES.map((x) => <button key={x} className="chip" onClick={() => ask(x)}>{x}</button>)}</div>
        <ErrorBox error={error} />
      </Card>
      {ans && (
        <Card title={<>{ans.grounded ? <Badge value="PASS" /> : <Badge value="UNCERTAIN" />} {ans.grounded ? `Grounded answer (${ans.mode})` : "No sufficient evidence"}</>}>
          <p className="answer">{ans.answer}</p>
          <h4>{ans.grounded ? "Citations" : "Closest clauses (below the relevance threshold)"}</h4>
          <ol className="citations">{ans.citations.map((c) => (
            <li key={c.clause_id}>
              <strong>{c.product_code} v{c.version} §{c.clause_ref} {c.title}</strong> <span className="muted small">· {c.section} · page {c.page} · score {c.score} · BM25 rank {c.bm25_rank ?? "—"} · vector rank {c.vector_rank ?? "—"}</span>
              <blockquote>{c.text}</blockquote>
            </li>))}</ol>
        </Card>
      )}
    </>
  );
}
