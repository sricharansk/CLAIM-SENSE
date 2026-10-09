import { Link } from "react-router-dom";
import { useSession } from "../components/session";
import { Card } from "../components/ui";

const REPO = "https://github.com/sricharansk/CLAIM-SENSE";

const ACCOUNTS = [
  ["adjuster", "Adjuster", "Creates claims, uploads documents, runs the analysis and decides claims up to ₹2,00,000. Escalates anything larger."],
  ["supervisor", "Supervisor", "No approval limit. Decides escalated claims, reassigns review tasks and ingests new policy wordings."],
  ["auditor", "Auditor", "Read-only. Sees every claim, the audit trail, the evaluation and the data sources."],
];

const TOUR: { title: string; to: string; cta: string; body: string }[] = [
  { title: "Read the dashboard", to: "/", cta: "Open the dashboard",
    body: "Pick a line of business and a period at the top. Every tile and bar is a link: click High risk, an AI recommendation or a settlement state to open exactly those claims. Needs attention lists open claims that are overdue, escalated or high risk." },
  { title: "Open a claim", to: "/claims/CLM-H-1001", cta: "Open CLM-H-1001",
    body: "The tabs follow the pipeline. Overview shows the AI recommendation and the agents that ran. Documents shows each extracted fact with its source line, and lets a reviewer correct one with a reason. Policy & evidence quotes the clauses relied on. Coverage, Adjudication and Risk show each check, the rupee waterfall and the risk signals. Audit lists every step." },
  { title: "Create a claim yourself", to: "/claims/new", cta: "New claim",
    body: "As the adjuster or supervisor, press Use the sample packet, then Create, upload and analyse. The pipeline reads the three documents, matches the policy wording in force on the incident date and recommends a partial approval: ₹64,080 payable on ₹78,000 billed, after the room-rent cap, the consumables exclusion, the deductible and the co-pay." },
  { title: "Decide it", to: "/reviews", cta: "Open the review queue",
    body: "On the claim's Review tab, approve, reject, request information, refer for investigation or escalate, with a note (a note is required to reject, escalate or refer for investigation). An adjuster cannot approve above ₹2,00,000 and escalates instead. After a decision, Generate letter drafts the settlement or rejection letter, quoting the clause. In the review queue, adjusters take and release tasks; supervisors reassign them." },
  { title: "Ask the policy assistant", to: "/assistant", cta: "Open the assistant",
    body: "Ask a question about the wording, for example “Is cataract surgery covered in the first year?”. Answers cite the clause, page and version. A question the wording cannot answer gets a refusal rather than a guess." },
  { title: "Check the controls", to: "/audit", cta: "Open the audit trail",
    body: "The audit trail records every stage and human decision. Evaluation shows the golden test suite (every check passing). Data sources shows where each dataset came from, with checksums, and traces every indexed clause to its file, page and extraction run." },
];

const SCENARIOS: [string, string][] = [
  ["CLM-H-1002", "Recommended for rejection: cataract inside the 24-month waiting period (clause 3.3)"],
  ["CLM-H-1003", "Investigate: early claim at 94% of the sum insured, and above the adjuster's limit"],
  ["CLM-H-1004", "Request information: discharge summary missing"],
  ["CLM-H-1006", "Investigate: duplicate of CLM-H-1001"],
  ["CLM-M-2001", "Motor partial approval: depreciation by part type and vehicle age"],
  ["CLM-M-2002", "Recommended for rejection: driving under the influence (clause 3.1)"],
  ["CLM-H-1103", "Escalated by the adjuster, waiting for a supervisor (sign in as supervisor to decide it)"],
  ["CLM-M-2106", "Escalated, then approved by a supervisor"],
  ["CLM-H-1106", "Approved at an amount other than the AI's (counts towards the override rate)"],
  ["CLM-H-1107", "Accident 18 days into cover: exempt from the initial waiting period"],
  ["CLM-M-2112", "Rejected: driving licence expired before the accident (clause 3.2)"],
  ["CLM-M-2132", "Open past its settlement date (shows as overdue)"],
];

export default function Guide() {
  const { user } = useSession();
  return (
    <>
      <header className="page-head">
        <div>
          <h1>How to use Claim Sense</h1>
          <p className="muted">AI recommends, rules calculate, humans decide. Everything here is synthetic demo data.</p>
        </div>
      </header>
      <Card title="Demo accounts">
        <table>
          <thead><tr><th>Username</th><th>Role</th><th>What it can do</th></tr></thead>
          <tbody>
            {ACCOUNTS.map(([u, role, can]) => (
              <tr key={u}><td className="mono">{u}{u === user.username && <span className="muted small"> (you)</span>}</td><td>{role}</td><td>{can}</td></tr>
            ))}
          </tbody>
        </table>
        <p className="muted small">All three use the same password: <code>claimsense-demo</code> locally, or whatever <code>DEMO_PASSWORD</code> is set to on a deployment.
          Sign out from the sidebar to switch role.</p>
      </Card>
      <Card title="A ten-minute tour">
        <ol className="tour">
          {TOUR.map((s) => (
            <li key={s.title}>
              <div><strong>{s.title}</strong><p>{s.body}</p></div>
              <Link className="btn small" to={s.to}>{s.cta}</Link>
            </li>
          ))}
        </ol>
      </Card>
      <div className="grid2">
        <Card title="Claims worth opening">
          <table>
            <tbody>
              {SCENARIOS.map(([n, what]) => <tr key={n}><td className="nowrap"><Link to={`/claims/${n}`}>{n}</Link></td><td>{what}</td></tr>)}
            </tbody>
          </table>
          <p className="muted small">States are as seeded. Decisions you make change them until the demo database is re-seeded.</p>
        </Card>
        <Card title="Good to know">
          <ul className="plain">
            <li>Amounts come from a deterministic rules engine; the AI never calculates money or makes the final decision.</li>
            <li>Every recommendation needs a human decision. Rejections, escalations and investigation referrals need a note, and decisions above the adjuster's limit go to a supervisor.</li>
            <li>The 50 seeded claims include 42 demo-book claims whose earlier reviewer decisions are replayed as history; their notes start with “[Seeded demo history]”.</li>
            <li>On the free Render plan the database is re-seeded each time the service restarts, so your changes do not persist, and the first page can take a minute while a sleeping service starts.</li>
            <li>To try policy ingestion, sign in as the supervisor and upload the PDF wording and terms from <a href={`${REPO}/tree/main/data/policies/ingest_demo`} target="_blank" rel="noreferrer">data/policies/ingest_demo</a> in the Policy library.</li>
            <li>More synthetic claim packets for upload are in <a href={`${REPO}/tree/main/data/claims`} target="_blank" rel="noreferrer">data/claims</a>.</li>
          </ul>
        </Card>
      </div>
    </>
  );
}
