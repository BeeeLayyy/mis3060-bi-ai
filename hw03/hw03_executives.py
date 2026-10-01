"""
HW3 Part 3: Executive events pipeline (SEC 8-K Item 5.02)
Finds Item 5.02 8-Ks from the past 12 months, extracts departures and
appointments (one row per person), and saves a CSV.

Run from the repo root:  python hw03/hw03_executives.py
"""
import csv
import re
import time
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------- config
USER_AGENT = "MIS3060 Villanova ble02@villanova.edu"
HEADERS = {"User-Agent": USER_AGENT}
OUT_CSV = Path(__file__).resolve().parent / "executive_events.csv"
NF = "NOT_FOUND"
CUTOFF = (date.today() - timedelta(days=365)).isoformat()

COMPANIES = [
    ("Apple Inc.", "AAPL", "0000320193"),
    ("Microsoft Corporation", "MSFT", "0000789019"),
    ("NVIDIA Corporation", "NVDA", "0001045810"),
    ("JPMorgan Chase & Co.", "JPM", "0000019617"),
    ("Walmart Inc.", "WMT", "0000104169"),
]
COLUMNS = ["company", "ticker", "cik", "filing_date", "event_type",
           "person_name", "title", "effective_date"]

# ---------------------------------------------------------------- http
def get(url):
    """Every HTTP call goes through here, so the User-Agent is always set."""
    time.sleep(0.15)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def find_recent_502(cik):
    """8-K filings with Item 5.02 filed on or after CUTOFF, newest first."""
    recent = get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()["filings"]["recent"]
    out = []
    for i, form in enumerate(recent["form"]):
        items = [x.strip() for x in (recent["items"][i] or "").split(",")]
        if form == "8-K" and "5.02" in items and recent["filingDate"][i] >= CUTOFF:
            out.append({"accession": recent["accessionNumber"][i],
                        "filing_date": recent["filingDate"][i],
                        "primary_doc": recent["primaryDocument"][i]})
    return out


def html_to_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ").replace("\xa0", " "))

# ---------------------------------------------------------------- extraction
DEPARTURE = re.compile(
    r"resign|retire|step(?:s|ping)? down|stepped down|depart|terminat|"
    r"not (?:to )?stand for re-?election|cease[sd]? to serve|"
    r"leav(?:e|ing) the company|transition(?:ing)? (?:out )?from|separat", re.I)
APPOINTMENT = re.compile(
    r"appoint|\belect(?:ed|s)?\b|\bnamed\b|promot|\bhired?\b|"
    r"will (?:become|join|serve)|to serve as|\bsucceeds?\b|join(?:s|ed)? the company", re.I)
TITLE = re.compile(
    r"((?:Senior |Executive |Corporate |Group |Lead |Independent )*(?:"
    r"[Pp]resident and [Cc]hief [Ee]xecutive [Oo]fficer|"
    r"chief (?:executive|financial|operating|accounting) officer|"
    r"Vice President|Vice Chair(?:man)?|"
    r"Chief [A-Z][a-z]+(?: [A-Z][a-z]+)?(?: and [A-Z][a-z]+)? Officer|"
    r"Principal (?:Accounting|Financial|Executive) Officer|"
    r"President|Chair(?:man|woman)?|Treasurer|Controller|[Gg]eneral [Cc]ounsel|"
    r"Corporate Secretary|Board of Directors|[Dd]irector))")
TITLE_AS = re.compile(r"\b(?:as|become) (?:the |a |its )?(?:Company's |member of the )?" + TITLE.pattern)
REPORTING_TO = re.compile(r"reporting (?:directly )?to(?: [A-Z]{2,5})?\s*$")   # "reporting to CEO Tim Cook" is a bystander
SUCCEEDS = re.compile(r"\b(?:succeeds?|succeeding|replaces?|replacing)\s*$")     # "Mr. Borders succeeds Chris Kondo": Kondo leaves
DATE = r"((?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4})"
EFFECTIVE = re.compile(r"effective (?:as of |on |upon )?(?:the close of business on )?" + DATE)

STOP = set("""
on in as of the a an and or to for by with at from upon following pursuant under effective
his her their its he she they we our company corporation inc co llc ltd board directors director
committee chief officer executive senior vice president chair chairman chairwoman financial operating
accounting technology information legal human resources people marketing revenue general counsel
treasurer controller secretary principal corporate group global item form exhibit section securities
exchange commission act agreement plan stock annual meeting shareholders shareholder stockholders
apple microsoft nvidia jpmorgan chase walmart us u.s. united states america new york california
january february march april may june july august september october november december
mr mrs ms dr also this that these such each
officers certain compensatory arrangements departure election appointment transition date since not
lead independent investment bank banking community consumer commercial asset wealth worldwide field
operations hardware engineering management development compensation equity incentive target award
opportunity non-competition agreements covenant psus rsus my
""".split())

RUN = re.compile(r"[A-Z][A-Za-z'\-]*\.?(?:\s+[A-Z][A-Za-z'\-]*\.?)*")
SENT_END = re.compile(r"(?<!Mr)(?<!Ms)(?<!Dr)(?<!Inc)(?<!Jr)(?<!Sr)(?<!Mrs)(?<!\b[A-Z])\.\s+(?=[A-Z])")


def item_502_section(text):
    """Return the longest Item 5.02 section in the filing, minus the boilerplate title."""
    best = ""
    for m in re.finditer(r"Item\s*5\.02", text, re.I):
        rest = text[m.end():]
        stop = re.search(r"Item\s*\d\.\d{2}|SIGNATURES?\b", rest, re.I)
        section = rest[:stop.start()] if stop else rest
        if len(section) > len(best):
            best = section
    best = re.sub(r"^\W*(?:\([a-z]\)\s*)?Departure of Directors.{0,250}?Compensatory Arrangements of Certain Officers\.?",
                  " ", best, flags=re.I | re.S)
    return best or text


def is_stop(token):
    t = token.strip(".,").lower()
    return t in STOP or (token.isupper() and len(token.strip(".")) > 2)


def find_people(section):
    """Return [(name, start, end)] for full names (2-4 capitalized words), first mention only.
    A word that also appears in lowercase in the section ("transition", "award") is an ordinary
    word, not part of a name, so any candidate containing one is dropped."""
    lower_words = set(re.findall(r"\b[a-z][a-z'\-]+\b", section))
    people, seen_last = [], set()
    for run in RUN.finditer(section):
        tokens = [(t.group(), run.start() + t.start(), run.start() + t.end())
                  for t in re.finditer(r"\S+", run.group())]
        group = []
        for tok in tokens + [("STOP", None, None)]:
            if tok[0] != "STOP" and not is_stop(tok[0]):
                group.append(tok)
                continue
            if (2 <= len(group) <= 4 and (len(group[0][0].strip(".")) > 1 or len(group) >= 3)   # allow "C. Douglas McMillon"
                    and not any(t[0].strip(".,").lower() in lower_words for t in group)):
                name = " ".join(t[0] for t in group).rstrip(".,")
                last = group[-1][0].strip(".,").lower()
                if last not in seen_last:
                    seen_last.add(last)
                    people.append((name, group[0][1], group[-1][2]))
            group = []
    return people


def clip_after(section, end, next_start):
    window = section[end:min(next_start, end + 250)]
    m = SENT_END.search(window)
    return window[:m.start()] if m else window


def clip_before(section, start, prev_end):
    a = max(prev_end, start - 200)
    window = section[a:start]
    ends = list(SENT_END.finditer(section[a:start + 1]))   # +1 so a sentence ending right before the name counts
    return window[ends[-1].end():] if ends else window


def classify(chunk):
    dep, app = bool(DEPARTURE.search(chunk)), bool(APPOINTMENT.search(chunk))
    if dep and app:
        return "both"
    return "departure" if dep else "appointment" if app else None


def extract_events(section, filing_date):
    people = find_people(section)
    events = []
    for i, (name, start, end) in enumerate(people):
        next_start = people[i + 1][1] if i + 1 < len(people) else len(section)
        prev_end = people[i - 1][2] if i > 0 else 0
        after = clip_after(section, end, next_start)
        before = clip_before(section, start, prev_end)
        if REPORTING_TO.search(section[max(0, start - 40):start]):
            continue

        # later sentences that refer back to the person ("Ms. Adams will remain ... until her retirement")
        last = re.escape(name.split()[-1])
        followups = " ".join(clip_after(section, m.end(), len(section))
                             for m in re.finditer(r"\b(?:Mr|Ms|Mrs|Dr)\.? " + last + r"\b", section))

        if SUCCEEDS.search(section[max(0, start - 20):start]):
            event = "departure"
        else:
            event = classify(after) or classify(followups) or classify(before)
        if not event:
            continue   # person is mentioned but nothing happens to them

        # prefer the role the person is moving into/out of ("as Chief Financial Officer")
        title = (TITLE_AS.search(after) or TITLE_AS.search(before)
                 or TITLE.search(after) or TITLE.search(before))
        title = title.group(1) if title else NF
        if title.islower():
            title = title.title()           # "general counsel" -> "General Counsel"
        if "Board of Directors" in title or title.lower() == "director":
            title = "Director"

        context = before + " " + after
        eff = EFFECTIVE.search(context) or EFFECTIVE.search(section)
        if eff:
            effective = eff.group(1)
        elif re.search(r"effective immediately", context, re.I):
            effective = filing_date
        else:
            effective = NF
        events.append({"event_type": event, "person_name": name,
                       "title": title, "effective_date": effective})
    return events

# ---------------------------------------------------------------- main
def main():
    rows = []
    for company, ticker, cik in COMPANIES:
        try:
            filings = find_recent_502(cik)
        except Exception as e:
            print(f"WARNING [{ticker}]: could not load EDGAR submissions ({e})")
            continue
        if not filings:
            print(f"[{ticker}]: No executive events in past 12 months")
            continue

        for f in filings:
            base = {"company": company, "ticker": ticker, "cik": cik, "filing_date": f["filing_date"]}
            url = (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/"
                   f"{f['accession'].replace('-', '')}/{f['primary_doc']}")
            try:
                events = extract_events(item_502_section(html_to_text(get(url).text)), f["filing_date"])
            except Exception as e:
                print(f"WARNING [{ticker}] {f['filing_date']}: {e}")
                events = []

            if not events:
                rows.append({**base, "event_type": NF, "person_name": NF, "title": NF, "effective_date": NF})
                print(f"[{ticker}] | {f['filing_date']} | NOT_FOUND | NOT_FOUND | NOT_FOUND "
                      f"(5.02 filing with no parseable departure/appointment; check {url})")
                continue
            for ev in events:
                rows.append({**base, **ev})
                print(f"[{ticker}] | {f['filing_date']} | {ev['event_type']} | {ev['person_name']} | {ev['title']}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved {len(rows)} events to {OUT_CSV}")


if __name__ == "__main__":
    main()
