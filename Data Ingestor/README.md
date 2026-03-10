# Intelli-Credit
### AI-Powered Credit Risk & Fraud Detection Engine
**Part 1 — Data Ingestor**

---

## Overview

Intelli-Credit is an AI-powered credit decisioning engine that automates the evaluation of corporate loan applications. It ingests company financial documents, cross-references them with banking and tax records, and applies a structured fraud detection framework to produce a final credit decision.

The system processes any company's PDF annual report through a 5-step automated pipeline and produces one of three verdicts:

- ✅ **LOAN APPROVED**
- 🟡 **REVIEW REQUIRED**
- 🔴 **LOAN REJECTED**

Along with a full breakdown of all risk signals detected, penalty scores, and a visual knowledge graph.

---

## Architecture

### 5-Step Pipeline

| Step | Module | Description |
|------|--------|-------------|
| 1 | `extractor.py` | Reads PDF, selects relevant pages, sends to Cohere AI, extracts structured financials |
| 2 | `main.py` | Loads bank transaction CSV, retrieves real bank credits and GSTR values |
| 3 | `gst_analysis.py` | Calculates 12 GST compliance metrics, detects circular trading patterns |
| 4 | `fraud_detection.py` | Evaluates 7 fraud criteria, raises flags, calculates penalty score and verdict |
| 5 | `main.py` | Saves complete results to output JSON file |

### File Structure

```
intelli-credit-ingestor/
  Data Ingestor/
    main.py                    # Orchestrator — batch and dynamic modes
    extractor.py               # PDF reader + Cohere AI extraction engine
    fraud_detection.py         # 7-criteria fraud and credit risk checker
    gst_analysis.py            # GST mismatch analysis + circular trading detection
    sample_docs/
      *.pdf                    # Company annual reports
      universal_bank_transactions.csv
  index.html                   # Interactive web dashboard
  requirements.txt
  .gitignore
```

---

## Module Reference

### `extractor.py` — PDF Reader + AI Extractor

Reads any PDF annual report and extracts structured financial data using the Cohere language model.

**Page Selection Strategy**

Rather than sending the entire PDF (which exceeds token limits), the module uses a keyword-scoring system:

- All pages are scored against a `KEYWORD_MAP` of 100+ financial terms mapped to 7 fraud criteria
- Up to 15 financial highlight pages locked in first (balance sheets, P&L summaries)
- Up to 3 dedicated debt/borrowing pages added
- Up to 3 profit and loss pages added
- Remaining budget filled with highest-scoring pages
- Total trimmed to 25,000 characters before sending to Cohere

**AI Extraction**

Selected pages are sent to `command-a-03-2025` with a structured prompt enforcing rules — always use the most recent year, always pick consolidated figures, never swap revenue and profit.

**Post-Processing**

- Auto-detects and corrects revenue/profit swaps
- Estimates GST as 18% of revenue if not found in the document
- Validates and cleans all numeric fields

**Output Fields**

```
annual_revenue, net_profit, ebitda, total_debt, total_assets, shareholder_equity
debt_to_equity, current_ratio, dscr
auditor_qualification, auditor_remarks
related_party_transaction_percent
gst_calculated, gst_calculation_method
```

---

### `gst_analysis.py` — GST Compliance Module

Performs detailed GST compliance analysis by comparing bank credits, GSTR-1 filings, and GSTR-3B filings. Also detects circular trading patterns.

**Smart Approach Detection**

| Approach | When Used | Data Source |
|----------|-----------|-------------|
| Approach 1 — Real Data | Company found in bank CSV | Actual GSTR-1 and GSTR-3B values from CSV |
| Approach 2 — Estimated | Company not in bank CSV | GSTR-1 = revenue from PDF; GSTR-3B = revenue × 0.85 |

**12 Metrics Calculated**

| # | Metric | Description |
|---|--------|-------------|
| 1 | Bank Credits (Cr) | Total bank credits in Crores |
| 2 | GSTR-1 Turnover | Sales declared in GSTR-1 filing |
| 3 | GSTR-3B Turnover | Taxable sales reported in GSTR-3B |
| 4 | GSTR-1 vs Bank Amount | Absolute difference |
| 5 | GSTR-1 vs Bank Ratio | Percentage gap |
| 6 | GSTR-1 vs GSTR-3B Amount | Difference between the two returns |
| 7 | GSTR-1 vs GSTR-3B Ratio | Primary fraud signal — should be below 10% |
| 8 | Bank vs GSTR-3B Amount | Cross-check between deposits and tax paid |
| 9 | Bank vs GSTR-3B Ratio | Secondary consistency check |
| 10 | GST Compliance Score | 0 to 1 composite score (1.0 = perfect) |
| 11 | Monthly Variance | Std deviation of monthly credits — spikes = irregularity |
| 12 | GST Risk Flag | Low Risk / Moderate Risk / High Risk |

**Circular Trading Detection**

Scans all transactions for money sent to a counterparty and returned within 7 days at the same amount (within 10% tolerance) — a strong indicator of fictitious revenue inflation.

---

### `fraud_detection.py` — 7 Criteria Checker

The core credit risk assessment engine. Evaluates 7 standardised fraud criteria and produces a final verdict.

| Criterion | What It Checks | HIGH Flag | MEDIUM Flag | Penalty |
|-----------|---------------|-----------|-------------|---------|
| C1 — Revenue vs Bank | Reported revenue vs actual bank credits | < 10% ratio | < 30% ratio | -25 / -10 pts |
| C2 — GST Compliance | Reported GST vs 18% of revenue | > 2.5x expected | < 30% of expected | -15 pts |
| C3 — GSTR Mismatch | GSTR-1 vs GSTR-3B gap | > 20% gap | > 10% gap | -15 / -10 pts |
| C4 — Auditor | Statutory auditor opinion | Qualified opinion | — | -20 pts |
| C5 — Related Party | Related party transaction % | > 60% of revenue | > 40% of revenue | -20 / -10 pts |
| C6 — DSCR | Debt Service Coverage Ratio | < 1.0 | 1.0 to 1.5 | -25 / -10 pts |
| C7 — Profitability | D/E ratio, net profit, current ratio | D/E > 3.0 | Loss / CR < 1.0 | -20 / -10 pts |
| CT — Circular Trading | Money out and returned within 7 days | Detected | — | -25 pts |

**Verdict Logic**

```
2+ HIGH flags   →  LOAN REJECTED  🔴
1  HIGH flag    →  LOAN REJECTED  🔴
2+ MEDIUM flags →  REVIEW REQUIRED  🟡
1  MEDIUM flag  →  REVIEW REQUIRED  🟡
0  flags        →  LOAN APPROVED  ✅
```

Score starts at **100** and each flag deducts its penalty.

---

### `main.py` — Orchestrator

Coordinates all modules. Supports two processing modes.

**Batch Mode**
Processes a pre-configured list of companies automatically. Supports `known_revenue` and `known_profit` overrides to lock verified values and prevent AI extraction inconsistency across runs.

**Dynamic Mode**
Processes any company on demand — user provides company name, PDF path, and bank CSV path. System automatically detects Approach 1 or Approach 2 and adjusts analysis accordingly.

---

## Sample Results

| Company | Revenue | Net Profit | Score | Verdict |
|---------|---------|------------|-------|---------|
| Infosys | ₹1,62,990 Cr | ₹26,750 Cr | 100 / 100 | ✅ LOAN APPROVED |
| TCS | ₹2,55,324 Cr | ₹48,553 Cr | 100 / 100 | ✅ LOAN APPROVED |
| Tata Steel | ₹2,29,171 Cr | ₹-4,910 Cr | 70 / 100 | 🟡 REVIEW REQUIRED |

**Tata Steel — Flags Raised:**
- `C3` GSTR-1 vs GSTR-3B gap = 14.9% → MEDIUM → -10 pts
- `C7` Net Profit = ₹-4,910 Cr (loss-making) → MEDIUM → -10 pts
- `C7` Current Ratio = 0.80 (below 1.0) → MEDIUM → -10 pts

---

## Setup & Installation

### Prerequisites
- Python 3.8+
- Cohere API key — [cohere.com](https://cohere.com)
- PDF annual reports in `sample_docs/`
- Bank transaction CSV in `sample_docs/`

### Install Dependencies

```bash
pip install pdfplumber cohere pandas numpy python-dotenv
```

### Configure Environment

Create a `.env` file inside the `Data Ingestor` folder:

```
COHERE_API_KEY=your_api_key_here
```

### Run

```bash
cd "Data Ingestor"
python main.py
```

```
Select Mode
1 → Batch Mode   (processes all configured companies)
2 → Dynamic Mode (processes any company from user input)
```

---

## Dynamic Company Processing

The system processes any company without prior configuration. When new documents are provided:

| Field | Source | Notes |
|-------|--------|-------|
| Revenue, Profit, Debt | Cohere AI from PDF | Real values extracted from document |
| Auditor Opinion | Cohere AI from PDF | Scans for qualified opinions |
| DSCR, D/E, Current Ratio | Cohere AI from PDF | Calculated or directly stated |
| Related Party % | Cohere AI from PDF | As percentage of revenue |
| Bank Credits | Approach 2 — 50% of revenue | Estimated when company not in CSV |
| GSTR-1 | Approach 2 — equals revenue | Estimated when no GST data in CSV |
| GSTR-3B | Approach 2 — revenue × 0.85 | 15% under-reporting assumed |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3 |
| PDF Extraction | pdfplumber |
| AI Model | Cohere command-a-03-2025 |
| Data Processing | pandas, numpy |
| Configuration | python-dotenv |
| Dashboard | Vanilla JS + HTML5 |
| Output Format | JSON |

---

## Limitations

- Scanned or image-based PDFs are not supported — requires text-extractable PDFs
- AI extraction accuracy depends on document quality and formatting
- Bank credits and GSTR values are estimated for companies not present in the bank CSV
- Cohere free tier limited to 1,000 API calls per month
