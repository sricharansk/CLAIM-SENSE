# Design system — Claim Sense UI

One visual language across every screen. New screens reuse these pieces instead of inventing new ones.

## Tokens (`frontend/src/styles.css`, `:root`)

| Token | Use |
|---|---|
| `--bg`, `--panel`, `--line` | Page background, card surface, borders |
| `--ink`, `--muted` | Body text, secondary text |
| `--brand` | Links, primary buttons, active tab |
| `--green`, `--red`, `--amber`, `--blue`, `--teal`, `--purple`, `--gray` (+ `-bg`) | Status tones for badges and KPIs |

A dark-mode set of the same tokens applies under `prefers-color-scheme: dark`.

## Components (`frontend/src/components/ui.tsx`)

| Component | Use |
|---|---|
| `Card` | Every content block; optional title and actions |
| `Badge` | Every status or enum value; the tone comes from one `TONE` map, for example PASS green, FAIL red, MISSING amber, ESCALATED purple |
| `Bars` | Distribution charts on the dashboard and evaluation screen |
| `Due` | Settlement-clock badge with days left |
| `ErrorBox` | API errors, with message, correlation ID and retry |
| `Loading` | Loading state |
| `useLoad` | Data fetching with loading, error and reload |

## Layout patterns (CSS classes)

| Class | Use |
|---|---|
| `.shell` / `.sidebar` | Left navigation with the signed-in user, their role and limit, and API health |
| `.page-head` | Page title, subtitle and primary actions |
| `.kpis` / `.kpi` | Headline numbers |
| `.grid2` / `.grid3` | Two- or three-column card grids; they collapse on narrow screens |
| `nav.tabs` | Tabbed workspace (claim page), with counts and deep links via the URL hash |
| `.checks` | Pass/fail findings |
| `.evidence` | Evidence lists |
| `.cite` | Expandable clause citation: product, version, clause, title, page, quoted text and source file |
| `.timeline` | Decisions and audit events |
| `.letter` | Printable decision letter (print CSS hides the app chrome) |
| `ol.stages` | Processing states (policy ingestion) |

## States every screen handles

- **Loading:** `Loading`.
- **Empty:** a muted sentence saying what to do next.
- **Error:** `ErrorBox`, with retry where it makes sense.
- **Success:** `.ok-text`, or the updated data.
- **Pending, escalated, reviewed:** status badges, the review queue and the claim header.

## Rules

- Every button calls a real endpoint through `frontend/src/api.ts`. There are no placeholder buttons.
- Amounts are shown in INR with Indian digit grouping (`inr()`).
- Decision support is labelled as such: "AI recommendation · requires human review".
