import { Fragment, useState } from "react";
import { api, words } from "../api";
import { Badge, Card, ErrorBox, Loading, useLoad } from "../components/ui";

const short = (h: string | null) => (h ? `${h.slice(0, 12)}…` : "—");

export default function Datasets() {
  const d = useLoad(api.datasets);
  const m = useLoad(api.manifest);
  const [open, setOpen] = useState<string | null>(null);
  const reg = d.data, man = m.data;
  const inUse = reg?.sources.filter((s) => s.status === "IN_USE") ?? [];
  return (
    <>
      <header className="page-head"><div><h1>Data sources and provenance</h1>
        <p className="muted">Every source is registered with its publisher, dates, licence and intended use. Sources in use carry a SHA-256 that is checked against the files on every request; every indexed policy chunk traces back to its file, version, page, clause and extraction run.</p></div></header>
      <ErrorBox error={d.error ?? m.error} onRetry={() => { d.reload(); m.reload(); }} />
      {(d.loading && !reg) || (m.loading && !man) ? <Loading /> : reg && man && (
        <>
          <div className="kpis">
            <div className="kpi"><span>Sources registered</span><strong>{reg.sources.length}</strong></div>
            <div className="kpi"><span>In use (synthetic)</span><strong>{inUse.length}</strong></div>
            <div className={`kpi ${inUse.every((s) => s.valid) ? "" : "red"}`}><span>Checksums verified</span><strong>{inUse.filter((s) => s.valid).length} / {inUse.length}</strong></div>
            <div className={`kpi ${reg.problems.length ? "red" : ""}`}><span>Provenance problems</span><strong>{reg.problems.length}</strong></div>
            <div className="kpi"><span>Indexed policy chunks</span><strong>{man.indexed_chunks}</strong></div>
            <div className={`kpi ${man.rejected_chunks ? "red" : ""}`}><span>Chunks rejected</span><strong>{man.rejected_chunks}</strong></div>
          </div>
          <Card title="Source registry">
            <table>
              <thead><tr><th>Source</th><th>Type</th><th>Published</th><th>Retrieved</th><th>Licence</th><th>Use</th><th>Status</th><th>Provenance</th></tr></thead>
              <tbody>{reg.sources.map((s) => (
                <tr key={s.id}>
                  <td>{s.url.startsWith("http") ? <a href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : s.name}
                    <div className="mono small muted">{s.id}{s.paths.length ? ` · ${s.paths.length === 1 ? s.paths[0] : `${s.paths.length} paths`}` : ""}</div></td>
                  <td>{words(s.source_type)}<div className="muted small">{words(s.data_type)}{s.data_period ? ` · ${s.data_period}` : ""}</div></td>
                  <td className="nowrap">{s.publication_date}</td><td className="nowrap">{s.retrieval_date ?? <span className="muted">not downloaded</span>}</td>
                  <td className="small">{s.license === "CHECK_SOURCE" ? <Badge value="CHECK_SOURCE" /> : s.license}</td>
                  <td className="small">{s.intended_use.join(", ")}</td>
                  <td><Badge value={s.status} /></td>
                  <td>{s.valid
                    ? <><Badge value={s.status === "IN_USE" ? "VERIFIED" : "COMPLETE"} />{s.checksum_sha256 && <div className="mono small muted" title={s.checksum_sha256}>{short(s.checksum_sha256)}</div>}</>
                    : <><Badge value="FAIL" /><div className="err-text small">{s.problems.join("; ")}</div></>}</td>
                </tr>))}</tbody>
            </table>
          </Card>
          <Card title="RAG ingestion manifest">
            <p className="muted small">Policy wordings in the retrieval index. A chunk that cannot be traced to its source file, version, page, section, clause and extraction run is kept out of the index and listed here. The same manifest, built from a fresh database, is committed as <span className="mono">reports/rag_manifest.json</span> and CI checks it is reproducible.</p>
            <table>
              <thead><tr><th>Document</th><th>Source file</th><th>SHA-256</th><th>Extraction run</th><th>Pages</th><th>Chunks</th><th>In force</th></tr></thead>
              <tbody>{man.documents.map((doc) => (
                <Fragment key={doc.document}>
                  <tr>
                    <td><button className="link" onClick={() => setOpen(open === doc.document ? null : doc.document)}>{open === doc.document ? "▾" : "▸"} {doc.document}</button></td>
                    <td className="mono small">{doc.source_file}</td><td className="mono small" title={doc.source_sha256}>{short(doc.source_sha256)}</td>
                    <td>#{doc.extraction_run} <span className="muted small">{doc.file_type.toUpperCase()}</span></td><td>{doc.pages}</td><td>{doc.chunks}</td>
                    <td className="small nowrap">{doc.effective_from} to {doc.effective_to}</td>
                  </tr>
                  {open === doc.document && <tr><td colSpan={7}>
                    <table className="checks"><thead><tr><th>Chunk</th><th>Page</th><th>Section</th><th>Clause</th><th>Text SHA-256</th></tr></thead>
                      <tbody>{man.chunks.filter((c) => c.document === doc.document).map((c) => (
                        <tr key={c.chunk_id}><td className="mono small">{c.chunk_id}</td><td>{c.page}</td><td className="small">{c.section}</td>
                          <td className="small">§{c.clause_ref} {c.title}</td><td className="mono small" title={c.text_sha256}>{short(c.text_sha256)}</td></tr>))}</tbody></table>
                  </td></tr>}
                </Fragment>))}</tbody>
            </table>
            {man.rejected.length > 0 && <>
              <h4>Rejected chunks</h4>
              <ul>{man.rejected.map((r) => <li key={r.clause_id}>{r.product_code} v{r.version} §{r.clause_ref}: missing {r.missing.join(", ")}</li>)}</ul>
            </>}
          </Card>
        </>
      )}
    </>
  );
}
