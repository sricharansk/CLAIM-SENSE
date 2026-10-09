import { useCallback, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { User, api, auth, words } from "./api";
import { SessionContext } from "./components/session";
import { Loading, useLoad } from "./components/ui";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Claims from "./pages/Claims";
import NewClaim from "./pages/NewClaim";
import ClaimDetail from "./pages/ClaimDetail";
import Reviews from "./pages/Reviews";
import Policies from "./pages/Policies";
import Assistant from "./pages/Assistant";
import AuditLog from "./pages/AuditLog";
import Datasets from "./pages/Datasets";
import EvaluationPage from "./pages/Evaluation";

const NAV = [
  ["/", "Dashboard"], ["/claims", "Claims"], ["/claims/new", "New claim"], ["/reviews", "Review queue"],
  ["/policies", "Policy library"], ["/assistant", "Policy assistant"], ["/audit", "Audit trail"], ["/evaluation", "Evaluation"], ["/datasets", "Data sources"],
];

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(!!auth.get());
  const signOut = useCallback(() => { auth.set(null); setUser(null); }, []);
  useEffect(() => {
    if (auth.get()) api.me().then(setUser).catch(() => auth.set(null)).finally(() => setChecking(false));
    const onOut = () => setUser(null);
    window.addEventListener("claimsense:signed-out", onOut);
    return () => window.removeEventListener("claimsense:signed-out", onOut);
  }, []);
  if (checking) return <Loading />;
  if (!user) return <Login onSignedIn={setUser} />;
  return (
    <SessionContext.Provider value={{ user, signOut }}>
      <Shell user={user} signOut={signOut} />
    </SessionContext.Provider>
  );
}

function Shell({ user, signOut }: { user: User; signOut: () => void }) {
  const ready = useLoad(api.ready);
  const [menu, setMenu] = useState(false);
  return (
    <div className="shell">
      <aside className={`sidebar ${menu ? "open" : ""}`}>
        <div className="brand">
          <div className="logo">CS</div>
          <div><strong>Claim Sense</strong><small>Claims decision support</small></div>
          <button className="menu-btn" aria-expanded={menu} aria-controls="main-nav" onClick={() => setMenu(!menu)}>{menu ? "Close" : "Menu"}</button>
        </div>
        <nav id="main-nav">
          {NAV.filter(([to]) => to !== "/claims/new" || user.can_write).map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/" || to === "/claims"} onClick={() => setMenu(false)}>{label}</NavLink>
          ))}
        </nav>
        <div className="who">
          <strong>{user.display_name}</strong>
          <span>{words(user.role)}{user.approval_limit ? ` · limit ₹${Number(user.approval_limit).toLocaleString("en-IN")}` : user.role === "SUPERVISOR" ? " · no limit" : ""}</span>
          <button className="link light" onClick={signOut}>Sign out</button>
        </div>
        <div className="health">
          <span className={`dot ${ready.data ? "ok" : ready.error ? "bad" : ""}`} />
          {ready.data ? `API ready · ${ready.data.database_backend} · LLM ${ready.data.llm.startsWith("disabled") ? "off" : "on"}` : ready.error ? "API unreachable" : "Checking API…"}
        </div>
        <p className="disclaimer">Synthetic demo data. AI recommends, rules calculate, humans decide.</p>
      </aside>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/claims" element={<Claims />} />
          <Route path="/claims/new" element={<NewClaim />} />
          <Route path="/claims/:claimNumber" element={<ClaimDetail />} />
          <Route path="/reviews" element={<Reviews />} />
          <Route path="/policies" element={<Policies />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/audit" element={<AuditLog />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
