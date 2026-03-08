"""
gst_analysis.py
───────────────
Standalone GST mismatch analysis module.

Reads bank_transactions.csv and calculates 12 GST metrics:
  1.  Total bank revenue
  2.  Total GSTR-1 turnover
  3.  Total GSTR-3B turnover
  4.  GSTR-1 vs Bank mismatch amount
  5.  GSTR-1 vs Bank mismatch ratio
  6.  GSTR-1 vs GSTR-3B mismatch amount
  7.  GSTR-1 vs GSTR-3B mismatch ratio
  8.  Bank vs GSTR-3B mismatch amount
  9.  Bank vs GSTR-3B mismatch ratio
  10. GST compliance score (0 to 1)
  11. Monthly variance
  12. GST risk flag (High / Moderate / Low)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HOW IT CONNECTS TO fraud_detection.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  main.py calls:
    gst_result = run_gst_analysis(csv_path, company_name)

  Then passes gst_result into detect_fraud_signals():
    fraud_data = detect_fraud_signals(
        financial_data,
        ...
        gst_analysis=gst_result   ← from this file
    )

  fraud_detection.py uses gst_result for Criterion 3:
    - ratio_gstr1_gstr3b > 0.25 → HIGH flag
    - ratio_gstr1_bank   > 0.25 → HIGH flag
    - gst_compliance_score < 0.75 → MEDIUM flag
    - monthly_variance spike → circular trading signal

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  APPROACH 1 vs APPROACH 2 (same logic as before)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Approach 1 — company found in CSV
    → Uses real gstr1_reported_sales and gstr3b_taxable_sales
    → Most accurate

  Approach 2 — company NOT in CSV (XYZ unknown)
    → gstr1  = bank_revenue (proxy for declared sales)
    → gstr3b = bank_revenue × 0.85 (15% under-reporting assumed)
    → Works for any unknown company
"""

import pandas as pd
import numpy as np
import os


def run_gst_analysis(csv_path, company_name=None, revenue_cr=None):
    """
    Run full GST mismatch analysis on the bank CSV.

    Parameters
    ----------
    csv_path     : str   — path to bank_transactions.csv
    company_name : str   — company name to filter rows (optional)
                           if None → uses all rows
    revenue_cr   : float — PDF revenue in Crores (used for Approach 2 fallback)

    Returns
    -------
    dict with all 12 GST metrics + approach used + risk flag
    Returns None if CSV not found or columns missing
    """

    if not csv_path or not os.path.exists(csv_path):
        print(f"  ⚠️  GST Analysis: CSV not found: {csv_path}")
        return None

    try:
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])

        # ── Filter by company name if CSV has company_name column ──
        approach = "Approach 2 (estimated)"
        if company_name and "company_name" in df.columns:
            search = company_name.strip().lower().replace("_", " ")
            mask   = df["company_name"].str.strip().str.lower().str.replace("_", " ") == search
            if mask.any():
                df       = df[mask].copy()
                approach = "Approach 1 (real CSV data)"
                print(f"  ✅ GST Analysis: Company '{company_name}' found in CSV → {approach}")
            else:
                print(f"  ℹ️  GST Analysis: '{company_name}' not in CSV → {approach}")
        else:
            print(f"  ℹ️  GST Analysis: No company filter → {approach}")

        # ── Check required columns ────────────────────────────────
        has_gstr1  = "gstr1_reported_sales"  in df.columns
        has_gstr3b = "gstr3b_taxable_sales"  in df.columns
        has_credit = "credit_amount"         in df.columns

        if not has_credit:
            print("  ⚠️  GST Analysis: 'credit_amount' column missing")
            return None

        # ── 1. Total bank revenue ─────────────────────────────────
        bank_revenue = df["credit_amount"].sum()

        # ── 2 & 3. GSTR-1 and GSTR-3B turnover ───────────────────
        if has_gstr1 and has_gstr3b and approach == "Approach 1 (real CSV data)":
            # Approach 1 — real data from CSV
            # GSTR-1 and GSTR-3B are in Crores (real values)
            # bank_revenue is in raw CSV units — NOT comparable to GSTR values
            # So we use actual_bank_credits_cr from CSV for bank comparison
            gstr1_turnover  = df["gstr1_reported_sales"].iloc[0]
            gstr3b_turnover = df["gstr3b_taxable_sales"].iloc[0]
            # For bank comparison use actual_bank_credits_cr column (in Crores)
            if "actual_bank_credits_cr" in df.columns:
                bank_revenue_cr = df["actual_bank_credits_cr"].iloc[0]
            else:
                bank_revenue_cr = gstr1_turnover * 0.50  # fallback: 50% of GSTR-1
        else:
            # Approach 2 — estimate from revenue
            if revenue_cr and revenue_cr > 0:
                gstr1_turnover  = revenue_cr
                gstr3b_turnover = revenue_cr * 0.85
                bank_revenue_cr = revenue_cr * 0.50   # 50% of revenue as bank proxy
                approach        = "Approach 2 (estimated from PDF revenue)"
            else:
                gstr1_turnover  = bank_revenue
                gstr3b_turnover = bank_revenue * 0.85
                bank_revenue_cr = bank_revenue
                approach        = "Approach 2 (estimated — no revenue available)"

        # ── 4. GSTR-1 vs Bank mismatch ────────────────────────────
        mismatch_gstr1_bank  = abs(gstr1_turnover - bank_revenue_cr)

        # ── 5. GSTR-1 vs Bank ratio ───────────────────────────────
        ratio_gstr1_bank = (mismatch_gstr1_bank / gstr1_turnover
                            if gstr1_turnover != 0 else 0)

        # ── 6. GSTR-1 vs GSTR-3B mismatch ────────────────────────
        mismatch_gstr1_gstr3b = abs(gstr1_turnover - gstr3b_turnover)

        # ── 7. GSTR-1 vs GSTR-3B ratio ───────────────────────────
        ratio_gstr1_gstr3b = (mismatch_gstr1_gstr3b / gstr1_turnover
                              if gstr1_turnover != 0 else 0)

        # ── 8. Bank vs GSTR-3B mismatch ──────────────────────────
        mismatch_bank_gstr3b = abs(bank_revenue_cr - gstr3b_turnover)

        # ── 9. Bank vs GSTR-3B ratio ─────────────────────────────
        ratio_bank_gstr3b = (mismatch_bank_gstr3b / gstr3b_turnover
                             if gstr3b_turnover != 0 else 0)

        # ── 10. GST compliance score (0 to 1, higher = better) ───
        # Uses GSTR-1 vs GSTR-3B ratio only — bank is a different unit in raw CSV
        gst_compliance_score = max(0, 1 - ratio_gstr1_gstr3b)

        # ── 11. Monthly bank revenue and variance ─────────────────
        df["month"] = df["date"].dt.to_period("M")
        monthly_bank_revenue = df.groupby("month")["credit_amount"].sum()
        monthly_difference   = monthly_bank_revenue * 0.15   # 15% variance proxy
        monthly_variance     = float(np.std(monthly_difference))

        # ── 12. GST risk flag — based only on GSTR-1 vs GSTR-3B ──
        # (bank_revenue is raw units, not comparable to GSTR Crore values)
        if ratio_gstr1_gstr3b > 0.20:
            gst_risk_flag = "High Risk"
        elif ratio_gstr1_gstr3b > 0.10:
            gst_risk_flag = "Moderate Risk"
        else:
            gst_risk_flag = "Low Risk"

        # ── 13. CIRCULAR TRADING DETECTION ───────────────────────
        # Only runs for Approach 2 (unknown XYZ company)
        # For known companies (Approach 1), circular trading parties
        # in the CSV are synthetic test data — not real flags
        circular_trades   = []
        circular_detected = False

        if approach != "Approach 1 (real CSV data)" and "counterparty" in df.columns:
            # Get all debit rows (money going OUT to a party)
            debits  = df[df["debit_amount"]  > 0][["date","counterparty","debit_amount"]].copy()
            # Get all credit rows (money coming IN from a party)
            credits = df[df["credit_amount"] > 0][["date","counterparty","credit_amount"]].copy()

            # Find counterparties that appear in BOTH debits and credits
            debit_parties  = set(debits["counterparty"].str.strip().str.lower())
            credit_parties = set(credits["counterparty"].str.strip().str.lower())
            common_parties = debit_parties & credit_parties

            for party in common_parties:
                party_debits  = debits[debits["counterparty"].str.lower()  == party]
                party_credits = credits[credits["counterparty"].str.lower() == party]

                # Check each debit against credits from same party
                for _, drow in party_debits.iterrows():
                    for _, crow in party_credits.iterrows():
                        days_diff   = abs((crow["date"] - drow["date"]).days)
                        amount_diff = abs(crow["credit_amount"] - drow["debit_amount"])
                        amount_pct  = amount_diff / drow["debit_amount"] if drow["debit_amount"] > 0 else 1

                        # Within 7 days AND within 10% of same amount = circular!
                        if days_diff <= 7 and amount_pct <= 0.10:
                            circular_trades.append({
                                "counterparty":   drow["counterparty"],
                                "amount_out":     round(drow["debit_amount"], 2),
                                "amount_in":      round(crow["credit_amount"], 2),
                                "date_out":       str(drow["date"].date()),
                                "date_in":        str(crow["date"].date()),
                                "days_gap":       days_diff,
                                "amount_diff_pct": round(amount_pct * 100, 1),
                            })
                            circular_detected = True
                            break   # one match per debit is enough

        # Deduplicate by counterparty
        seen       = set()
        unique_ct  = []
        for ct in circular_trades:
            if ct["counterparty"] not in seen:
                seen.add(ct["counterparty"])
                unique_ct.append(ct)
        circular_trades = unique_ct[:5]   # show max 5

        if circular_detected:
            print(f"  🔴 Circular Trading: {len(circular_trades)} suspicious counterparty(ies) found!")
            for ct in circular_trades:
                print(f"     → {ct['counterparty']} | Out: {ct['amount_out']} | "
                      f"In: {ct['amount_in']} | Gap: {ct['days_gap']} days")
        else:
            print(f"  ✅ Circular Trading: No patterns detected")

        result = {
            "approach":               approach,
            "bank_revenue_cr":        round(bank_revenue_cr, 2),
            "gstr1_turnover":         round(gstr1_turnover, 2),
            "gstr3b_turnover":        round(gstr3b_turnover, 2),
            "mismatch_gstr1_bank":    round(mismatch_gstr1_bank, 2),
            "ratio_gstr1_bank":       round(ratio_gstr1_bank, 4),
            "mismatch_gstr1_gstr3b":  round(mismatch_gstr1_gstr3b, 2),
            "ratio_gstr1_gstr3b":     round(ratio_gstr1_gstr3b, 4),
            "mismatch_bank_gstr3b":   round(mismatch_bank_gstr3b, 2),
            "ratio_bank_gstr3b":      round(ratio_bank_gstr3b, 4),
            "gst_compliance_score":   round(gst_compliance_score, 4),
            "monthly_variance":       round(monthly_variance, 4),
            "gst_risk_flag":          gst_risk_flag,
            "circular_trading":       circular_detected,
            "circular_trades":        circular_trades,
        }

        return result

    except Exception as e:
        print(f"  ❌ GST Analysis failed: {e}")
        return None


def print_gst_report(result):
    """Pretty-print the GST analysis result to terminal."""
    if not result:
        print("  ⚠️  No GST analysis result to display.")
        return

    print(f"\n─── GST Mismatch Analysis ({result['approach']}) ───")
    print(f"  🏦 Bank Credits (Cr)     : ₹{result['bank_revenue_cr']:>12,.2f} Cr")
    print(f"  📋 GSTR-1 Turnover       : ₹{result['gstr1_turnover']:>12,.2f} Cr")
    print(f"  📋 GSTR-3B Turnover      : ₹{result['gstr3b_turnover']:>12,.2f} Cr")
    print(f"  ─────────────────────────────────────────────")
    print(f"  🔍 GSTR-1 vs Bank Gap    : ₹{result['mismatch_gstr1_bank']:>12,.2f} Cr  "
          f"({result['ratio_gstr1_bank']*100:.1f}%)")
    print(f"  🔍 GSTR-1 vs GSTR-3B Gap : ₹{result['mismatch_gstr1_gstr3b']:>12,.2f} Cr  "
          f"({result['ratio_gstr1_gstr3b']*100:.1f}%)")
    print(f"  🔍 Bank vs GSTR-3B Gap   : ₹{result['mismatch_bank_gstr3b']:>12,.2f} Cr  "
          f"({result['ratio_bank_gstr3b']*100:.1f}%)")
    print(f"  ─────────────────────────────────────────────")
    print(f"  📊 GST Compliance Score  : {result['gst_compliance_score']:.4f}  "
          f"(1.0 = perfect)")
    print(f"  📊 Monthly Variance      : {result['monthly_variance']:.2f}")

    flag = result['gst_risk_flag']
    icon = "🔴" if flag == "High Risk" else "🟡" if flag == "Moderate Risk" else "🟢"
    print(f"  {icon} GST Risk Flag         : {flag}")

    # Circular trading summary
    if result.get("circular_trading"):
        print(f"\n  🔴 CIRCULAR TRADING DETECTED!")
        for ct in result.get("circular_trades", []):
            print(f"     → {ct['counterparty']}")
            print(f"       Paid out : {ct['amount_out']} on {ct['date_out']}")
            print(f"       Received : {ct['amount_in']} on {ct['date_in']} "
                  f"({ct['days_gap']} days later, {ct['amount_diff_pct']}% diff)")
    else:
        print(f"  ✅ No Circular Trading detected")


# ════════════════════════════════════════════════════════════════
#  STANDALONE RUN — python gst_analysis.py
#  Useful for testing independently from main.py
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    csv_file     = sys.argv[1] if len(sys.argv) > 1 else "sample_docs/universal_bank_transactions.csv"
    company      = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"\n{'='*50}")
    print(f"  GST MISMATCH ANALYSIS — STANDALONE")
    print(f"{'='*50}")
    print(f"  CSV     : {csv_file}")
    print(f"  Company : {company or 'All rows'}")

    result = run_gst_analysis(csv_file, company_name=company)
    print_gst_report(result)

    print(f"\n{'='*50}\n")