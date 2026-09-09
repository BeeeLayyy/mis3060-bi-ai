# HW1 — Part 3: Prompt Engineering Comparison

**Course:** MIS3060 Business Intelligence with AI — Villanova University
**Student:** Brandon Le
**Tool:** Claude Desktop (Cowork), Wildcat Capital project

**Analytical question chosen:**
> *"What are the most important metrics for measuring credit risk in a consumer loan portfolio?"*

Each strategy below was run in a **new conversation inside the Wildcat Capital project** so prior context did not carry over. Strategy 1 (zero-shot) was run first as a genuine baseline before any related context was introduced.

---

## Strategy 1 — Zero-shot

**Complete prompt sent (copied exactly):**

> What are the most important metrics for measuring credit risk in a consumer loan portfolio?

**First 150 words of Claude's response:**

> Measuring credit risk in a consumer loan portfolio usually comes down to a handful of core metrics that fall into a few groups. At the borrower level, the most important is the **credit score** (e.g., FICO), which summarizes repayment history, followed by the **debt-to-income (DTI) ratio**, which measures how stretched a borrower's income already is, and **income and employment stability**. At the loan level, lenders track the **delinquency rate** (loans past due), the **default rate**, and the **charge-off rate** (loans written off as uncollectible). Portfolio-level metrics include the **probability of default (PD)**, **loss given default (LGD)**, and **exposure at default (EAD)**, which combine into **expected loss**. Analysts also watch the **loan-to-value ratio** on secured loans, the **net charge-off rate**, and **portfolio concentration** by segment. Finally, forward-looking measures like **roll rates** and **vintage analysis** help predict where losses are heading rather than just where they are.

*[150-word cutoff]*

**Evaluation — what it did well / what was missing or generic:**
The zero-shot answer is technically accurate and comprehensive; it correctly names the standard borrower-, loan-, and portfolio-level metrics and even reaches PD/LGD/EAD. Its weakness is that it is completely generic — it reads like a textbook glossary with no awareness of Wildcat Capital, its five loan purposes, its four status categories, or the fact that we have exactly three borrower attributes (credit score, DTI, income). It lists everything without prioritizing, so it gives no guidance on which metrics matter *most* for a lender like ours, and it includes metrics we can't even compute from our data (LTV, EAD). Useful as a checklist, weak as decision support.

---

## Strategy 2 — Role-assigned (role + audience)

**Complete prompt sent (copied exactly):**

> You are a senior credit risk analyst at Wildcat Capital, a regional consumer lender. You are presenting to our portfolio committee — three senior executives who are smart but not technical and who have limited time. In plain, decision-oriented language, tell them the most important metrics for measuring credit risk in our consumer loan portfolio, and for each one explain briefly why it matters and what threshold or trend should worry them. Keep it focused on what actually drives decisions.

**First 150 words of Claude's response:**

> Here are the five credit-risk metrics I'd ask this committee to watch, in priority order.
>
> **1. Delinquency rate (our early-warning signal).** This is the share of active loans that are behind on payments. It matters because delinquency is the pipeline that feeds future defaults — if it rises this quarter, losses rise next quarter. Watch the trend, not just the level: any sustained quarter-over-quarter increase is the first thing that should worry us.
>
> **2. Default / charge-off rate (realized losses).** This is money we've likely lost. It's a lagging indicator, so by the time it moves the damage is done; we track it to size reserves and confirm whether our underwriting is holding.
>
> **3. Debt-to-income (DTI) ratio.** DTI measures whether a borrower's income can absorb the payment. As a rule of thumb, a DTI above 43% is the standard regulatory threshold above which a borrower is considered high risk, so concentration above that line is worth flagging.

*[150-word cutoff]*

**Evaluation — what it did well / what was missing or generic:**
The role and audience transformed the output. Instead of an undifferentiated list, it prioritized the metrics ("in priority order"), translated each into plain-English executive language, and attached a "what should worry you" trend or threshold to each — which is exactly what a committee needs. It correctly elevated the delinquency rate as the leading indicator, matching the business logic from Part 2. The main risk introduced by this strategy is overconfidence: to sound authoritative for executives it stated a specific numeric threshold (DTI above 43%) as settled fact, which is precisely the kind of confident-but-shaky claim that needs fact-checking (see below). It was also lightly Wildcat-flavored but still didn't use our five purposes or four statuses explicitly.

---

## Strategy 3 — Few-shot

**Complete prompt sent (copied exactly):**

> I'm documenting credit-risk metrics for Wildcat Capital in a consistent format. Here is the exact format I want you to use for each metric — this example is just to show the structure, it is not one of the metrics I'm asking about:
>
> ---
> **Metric:** Application Approval Rate
> **What it measures:** The share of loan applications that are approved.
> **Why it matters:** Signals how tight or loose our underwriting is.
> **Data needed:** Count of applications, count of approvals.
> **Watch for:** A sudden jump may mean standards are slipping.
> ---
>
> Using that exact format, give me the most important metrics for measuring credit risk in a consumer loan portfolio.

**First 150 words of Claude's response:**

> ---
> **Metric:** Delinquency Rate
> **What it measures:** The share of active loans that are past due but not yet defaulted.
> **Why it matters:** It's the earliest warning that losses are building; delinquent loans feed future defaults.
> **Data needed:** Loan status field (Current, Delinquent, Default, Paid Off); count of Delinquent ÷ count of active loans.
> **Watch for:** Any sustained quarter-over-quarter rise, especially concentrated in one loan purpose.
>
> ---
> **Metric:** Default Rate
> **What it measures:** The share of loans that have failed and are unlikely to be repaid on original terms.
> **Why it matters:** Represents realized/near-certain losses and drives reserve levels.
> **Data needed:** Count of loans in Default status ÷ total originated loans.
> **Watch for:** A rising rate relative to prior vintages, or one segment defaulting faster than the book.
>
> ---
> **Metric:** Debt-to-Income (DTI) Ratio
> **What it measures:** Share of a borrower's income already committed to debt payments.
> **Why it matters:** Measures capacity to absorb the loan payment.

*[150-word cutoff]*

**Evaluation — what it did well / what was missing or generic:**
Few-shot produced the most immediately usable output for a BI analyst. By showing one example "card," the response adopted the exact structure for every metric — and, unprompted, wired in Wildcat's actual status categories (Current, Delinquent, Default, Paid Off) into the "Data needed" line, making each metric directly actionable against our dataset. The "Data needed" field is especially valuable because it maps each metric to fields we do or don't have, surfacing feasibility. The trade-off is that the rigid template slightly flattens nuance: the format has no room to explain how metrics *interact* (e.g., that delinquency leads default), which the zero-shot and role versions conveyed better in prose. Format control came at a small cost to narrative reasoning.

---

## Conclusion — comparing the three strategies

For a BI analyst, the **few-shot** strategy produced the most useful output because format control forced consistency and, as a side effect, pulled the answer closest to Wildcat's actual data by embedding our status fields and a "data needed" line that flags feasibility for each metric. The **role-assigned** strategy was a close second and would be the better choice for the *communication* step — presenting to the portfolio committee — because it prioritized metrics and translated them into decision-relevant thresholds and trends, though that same push for authority made it the version most prone to stating a shaky number as fact. The **zero-shot** baseline was accurate but generic: a good checklist of what exists, with no prioritization, no Wildcat context, and several metrics we can't even compute. The clear lesson is that adding structure (few-shot) or role and audience (role-assigned) moves Claude from "correct in general" to "useful for this specific analyst and this specific portfolio" — and that the more confident an unprompted output sounds, the more it needs verifying.

---

## Fact-Check

**1. The exact claim Claude made (quoted):**
From the Strategy 2 (role-assigned) response:
> *"As a rule of thumb, a DTI above 43% is the standard regulatory threshold above which a borrower is considered high risk..."*

**2. Source used:**
Consumer Financial Protection Bureau (CFPB) — *Qualified Mortgage Definition under the Truth in Lending Act (Regulation Z): General QM Loan Definition* (final rule, issued Dec. 10, 2020; 85 FR 86308).
URL: https://www.consumerfinance.gov/rules-policy/final-rules/qualified-mortgage-definition-under-truth-lending-act-regulation-z-general-qm-loan-definition/

**3. What the source says:**
The 43% DTI figure was real, but it was specific to the **Qualified Mortgage (QM)** rule for *mortgages*, not a general threshold for all consumer lending. More importantly, the CFPB has since changed it. The 2020 General QM final rule states that it **"removes the General QM loan definition's 43 percent DTI limit and replaces it with price-based thresholds."** In other words, the hard 43% DTI cap was eliminated and replaced with an approach based on the loan's price (its rate spread over a benchmark) rather than a single DTI number.

**4. Do they agree — and what I conclude:**
They **partially agree, but Claude's claim is misleading and outdated.** Claude was right that 43% DTI has been an influential industry benchmark, but wrong in three ways: (a) it framed 43% as a threshold for *consumer lending broadly*, when it applied specifically to *mortgages*; (b) it presented the number as a current "standard regulatory threshold," when the CFPB removed the hard 43% limit and replaced it with price-based thresholds; and (c) it stated all this with executive-facing confidence and no caveat. The conclusion for reliability: Claude is dependable for *concepts and directional reasoning* (high DTI does signal higher risk), but specific numeric thresholds, regulatory citations, and "standard" figures are exactly where it is most likely to be confidently wrong or out of date. Any hard number Claude produces — especially one tied to a regulation — should be verified against the primary regulator before it goes into a deliverable. This is the discipline the role-assigned strategy makes most necessary, because that framing is the one that pushes Claude to sound most authoritative.

**Sources:**
- [CFPB — Qualified Mortgage Definition under Regulation Z: General QM Loan Definition (final rule)](https://www.consumerfinance.gov/rules-policy/final-rules/qualified-mortgage-definition-under-truth-lending-act-regulation-z-general-qm-loan-definition/)
