def detect_fraud_signals(data):
    flags = []
    penalty = 0

    # CHECK 1 — GST vs Revenue cross-check (NEW)
    expected_gst = data.get("expected_gst_cr", "N/A")
    bank = data.get("bank_credited_amount", "N/A")
    if expected_gst != "N/A" and bank != "N/A":
        try:
            def clean(v):
                return float(str(v).replace("₹","").replace("Cr","").replace(",","").strip())
            gst_val = clean(expected_gst)
            bank_val = clean(bank)
            actual_gst_from_bank = bank_val * 0.18
            deviation = abs(gst_val - actual_gst_from_bank) / gst_val * 100
            if deviation > 30:
                flags.append({"type": "GST_REVENUE_MISMATCH", "severity": "HIGH",
                    "detail": f"Expected GST ₹{expected_gst} Cr but bank implies ₹{round(actual_gst_from_bank,2)} Cr. Deviation: {round(deviation,1)}%", "penalty": 20})
                penalty += 20
        except: pass

    # CHECK 2 — Circular Trading
    gst = data.get("gst_reported_revenue", "N/A")
    if gst != "N/A" and bank != "N/A":
        try:
            def clean(v):
                return float(str(v).replace("₹","").replace("Cr","").replace(",","").strip())
            if clean(gst) > clean(bank) * 1.3:
                flags.append({"type": "CIRCULAR_TRADING", "severity": "HIGH",
                    "detail": f"GST revenue {gst} is much higher than bank deposits {bank}. Possible fake revenue.", "penalty": 20})
                penalty += 20
        except: pass

    # CHECK 3 — GST Mismatch
    if data.get("gstr1_vs_gstr3b_mismatch") == True:
        flags.append({"type": "GST_MISMATCH", "severity": "HIGH",
            "detail": data.get("gstr_mismatch_details", "GSTR-1 and GSTR-3B do not match."), "penalty": 15})
        penalty += 15

    # CHECK 4 — Auditor Qualification
    if data.get("auditor_qualification") == True:
        flags.append({"type": "AUDITOR_QUALIFICATION", "severity": "HIGH",
            "detail": data.get("auditor_remarks", "Auditor has flagged the financials."), "penalty": 20})
        penalty += 20

    # CHECK 5 — High Related Party Transactions
    rpt = data.get("related_party_transaction_percent", "N/A")
    if rpt != "N/A":
        try:
            if float(str(rpt).replace("%","").strip()) > 40:
                flags.append({"type": "HIGH_RELATED_PARTY", "severity": "MEDIUM",
                    "detail": f"{rpt} of revenue from related parties. Risk of fund diversion.", "penalty": 10})
                penalty += 10
        except: pass

    # CHECK 6 — Weak DSCR
    dscr = data.get("dscr", "N/A")
    if dscr != "N/A":
        try:
            v = float(str(dscr).strip())
            if v < 1.0:
                flags.append({"type": "CRITICAL_DSCR", "severity": "HIGH",
                    "detail": f"DSCR {dscr} is below 1.0 — company cannot repay debt.", "penalty": 25})
                penalty += 25
            elif v < 1.5:
                flags.append({"type": "BORDERLINE_DSCR", "severity": "MEDIUM",
                    "detail": f"DSCR {dscr} is between 1.0 and 1.5 — borderline.", "penalty": 10})
                penalty += 10
        except: pass

    # CHECK 7 — High Debt to Equity
    de = data.get("debt_to_equity", "N/A")
    if de != "N/A":
        try:
            v = float(str(de).strip())
            if v > 2:
                flags.append({"type": "HIGH_LEVERAGE", "severity": "HIGH",
                    "detail": f"D/E ratio {de} exceeds 2.0 — too much debt.", "penalty": 15})
                penalty += 15
        except: pass

    high = [f for f in flags if f["severity"] == "HIGH"]
    risk = "CRITICAL" if len(high) >= 2 else "HIGH" if len(high) == 1 else "MEDIUM" if flags else "CLEAN"

    return {
        "fraud_flags": flags,
        "total_penalty": penalty,
        "overall_fraud_risk": risk,
        "circular_trading_detected": any(f["type"] == "CIRCULAR_TRADING" for f in flags),
        "high_risk_count": len(high),
        "summary": f"{len(flags)} flags found. Penalty: -{penalty} points. Risk level: {risk}"
    }