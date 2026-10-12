import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, LINES, api } from "../api";
import { Card, ErrorBox, useLoad } from "../components/ui";

// What each sample packet contains (the packets live in data/claims/demo_upload and are served by GET /demo-packet).
const SAMPLES: Record<string, string> = {
  health: "Health: a kidney-stone admission with a claim form, hospital bill and discharge summary.",
  travel: "Travel: a lost checked bag and a 14-hour flight delay, with the airline's irregularity report.",
  home: "Home: a night-time burglary of a television and jewellery, with the police report and survey.",
  personal_accident: "Personal accident: a thumb lost in a kitchen accident, with the medical certificate.",
  life: "Life: a death claim by the nominee seven months into cover, with the death and medical certificates.",
};

export default function NewClaim() {
  const nav = useNavigate();
  const insured = useLoad(api.insured);
  const [form, setForm] = useState({ policy_number: "", claim_type: "health", claimant_name: "", description: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [sample, setSample] = useState(false);
  const [sampleLine, setSampleLine] = useState<string>("health");

  const pickPolicy = (pn: string) => {
    const p = insured.data?.find((x) => x.policy_number === pn);
    setForm({ ...form, policy_number: pn, claimant_name: p?.holder_name ?? form.claimant_name,
      claim_type: p?.line_of_business ?? form.claim_type });
  };

  // Fill the form with the synthetic sample packet served by the API (no local files needed on a deployed demo).
  async function loadSample() {
    setError(null);
    setStep("Loading the sample packet…");
    try {
      const packet = await api.demoPacket(sampleLine);
      const docs = await Promise.all(packet.files.map((f) => api.demoFile(f.name, sampleLine)));
      setForm({ policy_number: packet.policy_number, claim_type: packet.claim_type, claimant_name: packet.claimant_name,
        description: packet.description });
      setFiles(docs);
      setSample(true);
    } catch (err) {
      setError(err as ApiError);
    } finally {
      setStep("");
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      setStep("Creating claim…");
      const c = await api.createClaim(form);
      if (files.length) {
        setStep(`Uploading and extracting ${files.length} document(s)…`);
        await api.upload(c.claim_number, files);
        setStep("Running the agent pipeline…");
        await api.analyze(c.claim_number);
      }
      nav(`/claims/${c.claim_number}`);
    } catch (err) {
      setError(err as ApiError);
      setStep("");
    }
  }

  return (
    <>
      <header className="page-head"><h1>New claim</h1></header>
      <div className="notice row between">
        <span>No claim documents to hand? Load a synthetic sample packet. {SAMPLES[sampleLine]}</span>
        <span className="row">
          <select aria-label="Sample packet line" value={sampleLine} onChange={(e) => setSampleLine(e.target.value)}>
            {LINES.filter(([v]) => v in SAMPLES).map(([v, label]) => <option key={v} value={v}>{label}</option>)}
          </select>
          <button type="button" className="btn small" onClick={loadSample} disabled={!!step}>Use the sample packet</button>
        </span>
      </div>
      <Card title="Claim intake">
        <form className="form" onSubmit={submit}>
          <label>Policy number
            <select required value={form.policy_number} onChange={(e) => pickPolicy(e.target.value)}>
              <option value="">Select a policy</option>
              {insured.data?.map((p) => <option key={p.policy_number} value={p.policy_number}>{p.policy_number} · {p.holder_name} · {p.product_code}</option>)}
            </select>
          </label>
          <label>Claim type
            <select value={form.claim_type} onChange={(e) => setForm({ ...form, claim_type: e.target.value })}>
              {LINES.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
            </select>
          </label>
          <label>Claimant name<input required value={form.claimant_name} onChange={(e) => setForm({ ...form, claimant_name: e.target.value })} /></label>
          <label className="wide">Description of loss<textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
          <label className="wide">Claim documents (PDF or text: claim form, bill or estimate, discharge summary, police report…)
            <input type="file" multiple accept=".pdf,.txt,.md" onChange={(e) => { setFiles(Array.from(e.target.files ?? [])); setSample(false); }} />
          </label>
          {files.length > 0 && (
            <div className="wide">
              {sample && <p className="ok-text small">Sample packet loaded. Press the button below to create the claim and run the analysis.</p>}
              <ul className="files">{files.map((f) => <li key={f.name}>{f.name} · {(f.size / 1024).toFixed(1)} KB</li>)}</ul>
            </div>
          )}
          <div className="wide row">
            <button className="btn primary" disabled={!!step}>{files.length ? "Create, upload and analyse" : "Create claim"}</button>
            {step && <span className="muted">{step}</span>}
          </div>
          <ErrorBox error={error} />
        </form>
        <p className="muted small">Incident date and amount are read from the uploaded documents. More synthetic packets are in <code>data/claims/</code> in the repository.</p>
      </Card>
    </>
  );
}
