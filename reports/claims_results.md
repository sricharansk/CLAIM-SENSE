# Claim Sense results on every claim packet

Generated 2026-10-12T07:17:15+00:00 by `python scripts/claims_report.py` on a fresh database. Synthetic data only; LLM off (deterministic rules and extractive retrieval). Rules adjudication-rules/1.0.0, risk risk-rules/1.0.0. Every figure is read back from the API.

**23 claims** across health, motor, property and travel: ₹3,529,100 billed, ₹2,317,150 recommended payable (65.7%). Every claim was routed to a human review queue; no claim was decided by the system.

## By line of business

| Line | Claims | Billed | Payable | Payout | Recommendations |
|---|---|---|---|---|---|
| Health | 11 | ₹1,421,600 | ₹1,015,700 | 71.4% | investigate 2, partial approval 7, recommend reject 1, request info 1 |
| Motor | 2 | ₹139,000 | ₹55,350 | 39.8% | partial approval 1, recommend reject 1 |
| Property | 4 | ₹909,000 | ₹534,100 | 58.8% | partial approval 3, recommend reject 1 |
| Travel | 6 | ₹1,059,500 | ₹712,000 | 67.2% | partial approval 3, recommend reject 2, request info 1 |

## Outcomes

| Recommendation | Claims |
|---|---|
| INVESTIGATE | 2 |
| PARTIAL_APPROVAL | 14 |
| RECOMMEND_REJECT | 5 |
| REQUEST_INFO | 2 |

| Risk level | Claims |
|---|---|
| HIGH | 2 |
| LOW | 20 |
| MEDIUM | 1 |

| Review queue | Claims |
|---|---|
| ADJUSTER_REVIEW | 19 |
| PENDING_INFORMATION | 2 |
| SIU_INVESTIGATION | 2 |

## Where the money went

Total reductions from billed to payable, by rule:

| Rule | Amount |
|---|---|
| Not payable (`R10_NON_PAYABLE`) | ₹152,100 |
| Depreciation (`R15_DEPRECIATION`) | ₹66,550 |
| Benefit limit (`R20_BENEFIT_LIMIT`) | ₹36,000 |
| Per-item limit (`R20_ITEM_LIMIT`) | ₹75,000 |
| Per-day limit (`R20_PER_DAY_LIMIT`) | ₹81,500 |
| Underinsurance (`R25_UNDERINSURANCE`) | ₹71,500 |
| Deductible / excess (`R30_DEDUCTIBLE`) | ₹112,000 |
| Co-payment (`R40_COPAY`) | ₹129,800 |
| Sum insured cap (`R50_MAX_LIABILITY`) | ₹64,500 |
| Not admissible (`R99_NOT_ADMISSIBLE`) | ₹423,000 |

## Every claim

| Claim | Line | Policy wording | Billed | Payable | Coverage | Reason / clause | Risk | Recommendation | Queue |
|---|---|---|---|---|---|---|---|---|---|
| CLM-H-1001 | health | HLT-SHIELD v2025.1 | ₹106,600 | ₹84,330 | COVERED | per-day limit, not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1002 | health | HLT-SHIELD v2025.1 | ₹61,500 | ₹0 | NOT_COVERED | SPECIFIED_DISEASE_WAITING §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1003 | health | HLT-SHIELD v2025.1 | ₹442,000 | ₹332,100 | COVERED | per-day limit, deductible / excess, co-payment | HIGH (HIGH_AMOUNT_RATIO, EARLY_CLAIM, AMOUNT_MISMATCH) | INVESTIGATE | SIU_INVESTIGATION |
| CLM-H-1004 | health | HLT-SHIELD v2025.1 | ₹43,400 | ₹34,560 | COVERED | missing discharge_summary | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-H-1005 | health | HLT-SHIELD v2024.1 | ₹76,500 | ₹50,800 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1006 | health | HLT-SHIELD v2025.1 | ₹106,600 | ₹84,330 | COVERED | per-day limit, not payable, deductible / excess, co-payment | HIGH (POSSIBLE_DUPLICATE) | INVESTIGATE | SIU_INVESTIGATION |
| CLM-H-3016 | health | HLT-SHIELD v2025.1 | ₹25,000 | ₹18,000 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3017 | health | HLT-SHIELD v2025.1 | ₹410,000 | ₹300,000 | COVERED | deductible / excess, co-payment, sum insured cap | MEDIUM (HIGH_AMOUNT_RATIO) | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3018 | health | HLT-SHIELD v2025.1 | ₹36,000 | ₹27,900 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3019 | health | HLT-SHIELD v2024.1 | ₹36,000 | ₹19,600 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3023 | health | HLT-SHIELD v2025.1 | ₹78,000 | ₹64,080 | COVERED | not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2001 | motor | MTR-SECURE v2025.1 | ₹73,500 | ₹55,350 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2002 | motor | MTR-SECURE v2025.1 | ₹65,500 | ₹0 | NOT_COVERED | EXCL_DUI §3.1 | LOW (EARLY_CLAIM) | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3001 | property | HOME-GUARD v2025.1 | ₹450,000 | ₹347,500 | COVERED | depreciation, underinsurance, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3002 | property | HOME-GUARD v2025.1 | ₹305,000 | ₹125,600 | COVERED | not payable, depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3003 | property | HOME-GUARD v2025.1 | ₹83,000 | ₹0 | NOT_COVERED | EXCL_GRADUAL_DETERIORATION §3.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3020 | property | HOME-GUARD v2025.1 | ₹71,000 | ₹61,000 | COVERED | deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3021 | travel | TRV-GLOBE v2025.1 | ₹180,000 | ₹145,000 | COVERED | benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3022 | travel | TRV-GLOBE v2025.1 | ₹12,000 | ₹0 | NOT_COVERED | OUTSIDE_TRIP §1.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4001 | travel | TRV-GLOBE v2025.1 | ₹442,500 | ₹434,000 | COVERED | not payable, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4002 | travel | TRV-GLOBE v2025.1 | ₹181,000 | ₹95,000 | COVERED | per-item limit, benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4003 | travel | TRV-GLOBE v2025.1 | ₹201,000 | ₹0 | NOT_COVERED | EXCL_HAZARDOUS_SPORTS §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4004 | travel | TRV-GLOBE v2025.1 | ₹43,000 | ₹38,000 | COVERED | missing property_irregularity_report | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |

## Risk rules on the 1,000-claim synthetic portfolio

1000 synthetic claims (health 659, motor 341) with 64 injected anomaly patterns. The transparent risk rules flagged 63: precision 84.1%, recall 82.8% (TP 53, FP 10, FN 11, TN 926). Synthetic portfolio with injected patterns; measures rule recall of injected patterns only.

## Golden evaluation

405 of 405 checks passed across 22 hand-worked claim cases and 26 policy-assistant questions (retrieval hit@1 100%). See `reports/evaluation.md`.
