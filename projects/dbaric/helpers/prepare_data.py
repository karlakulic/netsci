"""
One-time data preparation script.
Reads data/contracts.csv → writes data/contracts_clean.csv.

Hard cleans applied (irreversible exclusions):
  - Drop 4 always-empty columns
  - Deduplicate by Id (keep latest LastPublishedAt)
  - Drop reversed contracts (IsReversed=true)
  - Drop negative-value contracts
  - Zero-pad CAIdentificationNumber to 11 digits
  - Recode sentinel dates (year>2099) to NaT in DurationTo and TerminationDate
  - Parse CPV code and division

Flag columns added (analysis scripts filter on these as needed):
  - is_foreign_contractor, is_framework_calloff, is_eur
  - in_analysis_window (ContractDate >= 2024-01-01)
  - is_discretionary (ProcedureTypeId==11, unverified assumption)
  - is_competitive (ProcedureTypeId==1, unverified assumption)
  - contract_year, contract_quarter, contract_year_quarter

Rationale for every step: docs/DATA_PROFILE.md + docs/PLAN.md §Data preparation canon.
"""

import pathlib
import sys

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "contracts.csv"
OUTPUT = ROOT / "data" / "contracts_clean.csv"

ALWAYS_EMPTY_COLS = ["MainTenderId", "DurationFromText", "DurationToText", "ObjectId"]


def banner(msg: str) -> None:
    print(f"\n{'─' * 60}\n{msg}")


def main() -> None:
    banner(f"Loading {INPUT}")
    df = pd.read_csv(INPUT, low_memory=False)
    print(f"  Raw rows:    {len(df):>9,}")
    print(f"  Columns:     {df.shape[1]}")

    # ── Step 1: drop always-empty columns ──────────────────────────────────
    banner("Step 1 — drop always-empty columns")
    df = df.drop(columns=ALWAYS_EMPTY_COLS, errors="ignore")
    print(f"  Dropped: {ALWAYS_EMPTY_COLS}")

    # ── Step 2: deduplicate by Id, keep latest LastPublishedAt ─────────────
    banner("Step 2 — deduplicate by Id")
    df["LastPublishedAt"] = pd.to_datetime(df["LastPublishedAt"], errors="coerce", utc=True)
    before = len(df)
    df = df.sort_values("LastPublishedAt", ascending=False).drop_duplicates(subset="Id", keep="first")
    removed = before - len(df)
    print(f"  Removed duplicate rows: {removed:,}  (rows remaining: {len(df):,})")

    # ── Step 3: drop reversed contracts ────────────────────────────────────
    banner("Step 3 — drop reversed contracts (IsReversed=true)")
    before = len(df)
    df = df[df["IsReversed"] != True]
    print(f"  Removed: {before - len(df):,}  (rows remaining: {len(df):,})")

    # ── Step 4: drop negative-value contracts ──────────────────────────────
    banner("Step 4 — drop negative-value contracts")
    before = len(df)
    df = df[df["TotalValue"].isna() | (df["TotalValue"] >= 0)]
    print(f"  Removed: {before - len(df):,}  (rows remaining: {len(df):,})")

    # ── Step 5: zero-pad CAIdentificationNumber to 11 digits ───────────────
    banner("Step 5 — zero-pad CAIdentificationNumber to 11 digits")
    df["CAIdentificationNumber"] = (
        df["CAIdentificationNumber"]
        .astype(str)
        .str.strip()
        .str.zfill(11)
    )
    short = (df["CAIdentificationNumber"].str.len() != 11).sum()
    print(f"  CA OIBs not 11 digits after padding: {short:,} (should be 0)")

    # ── Step 6: recode sentinel dates ──────────────────────────────────────
    banner("Step 6 — recode sentinel dates (year > 2099) → NaT")
    for col in ("DurationTo", "TerminationDate"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
        mask = df[col].dt.year > 2099
        count = mask.sum()
        df.loc[mask, col] = pd.NaT
        print(f"  {col}: {count:,} sentinels recoded")

    # ── Step 7: parse CPV ──────────────────────────────────────────────────
    banner("Step 7 — parse CPV code and division")
    df["cpv_code"] = (
        df["Cpv"]
        .astype(str)
        .str.extract(r"^(\d{8})", expand=False)
    )
    df["cpv_division"] = df["cpv_code"].str[:2]
    missing_cpv = df["cpv_code"].isna().sum()
    print(f"  Rows with unparseable CPV: {missing_cpv:,}")

    # ── Step 8: add flag columns ───────────────────────────────────────────
    banner("Step 8 — add flag columns")

    # Foreign contractor: non-numeric ContractorIdentificationNumber
    df["is_foreign_contractor"] = ~df["ContractorIdentificationNumber"].astype(str).str.match(r"^\d+$")
    n_foreign = df["is_foreign_contractor"].sum()
    n_total = len(df)
    print(f"  is_foreign_contractor: {n_foreign:,} ({n_foreign / n_total * 100:.1f} %)")

    df["is_framework_calloff"] = df["IsUponFA"].astype(bool)
    print(f"  is_framework_calloff:  {df['is_framework_calloff'].sum():,}")

    df["is_eur"] = df["TotalValueCurrencyId"] == 1
    print(f"  is_eur:                {df['is_eur'].sum():,}")

    df["ContractDate"] = pd.to_datetime(df["ContractDate"], errors="coerce")
    df["in_analysis_window"] = df["ContractDate"] >= "2024-01-01"
    print(f"  in_analysis_window:    {df['in_analysis_window'].sum():,}")

    # Procedure type flags (working assumption — NOT verified against label table)
    df["is_discretionary"] = df["ProcedureTypeId"] == 11
    df["is_competitive"] = df["ProcedureTypeId"] == 1
    print(f"  is_discretionary (assumed ProcedureTypeId=11): {df['is_discretionary'].sum():,}")
    print(f"  is_competitive   (assumed ProcedureTypeId=1):  {df['is_competitive'].sum():,}")

    df["contract_year"] = df["ContractDate"].dt.year
    df["contract_quarter"] = df["ContractDate"].dt.quarter
    df["contract_year_quarter"] = (
        df["contract_year"].astype("Int64").astype(str)
        + "-Q"
        + df["contract_quarter"].astype("Int64").astype(str)
    )

    # ── Summary ────────────────────────────────────────────────────────────
    banner("Summary")
    print(f"  Final rows:    {len(df):,}")
    print(f"  Final columns: {df.shape[1]}")
    print(f"\n  Foreign contractor rate: {n_foreign / n_total * 100:.2f} %")
    print(f"  Analysis-window rows (ContractDate >= 2024-01-01): {df['in_analysis_window'].sum():,}")
    print(f"  Framework call-offs: {df['is_framework_calloff'].sum():,}")

    # ── Write output ───────────────────────────────────────────────────────
    banner(f"Writing {OUTPUT}")
    df.to_csv(OUTPUT, index=False)
    size_mb = OUTPUT.stat().st_size / 1_048_576
    print(f"  Done — {size_mb:.1f} MB")


if __name__ == "__main__":
    if not INPUT.exists():
        print(f"ERROR: {INPUT} not found", file=sys.stderr)
        sys.exit(1)
    main()
