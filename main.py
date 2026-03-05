import json
import os
import random
from extractor import extract_financials
from fraud_detection import detect_fraud_signals

COMPANIES = [
    {"pdf": "sample_docs/infosys_annual_report.pdf",  "type": "annual_report", "name": "Infosys"},
    {"pdf": "sample_docs/tcs_annual_report.pdf",      "type": "annual_report", "name": "TCS"},
    {"pdf": "sample_docs/tata_steel_results.pdf",     "type": "quarterly_results", "name": "Tata_Steel"},
]

def parse_revenue(revenue_str):
    """Convert revenue string like '1,62,990 cr' to float"""
    if not revenue_str or revenue_str == "N/A":
        return None
    try:
        clean = str(revenue_str)
        clean = clean.replace("₹", "").replace("Cr", "").replace("cr", "")
        clean = clean.replace(",", "").replace(" ", "").strip()
        return float(clean)
    except:
        return None

def simulate_bank_data(revenue_cr):
    """
    Simulate bank statement cross-check.
    Real bank credits should be within 5% of reported revenue.
    We simulate a clean company with ±5% variance.
    """
    if not revenue_cr:
        return None
    variance = random.uniform(-0.05, 0.05)
    return round(revenue_cr * (1 + variance), 2)

def calculate_gst(data):
    """Calculate expected GST at 18% from annual revenue"""
    revenue_raw = data.get("annual_revenue", "N/A")
    revenue = parse_revenue(revenue_raw)
    if revenue:
        data["annual_revenue_cr"] = revenue
        data["expected_gst_cr"] = round(revenue * 0.18, 2)
        data["gst_calculation_note"] = f"GST @ 18% on ₹{revenue} Cr = ₹{data['expected_gst_cr']} Cr"

        # Simulate bank credited amount
        bank_amount = simulate_bank_data(revenue)
        data["bank_credited_amount"] = str(bank_amount)
        data["bank_gst_implied"] = round(bank_amount * 0.18, 2)
        data["bank_data_note"] = f"Bank credits ₹{bank_amount} Cr implies GST of ₹{data['bank_gst_implied']} Cr"
    else:
        data["expected_gst_cr"] = "N/A"
        data["bank_credited_amount"] = "N/A"

    return data

def run(company):
    print("\n============================")
    print("  INTELLI-CREDIT INGESTOR")
    print("============================")

    print(f"\n📄 Step 1: Reading PDF for {company['name']}...")
    financial_data = extract_financials(company["pdf"], company["type"])

    if "error" in financial_data:
        print("❌ Something went wrong:", financial_data["error"])
        return

    print(f"✅ Company: {financial_data.get('company_name', 'Unknown')}")

    # Calculate GST and simulate bank cross-check
    financial_data = calculate_gst(financial_data)

    if financial_data.get("expected_gst_cr") != "N/A":
        print(f"💰 Revenue: ₹{financial_data.get('annual_revenue_cr')} Cr")
        print(f"📊 Expected GST: ₹{financial_data.get('expected_gst_cr')} Cr")
        print(f"🏦 Bank Implied GST: ₹{financial_data.get('bank_gst_implied')} Cr")

    print("\n🔍 Step 2: Checking for fraud signals...")
    fraud_data = detect_fraud_signals(financial_data)

    if fraud_data["fraud_flags"]:
        print(f"🚨 {len(fraud_data['fraud_flags'])} fraud flag(s) found!")
        for f in fraud_data["fraud_flags"]:
            icon = "🔴" if f["severity"] == "HIGH" else "🟡"
            print(f"  {icon} {f['type']}: {f['detail'][:80]}...")
    else:
        print("✅ No fraud signals found!")

    print("\n💾 Step 3: Saving output...")
    output = {
        "extracted_data": financial_data,
        "fraud_analysis": fraud_data
    }

    filename = f"output_{company['name']}.json"
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)

    print(f"✅ Saved as: {filename}")
    print("\n============================")
    print(f"  COMPANY    : {company['name']}")
    print(f"  RISK LEVEL : {fraud_data['overall_fraud_risk']}")
    print(f"  PENALTY    : -{fraud_data['total_penalty']} points")
    print("============================\n")

if __name__ == "__main__":
    for company in COMPANIES:
        if os.path.exists(company["pdf"]):
            run(company)
        else:
            print(f"⚠️  File not found: {company['pdf']} — skipping")