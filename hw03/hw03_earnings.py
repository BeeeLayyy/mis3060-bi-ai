"""
HW3 Part 2: Earnings pipeline (SEC 8-K Item 2.02)
Pulls the 4 most recent earnings press releases per company from EDGAR,
extracts revenue, diluted EPS, net income and period, and saves a CSV.

Run from the repo root:  python hw03/hw03_earnings.py
"""
import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------- config
USER_AGENT = "MIS3060 Villanova ble02@villanova.edu"
HEADERS = {"User-Agent": USER_AGENT}
OUT_CSV = Path(__file__).resolve().parent / "earnings_history.csv"
FILINGS_PER_COMPANY = 4
NF = "NOT_FOUND"

COMPANIES = [
    ("Apple Inc.", "AAPL", "0000320193"),
    ("Microsoft Corporation", "MSFT", "0000789019"),
    ("NVIDIA Corporation", "NVDA", "0001045810"),
    ("JPMorgan Chase & Co.", "JPM", "0000019617"),
    ("Walmart Inc.", "WMT", "0000104169"),
]
COLUMNS = ["company", "ticker", "cik", "filing_date", "period",
           "revenue_reported", "eps_diluted", "net_income"]

# ---------------------------------------------------------------- http
def get(url):
    """Every HTTP call goes through here, so the User-Agent is always set."""
    time.sleep(0.15)                      # SEC limit is 10 requests/second
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def find_filings(cik, item, limit=None):
    """Return 8-K filings (newest first) whose items include `item`."""
    data = get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()
    blocks = [data["filings"]["recent"]]
    extra_files = [f["name"] for f in data["filings"].get("files", [])]

    results = []
    while blocks:
        block = blocks.pop(0)
        for i, form in enumerate(block["form"]):
            if form != "8-K":
                continue
            items = [x.strip() for x in (block["items"][i] or "").split(",")]
            if item in items:
                results.append({
                    "accession": block["accessionNumber"][i],
                    "filing_date": block["filingDate"][i],
                    "primary_doc": block["primaryDocument"][i],
                })
        # only page into older files if we still need more filings
        if limit and len(results) < limit and extra_files:
            blocks.append(get(f"https://data.sec.gov/submissions/{extra_files.pop(0)}").json())

    results.sort(key=lambda r: r["filing_date"], reverse=True)
    return results[:limit] if limit else results


def filing_base_url(cik, accession):
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/"


def find_press_release(cik, accession):
    """Parse the filing index page and return the EX-99.1 (press release) URL."""
    base = filing_base_url(cik, accession)
    soup = BeautifulSoup(get(base + f"{accession}-index.htm").text, "html.parser")

    docs = []
    for tr in soup.select("table.tableFile tr"):
        tds = tr.find_all("td")
        if len(tds) < 4 or not tds[2].find("a"):
            continue
        name = tds[2].find("a").get("href", "").split("/")[-1]   # handles /ix?doc= links
        doc_type = tds[3].get_text(strip=True).upper()
        if name.lower().endswith((".htm", ".html")):
            docs.append((doc_type, name))

    for prefix in ("EX-99.1", "EX-99"):
        for doc_type, name in docs:
            if doc_type.startswith(prefix):
                return base + name
    for _, name in docs:
        if re.search(r"ex-?99", name, re.I):
            return base + name
    return None


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ").replace("\xa0", " ")
    return re.sub(r"\s+", " ", text)

# ---------------------------------------------------------------- extraction
NUM = r"([\d,]+(?:\.\d+)?)"
UNIT = r"\s*(billion|million)"

REVENUE_PROSE = [
    r"revenue for the [^$]{0,80}?of \$\s?" + NUM + UNIT,
    r"revenues?\s+(?:record\s+)?(?:was|were|of|totaled|increased to|grew to|rose to|reached)\s+"
    r"(?:a\s+)?(?:record\s+)?\$\s?" + NUM + UNIT,
]
REVENUE_TABLE = [   # income statement rows, already in millions
    r"(?:Total net sales|Total net revenues?|Total revenues?|Net revenues?)\s*\$\s*([\d,]{4,}(?:\.\d+)?)",
]
EPS_PATTERNS = [
    r"diluted (?:earnings|net income) per (?:common )?share (?:for the quarter )?(?:was|were|of)\s+\$\s?(\d+\.\d{2})",
    r"earnings per diluted share (?:for the quarter )?(?:was|were|of)\s+\$\s?(\d+\.\d{2})",
    r"(?<!non-)GAAP EPS (?:of|was)\s+\$\s?(\d+\.\d{2})",
    r"\(\s?\$\s?(\d+\.\d{2}) per (?:diluted )?share\)",     # JPM headline: "NET INCOME OF $21.2 BILLION ($7.70 PER SHARE)"
    r"(?<!dividend of )(?<!billion )or \$\s?(\d+\.\d{2}) per (?:diluted )?share",   # skip "dividend of $4.0 billion or $1.50 per share"
]
EPS_TABLE = [r"(?:Diluted(?: earnings per share)?|Earnings per share\s*-\s*diluted)\s*\$\s*(\d+\.\d{2})"]
NET_INCOME_PROSE = [
    r"(?<!non-GAAP )(?<!adjusted )net income,? (?:on a GAAP basis,? )?(?:attributable to [A-Za-z.&\s]{1,40}?)?"
    r"(?:was|of|totaled)\s+\$\s?" + NUM + UNIT,
]
NET_INCOME_TABLE = [
    r"Net income attributable to (?!noncontrolling)[^$\d]{0,40}?\$\s*([\d,]{3,}(?:\.\d+)?)",
    r"Net income[^$\d]{0,40}?\$\s*([\d,]{3,}(?:\.\d+)?)",
]
PERIOD_PATTERNS = [
    r"\b((?:first|second|third|fourth)[\s-]quarter(?: of)? fiscal(?: year)? (?:\d{4}|'?\d{2}))",
    r"\b(fiscal(?: year)? \d{4} (?:first|second|third|fourth)[\s-]quarter)",
    r"\b((?:first|second|third|fourth)[\s-]quarter ended [A-Za-z]+\.? \d{1,2}, \d{4})",
    r"\b((?:first|second|third|fourth)[\s-]quarter(?: of)? \d{4})",
    r"\b(Q[1-4]\s?(?:FY|fiscal )\s?'?\d{2,4})",
    r"\b([1-4]Q\s?\d{2,4})",
    r"\b(quarter ended [A-Za-z]+\.? \d{1,2}, \d{4})",
]


def earliest(patterns, text):
    """Return the match that appears earliest in the text across all patterns."""
    best = None
    for p in patterns:
        m = re.search(p, text, re.I)
        if m and (best is None or m.start() < best.start()):
            best = m
    return best


def to_millions(num, unit=None):
    value = float(num.replace(",", ""))
    if unit and unit.lower().startswith("b"):
        value *= 1000
    return round(value, 1)


def extract_money(text, prose, table):
    m = earliest(prose, text)
    if m:
        return to_millions(m.group(1), m.group(2))
    for pattern in table:                 # table patterns are tried in priority order
        m = re.search(pattern, text, re.I)
        if m:
            return to_millions(m.group(1))
    return NF


def extract_fields(text):
    eps = earliest(EPS_PATTERNS, text) or earliest(EPS_TABLE, text)
    period = earliest(PERIOD_PATTERNS, text)
    return {
        "period": period.group(1).strip() if period else NF,
        "revenue_reported": extract_money(text, REVENUE_PROSE, REVENUE_TABLE),
        "eps_diluted": float(eps.group(1)) if eps else NF,
        "net_income": extract_money(text, NET_INCOME_PROSE, NET_INCOME_TABLE),
    }


def fmt_m(v):
    return f"${v:,.1f}M" if isinstance(v, float) else v

# ---------------------------------------------------------------- main
def main():
    rows = []
    for company, ticker, cik in COMPANIES:
        try:
            filings = find_filings(cik, "2.02", limit=FILINGS_PER_COMPANY)
        except Exception as e:
            print(f"WARNING [{ticker}]: could not load EDGAR submissions ({e})")
            continue
        if not filings:
            print(f"WARNING [{ticker}]: no Item 2.02 filings found")
            continue

        for f in filings:
            row = {"company": company, "ticker": ticker, "cik": cik,
                   "filing_date": f["filing_date"], "period": NF,
                   "revenue_reported": NF, "eps_diluted": NF, "net_income": NF}
            try:
                url = find_press_release(cik, f["accession"])
                if not url:
                    print(f"WARNING [{ticker}] {f['filing_date']}: no press release exhibit found, skipping")
                    rows.append(row)
                    continue
                row.update(extract_fields(html_to_text(get(url).text)))
            except Exception as e:
                print(f"WARNING [{ticker}] {f['filing_date']}: {e}")
            rows.append(row)
            eps = f"${row['eps_diluted']:.2f}" if isinstance(row["eps_diluted"], float) else NF
            print(f"[{ticker}] | {row['period']} | Revenue: {fmt_m(row['revenue_reported'])} "
                  f"| EPS: {eps} | Net Income: {fmt_m(row['net_income'])}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} rows to {OUT_CSV} (revenue and net income in $ millions)")


if __name__ == "__main__":
    main()
