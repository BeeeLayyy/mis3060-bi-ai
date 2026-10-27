# HW4 Decision Log — Wildcat Capital cleaning

Written from the Part A audit (`reports/dq_summary_raw.csv`) **before** the cleaning code. Each entry was the prompt for the matching step in `scripts/02_clean.py`. Issues left alone are logged too.

Dimensions: Validity, Completeness, Uniqueness, Consistency, Accuracy/Plausibility, Referential Integrity.

---

## 1. dim_client — near-duplicate clients
| Field | |
|---|---|
| **Table / column** | dim_client / last_name (whole row) |
| **Evidence** | 25 clients (IDs 2501–2525) match an existing client on every column except last name, which is truncated or misspelled (2501 "Taylo" vs 674 "Taylor", 2512 "Leen" vs 1193 "Lee"). None of the 25 has a single fee, snapshot or transaction row. |
| **Dimension violated** | Uniqueness, Accuracy |
| **Decision** | Quarantine (keep the original ID, move the copy to `quarantine_dim_client_near_duplicates.csv` with `matched_client_id`) |
| **Justification** | Same person entered twice. Keeping both inflates client counts by 1% and splits the advisor book. Because the copies have no facts, removing them loses nothing. |
| **Risk** | If any of the 25 is actually a different person with a similar name, they disappear from client counts. Low: all 11 other columns match exactly, including AUM to the cent and the start date. |
| **Verified by** | Script asserts the duplicates have zero fact rows and that last names differ only by a truncation/typo. |

## 2. dim_client — state spelled out
| Field | |
|---|---|
| **Table / column** | dim_client / state |
| **Evidence** | 78 rows use full names (Pennsylvania 25, Florida 15, New York 14, New Jersey 13, California 5, Illinois 4, Texas 2) while the rest use 2-letter codes. |
| **Dimension violated** | Consistency, Validity |
| **Decision** | Standardize to USPS 2-letter code |
| **Justification** | A state slicer would show "PA" and "Pennsylvania" as two states and split the region totals. |
| **Risk** | Very low; mapping is a fixed lookup. Script asserts every value is two capital letters after. |

## 3. dim_client — blank risk_profile
| Field | |
|---|---|
| **Table / column** | dim_client / risk_profile |
| **Evidence** | 76 blanks (1 of them is a near-duplicate from #1). In the snapshot table, each risk profile maps to exactly one benchmark (Aggressive and Mod. Aggressive → 1, Balanced → 3, Conservative and Mod. Conservative → 8). Every client with a blank profile is benchmarked to 3 in all their snapshots, and benchmark 3 is used only by Balanced clients. |
| **Dimension violated** | Completeness |
| **Decision** | Fill with "Balanced" **only** where the snapshot benchmark proves it; add flag `risk_profile_imputed = 1` |
| **Justification** | This is not a guess: the firm's own benchmark assignment encodes the profile, and it is one-to-one for benchmark 3. Risk profile drives suitability and benchmark reporting, so blanks would drop these clients from every risk view. |
| **Risk** | If the benchmark was assigned by default when the profile was missing, we would label unprofiled clients as Balanced. The flag column lets anyone exclude them. |

## 4. dim_client — tier vs initial AUM
| Field | |
|---|---|
| **Table / column** | dim_client / client_tier, initial_aum |
| **Evidence** | 102 HNW clients have initial AUM under $1M; 25 UHNW clients are under $10M. |
| **Dimension violated** | Consistency, Accuracy/Plausibility |
| **Decision** | Flag (`flag_tier_aum_mismatch`), leave values |
| **Justification** | Tier is likely set on household or current AUM, which this extract does not have. Changing tier would be inventing data. |
| **Risk** | Tier-level fee or AUM analysis may include clients in the "wrong" tier; the flag makes that visible. |

## 5. fact_transactions — security_id stored as "45.0"
| Field | |
|---|---|
| **Table / column** | fact_transactions / security_id |
| **Evidence** | All 197,175 non-blank values are float text ("45.0") while dim_security uses "45". A text join matches 0% of trades. |
| **Dimension violated** | Validity, Referential Integrity |
| **Decision** | Convert to integer text |
| **Justification** | Format artifact from an upstream float column; value unchanged. Required for the security relationship to work. |
| **Risk** | None: script asserts every value is a whole number before and after. |

## 6. fact_transactions — blank security, shares, price
| Field | |
|---|---|
| **Table / column** | fact_transactions / security_id, shares, price |
| **Evidence** | 101,597 blanks = exactly Deposit (35,981) + Withdrawal (29,850) + Advisory Fee (35,766). Zero blanks on Buy/Sell/Dividend. |
| **Dimension violated** | None (legitimate structure) |
| **Decision** | **Leave as is** |
| **Justification** | Cash movements have no security. Filling them would invent trades. |
| **Risk** | A BI tool may show "(Blank)" in a security slicer; documented in README_clean.md. |

## 7. fact_transactions — negative shares on Buy
| Field | |
|---|---|
| **Table / column** | fact_transactions / shares |
| **Evidence** | 836 Buy rows have negative shares; no other type does. For all 836, amount = \|shares\| × price to the cent, and amount is positive. |
| **Dimension violated** | Validity, Consistency |
| **Decision** | Convert to absolute value |
| **Justification** | Sign is carried by txn_type everywhere else. The stored amount confirms the magnitude, so only the sign is wrong. |
| **Risk** | If these were reversals, they would now count as purchases. Ruled out: there is no separate reversal type and the amounts are positive. |

## 8. fact_transactions — orphan client_id
| Field | |
|---|---|
| **Table / column** | fact_transactions / client_id |
| **Evidence** | 200 rows, 200 distinct client IDs between 2702 and 3192; dim_client stops at 2525. Mix of all six types. |
| **Dimension violated** | Referential Integrity |
| **Decision** | Quarantine (`quarantine_fact_transactions_orphan_client.csv`) |
| **Justification** | No column links these rows to a real client, so they cannot be attributed to an advisor's book correctly. Keeping them would create a "(Blank)" client in every report. |
| **Risk** | 200 of 298,772 rows (0.07%) leave the transaction totals; the quarantine file keeps them traceable. |

## 9. fact_portfolio_snapshot — return_ytd as percent strings
| Field | |
|---|---|
| **Table / column** | fact_portfolio_snapshot / return_ytd |
| **Evidence** | 300 rows hold strings like "9.28%" while all others are decimals (0.0928). Default parsing would make these 100× too large or NaN. |
| **Dimension violated** | Validity, Consistency |
| **Decision** | Convert: strip "%", divide by 100 |
| **Justification** | Reconciled, not assumed: after /100 every one of the 300 equals benchmark_return_ytd + active_alpha_ytd within rounding (the % strings were rounded to 2 decimals). |
| **Risk** | None if the reconciliation passes; the script stops if any row misses. |

## 10. fact_portfolio_snapshot — active_alpha_ytd in scientific notation
| Field | |
|---|---|
| **Table / column** | fact_portfolio_snapshot / active_alpha_ytd |
| **Evidence** | 756 values like "-1.9e-05". |
| **Dimension violated** | Consistency (format only) |
| **Decision** | Rewrite as fixed decimal (-0.000019) |
| **Justification** | Same value; some BI tools import "e" values as text. |
| **Risk** | None; script asserts the numeric value is unchanged. |

## 11. fact_portfolio_snapshot — extreme YTD returns
| Field | |
|---|---|
| **Table / column** | fact_portfolio_snapshot / return_ytd, aum |
| **Evidence** | 977 rows have \|return_ytd\| above 100% (max 9,467%); some accounts sit at an AUM of exactly 1,000.00. Example: client 29 sits at AUM 1,000.00 with return -97.7% in early 2021, then shows +287% YTD by mid-2022. |
| **Dimension violated** | Accuracy/Plausibility |
| **Decision** | Flag (`flag_extreme_return`), leave values |
| **Justification** | Looks like return computed from AUM change including deposits and withdrawals. A true time-weighted return can't be rebuilt from this extract, so any fix would be invented. |
| **Risk** | Averages of return/alpha will be distorted unless flagged rows are excluded; called out in the report. |

## 12. fact_portfolio_snapshot — account_type "529"
| Field | |
|---|---|
| **Table / column** | fact_portfolio_snapshot / account_type; dim_client / primary_account_type |
| **Evidence** | 26,882 snapshot rows and 523 clients have "529", which looks numeric. Snapshot account_type matches dim_client on 100% of rows. |
| **Dimension violated** | None (legitimate value) |
| **Decision** | **Leave as is**; document as text column |
| **Justification** | 529 is a college-savings plan name, not a number. |
| **Risk** | A BI tool auto-typing the column as number would break it; covered in README_clean.md. |

## 13. dim_security — blank sector and expense ratio
| Field | |
|---|---|
| **Table / column** | dim_security / sector, expense_ratio_bps |
| **Evidence** | Sector blank on 219 rows = exactly the 219 ETFs. Expense ratio blank on 281 rows = exactly the 281 single securities. |
| **Dimension violated** | None (legitimate structure) |
| **Decision** | **Leave as is** |
| **Justification** | ETFs span sectors; single stocks have no expense ratio. |
| **Risk** | None. |

## 14. dim_advisor — certifications "None"
| Field | |
|---|---|
| **Table / column** | dim_advisor / certifications |
| **Evidence** | 6 advisors have the literal text "None". Default pandas parsing turns this into NaN. |
| **Dimension violated** | None if read as text |
| **Decision** | **Leave as is** |
| **Justification** | It means "no certification", which is a real answer, not a missing value. |
| **Risk** | Must be read as text downstream (documented). |

## 15. dim_date — is_trading_day
| Field | |
|---|---|
| **Table / column** | dim_date / is_trading_day |
| **Evidence** | 522 non-trading days = exactly the weekends in 2020–2024; holidays (e.g. Jan 1, Dec 25) are marked trading days. All other date attributes agree with the date (0 errors). |
| **Dimension violated** | Accuracy (minor) |
| **Decision** | **Leave as is**; listed as known limitation |
| **Justification** | Fixing needs an outside NYSE holiday calendar; not needed for monthly reporting. |
| **Risk** | Daily trading-day counts are overstated by ~9–10 days a year. |

## 16. fact_fees — no defects
| Field | |
|---|---|
| **Table / column** | fact_fees / all |
| **Evidence** | amount = aum_basis × bps / 10,000 / 12 on all 122,197 rows; aum_basis equals the same client-month snapshot AUM on all rows; no duplicates, no orphan keys, advisor matches dim_client. |
| **Dimension violated** | None |
| **Decision** | **Leave as is** |
| **Justification** | Verified against two independent sources. |
| **Risk** | None. |
