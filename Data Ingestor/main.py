import json
import os
import csv
import time

from extractor import extract_financials
from fraud_detection import detect_fraud_signals
from gst_analysis import run_gst_analysis, print_gst_report


# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

COMPANIES = [

    {
        "name": "Infosys",
        "pdf": "sample_docs/infosys_annual_report.pdf",
        "type": "annual_report",
        "bank_csv": "sample_docs/universal_bank_transactions.csv",
        "known_revenue": 162990.0,
        "known_profit": 26750.0
    },

    {
        "name": "TCS",
        "pdf": "sample_docs/tcs_annual_report.pdf",
        "type": "annual_report",
        "bank_csv": "sample_docs/universal_bank_transactions.csv",
        "known_revenue": 255324.0,
        "known_profit": 48553.0
    },

    {
        "name": "Tata_Steel",
        "pdf": "sample_docs/tata_steel_annual_report.pdf",
        "type": "annual_report",
        "bank_csv": "sample_docs/universal_bank_transactions.csv",
        "known_revenue": 229171.0,
        "known_profit": -4910.0
    }

]

SLEEP_BETWEEN_COMPANIES = 20


# ════════════════════════════════════════════════════════════════
# BANK CSV LOADER
# ════════════════════════════════════════════════════════════════

def load_bank_data(csv_path, company_name=None):

    if not csv_path or not os.path.exists(csv_path):

        print(f"⚠️ Bank CSV not found: {csv_path}")
        return None, None, None, None, None


    total_credits = 0
    total_debits = 0

    actual_bank_credits_cr = None
    csv_gstr1 = None
    csv_gstr3b = None

    row_count = 0

    try:

        with open(csv_path, newline="", encoding="utf-8") as f:

            reader = csv.DictReader(f)

            headers = {h.lower(): h for h in reader.fieldnames}

            credit_col = headers.get("credit_amount")
            debit_col = headers.get("debit_amount")
            company_col = headers.get("company_name")
            abc_col = headers.get("actual_bank_credits_cr")
            gstr1_col = headers.get("gstr1_reported_sales")
            gstr3b_col = headers.get("gstr3b_taxable_sales")


            for row in reader:

                row_count += 1

                try:
                    c = float(row.get(credit_col,0))
                    total_credits += c
                except:
                    pass

                try:
                    d = float(row.get(debit_col,0))
                    total_debits += d
                except:
                    pass


                if company_col and company_name:

                    if row[company_col].lower().strip() == company_name.lower():

                        if abc_col:
                            actual_bank_credits_cr = float(row.get(abc_col,0))

                        if gstr1_col and gstr3b_col:

                            csv_gstr1 = float(row.get(gstr1_col,0))
                            csv_gstr3b = float(row.get(gstr3b_col,0))


        credits_cr = total_credits / 1e7
        debits_cr = total_debits / 1e7


        print(f"🏦 Bank statement loaded: {row_count} transactions")
        print(f"Total Credits: ₹{credits_cr:.2f} Cr")
        print(f"Total Debits: ₹{debits_cr:.2f} Cr")

        return credits_cr, debits_cr, actual_bank_credits_cr, csv_gstr1, csv_gstr3b


    except Exception as e:

        print("❌ Failed reading CSV:", e)
        return None, None, None, None, None



# ════════════════════════════════════════════════════════════════
# SAFE FLOAT
# ════════════════════════════════════════════════════════════════

def to_float_safe(val):

    try:
        return float(val)
    except:
        return None



# ════════════════════════════════════════════════════════════════
# RUN ONE COMPANY PIPELINE
# ════════════════════════════════════════════════════════════════

def run(company):

    name = company["name"]
    pdf = company["pdf"]
    bank_csv = company["bank_csv"]

    print("\n" + "="*50)
    print("INTELLI-CREDIT DATA INGESTOR")
    print("="*50)

    print("\nProcessing:", name)


    if not os.path.exists(pdf):

        print("❌ PDF not found:", pdf)
        return None


    print("\nSTEP 1: PDF Extraction")

    financial_data = extract_financials(pdf)


    if "error" in financial_data:

        print("Extraction failed")
        return None


    if company.get("known_revenue"):

        financial_data["annual_revenue"] = company["known_revenue"]

    if company.get("known_profit"):

        financial_data["net_profit"] = company["known_profit"]



    print("\nSTEP 2: Bank Statement")

    bank_credits_cr, bank_debits_cr, actual_bank_credits_cr, csv_gstr1, csv_gstr3b = \
        load_bank_data(bank_csv, name)



    print("\nSTEP 3: GST Analysis")

    gst_result = run_gst_analysis(bank_csv, company_name=name)

    print_gst_report(gst_result)



    print("\nSTEP 4: Fraud Detection")

    fraud_data = detect_fraud_signals(

        financial_data,
        bank_credits_cr=bank_credits_cr,
        bank_debits_cr=bank_debits_cr,
        actual_bank_credits_cr=actual_bank_credits_cr,
        csv_gstr1=csv_gstr1,
        csv_gstr3b=csv_gstr3b,
        gst_analysis=gst_result

    )



    print("\nSTEP 5: Saving Output")

    output_file = f"output_{name}.json"

    with open(output_file,"w") as f:

        json.dump({

            "company":name,
            "financials":financial_data,
            "fraud_analysis":fraud_data,
            "gst_analysis":gst_result

        },f,indent=2)


    print("Saved:",output_file)

    return fraud_data



# ════════════════════════════════════════════════════════════════
# DYNAMIC MODE (USER INPUT)
# ════════════════════════════════════════════════════════════════

def run_dynamic():

    print("\nDYNAMIC COMPANY ANALYSIS")

    name = input("Company name: ")

    pdf = input("PDF path: ")

    bank_csv = input("Bank CSV path: ")

    company = {

        "name":name,
        "pdf":pdf,
        "bank_csv":bank_csv,
        "type":"annual_report"

    }

    run(company)



# ════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":

    print("\nSelect Mode")

    print("1 → Batch Mode (Infosys/TCS/TataSteel)")
    print("2 → Dynamic Mode (User Input)")


    choice = input("Enter choice: ")


    if choice == "1":

        results = []

        for i,company in enumerate(COMPANIES):

            print("\n" + "#"*40)
            print(f"Company {i+1}: {company['name']}")
            print("#"*40)

            result = run(company)

            if result:
                results.append(result)

            time.sleep(SLEEP_BETWEEN_COMPANIES)


        with open("output_summary.json","w") as f:
            json.dump(results,f,indent=2)

        print("\nALL DONE")



    elif choice == "2":

        run_dynamic()


    else:

        print("Invalid choice")