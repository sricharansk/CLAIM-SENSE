// Typed client for the Claim Sense API. Every screen calls these real endpoints.
export type Settlement = { start: string; due_date: string; days: number; clause: string | null; days_left: number | null;
  state: "ON_TRACK" | "DUE_SOON" | "OVERDUE" | "MET" | "BREACHED"; decided_on: string | null };
export type Letter = { claim_number: string; kind: string; status: "FINAL" | "DRAFT"; date: string;
  to: { name: string; policy_number: string; holder: string }; from: string; subject: string; paragraphs: string[];
  references: { clause_ref: string; title: string; page: number; text: string; policy: string }[];
  signed_by: string | null; based_on: string };
export type ClaimSummary = {
  settlement: Settlement;
  claim_number: string; policy_number: string; claim_type: "health" | "motor"; claimant_name: string;
  incident_date: string | null; claimed_amount: string | null; status: string; created_at: string; updated_at: string;
  recommendation: string | null; recommended_payable: string | null; risk_level: string | null; documents: number;
};
export type Citation = {
  clause_id: number; clause_ref: string; title: string; section: string; page: number; policy: string;
  product_code: string; version: string; document: string; text: string; score?: number;
  bm25_rank?: number | null; vector_rank?: number | null;
};
export type Finding = { code: string; outcome: "PASS" | "FAIL" | "MISSING"; message: string; citation: Citation | null };
export type Step = { rule_id: string; label: string; adjustment: string; running_total: string; clause_ref: string | null; detail: string };
export type Signal = { code: string; weight: number; message: string };
export type Evidence = Record<string, unknown> & { kind: string; used_for: string; finding: string };
export type AnalysisResult = {
  claim_number: string; correlation_id: string;
  policy: { policy_number: string; holder: string; product_code: string; product_name: string; version: string;
    effective_from: string; effective_to: string; sum_insured: string; start_date: string; end_date: string };
  facts: Record<string, unknown>;
  line_items: { description: string; amount: number; category: string; source: { line: number; document_type: string } }[];
  coverage: { status: string; accident: boolean; days_since_commencement: number; missing_documents: string[]; findings: Finding[] };
  adjudication: { claimed_amount: string; gross_billed: string; non_covered: string; deductible: string; copay: string;
    depreciation: string; payable_amount: string; rules_version: string; waterfall: Step[] };
  risk: { score: number; level: string; signals: Signal[]; features: Record<string, unknown>; rules_version: string };
  evidence: Evidence[];
  recommendation: { decision: string; label: string; reasons: string[]; summary: string; payable_amount: string; requires_human_review: boolean };
};
export type Analysis = {
  run_id: number; correlation_id: string; status: string; error: string | null; started_at: string; finished_at: string | null;
  rules_version: string;
  agents: { agent: string; status: string; summary: string; duration_ms: number; tool_calls: { tool: string; args: unknown; result: string; ms: number }[] }[];
  result: AnalysisResult | null;
};
export type ClaimDetail = Omit<ClaimSummary, "documents"> & {
  description: string;
  documents: { id: number; filename: string; doc_type: string; pages: number; status: string; sha256: string; uploaded_at: string }[];
  facts: { id: number; document_id: number; name: string; value: string; confidence: number; line: number | null; source_text: string }[];
  analysis: Analysis | null;
  decisions: { id: number; source: string; decision: string; payable_amount: string | null; actor: string; notes: string; created_at: string }[];
  workflow_task: { id: number; queue: string; priority: string; status: string; assignee: string | null } | null;
  audit: AuditEvent[];
};
export type AuditEvent = { id: number; claim_number?: string | null; event_type: string; actor: string; details: Record<string, unknown>; correlation_id: string | null; created_at: string };
export type PolicyVersionInfo = { id: number; version: string; effective_from: string; effective_to: string; clauses: number; source_file: string };
export type Policy = { product_code: string; name: string; line_of_business: string; insurer: string; synthetic: boolean; versions: PolicyVersionInfo[] };
export type PolicyVersionFull = { id: number; version: string; effective_from: string; effective_to: string; terms: Record<string, unknown>;
  clauses: { id: number; clause_ref: string; title: string; section: string; page: number; text: string }[] };
export type InsuredPolicy = { policy_number: string; product_code: string; holder_name: string; start_date: string; end_date: string; sum_insured: string };
export type RagAnswer = { question: string; grounded: boolean; mode: string; answer: string; citations: Citation[] };
export type ReviewTask = { settlement: Settlement; task_id: number; queue: string; priority: string; claim_number: string; claimant_name: string; claim_type: string;
  claimed_amount: string | null; status: string; recommendation: string | null; recommended_payable: string | null; created_at: string };
export type Analytics = {
  settlement: Record<string, number>;
  totals: { overdue: number; claims: number; pending_review: number; high_risk: number; decided: number; claimed_amount: string; recommended_payable: string; avg_analysis_ms: number | null };
  by_status: Record<string, number>; by_recommendation: Record<string, number>; by_risk: Record<string, number>;
  by_line: Record<string, number>; queues: Record<string, number>;
  human_vs_ai: { decided: number; agreed: number; overridden: number };
  portfolio: null | { claims: number; by_risk: Record<string, number>; by_line: Record<string, number>; injected_anomalies: number;
    flagged: number; precision: number; recall: number; confusion: Record<string, number>; median_claim: number; note: string };
};
export type Dataset = { name: string; publisher: string; year: string; url: string; purpose: string; status: string };
export type Ready = { status: string; database: string; policy_index: string; llm: string; database_backend: string };

export type User = { username: string; display_name: string; role: "ADJUSTER" | "SUPERVISOR" | "AUDITOR";
  approval_limit: string | null; can_write: boolean; is_supervisor: boolean };

const TOKEN_KEY = "claimsense.token";
let token: string | null = (() => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } })();
export const auth = {
  get: () => token,
  set: (t: string | null) => {
    token = t;
    try { if (t) localStorage.setItem(TOKEN_KEY, t); else localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  },
};

export class ApiError extends Error {
  constructor(message: string, public status: number, public correlationId?: string) { super(message); }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  const headers = new Headers(init?.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  try {
    res = await fetch(`/api/v1${path}`, { ...init, headers });
  } catch {
    throw new ApiError("Cannot reach the Claim Sense API. Check that the backend is running.", 0);
  }
  const body = await res.json().catch(() => null);
  if (res.status === 401 && path !== "/auth/login") {
    auth.set(null);
    window.dispatchEvent(new Event("claimsense:signed-out"));
  }
  if (!res.ok) {
    const err = body?.error;
    throw new ApiError(err?.message ?? `Request failed (${res.status})`, res.status, err?.correlation_id ?? res.headers.get("x-correlation-id") ?? undefined);
  }
  return body as T;
}
const json = (method: string, data: unknown): RequestInit => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });

export const api = {
  login: (username: string, password: string) => request<{ token: string; user: User }>("/auth/login", json("POST", { username, password })),
  me: () => request<User>("/auth/me"),
  ready: () => request<Ready>("/ready"),
  analytics: () => request<Analytics>("/analytics"),
  claims: (q = "", status = "") => request<ClaimSummary[]>(`/claims?${new URLSearchParams({ ...(q && { q }), ...(status && { status }) })}`),
  claim: (n: string) => request<ClaimDetail>(`/claims/${n}`),
  createClaim: (data: { policy_number: string; claim_type: string; claimant_name: string; description: string; incident_date?: string; claimed_amount?: string }) =>
    request<ClaimSummary>("/claims", json("POST", data)),
  upload: (n: string, files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    return request<{ id: number; filename: string; doc_type: string; facts_extracted: number }[]>(`/claims/${n}/documents`, { method: "POST", body: fd });
  },
  letter: (n: string) => request<Letter>(`/claims/${n}/letter`),
  exportCsv: async () => {
    const res = await fetch("/api/v1/claims-export.csv", { headers: token ? { Authorization: `Bearer ${token}` } : {} });
    if (!res.ok) throw new ApiError(`Export failed (${res.status})`, res.status);
    const url = URL.createObjectURL(await res.blob());
    const a = document.createElement("a");
    a.href = url; a.download = "claim-sense-claims.csv"; a.click();
    URL.revokeObjectURL(url);
  },
  document: (n: string, id: number) => request<{ filename: string; doc_type: string; text: string }>(`/claims/${n}/documents/${id}`),
  analyze: (n: string) => request<Analysis>(`/claims/${n}/analyze`, { method: "POST" }),
  review: (n: string, data: { action: string; notes: string; payable_amount?: string }) =>
    request<{ status: string }>(`/claims/${n}/review`, json("POST", data)),
  reviews: () => request<ReviewTask[]>("/reviews"),
  policies: () => request<Policy[]>("/policies"),
  versions: (code: string) => request<PolicyVersionFull[]>(`/policies/${code}/versions`),
  uploadPolicy: (wording: File, terms: File) => {
    const fd = new FormData();
    fd.append("wording", wording);
    fd.append("terms", terms);
    return request<{ product_code: string; version: string; clauses: number }>("/policies", { method: "POST", body: fd });
  },
  insured: () => request<InsuredPolicy[]>("/insured-policies"),
  ask: (question: string, product_code?: string, version?: string) =>
    request<RagAnswer>("/rag/query", json("POST", { question, product_code: product_code || null, version: version || null })),
  audit: (claim_number?: string) => request<AuditEvent[]>(`/audit${claim_number ? `?claim_number=${claim_number}` : ""}`),
  datasets: () => request<Dataset[]>("/datasets"),
};

export const inr = (v: string | number | null | undefined) =>
  v === null || v === undefined || v === "" ? "—" : `₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 2, minimumFractionDigits: 0 })}`;
export const when = (s: string | null | undefined) => (s ? new Date(s).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "—");
export const words = (s: string | null | undefined) => (s ? s.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase()) : "—");
