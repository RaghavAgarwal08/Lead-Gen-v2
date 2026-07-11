# Project Architecture

> This document describes the repository scaffold, directory layout, and the responsibility of every file in the codebase.

---

## Directory Structure

```
Lead Gen V2/
├── .env.example              # Template for environment variables (safe to commit)
├── .env                      # Actual credentials (git-ignored, never committed)
├── .gitignore                # Git exclusion rules
├── README.md                 # Project overview and quick start
├── ARCHITECTURE.md           # This file — scaffold and module map
├── WORKFLOW.md               # End-to-end technical workflow documentation
├── USAGE.md                  # Setup and usage instructions
├── OWASP_TOP_10.md           # OWASP Top 10 compliance checklist and remediations
├── requirements.txt          # Python dependency manifest (pinned versions)
├── config.py                 # Centralized configuration loader
├── main.py                   # CLI entry point and pipeline orchestrator
├── app.py                    # FastAPI web server backend & secure api endpoints
│
├── core/                     # Core business logic modules
│   ├── __init__.py
│   ├── discovery.py          # ICP analysis and target company search
│   ├── contacts.py           # LinkedIn contact lookups and email extraction
│   ├── enricher.py           # Website scraping, firmographics, and country lookup
│   ├── generator.py          # OpenAI pitch generation with self-learning memory
│   └── exporter.py           # DOCX, CSV, and JSON report generation
│
├── utils/                    # Utility modules
│   ├── __init__.py
│   └── mailer.py             # Gmail SMTP email delivery & Resend HTTP API support
│
├── static/                   # Web Dashboard frontend assets
│   ├── index.html            # Dashboard structure (features glassmorphic auth modal)
│   ├── style.css             # Stylesheet (animations, colors, design rules)
│   └── app.js                # Frontend client logic (XSS sanitization, fetch interceptor)
│
├── data/                     # Reference data (ICP profiles)
│   ├── New Prospect List.docx    # Original ICP prospect list (Word format)
│   └── extracted_prospects.md    # Parsed markdown version of the prospect list
│
└── output/                   # Generated reports (git-ignored)
    ├── Timidly_Prospects_Report.docx
    ├── Timidly_Prospects_Report.csv
    └── Timidly_Prospects_Report.json
```

---

## Module Responsibilities

### Entry Points

| File | Role |
|------|------|
| **`main.py`** | CLI argument parsing, interactive prompts, and full pipeline orchestration. Manages the self-learning memory cache (`learned_leads.json`), coordinates all core modules in sequence, and handles error recovery per-lead so a single failure never aborts the entire batch. |
| **`app.py`** | FastAPI server hosting the Web Admin Dashboard. Declares background runner threads (`PipelineManager`) and secures REST API endpoints via `APP_PASSWORD` checks. |

### Configuration

| File | Role |
|------|------|
| **`config.py`** | Loads environment variables from `.env` via `python-dotenv`. Exposes API keys (`APIFY_API_TOKEN`, `OPENAI_API_KEY`, `FIRECRAWL_API_KEY`), SMTP settings, and the sponsorship package catalog used by the AI pitch generator. |
| **`.env.example`** | Documented template listing every required environment variable with inline setup instructions. Collaborators copy this to `.env` and populate their own credentials. |

### Core Modules (`core/`)

| Module | Responsibility |
|--------|---------------|
| **`discovery.py`** | **ICP-Driven Target Discovery.** Loads the prospect list to understand the ideal customer profile. Calls OpenAI to generate 3 search queries from that profile. Scrapes Product Hunt and Y Combinator via Apify Google Search Scraper. Filters out companies already in the ICP list or learned database to ensure net-new results. Includes URL slug parsing to extract clean company names. |
| **`contacts.py`** | **Contact Person Lookup.** Uses Apify Google Search Scraper to find decision-makers (Founder, CEO, Head of Marketing, Partnerships) on LinkedIn for each target company. Parses names, titles, and profile URLs from search results. Also runs the `vdrmota/contact-info-scraper` Apify actor to extract emails, phone numbers, and social handles directly from target websites. |
| **`enricher.py`** | **Website & Firmographic Enrichment.** Scrapes landing page content via Firecrawl and converts it to markdown for LLM context. Queries Google via Apify for funding data, valuation, and employee count. Also performs a dedicated headquarters/country search to feed into the AI generator. |
| **`generator.py`** | **AI Pitch Generation.** Uses OpenAI GPT-4o-mini with Pydantic structured outputs to produce: (1) why the company is a good lead, (2) recommended sponsorship package, (3) tailored outreach angle, (4) headquarters country, and (5) founder background analysis. Implements **self-learning**: loads the last 5 leads from `learned_leads.json` as few-shot examples in the system prompt, so pitch quality improves over successive runs. |
| **`exporter.py`** | **Report Generation.** Produces a professionally styled Word document with Calibri typography, navy headings, and labeled field sections matching the original prospect list format. Also exports CSV (for CRM import) and JSON (for programmatic consumption). |

### Utilities (`utils/`)

| Module | Responsibility |
|--------|---------------|
| **`mailer.py`** | **Email Delivery.** Sends the generated DOCX and CSV as email attachments via Gmail SMTP with TLS. Uses the credentials from `.env`. Gracefully skips sending if SMTP is not configured. |

### Web Dashboard Client (`static/`)

| File | Responsibility |
|------|----------------|
| **`index.html`** | Structure of the administrator panel (includes the glassmorphic authentication modal block). |
| **`style.css`** | Premium CSS guidelines, transitions, layout rules, and animations. |
| **`app.js`** | JavaScript client-side operations. Intercepts fetch calls to append authentication headers, handles session timeout redirects, and escapes dynamic crawled output parameters to prevent XSS. |

### Data Files

| File | Role |
|------|------|
| **`data/New Prospect List.docx`** | The original 49-company ICP prospect list in Word format. This is the "training data" the tool uses to understand the profile of ideal targets. |
| **`data/extracted_prospects.md`** | Auto-generated markdown parse of the Word document. The discovery module reads this file to extract company names, taglines, contacts, and pitch angles for ICP profiling and duplicate filtering. |
| **`learned_leads.json`** | Self-learning memory database (git-ignored). Accumulates every successfully processed lead. Used for: (1) few-shot training of the AI generator, (2) deduplication across runs, and (3) instant cache hits to skip API calls for previously processed companies. |

---

## Design Decisions

### Why Apify Google Search instead of direct LinkedIn/Apollo APIs?
The Apify free tier ($5/month) provides access to Google Search scraping, which can surface LinkedIn profiles, Product Hunt posts, Y Combinator listings, funding data, and headquarters information — all through a single API token. This eliminates the need for separate (and expensive) subscriptions to Apollo, Proxycurl, or LinkedIn Sales Navigator.

### Why structured outputs instead of free-form LLM text?
Using Pydantic models with OpenAI's `response_format` parameter guarantees that every AI response maps exactly to the required lead record schema. This eliminates JSON parsing errors and ensures consistent field coverage across hundreds of leads.

### Why a local JSON file for self-learning instead of a vector database?
For a tool processing 5–50 leads per run, a flat JSON file is simpler, faster, and requires zero infrastructure. The last 5 leads are loaded as few-shot examples — well within GPT-4o-mini's context window — making a vector database unnecessary overhead at this scale.
