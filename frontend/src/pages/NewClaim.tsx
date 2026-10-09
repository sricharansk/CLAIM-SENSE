import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { Card, ErrorBox, useLoad } from "../components/ui";

export default function NewClaim() {
  const nav = useNavigate();
  const insured = useLoad(api.insured);
  const [form, setForm] = useState({ policy_number: "", claim_type: "health", claimant_name: "", description: "" });
  const [files, setFiles] = useState<File[]>([]);
  const [step, setStep] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [sample, setSample] = useState(false);

  const pickPolicy = (pn: string) => {
    const p = insured.data?.find((x) => x.policy_number === pn);
    setForm({ ...form, policy_number: pn, claimant_name: p?.holder_name ?? form.claimant_name,
      claim_type: p?.product_code.startsWith("MTR") ? "motor" : "health" });
  };

  // Fill the form with the synthetic sample packet served by the API (no local files needed on a deployed demo).
  async function loadSample() {
    setError(null);
    setStep("Loading the sample packet…");
    try {
      const packet = await api.demoPacket();
      const docs = await Promise.all(packet.files.map((f) => api.demoFile(f.name)));
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
        <span>No claim documents to hand? Load the synthetic sample packet: a kidney-stone admission with a claim form, hospital bill and discharge summary.</span>
        <button type="button" className="btn small" onClick={loadSample} disabled={!!step}>Use the sample packet</button>
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
              <option value="health">Health</option><option value="motor">Motor</option>
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
