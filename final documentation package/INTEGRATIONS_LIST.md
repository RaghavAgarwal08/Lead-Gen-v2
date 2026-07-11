# Third-Party Integrations List

This document lists every API, integration, and communication protocol utilized by the Timidly Inc Lead Gen platform, including authentication methods, default rate limits, and cost structures.

---

## 1. OpenAI API (AI Analysis & Pitching)

*   **Role**: Generates search queries from target profiles, runs the lightweight Stage 1 pre-qualification filter, and performs 4-dimensional lead scoring and pitch copywriting.
*   **Authentication**: 
    *   Variable: `OPENAI_API_KEY`
    *   Format: `sk-proj-xxxxxxxx...` or `sk-admin-xxxxxxx...` (Requires Admin key to view cost organization programmatically).
*   **Rate Limits**:
    *   *Usage Tier 1 (Free Trial / Minimal Deposit)*: 3 Requests Per Minute (RPM), 40,000 Tokens Per Minute (TPM) for GPT-4.
    *   *GPT-4o-mini Standard limits*: 10,000 RPM, 200,000 TPM.
*   **Pricing / Costs**:
    *   Pay-as-you-go based on token usage.
    *   **GPT-4o-mini Costs**:
        *   Input Tokens: **$0.15** per 1,000,000 tokens.
        *   Output Tokens: **$0.60** per 1,000,000 tokens.
    *   *Average Cost per Qualified Lead*: ~**$0.002 to $0.005 USD**.

---

## 2. Apify Platform (Web & Contact Scraping)

*   **Role**: Discovers new target companies on Product Hunt/YC via the Google Search Scraper and scrapes LinkedIn contact profiles for lead targeting.
*   **Authentication**:
    *   Variable: `APIFY_API_TOKEN`
    *   Format: `apify_api_xxxxxxxxxxxxxxxxxxxxxxxx`
*   **Rate Limits**:
    *   *API Requests*: 100 requests per second.
    *   *Concurrency (Free Plan)*: Up to 25-30 concurrent actor container jobs.
*   **Pricing / Costs**:
    *   **Free Plan**: **$5.00** recurring monthly usage credits (covers compute units, storage, and proxy transfer).
    *   **Paid Plans**: Starter tier begins at **$49.00/month**.
    *   *Average Actor Run Cost*:
        *   `apify/google-search-scraper`: ~$0.05 to $0.15 USD per search run (depending on result count and page limits).

---

## 3. Firecrawl API (Landing Page Markdown Scraper)

*   **Role**: Crawls target landing pages and converts raw HTML into clean, code-stripped Markdown text to serve as prompt context for the LLM.
*   **Authentication**:
    *   Variable: `FIRECRAWL_API_KEY`
    *   Format: `fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
*   **Rate Limits**:
    *   *Free Plan*: 5 requests per second.
    *   *Paid Plans*: Scaled up dynamically based on plan level.
*   **Pricing / Costs**:
    *   **Free Tier**: **$0** (Allocates 500 scrape credits per month).
    *   **Hobby / Starter Tier**: **$16.00/month** (Allocates 10,000 scrape credits).
    *   *Average Cost per Lead*: **1 credit** per scraped landing page.

---

## 4. Resend API (HTTPS Email Service)

*   **Role**: Primary fail-safe email deliverer. Communicates over HTTPS port 443, bypassing outbound SMTP port blocks imposed by cloud environments like Render (Free Tier).
*   **Authentication**:
    *   Variable: `RESEND_API_KEY`
    *   Format: `re_xxxxxxxxxxxxxxxxxxxxxxxx`
*   **Rate Limits**:
    *   *Free Tier*: 2 requests per second.
    *   *Paid Tiers*: Increases dynamically.
*   **Pricing / Costs**:
    *   **Free Tier**: **$0** (Allows up to 100 emails per day, max 3,000 emails per month).
    *   **Pro Tier**: Starts at **$20.00/month** (Allows up to 50,000 emails per month).
    *   *Average Cost*: Free.

---

## 5. Gmail SMTP Server (Standard Email Fallback)

*   **Role**: Fallback email deliverer. Utilized if `RESEND_API_KEY` is not set. Runs over ports 465 (SSL) or 587 (STARTTLS).
*   **Authentication**:
    *   Variables: `SMTP_USER` (Gmail address) and `SMTP_PASSWORD` (16-character Google App Password).
*   **Rate Limits**:
    *   *Personal Gmail*: **500 emails** per 24 hours.
    *   *Google Workspace*: **2,000 emails** per 24 hours.
*   **Pricing / Costs**:
    *   **Free** ($0).

---

## Document Navigation

*   [README.md](../README.md) — Product Overview & Launch
*   [DOCUMENTATION_V1.md](DOCUMENTATION_V1.md) — User & Admin Operations Guide
*   [USAGE.md](USAGE.md) — Environment variables & CLI usage reference
*   [ARCHITECTURE.md](ARCHITECTURE.md) — Project layout & Module maps
*   [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — Technical system design details
*   [WORKFLOW.md](WORKFLOW.md) — Pipeline data processing stages
*   [OWASP_TOP_10.md](OWASP_TOP_10.md) — Security remediations & Checklist
*   [Operations-Runbook.md](Operations-Runbook.md) — Operations & Troubleshooting runbook
*   [Client-UAT-Package.md](Client-UAT-Package.md) — Client User Acceptance Testing Package
*   [INTEGRATIONS_LIST.md](INTEGRATIONS_LIST.md) — API configurations & Cost structure
*   [LEAD_QUALIFICATION_CRITERIA.md](LEAD_QUALIFICATION_CRITERIA.md) — Fit scoring framework & Criteria
