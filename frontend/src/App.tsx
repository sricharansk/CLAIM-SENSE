import { NavLink, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { useLoad } from "./components/ui";
import Dashboard from "./pages/Dashboard";
import Claims from "./pages/Claims";
import NewClaim from "./pages/NewClaim";
import ClaimDetail from "./pages/ClaimDetail";
import Reviews from "./pages/Reviews";
import Policies from "./pages/Policies";
import Assistant from "./pages/Assistant";
import AuditLog from "./pages/AuditLog";
import Datasets from "./pages/Datasets";

const NAV = [
  ["/", "Dashboard"], ["/claims", "Claims"], ["/claims/new", "New claim"], ["/reviews", "Review queue"],
  ["/policies", "Policy library"], ["/assistant", "Policy assistant"], ["/audit", "Audit trail"], ["/datasets", "Data sources"],
];

export default function App() {
  const ready = useLoad(api.ready);
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">CS</div>
          <div><strong>Claim Sense</strong><small>Claims decision support</small></div>
        </div>
        <nav>
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/" || to === "/claims"}>{label}</NavLink>
          ))}
        </nav>
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
          <Route path="/datasets" element={<Datasets />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
    </div>
  );
}
