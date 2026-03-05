# ============================================
# DIGITAL CREDIT MANAGER - RESEARCH AGENT
# ============================================
# This script implements an AI-based credit research agent
# that combines financial risk modeling, fraud detection,
# web news analysis, and qualitative insights to produce
# a final company risk assessment.
# ============================================

# -----------------------------
# Import Required Libraries
# -----------------------------

import pandas as pd
import numpy as np
import json
import feedparser

from urllib.parse import quote

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

from transformers import pipeline


# ============================================
# 1. FINANCIAL RISK MODEL
# ============================================
# This section trains a Random Forest model to
# estimate financial risk based on company
# financial indicators.

# Load financial dataset
df = pd.read_csv("Corporate_Financial_Risk_Assessment_Data.csv")

# Remove non-numeric columns
df = df.drop(["Company_ID", "Date", "Industry_Sector"], axis=1)

# Separate features and target
X = df.drop("Financial_Risk_Label", axis=1)
y = df["Financial_Risk_Label"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Train Random Forest model
financial_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight="balanced"
)

financial_model.fit(X_train, y_train)

# Evaluate model
y_pred = financial_model.predict(X_test)

print("Financial Model Accuracy:", financial_model.score(X_test, y_test))
print(classification_report(y_test, y_pred))


# Predict risk probability for sample companies
sample_company = X.iloc[0:10]

risk_scores = financial_model.predict_proba(sample_company)

for i, score in enumerate(risk_scores):
    print(f"Company {i+1} Financial Risk Score:", score[1])

# Average financial risk score
financial_risk = risk_scores[:, 1].mean()


# ============================================
# 2. FRAUD DETECTION MODEL
# ============================================
# This module detects suspicious transactions
# using Isolation Forest anomaly detection.

# Load transaction datasets
users = pd.read_csv("users_data.csv")
cards = pd.read_csv("cards_data.csv")
transactions = pd.read_csv("transactions_data.csv")

# Load fraud labels
with open("train_fraud_labels.json") as f:
    data = json.load(f)

fraud_labels = pd.DataFrame(list(data["target"].items()),
                            columns=["id", "fraud"])

fraud_labels["id"] = fraud_labels["id"].astype(int)
fraud_labels["fraud"] = fraud_labels["fraud"].map({"No":0, "Yes":1})

# Merge transaction data with fraud labels
df_transactions = transactions.merge(fraud_labels, on="id")

# Select numeric columns
fraud_data = df_transactions.select_dtypes(include=["int64", "float64"])

# Remove identifiers
fraud_data = fraud_data.drop(columns=["id", "fraud"], errors="ignore")

# Handle missing values
fraud_data = fraud_data.fillna(fraud_data.median())

# Train anomaly detection model
fraud_model = IsolationForest(
    contamination=0.02,
    random_state=42
)

fraud_model.fit(fraud_data)

# Compute fraud scores
fraud_scores = fraud_model.decision_function(fraud_data)

df_transactions["fraud_score"] = fraud_scores

fraud_risk = df_transactions["fraud_score"].mean()


# ============================================
# 3. WEB NEWS SCRAPER (SECONDARY RESEARCH)
# ============================================
# Crawls Google News RSS to gather information
# related to company performance, regulation,
# promoters, and legal risks.

def get_company_news(company):

    queries = [
        company,
        company + " promoter",
        company + " investigation",
        company + " regulation",
        company + " lawsuit",
        company + " RBI regulation",
        company + " sector policy"
    ]

    headlines = []

    for q in queries:

        encoded_query = quote(q)

        url = f"https://news.google.com/rss/search?q={encoded_query}"

        feed = feedparser.parse(url)

        for entry in feed.entries[:5]:
            headlines.append(entry.title)

    return list(set(headlines))


company = "Tata Steel"

news = get_company_news(company)

print("\nNews Headlines:")
for n in news:
    print("-", n)


# ============================================
# 4. SENTIMENT ANALYSIS
# ============================================
# Uses a pretrained NLP model to determine
# whether news sentiment is positive or negative.

sentiment_model = pipeline("sentiment-analysis")

def analyze_news_risk(headlines):

    negative = 0

    for h in headlines:

        result = sentiment_model(h)[0]

        if result["label"] == "NEGATIVE":
            negative += 1

    return negative / len(headlines)


news_risk = analyze_news_risk(news)

print("News Risk Score:", news_risk)


# ============================================
# 5. PROMOTER RISK DETECTION
# ============================================

def detect_promoter_risk(headlines):

    promoter_keywords = [
        "promoter",
        "insider trading",
        "governance",
        "fraud",
        "investigation"
    ]

    risk = 0

    for h in headlines:
        for k in promoter_keywords:
            if k in h.lower():
                risk += 1

    return risk / len(headlines)


promoter_risk = detect_promoter_risk(news)


# ============================================
# 6. SECTOR HEADWIND DETECTION
# ============================================

def detect_sector_risk(headlines):

    sector_keywords = [
        "rbi",
        "regulation",
        "policy change",
        "interest rate hike",
        "new tax",
        "government ban"
    ]

    risk = 0

    for h in headlines:
        for k in sector_keywords:
            if k in h.lower():
                risk += 1

    return risk / len(headlines)


sector_risk = detect_sector_risk(news)


# ============================================
# 7. LITIGATION RISK DETECTION
# ============================================

def detect_litigation_risk(headlines):

    legal_keywords = [
        "lawsuit",
        "court",
        "sebi investigation",
        "penalty",
        "legal action",
        "fraud case"
    ]

    risk = 0

    for h in headlines:
        for k in legal_keywords:
            if k in h.lower():
                risk += 1

    return risk / len(headlines)


litigation_risk = detect_litigation_risk(news)


# ============================================
# 8. SECONDARY RISK ENGINE
# ============================================
# Combines financial, news, fraud, and governance
# signals to compute an overall secondary risk score.

def calculate_secondary_risk(financial, news, fraud,
                             promoter, sector, litigation):

    secondary_risk = (
        0.35 * financial +
        0.20 * news +
        0.15 * abs(fraud) +
        0.15 * promoter +
        0.10 * sector +
        0.05 * litigation
    )

    return secondary_risk


secondary_risk = calculate_secondary_risk(
    financial_risk,
    news_risk,
    fraud_risk,
    promoter_risk,
    sector_risk,
    litigation_risk
)

print("Secondary Risk Score:", secondary_risk)


# ============================================
# 9. PRIMARY RESEARCH (CREDIT OFFICER NOTES)
# ============================================

def qualitative_adjustment(notes):

    adjustment = 0

    if "40% capacity" in notes:
        adjustment += 0.15

    if "attrition" in notes:
        adjustment += 0.10

    if "delayed payment" in notes:
        adjustment += 0.12

    return adjustment


notes = "Factory operating at 40% capacity"

primary_adjustment = qualitative_adjustment(notes)


# ============================================
# 10. FINAL RISK SCORE
# ============================================

final_risk = secondary_risk + primary_adjustment

print("Final Risk Score:", final_risk)


# ============================================
# 11. RISK CLASSIFICATION
# ============================================

def classify_risk(score):

    if score < 0.3:
        return "LOW RISK"

    elif score < 0.6:
        return "MEDIUM RISK"

    else:
        return "HIGH RISK"


risk_category = classify_risk(final_risk)


# ============================================
# 12. FINAL CREDIT REPORT
# ============================================

def generate_report(company):

    print("\n===================================")
    print(" DIGITAL CREDIT MANAGER REPORT")
    print("===================================")

    print("\nCompany:", company)

    print("\n--- Secondary Research ---")

    print("Financial Risk:", round(financial_risk,3))
    print("Fraud Risk:", round(fraud_risk,3))

    print("\nNews Risk:", round(news_risk,3))
    print("Promoter Risk:", round(promoter_risk,3))
    print("Sector Risk:", round(sector_risk,3))
    print("Litigation Risk:", round(litigation_risk,3))

    print("\nSecondary Risk Score:", round(secondary_risk,3))

    print("\n--- Primary Research ---")

    print("Credit Officer Notes:", notes)

    print("\nFinal Risk Score:", round(final_risk,3))

    print("Risk Category:", risk_category)


generate_report(company)

#SAMPLE OUTPUT
#===================================
 #DIGITAL CREDIT MANAGER REPORT
#===================================

#Company: Tata Steel

#--- Secondary Research ---
#Financial Risk: 0.002
#Fraud Risk: 0.105

#News Risk: 0.3
#Promoter Risk: 0.03
#Sector Risk: 0.152
#Litigation Risk: 0.152

#Secondary Risk Score: 0.104

#--- Primary Research ---
#Credit Officer Notes: Factory operating at 40% capacity

#Final Risk Score: 0.254
#Risk Category: LOW RISK*/
