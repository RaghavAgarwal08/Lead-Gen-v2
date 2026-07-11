# Timidly Inc — AI-Powered Lead Generation Pipeline

> An intelligent, self-learning lead generation tool built for [Timidly Inc](https://timidly.com) (SomitraSR). The pipeline autonomously discovers, enriches, and scores startup companies as potential sponsorship leads — then delivers fully formatted prospect reports with tailored outreach strategies.

🔗 **Live App:** [https://lead-gen-v2.onrender.com/](https://lead-gen-v2.onrender.com/)

---

## Deploy to Render (Production Web Service Launch)

You can launch and operate this application in the cloud using Render:

### Setup Steps:
1. **Push to GitHub**: Create a private repository on GitHub and push this project directory to it.
2. **Create Web Service on Render**:
   - Go to your [Render Dashboard](https://dashboard.render.com).
   - Click **New + > Web Service** and connect your GitHub repository.
3. **Configure Settings**:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
4. **Set Environment Variables**: In the **Environment** tab, click **Add Environment Variable** and add the following keys:
   - `OPENAI_API_KEY`
   - `APIFY_API_TOKEN`
   - `FIRECRAWL_API_KEY`
   - `APP_PASSWORD` (Highly Recommended - secure administrative passkey to lock the dashboard UI)
   - `SMTP_USER` (Optional - fallback Gmail address for email reports)
   - `SMTP_PASSWORD` (Optional - Google App Password for email reports)
5. **Launch**: Render will build the container and deploy it, generating a secure live HTTPS URL. Open this URL to access your dashboard panel.

---

## Features

- **ICP-Driven Discovery** — Analyzes your existing prospect list to understand your Ideal Customer Profile, then autonomously generates search queries and scrapes Product Hunt and Y Combinator for fresh, matching targets.
- **Multi-Source Enrichment** — Extracts contact details (email, phone, LinkedIn, X/Twitter), headquarters country, funding stage, and landing page content using Apify, Firecrawl, and Google Search.
- **AI-Powered Pitch Generation** — Uses OpenAI GPT-4o-mini with structured outputs to produce tailored outreach angles, package recommendations, and founder background analysis for every lead.
- **Self-Learning Memory** — Every generated lead is stored in a local database. On subsequent runs, the model reads past leads as few-shot training examples to produce progressively better pitches.
- **Duplicate Filtering** — Automatically excludes companies already in the ICP list or previously processed, ensuring every run surfaces net-new targets.
- **Multi-Format Export** — Outputs a professionally formatted Word document (DOCX), CSV for CRM import, and JSON for programmatic use.
- **Email Delivery** — Optionally emails the completed reports to any address via Gmail SMTP.

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/your-username/lead-gen-v0.git
cd lead-gen-v0

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Open .env and fill in your API keys (see USAGE.md for details)

# 4. Run the pipeline
python main.py
```

The tool will prompt you for:
1. **Email address** — where to send the finished reports
2. **Number of leads** — how many new companies to discover and analyze

---

## Documentation

| Document | Description |
|----------|-------------|
| [`ARCHITECTURE.md`](final%20documentation%20package/ARCHITECTURE.md) | Project structure, scaffold, and module responsibilities |
| [`WORKFLOW.md`](final%20documentation%20package/WORKFLOW.md) | End-to-end technical workflow, tools, and data flow |
| [`USAGE.md`](final%20documentation%20package/USAGE.md) | Setup instructions, API key configuration, and CLI reference |

---

## Output Example

Each run produces three files:

- **`Timidly_Prospects_Report.docx`** — Formatted Word document matching the original prospect list style
- **`Timidly_Prospects_Report.csv`** — Flat CSV for CRM import
- **`Timidly_Prospects_Report.json`** — Machine-readable JSON

Every lead record includes:

| Field | Description |
|-------|-------------|
| Company Name | Target startup/company |
| Tagline | One-line product description |
| Point of Contact | Decision-maker name |
| Title | Job title |
| Email | Verified or inferred email |
| LinkedIn | Profile URL |
| X / Twitter | Handle (if available) |
| Phone | Number (if available) |
| Country | Headquarters location |
| Funding Status | Stage and amount raised |
| Background of Founders | Experience and achievements |
| Why This Company is a Lead | Strategic fit reasoning |
| Recommended Package | Sponsorship tier suggestion |
| Tailored Outreach Angle | Personalized opening message |

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| **Python 3.12+** | Core runtime |
| **FastAPI** | Web server backend & secure REST endpoints |
| **Vanilla HTML/CSS/JS** | Responsive glassmorphic dashboard UI |
| **OpenAI GPT-4o-mini** | Pitch generation with structured outputs |
| **Apify** | Google Search scraping, LinkedIn lookups, contact extraction |
| **Firecrawl** | Website crawling and markdown conversion |
| **python-docx** | DOCX report generation |
| **Gmail SMTP / Resend** | Email delivery |

---

## License

Private — Timidly Inc. All rights reserved.

---

## Document Navigation

*   [README.md](README.md) — Product Overview & Launch
*   [DOCUMENTATION_V1.md](final%20documentation%20package/DOCUMENTATION_V1.md) — User & Admin Operations Guide
*   [USAGE.md](final%20documentation%20package/USAGE.md) — Environment variables & CLI usage reference
*   [ARCHITECTURE.md](final%20documentation%20package/ARCHITECTURE.md) — Project layout & Module maps
*   [TECHNICAL_ARCHITECTURE.md](final%20documentation%20package/TECHNICAL_ARCHITECTURE.md) — Technical system design details
*   [WORKFLOW.md](final%20documentation%20package/WORKFLOW.md) — Pipeline data processing stages
*   [OWASP_TOP_10.md](final%20documentation%20package/OWASP_TOP_10.md) — Security remediations & Checklist
*   [Operations-Runbook.md](final%20documentation%20package/Operations-Runbook.md) — Operations & Troubleshooting runbook
*   [Client-UAT-Package.md](final%20documentation%20package/Client-UAT-Package.md) — Client User Acceptance Testing Package
*   [INTEGRATIONS_LIST.md](final%20documentation%20package/INTEGRATIONS_LIST.md) — API configurations & Cost structure
*   [LEAD_QUALIFICATION_CRITERIA.md](final%20documentation%20package/LEAD_QUALIFICATION_CRITERIA.md) — Fit scoring framework & Criteria
