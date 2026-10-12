# Using Claim Sense

Claim Sense is decision support. The AI recommends, a deterministic rules engine calculates the money, and a person makes every decision. Everything in the demo is synthetic.

The same guide is built into the app under **How to use** (`/guide`).

## Sign in

| Username | Role | What it can do |
|---|---|---|
| `adjuster` | Adjuster | Create claims, upload documents, run the analysis, decide claims up to ₹2,00,000 and escalate anything larger |
| `supervisor` | Supervisor | No approval limit; decides escalated claims, reassigns review tasks, ingests new policy wordings |
| `auditor` | Auditor | Read-only access to every claim, the audit trail, the evaluation and the data sources |

All three share one password: `claimsense-demo` locally, or the `DEMO_PASSWORD` set on the deployment. When the deployment uses the default password the sign-in screen fills it in for you; otherwise the account buttons only fill the username. Sign out from the sidebar to switch role.

On Render's free plan the service sleeps when idle, so the first page can take about a minute. The database is re-seeded each time the service starts, so changes you make do not persist.

## The demo data

The database starts with 85 claims across six lines of business: health, motor, travel, home, personal accident and life.

- 8 golden scenarios (`CLM-H-1001`…`CLM-M-2002`), the cases the tests and evaluation check by hand.
- 77 demo-book claims spread over the last eight weeks: 42 health and motor (`CLM-H-11xx`, `CLM-M-21xx`) and 35 in the newer lines (`CLM-T-41xx` travel, `CLM-P-51xx` home, `CLM-A-61xx` personal accident, `CLM-L-71xx` life). They include partial approvals, waiting-period and exclusion rejections, missing documents, duplicates and high-value early claims. Many already carry reviewer decisions, replayed through the same review rules a person uses; their notes start with `[Seeded demo history]`.

Each claim is analysed by the real pipeline at start-up; nothing on the dashboard is hard-coded. The scenarios are listed in [`data/claims/demo_book.json`](../data/claims/demo_book.json) with the outcome each one is designed to reach.

## A ten-minute tour

1. **Dashboard.** Choose a line of business (All, Health, Motor, Travel, Home, Personal accident, Life) and a period (all time, last 7, 30 or 90 days) at the top. Every tile and every bar is a link: click *High risk*, a recommendation or a settlement state to open exactly those claims. *Weekly activity* compares claims filed with claims decided; *Needs attention* lists open claims that are overdue, escalated or high risk; *Why claims are declined or held* counts failing coverage checks with the clause behind each.
2. **Claims.** Filter by status, line, recommendation, risk, settlement state or period. Active filters show as tags; click a tag to remove it. Click a column heading to sort, and a row to open the claim. Filters live in the address, so a filtered list can be bookmarked or shared.
3. **A claim.** Open `CLM-H-1001`. The tabs follow the pipeline: Overview (recommendation and the agents that ran), Documents (each extracted fact with its source line; a reviewer can correct one with a reason and re-run), Policy & evidence (the clauses relied on, with page and version), Coverage, Adjudication (the rupee waterfall), Risk, Review and Audit.
4. **Create a claim.** As adjuster or supervisor, open **New claim**, choose a line next to **Use the sample packet**, press it, then **Create, upload and analyse**. What each sample should give:

   | Sample | Recommendation | Payable | Why |
   |---|---|---:|---|
   | Health | Partial approval | ₹64,080 on ₹78,000 | Room-rent cap, consumables exclusion, deductible and co-pay |
   | Travel | Partial approval | ₹35,800 on ₹64,500 | 10% baggage depreciation, ₹15,000 per-item limit (2.3), trip-delay cap ₹10,000 (2.4) |
   | Home | Partial approval | ₹74,000 on ₹2,30,000 | Depreciation, jewellery limit ₹1,00,000 (2.3), average clause for 50% under-insurance (1.3), deductible |
   | Personal accident | Approve | ₹1,90,000 on ₹1,78,000 | The benefit schedule pays 25% of the sum insured for a thumb (2.3), more than was claimed |
   | Life | Recommend rejection | ₹0 | Suicide seven months after commencement, inside the 12-month exclusion (3.1) |

   Each sample is a fixed packet, so creating it twice raises a duplicate-claim signal.
5. **Decide it.** On the Review tab, approve, reject, request information, refer for investigation or escalate. A note is required to reject, escalate or refer for investigation. An adjuster cannot approve above ₹2,00,000. After a decision, **Generate letter** drafts the settlement or rejection letter quoting the clause. In the **Review queue**, adjusters take and release tasks and supervisors reassign them.
6. **Ask the policy assistant.** For example, "Is cataract surgery covered in the first year?". Answers cite clause, page and version, and a question the wording cannot answer is refused.
7. **Check the controls.** The **Audit trail** records every stage and decision; **Evaluation** shows the golden test suite; **Data sources** shows where every dataset came from, with checksums, the industry benchmark from the CAS Schedule P loss database, and traces every indexed clause to its file and page.

## Claims worth opening

| Claim | What it shows |
|---|---|
| `CLM-H-1002` | Recommended for rejection: cataract inside the 24-month waiting period (clause 3.3) |
| `CLM-H-1003` | Investigate: early claim at 94% of the sum insured, above the adjuster's limit |
| `CLM-H-1004` | Request information: discharge summary missing |
| `CLM-H-1006` | Investigate: duplicate of `CLM-H-1001` |
| `CLM-M-2001` | Motor partial approval: depreciation by part type and vehicle age |
| `CLM-M-2002` | Recommended for rejection: driving under the influence (clause 3.1) |
| `CLM-H-1103` | Escalated by the adjuster; sign in as supervisor to decide it |
| `CLM-M-2106` | Escalated, then approved by a supervisor |
| `CLM-H-1106` | Approved at an amount other than the AI's (counts towards the override rate) |
| `CLM-H-1107` | Accident 18 days into cover: exempt from the initial waiting period |
| `CLM-M-2112` | Rejected: driving licence expired before the accident (clause 3.2) |
| `CLM-M-2132` | Open past its settlement date, so it shows as overdue |
| `CLM-T-4102` | Travel: lost baggage with depreciation, the per-item limit and the trip limit |
| `CLM-P-5103` | Home: flood in an under-insured home; the average clause scales the loss down (clause 1.3) |
| `CLM-A-6103` | Personal accident: accidental death, 100% of the capital sum insured |
| `CLM-L-7103` | Life: suicide eight months after commencement, excluded (clause 3.1) |
| `CLM-L-7104` | Life: suicide 55 months after commencement; the exclusion no longer applies |
| `CLM-L-7102` | Life: death 17 months in, inside the section 45 window, so it is investigated |

States are as seeded; decisions you make change them until the database is re-seeded.

## Policy ingestion

Sign in as `supervisor`, open **Policy library** and upload [`data/policies/ingest_demo/HLT-SHIELD_2026.1.pdf`](../data/policies/ingest_demo) with its `.terms.json`. The six-page PDF becomes 21 cited clauses of a new 2026.1 version, and the assistant can answer from it.
