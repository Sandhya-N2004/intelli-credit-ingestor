# Part-3: Recommendation Engine — Intelli-Credit

## Overview

The **Recommendation Engine** is the final stage of the Intelli-Credit pipeline.
It combines outputs from **Part-1 (Data Ingestor)** and **Part-2 (Research Agent)** to produce an **AI-driven loan recommendation** and generate a professional **Credit Appraisal Memo (CAM)**.

This module simulates how a **bank credit committee** evaluates corporate loan applications using the **Five C’s of Credit framework** along with explainable AI analytics.

---

# Pipeline Integration

The Recommendation Engine consumes outputs from earlier stages:

```
Part-1 → Data Ingestor
        ↓
Financial extraction
GST analysis
Fraud detection
        ↓
output_company.json
```

```
Part-2 → Research Agent
        ↓
Financial risk model
News analysis
Promoter risk detection
Sector risk detection
Litigation risk detection
        ↓
part2_output.json
```

```
Part-3 → Recommendation Engine
        ↓
Five C's credit scoring
Explainable AI
Risk visualization
Default probability simulation
Loan decision engine
CAM generation
```

---

# Features

## 1. Five C’s Credit Analysis

The model evaluates companies using the standard banking credit framework:

| Factor     | Description                                     |
| ---------- | ----------------------------------------------- |
| Character  | Management credibility and overall risk profile |
| Capacity   | Ability to repay debt based on profitability    |
| Capital    | Financial strength and revenue base             |
| Collateral | Security coverage and fraud indicators          |
| Conditions | External market and sector risks                |

Each factor contributes to a **weighted credit score**.

---

## 2. Explainable AI

The system uses **SHAP (SHapley Additive Explanations)** to explain how each factor contributes to the final credit decision.

Example output:

```
Explainable AI Contribution:

Character : 0.252
Capacity : -0.594
Capital : -0.052
Collateral : 0.585
Conditions : 0.160
```

This provides transparency into the model’s reasoning.

---

## 3. Risk Visualization

### Credit Profile Donut Chart

Displays the distribution of the Five C’s for quick credit risk interpretation.

Output:

```
Tata_Steel_credit_donut.png
```

---

### Risk Breakdown Chart

Shows the contribution of various risk sources:

* Financial Risk
* Fraud Risk
* News Sentiment Risk
* Promoter Risk
* Sector Risk
* Litigation Risk

Output:

```
Tata_Steel_risk_breakdown.png
```

---

## 4. Default Probability Simulation

A **Monte Carlo simulation** estimates the probability of loan default based on credit score variability.

Example:

```
Default Probability: 0.378
```

---

## 5. Loan Decision Engine

Based on the computed credit score, the system recommends:

* Loan approval / rejection
* Suggested loan amount
* Interest rate

Decision logic:

| Credit Score | Decision             |
| ------------ | -------------------- |
| < 0.40       | Rejected             |
| 0.40 – 0.65  | Conditional Approval |
| > 0.65       | Approved             |

Example output:

```
FINAL CREDIT SCORE: 0.51

Decision: CONDITIONAL APPROVAL
Recommended Loan: ₹11458.55
Interest Rate: 13.5%
```

---

## 6. Credit Appraisal Memo Generator

The system automatically generates a **structured CAM report** similar to internal bank reports.

Output file:

```
CAM_Tata_Steel.docx
```

Contents include:

* Company overview
* Five C's analysis
* Loan recommendation
* Risk simulation
* Sector benchmarking

---

## 7. AI Decision Explanation

The engine produces a **human-readable explanation** of the credit decision.

Output file:

```
Tata_Steel_decision_explanation.txt
```

Example:

```
Loan Decision: Conditional Approval
Recommended Loan: ₹11458.55

Five C's Evaluation:
Character risk is MODERATE
Capacity risk is HIGH
Collateral is STRONG
```

---

# Generated Outputs

Running the engine produces the following artifacts:

```
CAM_Tata_Steel.docx
Tata_Steel_credit_donut.png
Tata_Steel_risk_breakdown.png
Tata_Steel_decision_explanation.txt
```

---

# How to Run

Navigate to the Part-3 folder and execute:

```
python part3_engine.py
```

Ensure the following files exist from earlier modules:

```
output_company.json
part2_output.json
```

---

# Technologies Used

* Python
* NumPy
* Matplotlib
* SHAP
* python-docx

---

# Future Improvements

Potential upgrades include:

* Streamlit dashboard for interactive credit evaluation
* LLM-generated Credit Appraisal Memo summaries
* Sector benchmarking using industry datasets
* Integration with bank loan management systems

---

# Author

Developed as part of the **Intelli-Credit AI Hackathon Project**.

