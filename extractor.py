import cohere
import fitz
import json
import os
from dotenv import load_dotenv

load_dotenv()
client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    financial_keywords = ["revenue", "profit", "ebitda", "total assets",
                          "debt", "equity", "crore", "₹", "balance sheet"]
    financial_pages = []
    other_pages = []
    for i, page in enumerate(doc):
        page_text = page.get_text().lower()
        if any(kw in page_text for kw in financial_keywords):
            financial_pages.append(page.get_text())
        else:
            other_pages.append(page.get_text())
    all_text = " ".join(financial_pages) + " ".join(other_pages)
    return all_text[:20000]

def extract_financials(pdf_path, doc_type="annual_report"):
    print(f"  📖 Reading PDF: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are an expert Indian corporate credit analyst.
Document type: {doc_type}
Document content:
{raw_text}

IMPORTANT RULES:
1. All monetary values MUST be in Indian Rupees in Crores (Cr) only.
2. If you find USD values, convert using 1 USD = 84 INR. Example: US $30 billion = 2,52,000 Cr.
3. Look specifically for revenue, profit, debt figures in the financial statements section.
4. Do NOT pick intro/overview numbers. Pick actual audited financial statement numbers.

Extract everything as raw JSON only. No explanation. No markdown. No backticks.
Just the JSON starting with {{ and ending with }}

{{
  "company_name": "",
  "industry": "",
  "annual_revenue": "",
  "net_profit": "",
  "ebitda": "",
  "total_debt": "",
  "total_assets": "",
  "shareholder_equity": "",
  "debt_to_equity": "",
  "current_ratio": "",
  "dscr": "",
  "gst_reported_revenue": "",
  "bank_credited_amount": "",
  "gstr1_vs_gstr3b_mismatch": false,
  "gstr_mismatch_details": "",
  "related_party_transaction_percent": "",
  "auditor_qualification": false,
  "auditor_remarks": "",
  "promoter_names": [],
  "collateral_mentioned": "",
  "existing_loans": "",
  "years_in_business": "",
  "credit_rating": "",
  "key_risks": [],
  "key_strengths": [],
  "summary": ""
}}

Use "N/A" if value not found.
"""

    print("  🤖 Asking Cohere AI to analyse...")

    response = client.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.message.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(clean)
        print("  ✅ Extraction done!")
        return result
    except:
        print("  ⚠️ Trying to fix response...")
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            result = json.loads(raw[start:end])
            print("  ✅ Fixed and done!")
            return result
        except:
            return {"error": "Parse failed", "raw": raw}