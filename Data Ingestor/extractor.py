import pdfplumber
import json
import re
import os
import time
import cohere
from dotenv import load_dotenv

load_dotenv()
client = cohere.ClientV2(api_key=os.getenv("COHERE_API_KEY"))


# ══════════════════════════════════════════════════════════════════════
#
#  SMART PDF SUMMARIZER  — v3  (pdfplumber edition)
#
#  Why pdfplumber instead of PyMuPDF?
#    PyMuPDF reads tables as raw text → columns get scrambled
#    pdfplumber detects table boundaries → clean pipe-separated rows
#
#  Flow per page:
#    1. Extract tables → pipe-separated rows  (numbers preserved)
#    2. Extract plain text → auditor notes, MD&A paragraphs
#    3. Keyword-score the combined content
#    4. Lock in up to 15 financial highlights pages (deterministic)
#    5. Lock in up to 3 debt/balance sheet pages (guaranteed)
#    6. Fill remaining budget with top-scored pages
#
#  7 Fraud Criteria keywords drive page selection:
#    1. Revenue / Income
#    2. GST filings
#    3. Auditor qualification
#    4. Related-party transactions
#    5. DSCR
#    6. Debt-to-Equity
#    7. Current Ratio / Liquidity
#
# ══════════════════════════════════════════════════════════════════════

MAX_CHARS      = 25_000
MAX_HIGHLIGHTS = 15

KEYWORD_MAP = {
    "revenue":                       1,
    "revenue from operations":       1,
    "total income":                  1,
    "turnover":                      1,
    "net revenue":                   1,
    "gross revenue":                 1,
    "sales":                         1,
    "income from operations":        1,
    "gst":                           2,
    "goods and services tax":        2,
    "gstr":                          2,
    "gstr-1":                        2,
    "gstr-3b":                       2,
    "output tax":                    2,
    "input tax credit":              2,
    "tax liability":                 2,
    "indirect tax":                  2,
    "gst payable":                   2,
    "gst collected":                 2,
    "auditor":                       3,
    "audit report":                  3,
    "statutory auditor":             3,
    "independent auditor":           3,
    "qualified opinion":             3,
    "emphasis of matter":            3,
    "basis for qualification":       3,
    "we draw attention":             3,
    "material uncertainty":          3,
    "going concern":                 3,
    "caro":                          3,
    "related party":                 4,
    "related-party":                 4,
    "arm's length":                  4,
    "promoter":                      4,
    "subsidiary":                    4,
    "associate company":             4,
    "inter-company":                 4,
    "transactions with directors":   4,
    "key managerial":                4,
    "dscr":                          5,
    "debt service":                  5,
    "debt coverage":                 5,
    "interest coverage":             5,
    "debt servicing":                5,
    "loan repayment":                5,
    "principal repayment":           5,
    "debt service coverage":         5,
    "fixed charge coverage":         5,
    "debt service ratio":            5,
    "interest paid":                 5,
    "finance cost":                  5,
    "finance charges":               5,
    "interest expense":              5,
    "debt to equity":                6,
    "debt-to-equity":                6,
    "leverage":                      6,
    "long term debt":                6,
    "long-term debt":                6,
    "borrowings":                    6,
    "total debt":                    6,
    "net debt":                      6,
    "shareholder equity":            6,
    "shareholders equity":           6,
    "networth":                      6,
    "net worth":                     6,
    "term loan":                     6,
    "secured loan":                  6,
    "unsecured loan":                6,
    "debenture":                     6,
    "ncd":                           6,
    "external commercial borrowing": 6,
    "ecb":                           6,
    "capital structure":             6,
    "total borrowings":              6,
    "current ratio":                 7,
    "current assets":                7,
    "current liabilities":           7,
    "working capital":               7,
    "liquidity":                     7,
    "quick ratio":                   7,
    "cash and cash equivalents":     7,
    "acid test":                     7,
    "liquid assets":                 7,
    "trade payables":                7,
    "trade receivables":             7,
    "inventory":                     7,
    "cash flow from operations":     7,
    "net profit":                    0,
    "profit after tax":              0,
    "pat":                           0,
    "ebitda":                        0,
    "ebit":                          0,
    "operating profit":              0,
    "balance sheet":                 0,
    "financial highlights":          0,
    "key financial":                 0,
    "financial summary":             0,
    "five year":                     0,
    "ten year":                      0,
    "consolidated":                  0,
    "standalone":                    0,
    "total assets":                  0,
    "return on equity":              0,
    "return on assets":              0,
    "roce":                          0,
    "roe":                           0,
    "roa":                           0,
    "earnings per share":            0,
    "eps":                           0,
    "gross profit":                  0,
    "operating margin":              0,
    "profit margin":                 0,
    "management discussion":         0,
    "ratio analysis":                0,
    "key ratios":                    0,
}

HIGHLIGHT_ANCHORS = [
    "financial highlights", "key financial", "financial summary",
    "financial performance", "five year financial", "ten year financial",
    "at a glance", "financial overview", "financial snapshot",
    "financial results", "financial review", "selected financial",
    "key metrics", "financial data", "annual financial",
    "management discussion", "md&a", "mda",
    "revenue from operations", "total income", "gross revenue",
    "statement of profit", "profit and loss", "income statement",
    "total borrowings", "debt profile", "debt summary",
    "long term borrowings", "short term borrowings",
    "term loan", "secured loan", "unsecured loan",
    "debt maturity", "maturity profile",
    "dscr", "debt service coverage", "interest coverage ratio",
    "debt service ratio", "fixed charge coverage",
    "auditor's report", "audit report", "independent auditor",
    "statutory auditor", "qualified opinion", "emphasis of matter",
    "going concern", "caro report",
    "gst summary", "gst reconciliation", "gstr-1", "gstr-3b",
    "output gst", "input tax credit", "indirect tax summary",
    "tax reconciliation", "tax expense",
    "related party transactions", "related party disclosures",
    "transactions with related", "promoter transactions",
    "current ratio", "quick ratio", "financial ratios",
    "key ratios", "ratio analysis", "debt to equity",
    "return on equity", "roce", "roe", "roa",
]

DEBT_ANCHORS = [
    "total borrowings",
    "long term borrowings",
    "short term borrowings",
    "long-term debt",
    "notes to accounts",
    "schedule of borrowings",
    "non-current liabilities",
    "financial liabilities",
    "note on borrowings",
    "secured loans",
    "unsecured loans",
    "debentures",
    "term loans from banks",
    "balance sheet",
]

# ── Dedicated profit/P&L anchors ─────────────────────────────────────
# These pages are SEPARATELY guaranteed slots so net profit
# is never N/A due to budget constraints
PROFIT_ANCHORS = [
    "statement of profit and loss",
    "profit and loss account",
    "profit after tax",
    "net profit",
    "pat",
    "profit for the year",
    "profit/(loss) for the year",
    "profit/(loss) after tax",
    "consolidated statement of profit",
    "standalone statement of profit",
    "total comprehensive income",
    "earnings per share",
    "basic eps",
]

CRITERIA_NAMES = {
    1: "Revenue", 2: "GST", 3: "Auditor",
    4: "Related Party", 5: "DSCR",
    6: "Debt/Equity", 7: "Current Ratio",
}


def extract_page_content(page):
    parts = []
    try:
        tables = page.extract_tables()
        if tables:
            for table in tables:
                rows = []
                for row in table:
                    if row:
                        clean = [str(c).strip() if c is not None else "" for c in row]
                        if any(clean):
                            rows.append(" | ".join(clean))
                if rows:
                    parts.append("[TABLE]\n" + "\n".join(rows) + "\n[/TABLE]")
    except Exception:
        pass
    try:
        text = page.extract_text()
        if text:
            parts.append(text)
    except Exception:
        pass
    return "\n".join(parts)


def smart_pdf_summarizer(pdf_path, max_chars=MAX_CHARS):
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"  📖 PDF loaded: {total_pages} pages — scanning ALL pages...")

        page_data       = []
        highlight_pages = []
        debt_pages      = []
        profit_pages    = []

        for page_num, page in enumerate(pdf.pages):
            content     = extract_page_content(page)
            content_low = content.lower()

            score     = 0
            page_crit = set()
            for keyword, crit_id in KEYWORD_MAP.items():
                if keyword in content_low:
                    weight = 3 if crit_id > 0 else 1
                    count  = content_low.count(keyword)
                    score += weight * min(count, 5)
                    page_crit.add(crit_id)

            is_highlight = any(a in content_low for a in HIGHLIGHT_ANCHORS)
            is_debt      = any(a in content_low for a in DEBT_ANCHORS)
            is_profit    = any(a in content_low for a in PROFIT_ANCHORS)

            if score > 0:
                page_data.append((score, page_crit, page_num, content))
            if is_highlight:
                highlight_pages.append((score, page_num, content))
            if is_debt:
                debt_pages.append((score, page_num, content))
            if is_profit:
                profit_pages.append((score, page_num, content))

        relevant_count = len(page_data)
        print(f"  🔍 {relevant_count} keyword-relevant pages out of {total_pages}")

        page_data.sort(key=lambda x: x[0], reverse=True)
        highlight_pages.sort(key=lambda x: x[0], reverse=True)
        highlight_pages = highlight_pages[:MAX_HIGHLIGHTS]
        debt_pages.sort(key=lambda x: x[0], reverse=True)
        debt_pages = debt_pages[:3]
        profit_pages.sort(key=lambda x: x[0], reverse=True)
        profit_pages = profit_pages[:3]

        print(f"  📌 {len(highlight_pages)} financial highlights pages locked in")
        print(f"  💰 {len(debt_pages)} debt/balance sheet pages locked in")
        print(f"  📈 {len(profit_pages)} profit/P&L pages locked in")

        summary_parts  = []
        chars_used     = 0
        pages_included = set()
        criteria_found = set()

        # Cover page
        cover = extract_page_content(pdf.pages[0])
        snippet = cover[:2000]
        summary_parts.append(f"\n--- PAGE 1 (cover) ---\n{snippet}")
        chars_used += len(snippet)
        pages_included.add(0)

        # Phase 1a — financial highlights pages
        for score, page_num, content in highlight_pages:
            if page_num in pages_included or chars_used >= max_chars:
                continue
            snippet = content[:3000]
            summary_parts.append(f"\n--- PAGE {page_num+1} [HIGHLIGHTS] ---\n{snippet}")
            chars_used += len(snippet)
            pages_included.add(page_num)
            cl = content.lower()
            for kw, cid in KEYWORD_MAP.items():
                if cid > 0 and kw in cl:
                    criteria_found.add(cid)

        # Phase 1b — debt/balance sheet pages (guaranteed slots)
        for score, page_num, content in debt_pages:
            if page_num in pages_included or chars_used >= max_chars:
                continue
            snippet = content[:3000]
            summary_parts.append(f"\n--- PAGE {page_num+1} [BALANCE SHEET / DEBT] ---\n{snippet}")
            chars_used += len(snippet)
            pages_included.add(page_num)
            cl = content.lower()
            for kw, cid in KEYWORD_MAP.items():
                if cid > 0 and kw in cl:
                    criteria_found.add(cid)

        # Phase 1c — profit/P&L pages (guaranteed slots)
        for score, page_num, content in profit_pages:
            if page_num in pages_included or chars_used >= max_chars:
                continue
            snippet = content[:3000]
            summary_parts.append(f"\n--- PAGE {page_num+1} [PROFIT & LOSS] ---\n{snippet}")
            chars_used += len(snippet)
            pages_included.add(page_num)
            cl = content.lower()
            for kw, cid in KEYWORD_MAP.items():
                if cid > 0 and kw in cl:
                    criteria_found.add(cid)

        # Phase 2 — top keyword-scored pages
        for score, page_crit, page_num, content in page_data:
            if page_num in pages_included or chars_used >= max_chars:
                continue
            remaining = max_chars - chars_used
            if len(content) > remaining:
                if remaining > 400:
                    content = content[:remaining]
                else:
                    continue
            summary_parts.append(f"\n--- PAGE {page_num+1} (score: {score}) ---\n{content}")
            chars_used += len(content)
            pages_included.add(page_num)
            criteria_found.update(page_crit)

    summary_text = "\n".join(summary_parts)
    missing_crit = [CRITERIA_NAMES[i] for i in range(1, 8) if i not in criteria_found]

    print(f"  ✅ Selected {len(pages_included)} pages → {len(summary_text):,} chars "
          f"(limit: {max_chars:,})")
    if criteria_found:
        found = [CRITERIA_NAMES[i] for i in sorted(criteria_found) if i in CRITERIA_NAMES]
        print(f"  📋 Criteria covered : {', '.join(found)}")
    if missing_crit:
        print(f"  ⚠️  Not found       : {', '.join(missing_crit)} → N/A or estimated")

    return summary_text, {
        "total_pages":      total_pages,
        "relevant_pages":   relevant_count,
        "highlight_pages":  len(highlight_pages),
        "pages_used":       len(pages_included),
        "chars_extracted":  len(summary_text),
        "criteria_found":   list(criteria_found),
        "criteria_missing": missing_crit,
    }


def ask_llm(prompt, retries=3, retry_delay=15):
    for attempt in range(1, retries + 1):
        try:
            response = client.chat(
                model="command-a-03-2025",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.message.content[0].text
        except Exception as e:
            print(f"  ⚠️  Cohere error (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"  ⏳ Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
            else:
                raise RuntimeError(f"Cohere API failed after {retries} attempts: {e}")


def safe_parse_json(raw):
    def fix_bare_na(text):
        return re.sub(r':\s*N/A\b', ': "N/A"', text, flags=re.IGNORECASE)

    clean = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except Exception:
        pass
    try:
        return json.loads(fix_bare_na(clean))
    except Exception:
        pass
    start = raw.find("{")
    end   = raw.rfind("}") + 1
    if start != -1 and end > start:
        chunk = raw[start:end]
        try:
            return json.loads(chunk)
        except Exception:
            pass
        try:
            return json.loads(fix_bare_na(chunk))
        except Exception:
            pass
    return None


def calculate_gst(financial_data):
    def to_float(val):
        if val in (None, "N/A", "", "n/a", "NA"):
            return None
        try:
            return float(str(val).replace(",", "").replace("₹", "").replace("Cr", "").strip())
        except (ValueError, TypeError):
            return None

    gst_pdf = to_float(financial_data.get("gst_reported_revenue"))
    if gst_pdf is not None and gst_pdf > 0:
        return gst_pdf, "extracted_from_pdf"

    revenue = to_float(financial_data.get("annual_revenue"))
    if revenue is not None and revenue > 0:
        return round(revenue * 0.18, 2), "estimated_18pct_of_revenue"

    return None, "unavailable"


def extract_financials(pdf_path, doc_type="annual_report"):
    print(f"  📖 Reading PDF: {pdf_path}")

    summary_text, stats = smart_pdf_summarizer(pdf_path)

    prompt = f"""
You are an expert Indian corporate credit analyst.
Extract key financial data from the document sections below.

Document type: {doc_type}

IMPORTANT: Pages contain [TABLE] blocks with pipe-separated rows.
These are real financial tables extracted directly from the PDF.
ALWAYS read numbers from [TABLE] blocks first — they are most accurate.

Example:
  [TABLE]
  Particulars | FY 2024 | FY 2023
  Revenue from Operations | 1,62,990 | 1,40,987
  Net Profit | 26,568 | 22,110
  Total Borrowings | 3,200 | 2,800
  [/TABLE]

Pages selected using 7 fraud-detection criteria:
  1. Revenue / Income
  2. GST (GSTR-1, GSTR-3B, output tax)
  3. Auditor qualification / emphasis of matter
  4. Related-party transactions
  5. DSCR (Debt Service Coverage Ratio)
  6. Debt-to-Equity ratio
  7. Current Ratio / Liquidity

Document sections:
{summary_text}

STRICT RULES:
1. Return raw JSON only. No explanation. No markdown. No backticks.
2. Start with {{ and end with }}
3. Numeric fields: plain float in Indian Crores.
   - Lakhs  → divide by 100
   - Millions → multiply by 0.1
   - No symbols, no commas, no units. Example: 162990.5
4. Boolean fields: true or false (lowercase, no quotes).
5. Missing values → "N/A" WITH double quotes.
6. ALWAYS use the MOST RECENT financial year's numbers.
   Tables often show multiple years — ALWAYS pick the FIRST/LEFT column after the header.
   Example: if table shows FY2024 | FY2023, use FY2024 (left column).
   Example: if table shows 2023-24 | 2022-23, use 2023-24 (left column).
   NEVER use prior year numbers. If unsure, pick the LARGER revenue value.
7. CRITICAL — DO NOT SWAP FIELDS:
   annual_revenue = Revenue from Operations or Total Income (LARGEST number, typically > net_profit)
   net_profit     = Profit After Tax or PAT (SMALLER number, typically < annual_revenue)
   Revenue is ALWAYS larger than net profit. If you see profit > revenue, you have them swapped.
   Example: Revenue=₹2,29,171 Cr, Profit=₹-4,910 Cr → correct
            Revenue=₹1,40,987 Cr, Profit=₹2,29,171 Cr → WRONG, these are swapped
8. GST: look in [TABLE] blocks for "output GST", "GST collected",
   "indirect tax", "tax expense". Convert to Crores.
   If not found, return "N/A" — we calculate it separately.
8. DSCR: use stated ratio OR calculate EBITDA ÷ (Interest + Principal).
9. related_party_transaction_percent: RPT total as % of revenue.
10. Every field must be present. Never skip any field.

Return EXACTLY this JSON:
{{
  "company_name": "",
  "industry": "",
  "annual_revenue": "N/A",
  "net_profit": "N/A",
  "ebitda": "N/A",
  "total_debt": "N/A",
  "total_assets": "N/A",
  "shareholder_equity": "N/A",
  "debt_to_equity": "N/A",
  "current_ratio": "N/A",
  "dscr": "N/A",
  "gst_reported_revenue": "N/A",
  "gstr1_vs_gstr3b_mismatch": false,
  "gstr_mismatch_details": "N/A",
  "related_party_transaction_percent": "N/A",
  "auditor_qualification": false,
  "auditor_remarks": "N/A",
  "promoter_names": [],
  "collateral_mentioned": "N/A",
  "existing_loans": "N/A",
  "years_in_business": "N/A",
  "credit_rating": "N/A",
  "key_risks": [],
  "key_strengths": [],
  "summary": ""
}}
"""

    print("  🤖 Asking Groq AI to extract financials...")
    raw    = ask_llm(prompt)
    result = safe_parse_json(raw)

    if result:
        # ── Safety net: auto-fix revenue/profit swap ──────────
        def to_f(v):
            try: return float(str(v).replace(",","").replace("₹","").replace("Cr","").strip())
            except: return None

        rev = to_f(result.get("annual_revenue"))
        pft = to_f(result.get("net_profit"))
        if rev is not None and pft is not None and rev > 0 and pft > 0 and pft > rev:
            print(f"  ⚠️  Revenue/Profit swap detected! Auto-correcting...")
            result["annual_revenue"], result["net_profit"] = result["net_profit"], result["annual_revenue"]
        gst_value, gst_method = calculate_gst(result)
        result["gst_calculated"]         = gst_value
        result["gst_calculation_method"] = gst_method

        if gst_method == "estimated_18pct_of_revenue":
            print(f"  💡 GST not in PDF → estimated 18% of revenue = ₹{gst_value} Cr")
        elif gst_method == "extracted_from_pdf":
            print(f"  ✅ GST extracted from PDF tables = ₹{gst_value} Cr")
        else:
            print("  ⚠️  GST unavailable (revenue also not found)")

        result["_extraction_stats"] = stats
        print("  ✅ Extraction complete!")
        return result
    else:
        print("  ❌ JSON parse failed.")
        print(f"  Raw preview: {raw[:300]}")
        return {"error": "Parse failed", "raw": raw[:500]}