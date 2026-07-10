# Timidly Inc — AI-Powered Lead Generation Pipeline

> An intelligent, self-learning lead generation tool built for [Timidly Inc](https://timidly.com) (SomitraSR). The pipeline autonomously discovers, enriches, and scores startup companies as potential sponsorship leads — then delivers fully formatted prospect reports with tailored outreach strategies.

🔗 **Live App:** [https://lead-gen-v2-if0t931gi-raghav-agarwals-projects-306aac5f.vercel.app](https://lead-gen-v2-if0t931gi-raghav-agarwals-projects-306aac5f.vercel.app)

---

## Deploy to Vercel (One-Click Launch)

You can launch and run this application directly in your browser without using the terminal:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fyour-username%2Fyour-repo-name)

### Setup Steps:
1. **Push to GitHub**: Create a new private repository on GitHub and push this project directory to it.
2. **Import to Vercel**:
   - Go to your [Vercel Dashboard](https://vercel.com), click **Add New > Project**, and import your repository.
   - Or click the **Deploy with Vercel** button above (update `your-username/your-repo-name` to match your repository link).
3. **Set Environment Variables**: During import or under Project Settings > Environment Variables, add the following credentials:
   - `OPENAI_API_KEY`
   - `APIFY_API_TOKEN`
   - `FIRECRAWL_API_KEY`
   - `SMTP_USER` (Optional - for email report dispatch)
   - `SMTP_PASSWORD` (Optional - for email report dispatch)
4. **Launch**: Once Vercel completes the deployment, it will generate a permanent live URL (e.g., `https://your-project.vercel.app`). Bookmark this URL to launch the dashboard and run the lead generation pipeline with a single click anytime!

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
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Project structure, scaffold, and module responsibilities |
| [`WORKFLOW.md`](WORKFLOW.md) | End-to-end technical workflow, tools, and data flow |
| [`USAGE.md`](USAGE.md) | Setup instructions, API key configuration, and CLI reference |

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
| **OpenAI GPT-4o-mini** | Pitch generation with structured outputs |
| **Apify** | Google Search scraping, LinkedIn lookups, contact extraction |
| **Firecrawl** | Website crawling and markdown conversion |
| **python-docx** | DOCX report generation |
| **Gmail SMTP** | Email delivery |

---

## License

Private — Timidly Inc. All rights reserved.
