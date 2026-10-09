import { FormEvent, useRef, useState } from "react";
import { ApiError, User, api, auth } from "../api";
import { ErrorBox, useLoad } from "../components/ui";

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
  const info = useLoad(api.demoInfo);
  const pw = useRef<HTMLInputElement>(null);
  // Fill the documented default only when this deployment still uses it; otherwise ask for the deployment's password.
  const pick = (u: string) => {
    setUsername(u);
    if (info.data?.default_password) setPassword("claimsense-demo");
    else pw.current?.focus();
  };
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
        <label>Password<input ref={pw} type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
        <button className="btn primary" disabled={busy || !password}>{busy ? "Signing in…" : "Sign in"}</button>
        <ErrorBox error={error} />
        <div className="demo-accounts">
          <p className="muted small">{info.data && !info.data.default_password
            ? <>Synthetic demo accounts. This deployment uses its own password (the <code>DEMO_PASSWORD</code> setting); pick an account, then type it.</>
            : <>Synthetic demo accounts (password <code>claimsense-demo</code> unless <code>DEMO_PASSWORD</code> is set). Pick one to fill the form:</>}</p>
          {DEMO.map(([u, label, desc]) => (
            <button type="button" key={u} className="chip" onClick={() => pick(u)}>
              <strong>{label}</strong> · {desc}
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
