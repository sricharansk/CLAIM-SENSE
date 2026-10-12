# Claim Sense results on every claim packet

Generated 2026-10-12T15:05:45+00:00 by `python scripts/claims_report.py` on a fresh database. Synthetic data only; LLM off (deterministic rules and extractive retrieval). Rules adjudication-rules/1.0.0, risk risk-rules/1.0.0. Every figure is read back from the API.

**27 claims** across health, motor, property and travel: ₹4,115,100 billed, ₹2,317,150 recommended payable (56.3%). Every claim was routed to a human review queue; no claim was decided by the system.

## By line of business

| Line | Claims | Billed | Payable | Payout | Recommendations |
|---|---|---|---|---|---|
| Health | 12 | ₹1,499,100 | ₹1,015,700 | 67.8% | investigate 2, partial approval 7, recommend reject 2, request info 1 |
| Motor | 3 | ₹197,500 | ₹55,350 | 28.0% | partial approval 1, recommend reject 2 |
| Property | 5 | ₹1,081,000 | ₹534,100 | 49.4% | partial approval 3, recommend reject 2 |
| Travel | 7 | ₹1,337,500 | ₹712,000 | 53.2% | partial approval 3, recommend reject 3, request info 1 |

## Outcomes

| Recommendation | Claims |
|---|---|
| INVESTIGATE | 2 |
| PARTIAL_APPROVAL | 14 |
| RECOMMEND_REJECT | 9 |
| REQUEST_INFO | 2 |

| Risk level | Claims |
|---|---|
| HIGH | 2 |
| LOW | 24 |
| MEDIUM | 1 |

| Review queue | Claims |
|---|---|
| ADJUSTER_REVIEW | 23 |
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
| Not admissible (`R99_NOT_ADMISSIBLE`) | ₹1,009,000 |

## Every claim

| Claim | Line | Policy wording | Billed | Payable | Coverage | Reason / clause | Risk | Recommendation | Queue |
|---|---|---|---|---|---|---|---|---|---|
| CLM-H-1001 | health | HLT-SHIELD v2025.1 | ₹106,600 | ₹84,330 | COVERED | per-day limit, not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1002 | health | HLT-SHIELD v2025.1 | ₹61,500 | ₹0 | NOT_COVERED | SPECIFIED_DISEASE_WAITING §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1003 | health | HLT-SHIELD v2025.1 | ₹442,000 | ₹332,100 | COVERED | per-day limit, deductible / excess, co-payment | HIGH (HIGH_AMOUNT_RATIO, EARLY_CLAIM, AMOUNT_MISMATCH) | INVESTIGATE | SIU_INVESTIGATION |
| CLM-H-1004 | health | HLT-SHIELD v2025.1 | ₹43,400 | ₹34,560 | COVERED | missing discharge_summary | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-H-1005 | health | HLT-SHIELD v2024.1 | ₹76,500 | ₹50,800 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1006 | health | HLT-SHIELD v2025.1 | ₹106,600 | ₹84,330 | COVERED | per-day limit, not payable, deductible / excess, co-payment | HIGH (POSSIBLE_DUPLICATE) | INVESTIGATE | SIU_INVESTIGATION |
| CLM-H-1007 | health | HLT-SHIELD v2025.1 | ₹77,500 | ₹0 | NOT_COVERED | EXCL_MATERNITY §4.4 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-3020 | health | HLT-SHIELD v2025.1 | ₹25,000 | ₹18,000 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3021 | health | HLT-SHIELD v2025.1 | ₹410,000 | ₹300,000 | COVERED | deductible / excess, co-payment, sum insured cap | MEDIUM (HIGH_AMOUNT_RATIO) | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3022 | health | HLT-SHIELD v2025.1 | ₹36,000 | ₹27,900 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3023 | health | HLT-SHIELD v2024.1 | ₹36,000 | ₹19,600 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3027 | health | HLT-SHIELD v2025.1 | ₹78,000 | ₹64,080 | COVERED | not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2001 | motor | MTR-SECURE v2025.1 | ₹73,500 | ₹55,350 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2002 | motor | MTR-SECURE v2025.1 | ₹65,500 | ₹0 | NOT_COVERED | EXCL_DUI §3.1 | LOW (EARLY_CLAIM) | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-M-2003 | motor | MTR-SECURE v2025.1 | ₹58,500 | ₹0 | NOT_COVERED | EXCL_NO_LICENCE §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3001 | property | HOME-GUARD v2025.1 | ₹450,000 | ₹347,500 | COVERED | depreciation, underinsurance, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3002 | property | HOME-GUARD v2025.1 | ₹305,000 | ₹125,600 | COVERED | not payable, depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3003 | property | HOME-GUARD v2025.1 | ₹83,000 | ₹0 | NOT_COVERED | EXCL_GRADUAL_DETERIORATION §3.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3004 | property | HOME-GUARD v2025.1 | ₹172,000 | ₹0 | NOT_COVERED | EXCL_UNOCCUPIED §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3024 | property | HOME-GUARD v2025.1 | ₹71,000 | ₹61,000 | COVERED | deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3025 | travel | TRV-GLOBE v2025.1 | ₹180,000 | ₹145,000 | COVERED | benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3026 | travel | TRV-GLOBE v2025.1 | ₹12,000 | ₹0 | NOT_COVERED | OUTSIDE_TRIP §1.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4001 | travel | TRV-GLOBE v2025.1 | ₹442,500 | ₹434,000 | COVERED | not payable, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4002 | travel | TRV-GLOBE v2025.1 | ₹181,000 | ₹95,000 | COVERED | per-item limit, benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4003 | travel | TRV-GLOBE v2025.1 | ₹201,000 | ₹0 | NOT_COVERED | EXCL_HAZARDOUS_SPORTS §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4004 | travel | TRV-GLOBE v2025.1 | ₹43,000 | ₹38,000 | COVERED | missing property_irregularity_report | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-T-4005 | travel | TRV-GLOBE v2025.1 | ₹278,000 | ₹0 | NOT_COVERED | EXCL_PRE_EXISTING §3.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |

## Risk rules on the 1,000-claim synthetic portfolio

1000 synthetic claims (motor 241, health 507, travel 128, property 124) with 69 injected anomaly patterns. The transparent risk rules flagged 67: precision 86.6%, recall 84.1% (TP 58, FP 9, FN 11, TN 922). Synthetic portfolio with injected patterns; measures rule recall of injected patterns only.

## Golden evaluation

449 of 449 checks passed across 26 hand-worked claim cases and 26 policy-assistant questions (retrieval hit@1 100%). See `reports/evaluation.md`.
