# HW1 — Part 2: Business Context Exploration

**Course:** MIS3060 Business Intelligence with AI — Villanova University
**Student:** Brandon Le
**Company context:** Wildcat Capital, a regional consumer lender (2,340 loan records)
**Tool:** Claude Desktop (Cowork), Wildcat Capital project

> Note on count: The Part 2 body asks for three questions, but the submission checklist and rubric ask for five. To satisfy the rubric, five grounded strategic questions are documented below. Questions 1–3 cover the three required topics (credit risk metrics, portfolio committee review, delinquency vs. default). Questions 4–5 are additional strategic questions grounded in Wildcat's data.

---

## Question 1 — Credit risk metrics applied to Wildcat's attributes

**Exact prompt sent:**

> I'm a junior BI analyst at Wildcat Capital, a regional consumer lender. Each of our loan records carries three borrower attributes: credit score, debt-to-income (DTI) ratio, and annual income. Before we build analytics on these, I want to understand what they actually mean as credit risk metrics. For consumer lending specifically, what does each of these three attributes tell a lender about the likelihood of repayment, and how do they interact with each other? I'm not asking you to calculate anything from our data — I want the conceptual grounding.

**Summary of Claude's response (3–5 sentences):**
Credit score is a standardized snapshot of a borrower's past repayment behavior and is used as the single best predictor of the probability of default, while DTI measures current capacity — how much of the borrower's income is already committed to debt, and therefore how much room they have to absorb a new payment. Annual income sets the absolute ceiling on what a borrower can afford and is used to size the loan, but on its own it is a weak risk signal because a high earner can still be over-leveraged. The three are complementary rather than substitutable: a strong credit score does not cancel out a high DTI, and high income does not rescue a thin credit file. Lenders typically combine all three into risk tiers or a scorecard rather than gating on any one metric, because each captures a different dimension (willingness, capacity, and scale).

**Follow-up question this raised:**
If credit score captures *willingness* to repay and DTI captures *capacity*, which of the two tends to be the stronger early-warning signal when a previously-current borrower is about to become delinquent — and does that change by loan purpose?

---

## Question 2 — What a portfolio committee wants in a quarterly review

**Exact prompt sent:**

> At Wildcat Capital our portfolio spans five loan purposes — Auto, Personal, Home Improvement, Education, and Business. I'm preparing analytics that will eventually feed a quarterly portfolio committee review. For a consumer lender with this specific loan-purpose mix, what does a portfolio committee typically want to see each quarter, and why does each item matter to them? I want to understand the committee's priorities before I decide what to build.

**Summary of Claude's response (3–5 sentences):**
A portfolio committee generally opens with portfolio-level health — outstanding balance, number of active loans, and the split between performing and non-performing — then drills into performance *by segment*, because a blended number can hide a deteriorating pocket like Business or Education. Standard items include delinquency and default rates by loan purpose, roll-rate or vintage analysis to show whether newer loans are performing worse than older ones, concentration exposure (how much of the book sits in any one purpose), and yield-versus-loss so the committee can see whether the return on a segment justifies its risk. Committees also want quarter-over-quarter trend and adequacy of loss reserves or allowance, since their job is forward-looking risk governance, not just a status snapshot. The response emphasized that everything should be sliced by the five purposes because Wildcat's segments carry very different loss profiles.

**Follow-up question this raised:**
For a lender Wildcat's size, is vintage (cohort-by-origination-quarter) analysis realistically worth building with only 2,340 records, or does the sample get too thin once you split by five purposes and origination quarter?

---

## Question 3 — Delinquency vs. default, mapped to Wildcat's four statuses

**Exact prompt sent:**

> Our loan records use four status categories: Current, Paid Off, Default, and Delinquent. I keep seeing "delinquency" and "default" used almost interchangeably, but I suspect they mean different things and I want to map them correctly onto our four categories. What is the actual difference between delinquency and default in consumer lending, how do those two concepts relate to each other over the life of a troubled loan, and which of our four statuses does each one correspond to?

**Summary of Claude's response (3–5 sentences):**
Delinquency and default sit on a continuum rather than being two separate events: delinquency is the early, still-curable stage where a borrower has missed one or more scheduled payments but the loan is active and can return to good standing, while default is the severe, typically terminal stage where the borrower has failed to pay for long enough (often 90+ days past due, or after a charge-off) that the lender treats the debt as unlikely to be repaid on its original terms. Mapped onto Wildcat's four categories: *Current* is a performing loan that is paid up, *Paid Off* is a loan that was successfully closed, *Delinquent* is a loan that is behind but still active and recoverable, and *Default* is a loan that has crossed the threshold into serious, likely-unrecoverable non-payment. The key analytical point is that delinquency is a *leading* indicator and default is a *lagging* one — delinquent loans are the pipeline that feeds future defaults, so watching the delinquent bucket gives earlier warning than watching defaults.

**Follow-up question this raised:**
Since Wildcat only records a single current status per loan rather than days-past-due, we can't see *how* delinquent a loan is — should the analytics team push to capture a days-past-due field so we can distinguish 30-day from 90-day delinquency, or is the four-bucket status enough for portfolio-level reporting?

---

## Question 4 — Risk differences across the loan-purpose mix

**Exact prompt sent:**

> Wildcat's five loan purposes are Auto, Personal, Home Improvement, Education, and Business. Intuitively these feel like they carry very different risk, but I want to understand why. What structural differences between these purposes — collateral, loan size, borrower profile, and how the borrower's ability to repay is tied to the purpose — make some of these segments inherently riskier than others, and which ones should I expect to behave most differently from the rest?

**Summary of Claude's response (3–5 sentences):**
The response framed the differences around collateral and the source of repayment. Auto is secured by a depreciating but repossessable asset, so losses given default are cushioned; Home Improvement is often tied to home equity and tends to attract more established borrowers; Personal loans are usually unsecured, so a default means a near-total loss on that balance. Education and Business were flagged as the two that behave most differently: Education repayment depends on a future income stream that may not materialize on schedule, and Business loans are typically larger, more idiosyncratic, and tied to the success of a venture, which makes them the highest-severity segment even if not always the highest-frequency. The takeaway was that unsecured and future-income-dependent segments (Personal, Education, Business) deserve closer monitoring than the collateral-backed ones.

**Follow-up question this raised:**
If Business loans are individually large and idiosyncratic, does it make more sense to monitor them loan-by-loan (a watchlist) rather than as a statistical segment the way we'd treat Auto or Personal?

---

## Question 5 — Credit score bands and where to draw risk-tier cutoffs

**Exact prompt sent:**

> When we start segmenting Wildcat's borrowers by credit score, I'll need to group them into risk tiers rather than treating score as a raw number. In consumer lending, what are the conventional credit score bands (for example, where subprime, near-prime, and prime are usually drawn), where do those cutoffs come from, and what should I be careful about before hard-coding any specific threshold into our analytics?

**Summary of Claude's response (3–5 sentences):**
The response gave the conventional FICO framing — roughly 300–850 overall, with common industry bands such as subprime below about 620–660, near-prime in the 620s–670s to high 600s, prime in the low-to-mid 700s, and super-prime above about 780–800 — while stressing that these cutoffs are conventions, not fixed laws, and vary by lender, scoring model (FICO vs. VantageScore), and product. It cautioned that different score versions and vendors draw the lines differently, so a threshold copied from one source may not match Wildcat's own loss experience. The recommendation was to validate any band against Wildcat's actual default rates by score range before treating a cutoff as meaningful, rather than importing an external threshold wholesale.

**Follow-up question this raised:**
Should we define Wildcat's risk tiers empirically from our own default-rate-by-score curve instead of using the standard subprime/prime bands, and if so, is 2,340 records enough data to draw statistically stable cutoffs?
