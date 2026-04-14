# KERN — Business Intelligence for Small Business Owners

KERN turns your raw sales data into clear, actionable business decisions — no data science team required. Upload a CSV or Excel export from any POS system (Square, Shopify, Toast, Clover, and more) and instantly see what's selling, what's declining, when to staff up, where to raise prices, and what products to bundle. Built for independent small business owners who have data but no time to analyze it.

---

## What Changed from BrewSmart

BrewSmart started as a coffee-shop-specific tool built at Hack@URI 2026. KERN is the evolution: the same intelligence engine, now generalized for **any small business** — retail, food service, e-commerce, or service businesses. The coffee branding is gone; the analytical depth is not.

---

## Features

| Feature | What it does | Technique |
|---|---|---|
| Action Center | Every signal ranked by estimated dollar impact — quick wins and watch-outs in one view | Multi-signal aggregation |
| Business Overview | Revenue, orders, avg ticket, AI weekly priorities, anomaly detection, period-over-period comparison, quick price simulator | Revenue aggregation + robust anomaly detection (MAD) |
| Best Sellers | Products grouped into Stars, Cash Cows, Hidden Gems, Low Activity — with rising star detection and decline alerts | K-Means clustering + momentum analysis |
| Peak Hours | Hour x day revenue heatmap with staffing recommendations and day-part breakdown | Time series analysis |
| Price Intelligence | Per-product raise / lower / maintain recommendations with price simulator and elasticity estimates | Log-log OLS regression + category heuristics |
| Growth Forecast | 1-8 week revenue projection with per-product trends and growth action plan | statsforecast (AutoARIMA + AutoETS) then Prophet then linear fallback |
| Market Basket | Product co-occurrence heatmap and bundle recommendations | Apriori association rules (mlxtend) |
| AI Advisor | Streaming chat that has read your entire dataset and answers like a business consultant | Groq API (Llama 3.3) + proactive AI Brief |

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Groq API key (optional — needed for AI features only)
```bash
export GROQ_API_KEY=your_key_here
```
Get a free key at: [console.groq.com](https://console.groq.com)

### 3. Launch
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Upload your data or click **Try Demo Data (Coffee Shop)** to explore with sample transactions.

---

## Deploy to Production

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions covering Streamlit Community Cloud (recommended), Docker, and Railway.

---

## Data Format

KERN works with **any** CSV or Excel export from any POS system. Columns are auto-detected using broad candidate lists covering 10+ major POS formats (Square, Shopify, Toast, Lightspeed, Clover, Revel, TouchBistro, Aloha, NCR, Heartland, iZettle).

**Minimum required columns:** product name + revenue (or unit price)

**Optional but unlocking more features:** quantity, date/time, location, cost/COGS, transaction/order ID

### Manual override
If auto-detection misses a column, use the sidebar's **Override Column Mapping** expander to set it manually.

---

## Built-in Demo
Click **Try Demo Data (Coffee Shop)** in the sidebar — no file upload needed. Loads 1,400 synthetic transactions across 2 locations and 18 products over 6 months.

---

## Frameworks & Libraries

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) 1.41.1 | Web app framework |
| [pandas](https://pandas.pydata.org) 2.2.3 | Data manipulation |
| [NumPy](https://numpy.org) 1.26.4 | Numerical computing |
| [scikit-learn](https://scikit-learn.org) 1.5.2 | K-Means clustering, StandardScaler |
| [Plotly](https://plotly.com) 5.24.1 | Interactive charts |
| [statsforecast](https://nixtlaverse.nixtla.io/statsforecast) 1.7.8 | AutoARIMA + AutoETS forecasting |
| [prophet](https://facebook.github.io/prophet/) 1.1.6 | Fallback forecasting model |
| [mlxtend](http://rasbt.github.io/mlxtend/) 0.23.2 | Apriori market basket analysis |
| [openpyxl](https://openpyxl.readthedocs.io) 3.1.5 | Excel file support |
| [Groq Python SDK](https://github.com/groq/groq-python) 0.13.0 | Groq API for AI Advisor + AI Brief |

---

## AI Usage Disclosure

In compliance with the hackathon AI policy:

- **Claude (claude.ai)** was used as a development assistant during the hacking period to help write, debug, and refine code
- **Groq API (Llama 3.3)** is integrated directly into the app as the AI Advisor and AI Brief features
- The core architecture, data science methodology, statistical implementations, and product decisions are the original work of the team
- All AI-generated code was reviewed, understood, and validated before inclusion

---

## Tech Stack

Python · Streamlit · pandas · NumPy · scikit-learn · Plotly · statsforecast · Prophet · mlxtend · Groq API

---

*Built at Hack@URI 2026 — evolved from BrewSmart to KERN*
