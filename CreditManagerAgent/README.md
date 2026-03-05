# Intelli Credit Ingestor – Credit Manager Agent

This project implements a **Digital Credit Manager (Research Agent)** that analyzes a company’s financial and operational risk using machine learning, fraud detection, and automated secondary research.

The system combines **financial indicators, transaction fraud signals, web news analysis, and qualitative credit officer inputs** to generate a final company risk score.

---

## Features

- **Financial Risk Prediction**
  - Random Forest model trained on corporate financial indicators.

- **Fraud Detection**
  - Isolation Forest model used to detect anomalous transaction behavior.

- **Automated Secondary Research**
  - Crawls Google News to gather company-related information.
  - Performs sentiment analysis on news headlines.

- **Risk Signal Detection**
  - Promoter governance risk detection  
  - Sector headwind detection  
  - Litigation risk detection  

- **Primary Insight Integration**
  - Allows qualitative notes from a credit officer (e.g., factory utilization issues).

- **Final Risk Scoring**
  - Combines multiple signals into a final credit risk classification.

---


---

## Tech Stack

- Python
- Scikit-learn
- Transformers (HuggingFace)
- Pandas / NumPy
- Feedparser (News scraping)

---

## How It Works

1. Train a **financial risk model** using corporate financial data.
2. Detect **transaction anomalies** using fraud detection.
3. Scrape **latest news headlines** related to the company.
4. Perform **sentiment analysis and risk signal detection**.
5. Combine signals into a **secondary research risk score**.
6. Adjust the score using **credit officer observations**.
7. Generate a **final company risk report**.

---

## Note on Dataset Size

Some datasets (such as fraud labels) exceed GitHub's file size limits.  
Only sample datasets are included in this repository for demonstration purposes.
https://www.kaggle.com/datasets/zoya77/corporate-financial-risk-assessment-dataset/data - FINANCIAL RISK ANALYSIS
https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets?utm_source=chatgpt.com - FRAUD DETECTION

---

## Example Output
DIGITAL CREDIT MANAGER REPORT

Company: Tata Steel

Financial Risk: 0.58
News Risk: 0.42
Promoter Risk: 0.10
Sector Risk: 0.15
Litigation Risk: 0.05

Final Risk Score: 0.54
Risk Category: MEDIUM RISK
