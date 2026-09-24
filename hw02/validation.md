# HW2 Validation Record — fact_transactions.csv

## Part 1C — Run Log

Script ran without errors on the first attempt. No debugging needed.

---

## 2A — Known-Answer Benchmarks

| Check | Expected | Your Script Produced | Match? | Notes |
|---|---|---|---|---|
| Dataset shape | (298772, 9) | (298772, 9) | Yes | Shape warning did not fire |
| Null count — `security_id` | 101,597 | 101,597 | Yes | `shares` and `price` also have exactly 101,597 nulls |
| Null count — `amount` | 0 | 0 | Yes | |
| Unique `txn_type` values | 6 | 6 | Yes | |
| Count of `Buy` transactions | 83,556 | 83,556 | Yes | Also confirmed by cross-validation (2C) |
| `txn_date` data type | object | str | Yes (see note) | pandas 3.x reports text columns as `str` instead of `object`. Both mean the column is text, not a datetime, so the finding is the same |
| Earliest `txn_date` | 2020-01-01 | 2020-01-01 | Yes | |
| Latest `txn_date` | 2024-12-30 | 2024-12-30 | Yes | |
| Duplicate `txn_id` count | 0 | 0 | Yes | |
| Mean `amount` | $54,075.17 | $54,075.17 | Yes | |
| Median `amount` | $41,220.48 | $41,220.49 | Yes (rounding) | Exact median is 41,220.485 (average of the two middle values). Benchmark truncated, script rounded |
| Skewness of `amount` | 1.15 | 1.15 | Yes | Mean > median, consistent with right skew |
| Correlation `shares`–`amount` | 0.65 | 0.65 | Yes | |
| Correlation `price`–`amount` | 0.64 | 0.64 | Yes | |
| Correlation `shares`–`price` | 0.00 | 0.00 | Yes | |
| Negative `shares` count (Buy only) | 836 | 836 | Yes | All 836 are Buy; min is −499.63 |
| Profile file created | Yes | Yes | Yes | `hw02/hw02_profile.txt` |
| Chart files created (3) | Yes | Yes | Yes | All three saved in `hw02/charts/` |

No true mismatches, so no Claude Cowork investigation was needed for this section.

---

## 2B — Explain the Code and Output

Review done in a new Claude chat, separate from the session that generated the script.

1. **Did Claude's predictions match the terminal?** Mostly yes. Claude said it couldn't give data values without the CSV, so it predicted structure and got that right: section order, the shape line, 0 duplicates expected, right skew with mean above median, NaN shares for non-trade types, and the three "Saved" chart lines. Discrepancies: (a) it predicted `txn_date` as `object`, but pandas 3 printed `str`; (b) it guessed Dividends would have null shares and price, but Dividends actually have shares, and the nulls are Deposit, Withdrawal, and Advisory Fee; (c) it said negative shares would most likely show up on Sells, but all 836 negatives are on Buys.

2. **What Claude flagged in the output:** (1) the 836 negative-share Buys; (2) Dividend amounts averaging about $64K, which looks like full position value (shares x price) rather than a realistic payout; (3) client_id max is 3,192 but only 2,700 clients appear, so 492 IDs are unused; (4) Advisory Fee outliers (median $859 vs mean $7,375); (5) no transactions on Dec 31, 2024; (6) amounts are all positive, so money direction has to come from `txn_type` before computing net flows. It also noted the round type percentages suggest synthetic data.

3. **The 101,597 nulls:** Yes. Claude showed they equal Deposit (35,981) + Advisory Fee (35,766) + Withdrawal (29,850) = 101,597, and called them structural because those transaction types don't involve a security. Not a data quality problem.

4. **`txn_date`:** Yes. Claude flagged it as a string, not a date, and said to parse it with `pd.to_datetime` before any time-based work. For time-series analysis this matters because you can't do date math (days between transactions), resample by month or quarter, or use date-aware plotting on text values.

5. **Charts vs. Claude's explanation:**
   - Histogram: matches. Right-skewed, with the red mean line ($54,075) to the right of the green median line ($41,220).
   - Box plot: matches. One horizontal box per type in the same order as the grouped table. Advisory Fee is much lower and tighter than the other types, with outliers stretching right, which fits Claude's point about fee outliers.
   - Scatter: matches Claude's description (only Buy, Sell, Dividend plotted, gray line at zero). One thing Claude didn't predict: the negative-share Buys form a separate cluster to the left of zero with positive amounts, a mirror image of the main group. Sells also plot on top of Buys, so most Buy points are hidden on the positive side.

6. **Follow-up question and answer:**

   > **Me:** You said the 836 negative-share Buys are errors. Couldn't some of them be legitimate reversal or correction entries that cancel an earlier Buy? How would I tell the difference?
   >
   > **Claude:** Yes, they could be. It said it jumped to "errors" too fast and "unexplained" is more accurate. A true reversal should mirror an earlier Buy: same client_id and security_id, same absolute share count and amount, dated on or after the original. It gave code to merge negative Buys against positive Buys on client, security, and absolute shares and count how many have a match. If most match within a few days, they're reversals; if few or none match, they're bad data. It also pointed out that the amounts are positive on these rows, so even real reversals would be miscounted as extra purchases, and that 836 is almost exactly 1% of Buys, which could mean deliberately injected noise. Real reversals tend to cluster by advisor or date.

---

## 2C — Business Check & Cross-Validation

### Business-reasonableness

1. I'd expect Deposits, Withdrawals, and Fees to have no security. They're just cash moving in or out of an account, so there's no stock involved and nothing to fill in for security_id, shares, or price. To check if they add up to 101,597, I'd filter to rows where all three columns are null and run value_counts on txn_type. If those three types make up all the null rows, the nulls are expected and not actually missing data. If another type shows up, like dividends, that's something to look into.

2. It means clients are mostly adding to their investments over time instead of pulling out. That could come from new deposits getting invested, dividend reinvestment, or clients buying in smaller chunks on a regular basis. For a wealth firm, that's generally a good sign of growing assets. But this only compares the number of trades, not the dollar amounts, so I'd want to compare total dollars bought vs. sold before drawing a real conclusion.

3. Since the dates are text, Python can't subtract them, so the calculation would just throw an error. Sorting would also be off because strings sort alphabetically, not by date. For example, "12/1/2022" would come before "5/10/2023" alphabetically, which happens to be right here, but "10/1/2023" would come before "9/1/2023", which is wrong. You'd need to convert the column with pd.to_datetime before doing any date math.

4. Yeah, I think it's plausible. Advisors at RIAs usually handle somewhere around 50 to 150 clients, so 108 is on the higher end but still realistic, especially if advisors have support staff or if "clients" means individual accounts rather than households.

5. One explanation is that these are reversals or corrections, where a buy got cancelled and was recorded as a negative Buy to undo it. Another is that they're data errors, like sells that were miscoded as Buys or a system that stores shares with a sign. To figure out which, I'd check whether each negative Buy has a matching positive Buy with the same client, security, and share amount around the same date. If most of them match, they're probably reversals. If they don't match and they're clustered in a certain time period or advisor, it's more likely a data issue.

### Cross-validation

6. Prompt A (direct filter) returned **83,556**. Prompt B (total 298,772 minus 215,216 non-Buy rows) returned **83,556**.

7. Both agree, and both match the benchmark.

8. Subtraction gives you an independent check. When you filter directly, you only catch values you expect, so things like "buy" in lowercase, extra spaces, or nulls can slip through. Subtracting everything else from the total accounts for every row, so if the two numbers don't match, you know there's something in the data you missed.
