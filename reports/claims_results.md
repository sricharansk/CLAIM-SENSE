# Claim Sense results on every claim packet

Generated 2026-10-12T23:36:25+00:00 by `python scripts/claims_report.py` on a fresh database. Synthetic data only; LLM off (deterministic rules and extractive retrieval). Rules adjudication-rules/1.0.0, risk risk-rules/1.0.0. Every figure is read back from the API.

**58 claims** across health, motor, property and travel: ₹8,773,600 billed, ₹5,405,550 recommended payable (61.6%). Every claim was routed to a human review queue; no claim was decided by the system.

## By line of business

| Line | Claims | Billed | Payable | Payout | Recommendations |
|---|---|---|---|---|---|
| Health | 22 | ₹2,240,100 | ₹1,255,100 | 56.0% | investigate 2, partial approval 11, recommend reject 8, request info 1 |
| Motor | 11 | ₹680,500 | ₹304,350 | 44.7% | partial approval 6, recommend reject 4, request info 1 |
| Property | 11 | ₹2,943,000 | ₹1,901,100 | 64.6% | partial approval 7, recommend reject 4 |
| Travel | 14 | ₹2,910,000 | ₹1,945,000 | 66.8% | partial approval 7, recommend reject 5, request info 2 |

## Outcomes

| Recommendation | Claims |
|---|---|
| INVESTIGATE | 2 |
| PARTIAL_APPROVAL | 31 |
| RECOMMEND_REJECT | 21 |
| REQUEST_INFO | 4 |

| Risk level | Claims |
|---|---|
| HIGH | 2 |
| LOW | 53 |
| MEDIUM | 3 |

| Review queue | Claims |
|---|---|
| ADJUSTER_REVIEW | 52 |
| PENDING_INFORMATION | 4 |
| SIU_INVESTIGATION | 2 |

## Where the money went

Total reductions from billed to payable, by rule:

| Rule | Amount |
|---|---|
| Not payable (`R10_NON_PAYABLE`) | ₹159,600 |
| Depreciation (`R15_DEPRECIATION`) | ₹194,350 |
| Benefit limit (`R20_BENEFIT_LIMIT`) | ₹36,000 |
| Per-item limit (`R20_ITEM_LIMIT`) | ₹75,000 |
| Per-day limit (`R20_PER_DAY_LIMIT`) | ₹96,500 |
| Underinsurance (`R25_UNDERINSURANCE`) | ₹98,700 |
| Deductible / excess (`R30_DEDUCTIBLE`) | ₹212,000 |
| Co-payment (`R40_COPAY`) | ₹156,400 |
| Sum insured cap (`R50_MAX_LIABILITY`) | ₹197,500 |
| Not admissible (`R99_NOT_ADMISSIBLE`) | ₹2,142,000 |

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
| CLM-H-1008 | health | HLT-SHIELD v2025.1 | ₹83,000 | ₹0 | NOT_COVERED | EXCL_COSMETIC §4.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1009 | health | HLT-SHIELD v2025.1 | ₹28,000 | ₹0 | NOT_COVERED | EXCL_ALCOHOL §4.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1010 | health | HLT-SHIELD v2025.1 | ₹211,000 | ₹0 | NOT_COVERED | EXCL_EXPERIMENTAL §4.5 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1011 | health | HLT-SHIELD v2025.1 | ₹32,000 | ₹0 | NOT_COVERED | INITIAL_WAITING_PERIOD §3.1 | LOW (EARLY_CLAIM) | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1012 | health | HLT-SHIELD v2025.1 | ₹57,000 | ₹0 | NOT_COVERED | PED_WAITING_PERIOD §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-1017 | health | HLT-SHIELD v2025.1 | ₹81,000 | ₹68,400 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1018 | health | HLT-SHIELD v2025.1 | ₹94,000 | ₹69,300 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1019 | health | HLT-SHIELD v2025.1 | ₹80,000 | ₹67,500 | COVERED | deductible / excess, co-payment | LOW (EARLY_CLAIM) | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1020 | health | HLT-SHIELD v2025.1 | ₹48,000 | ₹34,200 | COVERED | per-day limit, not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-1021 | health | HLT-SHIELD v2025.1 | ₹27,000 | ₹0 | NOT_COVERED | POLICY_NOT_IN_FORCE §2.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-H-3051 | health | HLT-SHIELD v2025.1 | ₹25,000 | ₹18,000 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3052 | health | HLT-SHIELD v2025.1 | ₹410,000 | ₹300,000 | COVERED | deductible / excess, co-payment, sum insured cap | MEDIUM (HIGH_AMOUNT_RATIO) | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3053 | health | HLT-SHIELD v2025.1 | ₹36,000 | ₹27,900 | COVERED | deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3054 | health | HLT-SHIELD v2024.1 | ₹36,000 | ₹19,600 | COVERED | per-day limit, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-H-3058 | health | HLT-SHIELD v2025.1 | ₹78,000 | ₹64,080 | COVERED | not payable, deductible / excess, co-payment | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2001 | motor | MTR-SECURE v2025.1 | ₹73,500 | ₹55,350 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2002 | motor | MTR-SECURE v2025.1 | ₹65,500 | ₹0 | NOT_COVERED | EXCL_DUI §3.1 | LOW (EARLY_CLAIM) | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-M-2003 | motor | MTR-SECURE v2025.1 | ₹58,500 | ₹0 | NOT_COVERED | EXCL_NO_LICENCE §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-M-2004 | motor | MTR-SECURE v2025.1 | ₹77,000 | ₹0 | NOT_COVERED | EXCL_WEAR_TEAR §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-M-2005 | motor | MTR-SECURE v2025.1 | ₹59,000 | ₹0 | NOT_COVERED | EXCL_OUTSIDE_INDIA §3.4 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-M-2006 | motor | MTR-SECURE v2025.1 | ₹82,000 | ₹56,100 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2007 | motor | MTR-SECURE v2025.1 | ₹33,000 | ₹26,500 | COVERED | missing police_report | MEDIUM (EARLY_CLAIM, MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-M-2008 | motor | MTR-SECURE v2025.1 | ₹47,000 | ₹30,400 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2009 | motor | MTR-SECURE v2025.1 | ₹68,000 | ₹48,000 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2010 | motor | MTR-SECURE v2025.1 | ₹69,000 | ₹50,000 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-M-2011 | motor | MTR-SECURE v2025.1 | ₹48,000 | ₹38,000 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3001 | property | HOME-GUARD v2025.1 | ₹450,000 | ₹347,500 | COVERED | depreciation, underinsurance, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3002 | property | HOME-GUARD v2025.1 | ₹305,000 | ₹125,600 | COVERED | not payable, depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3003 | property | HOME-GUARD v2025.1 | ₹83,000 | ₹0 | NOT_COVERED | EXCL_GRADUAL_DETERIORATION §3.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3004 | property | HOME-GUARD v2025.1 | ₹172,000 | ₹0 | NOT_COVERED | EXCL_UNOCCUPIED §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3005 | property | HOME-GUARD v2025.1 | ₹143,000 | ₹0 | NOT_COVERED | EXCL_WILFUL_ACT §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3006 | property | HOME-GUARD v2025.1 | ₹1,160,000 | ₹1,000,000 | COVERED | depreciation, deductible / excess, sum insured cap | MEDIUM (HIGH_AMOUNT_RATIO) | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3007 | property | HOME-GUARD v2025.1 | ₹107,000 | ₹0 | NOT_COVERED | EXCL_WAR_NUCLEAR §3.4 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-P-3009 | property | HOME-GUARD v2025.1 | ₹139,000 | ₹119,200 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3010 | property | HOME-GUARD v2025.1 | ₹145,000 | ₹98,800 | COVERED | depreciation, underinsurance, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3011 | property | HOME-GUARD v2025.1 | ₹168,000 | ₹149,000 | COVERED | depreciation, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-P-3055 | property | HOME-GUARD v2025.1 | ₹71,000 | ₹61,000 | COVERED | deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3056 | travel | TRV-GLOBE v2025.1 | ₹180,000 | ₹145,000 | COVERED | benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-3057 | travel | TRV-GLOBE v2025.1 | ₹12,000 | ₹0 | NOT_COVERED | OUTSIDE_TRIP §1.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4001 | travel | TRV-GLOBE v2025.1 | ₹442,500 | ₹434,000 | COVERED | not payable, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4002 | travel | TRV-GLOBE v2025.1 | ₹181,000 | ₹95,000 | COVERED | per-item limit, benefit limit, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4003 | travel | TRV-GLOBE v2025.1 | ₹201,000 | ₹0 | NOT_COVERED | EXCL_HAZARDOUS_SPORTS §3.2 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4004 | travel | TRV-GLOBE v2025.1 | ₹43,000 | ₹38,000 | COVERED | missing property_irregularity_report | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-T-4005 | travel | TRV-GLOBE v2025.1 | ₹278,000 | ₹0 | NOT_COVERED | EXCL_PRE_EXISTING §3.1 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4006 | travel | TRV-GLOBE v2025.1 | ₹114,000 | ₹0 | NOT_COVERED | EXCL_ALCOHOL §3.3 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4007 | travel | TRV-GLOBE v2025.1 | ₹195,000 | ₹0 | NOT_COVERED | EXCL_AGAINST_ADVICE §3.4 | LOW | RECOMMEND_REJECT | ADJUSTER_REVIEW |
| CLM-T-4008 | travel | TRV-GLOBE v2025.1 | ₹68,000 | ₹63,000 | COVERED | missing medical_report | LOW (MISSING_DOCUMENTS) | REQUEST_INFO | PENDING_INFORMATION |
| CLM-T-4011 | travel | TRV-GLOBE v2025.1 | ₹92,000 | ₹87,000 | COVERED | deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4012 | travel | TRV-GLOBE v2025.1 | ₹849,000 | ₹840,000 | COVERED | not payable, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4013 | travel | TRV-GLOBE v2025.1 | ₹69,000 | ₹64,000 | COVERED | deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |
| CLM-T-4014 | travel | TRV-GLOBE v2025.1 | ₹185,500 | ₹179,000 | COVERED | not payable, deductible / excess | LOW | PARTIAL_APPROVAL | ADJUSTER_REVIEW |

## Risk rules on the 1,000-claim synthetic portfolio

1000 synthetic claims (motor 241, health 507, travel 128, property 124) with 69 injected anomaly patterns. The transparent risk rules flagged 67: precision 86.6%, recall 84.1% (TP 58, FP 9, FN 11, TN 922). Synthetic portfolio with injected patterns; measures rule recall of injected patterns only.

## Golden evaluation

803 of 803 checks passed across 57 hand-worked claim cases and 26 policy-assistant questions (retrieval hit@1 100%). See `reports/evaluation.md`.
