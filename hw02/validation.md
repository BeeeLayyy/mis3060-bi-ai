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

6. **Follow-up question and answer** (pasted from the review chat):

   **My question:** You said the 836 negative-share Buys are errors. Couldn't some of them be legitimate reversal or correction entries that cancel an earlier Buy? How would I tell the difference?

   **Claude's answer:**

   > Yes, they could be. I jumped to "errors" too fast; "unexplained" is more accurate. Negative quantities are a common way to book a reversal. The dataset has no reversal flag or original_txn_id column, though, so you have to infer it from the data.
   >
   > **What a reversal would look like**
   >
   > A true reversal should mirror an earlier Buy:
   >
   > - same client_id and security_id
   > - same absolute share count (and usually the same price and amount)
   > - dated on or after the original, usually within days
   >
   > Example: txn 5001 is a Buy on 2023-03-10: client 42, security 17, 150.25 shares at $80 = $12,020. If txn 5090 on 2023-03-12 is a Buy for client 42, security 17, -150.25 shares, $12,020, that's almost certainly a cancel. If there's no matching positive Buy anywhere, it's a bad row.
   >
   > **How to check**
   >
   > ```python
   > buys = df[df["txn_type"] == "Buy"].copy()
   > buys["txn_date"] = pd.to_datetime(buys["txn_date"])
   > buys["abs_shares"] = buys["shares"].abs().round(2)
   >
   > neg = buys[buys["shares"] < 0]
   > pos = buys[buys["shares"] > 0]
   >
   > m = neg.merge(pos, on=["client_id", "security_id", "abs_shares"],
   >               suffixes=("_rev", "_orig"))
   > m = m[m["txn_date_orig"] <= m["txn_date_rev"]]
   > m["days_apart"] = (m["txn_date_rev"] - m["txn_date_orig"]).dt.days
   >
   > print("Negatives with a matching earlier Buy:", m["txn_id_rev"].nunique(), "of", len(neg))
   > print(m["days_apart"].describe())
   > print("Amount matches:", (m["amount_rev"].round(2) == m["amount_orig"].round(2)).mean())
   > ```
   >
   > **How to read the results**
   >
   > - Most negatives match, usually within a few days, with equal amounts: they're reversals. Net them against the originals, or drop both rows.
   > - Few or none match: they're bad data. Shares are recorded to 2 decimals across 500 securities and 2,700 clients, so accidental matches are very unlikely. Even a handful of matches means something.
   > - A mix: treat the matched rows as reversals and the rest as errors, and document both counts.
   >
   > **Two other clues**
   >
   > Amount is positive on these rows. If a reversal carries a positive amount, a naive "Buy = money out" calculation counts it as a second purchase instead of cancelling the first. So even if they are real reversals, you'd need to handle them explicitly.
   >
   > The pattern looks random. 836 is almost exactly 1% of Buys. If the negatives are spread evenly across dates, advisors, and securities, that looks like deliberately injected noise, which is common in class datasets built to test EDA. Check with neg["advisor_id"].value_counts() and neg["txn_date"].dt.year.value_counts(). Real reversals tend to cluster around specific advisors, operations issues, or dates.

---

## 2C — Business Check & Cross-Validation

### Business-reasonableness

1. I'd expect Deposits, Withdrawals, and Fees to have no security. They're just cash moving in or out of an account, so there's no stock involved and nothing to fill in for security_id, shares, or price. To check if they add up to 101,597, I'd filter to rows where all three columns are null and run value_counts on txn_type. If those three types make up all the null rows, the nulls are expected and not actually missing data. If another type shows up, like dividends, that's something to look into. And they do add up: Deposit (35,981) + Withdrawal (29,850) + Advisory Fee (35,766) = 101,597, which matches the null count exactly.

2. It means clients are mostly adding to their investments over time instead of pulling out. That could come from new deposits getting invested, dividend reinvestment, or clients buying in smaller chunks on a regular basis. For a wealth firm, that's generally a good sign of growing assets. The dollar totals back this up, not just the trade counts: Buys add up to about $5.33 billion versus about $3.80 billion for Sells, so roughly $1.5 billion more went into securities than came out over the five years.

3. Since the dates are text, Python can't subtract them. Subtracting one string from another throws an error, so the average-days calculation would fail before it produced anything. Grouping by month or year and resampling a time series wouldn't work either, because pandas only treats the values as dates once they're converted. Sorting is the one thing that happens to work here: every date is stored as YYYY-MM-DD (like 2023-05-29), so alphabetical order and date order line up, and that's why the min and max dates in the profile are correct. The fix is to convert the column with pd.to_datetime before doing any date math.

4. Yeah, I think it's plausible. Advisors at RIAs usually handle somewhere around 50 to 150 clients, so 108 is on the higher end but still realistic, especially if advisors have support staff or if "clients" means individual accounts rather than households.

5. One explanation is that these are reversals or corrections, where a Buy got cancelled and was recorded as a negative Buy to undo it. The other is that they're data errors, like a sign flipped during data entry, or Sells miscoded as Buys. To tell them apart, I checked whether each negative Buy has a matching earlier positive Buy with the same client, security, and share amount. None of the 836 do (0 matches). They're also spread across all 25 advisors (no more than 47 for any one advisor) and every year from 2020 to 2024, instead of clustering around one advisor or time period. Their amounts are all positive too, so they don't cancel anything out in dollars. That points to data errors rather than real reversals. Next I'd ask the data owner how reversals are supposed to be recorded, and I'd leave these 836 rows out of (or flag them in) any share-based analysis until that's answered.

### Cross-validation

6. Prompt A (direct filter) returned **83,556**. Prompt B (total 298,772 minus 215,216 non-Buy rows) returned **83,556**.

7. Both agree, and both match the benchmark.

8. Subtraction gives you an independent check. When you filter directly, you only catch values you expect, so things like "buy" in lowercase, extra spaces, or nulls can slip through. Subtracting everything else from the total accounts for every row, so if the two numbers don't match, you know there's something in the data you missed.
