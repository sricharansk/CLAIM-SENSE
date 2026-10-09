import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ClaimFilters, ClaimSummary, api, inr, words } from "../api";
import { useSession } from "../components/session";
import { Badge, Card, Due, ErrorBox, Loading, useLoad } from "../components/ui";

const OPTIONS: Record<string, [string, string[]]> = {
  status: ["All statuses", ["PENDING_REVIEW", "ESCALATED", "APPROVED", "REJECTED", "INFO_REQUESTED", "UNDER_INVESTIGATION", "DOCUMENTS_RECEIVED", "SUBMITTED", "NEEDS_ATTENTION"]],
  claim_type: ["All lines", ["health", "motor"]],
  recommendation: ["All recommendations", ["PARTIAL_APPROVAL", "APPROVE", "RECOMMEND_REJECT", "REQUEST_INFO", "INVESTIGATE"]],
  risk: ["All risk levels", ["HIGH", "MEDIUM", "LOW"]],
  settlement: ["All settlement states", ["ON_TRACK", "DUE_SOON", "OVERDUE", "MET", "BREACHED"]],
};
const KEYS = ["q", "status", "claim_type", "recommendation", "risk", "settlement", "days"] as const;

type SortKey = "claim_number" | "claimant_name" | "incident_date" | "claimed_amount" | "recommended_payable" | "risk" | "due";
const RISK_ORDER: Record<string, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };
const sortValue = (c: ClaimSummary, k: SortKey): string | number => {
  if (k === "claimed_amount" || k === "recommended_payable") return Number(c[k] ?? -1);
  if (k === "risk") return RISK_ORDER[c.risk_level ?? ""] ?? 9;
  if (k === "due") return c.settlement?.due_date ?? "";
  return (c[k] ?? "") as string;
};

export default function Claims() {
  const { user } = useSession();
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const filters = Object.fromEntries(KEYS.map((k) => [k, params.get(k) ?? ""])) as Required<ClaimFilters>;
  const list = useLoad(() => api.claims(filters), KEYS.map((k) => filters[k]));
  const [sort, setSort] = useState<{ key: SortKey; desc: boolean } | null>(null);
  const set = (k: string, v: string) => {
    const p = new URLSearchParams(params);
    if (v) p.set(k, v); else p.delete(k);
    setParams(p, { replace: true });
  };
  const active = KEYS.filter((k) => k !== "q" && filters[k]);
  const rows = useMemo(() => {
    const data = [...(list.data ?? [])];
    if (sort) data.sort((a, b) => {
      const x = sortValue(a, sort.key), y = sortValue(b, sort.key);
      return (x < y ? -1 : x > y ? 1 : 0) * (sort.desc ? -1 : 1);
    });
    return data;
  }, [list.data, sort]);
  const th = (key: SortKey, label: string, cls = "") => (
    <th className={cls} aria-sort={sort?.key === key ? (sort.desc ? "descending" : "ascending") : "none"}>
      <button className="sort" onClick={() => setSort(sort?.key === key ? { key, desc: !sort.desc } : { key, desc: false })}>
        {label}{sort?.key === key ? (sort.desc ? " ▼" : " ▲") : ""}
      </button>
    </th>
  );
  return (
    <>
      <header className="page-head">
        <h1>Claims</h1>
        <div className="row">
          <button className="btn" onClick={() => api.exportCsv().catch((e) => alert(e.message))}>Export CSV</button>
          {user.can_write && <Link className="btn primary" to="/claims/new">New claim</Link>}
        </div>
      </header>
      <Card>
        <div className="filters">
          <input placeholder="Search claim, claimant or policy number" value={filters.q} onChange={(e) => set("q", e.target.value)} />
          {Object.entries(OPTIONS).map(([k, [all, values]]) => (
            <select key={k} aria-label={all} value={values.includes(filters[k as keyof typeof filters]) ? filters[k as keyof typeof filters] : ""}
              onChange={(e) => set(k, e.target.value)}>
              <option value="">{all}</option>
              {values.map((v) => <option key={v} value={v}>{words(v)}</option>)}
            </select>
          ))}
        </div>
        <div className="row between filter-summary">
          <span className="muted small">
            {list.data ? `${list.data.length} claim${list.data.length === 1 ? "" : "s"}` : "…"}
            {active.map((k) => (
              <button key={k} className="tag removable" onClick={() => set(k, "")} title="Remove this filter">
                {k === "days" ? `Filed in the last ${filters.days} days` : filters[k].split(",").map(words).join(" or ")} ✕
              </button>
            ))}
          </span>
          {(active.length > 0 || filters.q) && <button className="link small" onClick={() => setParams({}, { replace: true })}>Clear all filters</button>}
        </div>
        <ErrorBox error={list.error} onRetry={list.reload} />
        {list.loading && !list.data ? <Loading /> : (
          <table className="clickable">
            <thead><tr>{th("claim_number", "Claim")}<th>Type</th>{th("claimant_name", "Claimant")}<th>Policy</th>{th("incident_date", "Incident")}
              {th("claimed_amount", "Claimed", "num")}{th("recommended_payable", "AI payable", "num")}<th>Recommendation</th>{th("risk", "Risk")}<th>Status</th>{th("due", "Settlement")}</tr></thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.claim_number} onClick={() => nav(`/claims/${c.claim_number}`)}>
                  <td className="nowrap"><Link to={`/claims/${c.claim_number}`} onClick={(e) => e.stopPropagation()}>{c.claim_number}</Link></td>
                  <td>{c.claim_type}</td><td>{c.claimant_name}</td><td className="mono nowrap">{c.policy_number}</td>
                  <td className="nowrap">{c.incident_date ?? "—"}</td><td className="num">{inr(c.claimed_amount)}</td><td className="num">{inr(c.recommended_payable)}</td>
                  <td><Badge value={c.recommendation} /></td><td><Badge value={c.risk_level} /></td><td><Badge value={c.status} /></td><td><Due s={c.settlement} /></td>
                </tr>
              ))}
              {list.data?.length === 0 && <tr><td colSpan={11} className="muted">No claims match these filters.</td></tr>}
            </tbody>
          </table>
        )}
      </Card>
    </>
  );
}
