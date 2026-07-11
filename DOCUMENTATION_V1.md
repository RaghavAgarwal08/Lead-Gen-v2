# Timidly Inc — AI-Powered Lead Intelligence Platform
## Client-Facing User Guide & Admin Guide (v1.0.0)

This document provides a comprehensive overview, user guide, and administrator guide for the **Timidly Inc AI Lead Generation & Intelligence Platform**. It outlines the core system capabilities, running instructions, detailed technical workflows, environment configurations, known limitations, and active roadmap items.

---

## 1. Overview

### Purpose of the Tool
The **Timidly Inc AI-Powered Lead Intelligence Platform** is an intelligent, self-learning pipeline designed to automate the discovery, enrichment, qualification, scoring, and personalized outreach pitching of high-value B2B startup sponsors. 

The tool was custom-built for **Timidly Inc** (founded by SomitraSR) to identify companies that align with Timidly’s creator brand and audience, which reaches over **100K+ developers, software engineering builders, and startup operators** across LinkedIn, X/Twitter, Instagram, and a highly engaged weekly newsletter.

### Problem It Solves
Manual lead generation is a slow, multi-tool, and highly labor-intensive process:
1. **Scouting**: Manually monitoring Product Hunt, Y Combinator, and tech blogs for new startups.
2. **Filtering**: Evaluating whether a startup is in a relevant vertical (e.g., dev tools or LLMOps) rather than a services agency or e-commerce shop.
3. **Contact Lookup**: Hunting LinkedIn and Google for decision-maker profiles (CEOs, Founders, Partnerships Leads) and verifying contact details.
4. **Research**: Scraping landing page text and reading social media feeds to find strategic outreach angles.
5. **Pitching & Scoring**: Synthesizing the data to select the right sponsorship package and draft personalized emails.
6. **Reporting**: Compiling leads into flat CSVs, clean DOCX reports, and JSON databases.

The pipeline automates this entire lifecycle. Within minutes, a single run discovers, qualifies, enriches, and scores dozens of leads, then outputs formatted assets and dispatches them via email.

### Intended Users
*   **Sponsorship Managers & Sales Reps**: To run targeted campaigns, export ready-to-use lists for CRM import, and review copy-paste outreach angles.
*   **Marketing Directors & Executives**: To review lead trends, evaluate budget maturity profiles, and oversee outbound growth strategies.
*   **System Administrators & Developers**: To configure API keys, update qualification weights, manage memory caches, and maintain production cloud deployments.

---

## 2. Features Implemented So Far

### Current Capabilities
*   **ICP-Driven Target Discovery**: OpenAI GPT-4o-mini analyzes the existing prospect list (`extracted_prospects.md`) to understand the Ideal Customer Profile. It then generates targeted, context-aware Google Search queries targeting `site:producthunt.com/posts/` and `site:ycombinator.com/companies`.
*   **Two-Stage Qualification Pipeline**:
    *   *Stage 1: AI-Driven Pre-Filter*: Instantly evaluates names and taglines using OpenAI to filter out unqualified targets (agencies, consultancies, local retail, low-tech B2C apps) before executing expensive API crawls.
    *   *Stage 2: Fit Scoring Model*: Crawls, enriches, and rates prospects out of 10. Startups scoring below $7.0$ are automatically filtered out.
*   **Multi-Source Firmographic Enrichment**: Crawls funding stages, valuation details, country location, and employee headcount estimates.
*   **Landing Page Crawling & Scraping**: Utilizes Firecrawl API to extract raw HTML landing page text and clean it into developer-friendly Markdown, which acts as direct context for AI pitch copy generation.
*   **Decision-Maker Contact Person Lookup**: Automatically searches Google/LinkedIn to identify target decision-makers (Founders, CEOs, Heads of Marketing, Partnerships Leads) along with their names, roles, and LinkedIn URLs.
*   **Contact Info Extraction**: Crawls the company's website to scrape corporate email addresses, phone numbers, and social links.
*   **Social Scraping & Twitter Synthesis**: Discovers Twitter/X handles and scrapes recent tweets using the Apify `apidojo/tweet-scraper`. If blocked or restricted, it executes a Google Search status fallback or utilizes OpenAI to synthesize product-focused tweets.
*   **Professional Pitch Writer & Package Matcher**: Maps company offerings to specific Timidly Inc sponsorship tiers (Newsletter Ads, LinkedIn posts, Instagram reels, etc.) and drafts tailored, high-converting outreach angles.
*   **Self-Learning Memory System (`learned_leads.json`)**: Every processed lead is appended to a local database. The pipeline uses this cache to:
    1. Instantly skip duplicate leads.
    2. Feed past successes as few-shot training examples to OpenAI to dynamically improve pitch quality over time.
*   **Multi-Format Export Engine**: Automatically saves leads to:
    *   `Timidly_Prospects_Report.docx` (Calibri typography, navy blue headings, matching the company's document brand guidelines).
    *   `Timidly_Prospects_Report.csv` (Flat structure optimized for HubSpot or Salesforce imports).
    *   `Timidly_Prospects_Report.json` (Structured JSON representation of all data fields).
*   **Dual Email Relay Delivery**: Bypasses cloud outbound port blocks (like on Render Free Tier) by trying the Resend HTTP API (via HTTPS Port 443) first, then falling back to Gmail SMTP over TLS.
*   **Web Admin Dashboard**: A premium, responsive glassmorphism web interface featuring real-time log streaming, progress percentages, active lead scoring charts, API credit consumption trackers, cache clearers, and download buttons.

### Features Still Under Development (Roadmap)
*   **Direct CRM Integrations**: Direct API push pipelines to HubSpot, Salesforce, and Pipedrive to bypass CSV exports.
*   **Outreach Sequencing Automation**: Triggering outreach sequences (via email/LinkedIn) directly from the dashboard.
*   **Scraper Proxy Rotation**: Native integration of rotating residential proxies to bypass CAPTCHA hurdles.
*   **Scoring Weights Configurator**: A dashboard GUI enabling administrators to adjust scoring weights (e.g. Audience Alignment, Budget Maturity) without changing source code.
*   **Real-time Webhook Triggers**: Integration of webhooks to trigger runs automatically when new startups launch on Product Hunt or raise funding.

---

## 3. User Guide (Draft)

### Install or Access the Tool
*   **Web Interface (Live Dashboard)**: Access the cloud dashboard at [https://lead-gen-v2-if0t931gi-raghav-agarwals-projects-306aac5f.vercel.app](https://lead-gen-v2-if0t931gi-raghav-agarwals-projects-306aac5f.vercel.app).
*   **Local Setup (CLI & Server)**: If running locally, clone the git repository, run the server, and navigate to `http://localhost:8000` in your web browser.

### Configure API Keys
To run the pipeline, ensure the following keys are set in your environment (or inside the local `.env` file):
*   `APP_PASSWORD`: secure dashboard passkey (if defined, all backend API routes and frontend interface access are password-secured).
*   `OPENAI_API_KEY`: For AI query generation, pre-filtering, 4D scoring, and pitch generation.
*   `APIFY_API_TOKEN`: For Google search scraping, LinkedIn profile checks, and contact/Twitter info extraction.
*   `FIRECRAWL_API_KEY`: For crawling and parsing target landing pages.
*   `RESEND_API_KEY`: Primary API key for emailing reports.
*   `SMTP_USER` / `SMTP_PASSWORD`: Standard Gmail SMTP details (fallback for email delivery).

### Start a Lead Search
#### 1. Via the Web Dashboard
1. Open the dashboard homepage.
2. Enter the **Email Address** where the reports should be delivered.
3. Enter the **Lead Count Limit** (the number of net-new prospects you want to generate).
4. Click the **Generate Leads** button.
5. Watch the real-time log stream and progress bar updates.

#### 2. Via the Command Line Interface (CLI)
Run the script interactively:
```bash
python main.py
```
Or run it with non-interactive CLI arguments:
```bash
python main.py --limit 10 --email "your-email@gmail.com"
```

### View Qualified Leads
*   **Dashboard View**: As leads successfully pass the threshold of $\ge 7.0$, they are displayed in a clean tabular list on the dashboard. Click on any lead to open its detailed modal showing the firmographics, contact person, social feed, and the complete AI pitch.
*   **Local Cache**: You can view the list of generated leads programmatically inside the `Timidly_Prospects_Report.json` file.

### Export Results
*   **Dashboard**: Under the "Actions" panel, click **Download Word Report (DOCX)**, **Download CSV**, or **Download JSON**.
*   **Local Run**: The reports are saved in the project root folder.
*   **Email Delivery**: If an email address is specified at runtime, the generated DOCX and CSV files will be emailed to your inbox.

### Administrative Authentication & Security (Logout)
*   **Secure Dashboard Access**: If `APP_PASSWORD` is configured in your staging or production environment, loading the dashboard will prompt you with a login modal overlay.
*   **Locking the Dashboard**: Click the red **Lock Dashboard** button at the bottom of the sidebar navigation to sign out. This immediately deletes the credentials cached in the browser's local memory (`localStorage`) and locks the admin dashboard panel.

### Handling Common Errors
*   **"No target prospects found"**: This occurs if the discovered companies were all flagged as duplicates (already processed or present in the ICP list) or if the Apify/Firecrawl free credits are fully exhausted. Reset your `learned_leads.json` to start fresh, or check credits in the Dashboard.
*   **"Firecrawl failed: DNS resolution failed"**: This means the company's domain name is incorrect or currently inactive. The pipeline ignores this failure and automatically falls back to firmographic Google snippets, meaning the pitch will still generate successfully.
*   **"SMTP: Username and Password not accepted"**: Verify that Gmail 2-Step Verification is enabled and that you are using a 16-character Google App Password (not your standard Gmail password).

---

## 4. Current Workflow

The diagram below represents the current lead-generation workflow, mapping abstract conceptual steps to their underlying Python implementation:

```
                  ┌──────────────────────────────────────────────┐
                  │          [1] START RUN: CLI or Web           │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    [2] ICP SCAN: Load existing prospects     │
                  │        (Reads extracted_prospects.md)        │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       [3] QUERY GEN: OpenAI GPT-4o-mini      │
                  │   Generates 3 seed queries based on ICP profile│
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │     [4] DISCOVERY: Google search via Apify   │
                  │       Scrapes Product Hunt + Y Combinator    │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │   [5] DEDUPLICATION: Filters company names   │
                  │   Checks ICP list + memory learned_leads.json│
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │     [6] STAGE 1 PRE-QUALIFICATION FILTER     │
                  │   OpenAI discards consultancies/B2C/agencies │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │    Iterate remaining leads  │
                          └──────────────┬──────────────┘
                                         │
                                         ├─────────────────────────┐
                                         ▼                         │
                  ┌──────────────────────────────────────────────┐ │
                  │       [7] CONTACT LOOKUP (Apify)             │ │
                  │    Finds executive profile on LinkedIn       │ │
                  └──────────────────────┬───────────────────────┘ │
                                         │                         │
                                         ▼                         │
                  ┌──────────────────────────────────────────────┐ │
                  │      [8] WEB SCRAPING & CONTACT DETAILS      │ │
                  │  Crawls site with Firecrawl & Apify contact  │ │
                  └──────────────────────┬───────────────────────┘ │
                                         │                         │
                                         ▼                         │
                  ┌──────────────────────────────────────────────┐ │ (Iterate for
                  │       [9] TWITTER & FIRMOGRAPHICS            │ │ each lead)
                  │   Scrapes location, funding & recent tweets  │ │
                  └──────────────────────┬───────────────────────┘ │
                                         │                         │
                                         ▼                         │
                  ┌──────────────────────────────────────────────┐ │
                  │          [10] 4D SCORING ENGINE              │ │
                  │     Audience (40%) + Budget (30%) +          │ │
                  │     Product (20%) + Traction (10%)           │ │
                  └──────────────────────┬───────────────────────┘ │
                                         │                         │
                                         ▼                         │
                  ┌──────────────────────────────────────────────┐ │
                  │        [11] THRESHOLD CHECK (Score >= 7)     │ │
                  │  YES: Save to learned_leads.json (Few-shot)  │ │
                  │  NO: Log [DISCARDED] and skip                │◄┘
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │         [12] REPORT COMPILATION              │
                  │       Exports to DOCX, CSV, and JSON         │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │      [13] EMAIL DISPATCH (SMTP / Resend)     │
                  │      Delivers reports directly to inbox      │
                  └──────────────────────────────────────────────┘
```

---

## 5. Installation Instructions

### Prerequisites
*   **Python 3.10+** (Python 3.12 is highly recommended)
*   **pip** (Python package installer)
*   A Google / Gmail account (for standard SMTP mailer backup)
*   A Resend API account (for the primary production email relay)

### Dependencies
The pipeline relies on several core python libraries. Install them via:
```bash
pip install -r requirements.txt
```

**Key Packages Loaded:**
*   `fastapi` and `uvicorn`: Web backend server & API hosting.
*   `pydantic`: Enforces strict schemas and types.
*   `openai`: For chat completion prompts and structured JSON schema parsing.
*   `apify-client`: Scraping interface for Google search and social networks.
*   `firecrawl-py`: Target website scraping.
*   `python-docx`: Programmatic building of Word document reports.
*   `requests` and `python-dotenv`: Environment variables and API requests.

### Environment Setup
Create a `.env` file in your project root using the example template:
```bash
cp .env.example .env
```
Open `.env` and populate your credentials:
```env
# Core API Credentials
OPENAI_API_KEY="sk-proj-..."
APIFY_API_TOKEN="apify_api_..."
FIRECRAWL_API_KEY="fc-..."

# Secure Admin Dashboard Authentication
APP_PASSWORD="your-secure-app-password-here"

# Primary Email Delivery (Resend API)
RESEND_API_KEY="re_..."

# Fallback Email Delivery (Gmail SMTP)
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-brand-email@gmail.com"
SMTP_PASSWORD="your-16-char-app-password"
```

### Running Locally
To launch the FastAPI server and the dashboard dashboard interface locally:
```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
Once the server starts, navigate to `http://127.0.0.1:8000` in your web browser.

---

## 6. Configuration

### Configuration Files
1.  **`.env`**: Stores all keys, tokens, port numbers, and authentication parameters. This file is git-ignored and must not be pushed to version control.
2.  **`config.py`**: Loads values from the environment and maps the catalog of sponsorship packages.

### Adjustable Parameters

#### 1. Sponsorship Packages (`config.py`)
You can adjust, rename, or add custom pricing packages inside the `CREATOR_PACKAGES` dictionary. The AI copy generator automatically imports these keys to structure its sponsorship advice:
```python
CREATOR_PACKAGES = {
    "linkedin_post": "LinkedIn Sponsored Post ($500)",
    "newsletter_ad": "Newsletter Ad ($199)",
    "dual_impact": "Dual Impact Package (LinkedIn Post + Newsletter Ad) ($600)",
    "sponsored_reel": "Instagram Sponsored Reel ($1,200)",
    "bundle": "Sponsored Reel + X Sponsored Thread bundle ($1,500)"
}
```

#### 2. Lead Qualification Threshold (`app.py` & `main.py`)
Leads with an overall score below **`7`** are skipped and omitted from final reports:
```python
if ai_pitch.lead_score < 7:
    # Skip processing and discard lead
```
To lower or raise this threshold, modify this conditional check inside `main.py` and `app.py`.

#### 3. Lead Scoring Weights (`core/generator.py`)
The scoring algorithm computes the final grade based on these hardcoded weights:
*   **Audience Alignment**: $40\%$ weight
*   **Budget Maturity**: $30\%$ weight
*   **Product & Vertical Relevance**: $20\%$ weight
*   **Traction & Growth Signals**: $10\%$ weight

These weights are described in detail in the system prompts inside `core/generator.py` and calculated using:
```python
lead_score = round(0.4 * audience + 0.3 * budget + 0.2 * product + 0.1 * traction)
```

---

## 7. Known Limitations

### Supported Data Sources
*   Target candidates are only sourced from Product Hunt (`site:producthunt.com/posts/`) and Y Combinator (`site:ycombinator.com/companies`) index search pages. Direct scraping of raw category directory lists is not supported due to scrapers encountering rate limits and anti-bot checks.
*   Web scrape context relies on a company's main homepage landing text. Deep site crawls (scraping internal blogs, pricing, or docs folders) are disabled by default to stay within Firecrawl API limits.

### Rate Limits
*   **Apify Scrapers**: The free account ($5/month credit) supports ~50-100 full searches per month. Executing concurrent scraper calls under the free plan will throttle speeds.
*   **Firecrawl**: The Free Tier limits requests to 5 scrape calls per second and 500 total page scrapes per month.
*   **OpenAI GPT-4o-mini**: Subject to standard RPM (Requests Per Minute) limits based on your platform tier.
*   **Email Relay (Resend)**: Free accounts are capped at 100 emails sent per day and 3,000 emails per month.

### Features Not Yet Implemented
*   Editing scoring weights directly through the web UI interface.
*   Active LinkedIn connection and messaging outreach automations.
*   Persistent relational SQL database backup (currently uses a local file `learned_leads.json`).

---

## 8. P1 Risks & Mitigation Strategies

To ensure platform reliability, data integrity, and cost management, the following high-priority (P1) risks have been identified along with their corresponding architectural and operational mitigations:

| Risk Category | Risk Description | Business/Technical Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Broken Access Control & Auth Failures** | Lacking login checks on dashboard UI and backend API routes. Anyone could trigger runs, download records, clear history, or view settings. | **High Impact**: Attackers can trigger repetitive discovery scripts, exhausting credit quotas of third-party APIs (OpenAI, Apify, Firecrawl, Resend) or read personal data of targets. | **Mitigation**: Configured `APP_PASSWORD` token validation. Backend requires `X-App-Password` header on all `/api/*` requests. Frontend automatically prompts a login modal and locks dashboard if unauthenticated. |
| **Data Loss & Session Reset** | The platform stores deduplicated leads and self-learning history in a local file (`learned_leads.json`). In containerized, serverless, or ephemeral hosting environments (like Vercel or Render Free Tier), local disk storage is wiped on restarts/redeployments. | **High Impact**: History is lost, causing the pipeline to re-process and re-charge for duplicate leads, exhausting API credits. It also wipes out the few-shot learning context for the AI writer. | **Mitigation**: Transition from a local flat file to a persistent cloud database (e.g., Supabase PostgreSQL, MongoDB, or AWS DynamoDB) or attach a persistent block storage volume to the container. |
| **API Limit & Credit Exhaustion** | The pipeline synchronously consumes credits across four critical paid APIs: OpenAI, Apify, Firecrawl, and Resend. Large searches or concurrent queries can quickly hit rate/token limits or exhaust monthly free tiers. | **High Impact**: The lead generation process will crash mid-run, leading to partial reports and dashboard failures. | **Mitigation**: Implement real-time usage tracking in the admin dashboard, enforce maximum search boundaries (e.g., hard caps in UI), and implement graceful fallback logging for when API keys hit limit caps. |
| **Anti-Scraping / IP Blocking** | Scrapers (for Product Hunt, Y Combinator, and target homepages) do not use proxy rotation on free plans. Target websites or Google Search may block crawler IPs, presenting CAPTCHAs or Cloudflare challenge walls. | **Medium to High**: Scrapers return empty results, causing the contact lookup, firmographics, and pitch generation modules to fail or output blank fields. | **Mitigation**: Integrate rotating residential proxies (e.g., via Apify Proxy or Firecrawl Proxy settings), randomize User-Agent headers, and use fallback web scraping methods when a block is detected. |
| **Silent Email Delivery Failures** | Hosting providers block outbound SMTP traffic on ports 25 and 587 by default. If the Resend API (HTTPS port 443) fails or credentials expire, fallback SMTP dispatch will also fail on restricted clouds. | **Medium**: The user will not receive reports via email. Since it happens at the end of the script, it could be a silent failure where the run looks successful but reports never arrive. | **Mitigation**: Implement robust retry logic, treat the Resend HTTPS API as the primary channel, and display an explicit delivery warning/log status on the Web Admin Dashboard. |
| **AI Hallucinations & Wrong Scoring** | The 4-Dimensional Scoring Model and customized pitch generation rely entirely on OpenAI processing raw crawled HTML. AI may misinterpret funding stages, confuse competitor listings, or construct inaccurate emails. | **Medium**: Unqualified leads might pass the threshold (False Positives) or premium prospects could be incorrectly discarded (False Negatives). | **Mitigation**: Enforce a "human-in-the-loop" review process inside the dashboard before outreach. Restrict GPT outputs using strict JSON Schema parsing (Pydantic) and refine prompts with precise scoring guidelines. |

---

## 9. Changelog

### v1.0.0
*   **Platform Scaffold**: Decoupled FastAPI backend and Vanilla JS dynamic dashboard UI.
*   **AI Stage-1 Pre-Filter**: Added lightweight query filters to ignore non-tech applications.
*   **Multi-Dimensional Scoring**: Implemented 4D lead scoring calculation engine (Audience, Budget, Relevance, Traction).
*   **Twitter/X Scraping Integration**: Added Google Search fallback and OpenAI synthetic generation for Twitter feeds.
*   **Resend HTTP Integration**: Configured secure HTTPS email relay to bypass SMTP cloud port blockades.
*   **Self-Learning Loop**: Integrated dynamic memory loading using the last 5 leads as few-shot context examples.
*   **DOCX Brand Formatting**: Re-formatted Word doc output to match Calibri styles and navy color guidelines.
