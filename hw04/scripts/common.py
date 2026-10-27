"""
Shared paths, table metadata and loaders for HW4.
Every table is read as text (dtype=str, keep_default_na=False) per the HW4 rule.
"""
import os
import sys

import pandas as pd

HW_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_DIR = os.path.dirname(HW_DIR)

# Raw folder: first CLI arg, else env var, else the usual locations.
_CANDIDATES = [
    os.environ.get("WILDCAT_RAW_DIR", ""),
    os.path.join(REPO_DIR, "Wildcat Capital"),
    os.path.join(REPO_DIR, "data", "raw"),
    os.path.join(HW_DIR, "data", "raw"),
]


def raw_dir():
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        return sys.argv[1]
    for c in _CANDIDATES:
        if c and os.path.isfile(os.path.join(c, "dim_client.csv")):
            return c
    raise FileNotFoundError(
        "Raw Wildcat Capital folder not found. Pass it as the first argument, "
        "e.g. python hw04/scripts/01_profile.py \"Wildcat Capital\""
    )


CLEAN_DIR = os.path.join(HW_DIR, "data", "clean")
AUDIT_DIR = os.path.join(HW_DIR, "data", "audit")
REPORT_DIR = os.path.join(HW_DIR, "reports")

TABLES = [
    "dim_advisor", "dim_benchmark", "dim_client", "dim_date", "dim_security",
    "fact_fees", "fact_portfolio_snapshot", "fact_transactions",
]

EXPECTED_SHAPE = {
    "dim_advisor": (25, 7), "dim_client": (2525, 14), "dim_date": (1827, 12),
    "dim_security": (500, 8), "dim_benchmark": (8, 4), "fact_fees": (122197, 8),
    "fact_portfolio_snapshot": (129547, 13), "fact_transactions": (298772, 9),
}

PRIMARY_KEY = {
    "dim_advisor": "advisor_id", "dim_benchmark": "benchmark_id",
    "dim_client": "client_id", "dim_date": "date_id", "dim_security": "security_id",
    "fact_fees": "fee_id", "fact_portfolio_snapshot": "snapshot_id",
    "fact_transactions": "txn_id",
}

# Expected type per column: int, float, date, bool, cat (allowed list), text
TYPES = {
    "dim_advisor": {"advisor_id": "int", "first_name": "text", "last_name": "text",
                    "region": "text", "years_experience": "int",
                    "aum_target_mm": "int", "certifications": "text"},
    "dim_benchmark": {"benchmark_id": "int", "name": "text", "asset_class": "text",
                      "ticker_proxy": "text"},
    "dim_client": {"client_id": "int", "first_name": "text", "last_name": "text",
                   "age": "int", "city": "text", "state": "text", "zip_code": "text",
                   "risk_profile": "text", "client_tier": "text",
                   "primary_account_type": "text", "initial_aum": "float",
                   "client_since": "date", "advisor_id": "int", "is_active": "bool"},
    "dim_date": {"date_id": "int", "date": "date", "year": "int", "quarter": "int",
                 "month": "int", "month_name": "text", "week_of_year": "int",
                 "day_of_week": "text", "is_month_end": "int", "is_quarter_end": "int",
                 "is_year_end": "int", "is_trading_day": "int"},
    "dim_security": {"security_id": "int", "ticker": "text", "name": "text",
                     "asset_class": "text", "sector": "text", "benchmark_id": "int",
                     "is_etf": "bool", "expense_ratio_bps": "float"},
    "fact_fees": {"fee_id": "int", "client_id": "int", "advisor_id": "int",
                  "fee_date": "date", "fee_type": "text", "aum_basis": "float",
                  "bps_charged": "float", "amount": "float"},
    "fact_portfolio_snapshot": {"snapshot_id": "int", "client_id": "int",
                                "advisor_id": "int", "benchmark_id": "int",
                                "snapshot_date": "date", "year": "int", "month": "int",
                                "aum": "float", "return_ytd": "float",
                                "benchmark_return_ytd": "float",
                                "active_alpha_ytd": "float", "cash_pct": "float",
                                "account_type": "text"},
    "fact_transactions": {"txn_id": "int", "client_id": "int", "advisor_id": "int",
                          "security_id": "int", "txn_date": "date", "txn_type": "text",
                          "shares": "float", "price": "float", "amount": "float"},
}

ALLOWED = {
    ("dim_advisor", "region"): {"Northeast", "Mid-Atlantic", "Southeast", "Midwest", "West"},
    ("dim_client", "risk_profile"): {"Conservative", "Moderately Conservative", "Balanced",
                                     "Moderately Aggressive", "Aggressive"},
    ("dim_client", "client_tier"): {"Retail", "HNW", "UHNW"},
    ("dim_client", "primary_account_type"): {"Taxable", "IRA", "Roth IRA", "Trust", "529"},
    ("dim_client", "is_active"): {"True", "False"},
    ("dim_security", "asset_class"): {"Equity", "Fixed Income", "Alternative", "Cash Equivalent"},
    ("dim_security", "is_etf"): {"True", "False"},
    ("fact_fees", "fee_type"): {"Advisory", "Management", "Custodial", "Performance"},
    ("fact_transactions", "txn_type"): {"Buy", "Sell", "Dividend", "Deposit",
                                        "Withdrawal", "Advisory Fee"},
    ("fact_portfolio_snapshot", "account_type"): {"Taxable", "IRA", "Roth IRA", "Trust", "529"},
}

# 10 ID-based relationships + 3 date relationships: (fact, fk, dim, pk)
RELATIONSHIPS = [
    ("dim_client", "advisor_id", "dim_advisor", "advisor_id"),
    ("dim_security", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_fees", "client_id", "dim_client", "client_id"),
    ("fact_fees", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "client_id", "dim_client", "client_id"),
    ("fact_portfolio_snapshot", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_portfolio_snapshot", "benchmark_id", "dim_benchmark", "benchmark_id"),
    ("fact_transactions", "client_id", "dim_client", "client_id"),
    ("fact_transactions", "advisor_id", "dim_advisor", "advisor_id"),
    ("fact_transactions", "security_id", "dim_security", "security_id"),
    ("fact_fees", "fee_date", "dim_date", "date"),
    ("fact_portfolio_snapshot", "snapshot_date", "dim_date", "date"),
    ("fact_transactions", "txn_date", "dim_date", "date"),
]

US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI",
    "Wyoming": "WY", "District of Columbia": "DC",
}


def read_table(folder, name):
    """Read one table entirely as text."""
    return pd.read_csv(os.path.join(folder, f"{name}.csv"), dtype=str,
                       keep_default_na=False)


def read_all(folder):
    return {t: read_table(folder, t) for t in TABLES}


def to_num(s):
    """Text -> float. Handles '9.28%' (-> 0.0928) and scientific notation."""
    s = s.astype(str).str.strip()
    pct = s.str.endswith("%")
    out = pd.to_numeric(s.str.rstrip("%"), errors="coerce")
    out[pct] = out[pct] / 100
    return out


def parse_ok(series, typ):
    """Boolean mask: non-blank value parses as the expected type."""
    s = series.astype(str).str.strip()
    if typ == "int":
        return s.str.fullmatch(r"-?\d+")
    if typ == "float":
        return s.str.fullmatch(r"-?\d+(\.\d+)?([eE]-?\d+)?")
    if typ == "date":
        return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce").notna()
    if typ == "bool":
        return s.isin(["True", "False"])
    return pd.Series(True, index=s.index)


def ensure_dirs():
    for d in (CLEAN_DIR, AUDIT_DIR, REPORT_DIR):
        os.makedirs(d, exist_ok=True)
