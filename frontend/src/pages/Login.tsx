import { FormEvent, useState } from "react";
import { ApiError, User, api, auth } from "../api";
import { ErrorBox } from "../components/ui";

const DEMO = [
  ["adjuster", "Adjuster", "Works claims; approves up to ₹2,00,000"],
  ["supervisor", "Supervisor", "No approval limit; decides escalations; ingests policies"],
  ["auditor", "Auditor", "Read-only access to claims and the audit trail"],
];

export default function Login({ onSignedIn }: { onSignedIn: (u: User) => void }) {
  const [username, setUsername] = useState("adjuster");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<ApiError | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const r = await api.login(username, password);
      auth.set(r.token);
      onSignedIn(r.user);
    } catch (err) { setError(err as ApiError); } finally { setBusy(false); }
  };
  return (
    <div className="login-wrap">
      <form className="card login" onSubmit={submit}>
        <div className="brand dark"><div className="logo">CS</div><div><strong>Claim Sense</strong><small>Claims decision support</small></div></div>
        <h2>Sign in</h2>
        <label>Username<input autoFocus value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
        <button className="btn primary" disabled={busy || !password}>{busy ? "Signing in…" : "Sign in"}</button>
        <ErrorBox error={error} />
        <div className="demo-accounts">
          <p className="muted small">Synthetic demo accounts (password set by <code>DEMO_PASSWORD</code>, default <code>claimsense-demo</code>):</p>
          {DEMO.map(([u, label, desc]) => (
            <button type="button" key={u} className="chip" onClick={() => { setUsername(u); setPassword("claimsense-demo"); }}>
              <strong>{label}</strong> · {desc}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
