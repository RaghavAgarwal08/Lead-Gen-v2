# Pipeline Workflow

> This document provides a comprehensive, end-to-end description of the Timidly Inc AI Lead Generation Pipeline — including every stage, the external tools involved, data transformations, and the self-learning mechanism.

---

## Overview

The pipeline transforms an existing Ideal Customer Profile (ICP) document into a stream of enriched, AI-scored, net-new startup leads — complete with decision-maker contacts, tailored pitches, and sponsorship recommendations. 

In **Lead Gen V2**, this workflow can be operated in two modes:
1. **Command Line Interface (CLI)**: Run `python main.py` directly to execute the pipeline locally.
2. **Web Admin Dashboard**: Start the FastAPI server (`app.py`), unlock the interface using the `APP_PASSWORD` access passkey, and run and monitor the discovery process in real-time. All backend endpoints are secured, and dynamic HTML renders are sanitized to prevent script injection.

```
 ICP Prospect List (49 companies)
         │
         ▼
 ┌───────────────────────┐
 │  1. PROFILE ANALYSIS  │  OpenAI GPT-4o-mini analyzes the ICP
 │     (discovery.py)     │  and generates 3 targeted search queries
 └───────────┬───────────┘
             ▼
 ┌───────────────────────┐
 │  2. TARGET DISCOVERY  │  Apify Google Search Scraper searches
 │     (discovery.py)     │  Product Hunt + Y Combinator
 └───────────┬───────────┘
             ▼
 ┌───────────────────────┐
 │  3. DEDUPLICATION     │  Filters out companies already in the
 │     (discovery.py)     │  ICP list or learned_leads.json
 └───────────┬───────────┘
             ▼
     ┌───────────────┐
     │ For each lead │──────────────────────────────────────┐
     └───────┬───────┘                                      │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  4. CONTACT LOOKUP    │  Apify → Google → LinkedIn       │
 │     (contacts.py)      │  Finds Founder/CEO/Marketing     │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  5. WEBSITE SCRAPING  │  Firecrawl → Markdown            │
 │     (enricher.py)      │  Extracts landing page content   │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  6. CONTACT DETAILS   │  Apify contact-info-scraper      │
 │     (contacts.py)      │  Extracts email, phone, socials  │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  7. COUNTRY LOOKUP    │  Apify → Google Search            │
 │     (enricher.py)      │  Finds headquarters location     │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  8. FIRMOGRAPHICS     │  Apify → Google → Crunchbase     │
 │     (enricher.py)      │  Funding stage, valuation, size  │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │  9. AI PITCH GEN      │  OpenAI GPT-4o-mini              │
 │     (generator.py)     │  Structured output + few-shot    │
 │                        │  from learned_leads.json         │
 └───────────┬───────────┘                                  │
             ▼                                              │
 ┌───────────────────────┐                                  │
 │ 10. SAVE TO MEMORY    │  Append to learned_leads.json    │
 │     (main.py)          │  for future training             │
 └───────────┬───────────┘                                  │
             │◄─────────────────────────────────────────────┘
             ▼
 ┌───────────────────────┐
 │ 11. EXPORT REPORTS    │  DOCX + CSV + JSON
 │     (exporter.py)      │  Saved to local filesystem
 └───────────┬───────────┘
             ▼
 ┌───────────────────────┐
 │ 12. EMAIL DELIVERY    │  Gmail SMTP with TLS
 │     (mailer.py)        │  DOCX + CSV as attachments
 └───────────────────────┘
```

---

## Stage-by-Stage Breakdown

### Stage 1 — ICP Profile Analysis

**Module:** `core/discovery.py` → `generate_search_queries_from_profile()`  
**Tool:** OpenAI GPT-4o-mini  
**Input:** First 15 companies from `extracted_prospects.md`  
**Output:** 3 search query strings (JSON response format)

The pipeline begins by reading the existing prospect list — a curated document of 49 target companies with their taglines, funding stages, and pitch angles. It feeds the first 15 company names and taglines to GPT-4o-mini with a system prompt instructing it to act as a "sales intelligence analyst" and produce 3 distinct search queries that would surface similar companies on Product Hunt and Y Combinator.

**Example output:**
```json
{"queries": ["AI startup tools for GTM teams", "generative AI platforms for developers", "AI-powered automation solutions for SaaS startups"]}
```

### Stage 2 — Target Discovery

**Module:** `core/discovery.py` → `discover_companies()`  
**Tool:** Apify Google Search Scraper (`apify/google-search-scraper`)  
**Input:** 6 combined queries (3 queries × 2 sites: `site:producthunt.com/posts/` and `site:ycombinator.com/companies`)  
**Output:** List of `{company_name, tagline, website, search_url}` dictionaries

The generated queries are prefixed with `site:` operators and sent as a batch to the Apify Google Search Scraper. The scraper returns organic search results containing company titles, snippets, and URLs. The module parses these results to extract clean company names — using URL slug parsing as a fallback when titles contain long descriptive phrases.

### Stage 3 — Deduplication

**Module:** `core/discovery.py` → `discover_companies()`  
**Data Sources:** `extracted_prospects.md` (ICP list) + `learned_leads.json` (memory)

Before any enrichment API calls are made, every discovered company is checked against two exclusion lists:
1. **ICP List** — The 49 companies in the original prospect document
2. **Learned Leads** — All companies from previous pipeline runs

This ensures every run surfaces genuinely new targets and prevents wasted API credits on duplicates.

### Stage 4 — Contact Person Lookup

**Module:** `core/contacts.py` → `find_contact_person()`  
**Tool:** Apify Google Search Scraper  
**Query Pattern:** `site:linkedin.com/in/ "{company_name}" (Founder OR CEO OR "Head of Marketing" OR "Partnerships")`

A Google search scoped to LinkedIn profiles identifies the most relevant decision-maker. The module parses the top result to extract the person's name, job title, and LinkedIn profile URL.

### Stage 5 — Website Scraping

**Module:** `core/enricher.py` → `scrape_website_content()`  
**Tool:** Firecrawl API  
**Output:** Markdown representation of the company's landing page

Firecrawl renders the target website and converts it to clean markdown. This content is passed to the AI generator as context, enabling it to reference specific product features, messaging, and positioning in the tailored pitch.

### Stage 6 — Contact Details Extraction

**Module:** `core/contacts.py` → `extract_contact_info()`  
**Tool:** Apify `vdrmota/contact-info-scraper`  
**Output:** `{email, phone, twitter, facebook}` from the company's website

The contact info scraper crawls the target website (following internal links to /contact, /about, /team pages) and extracts email addresses, phone numbers, and social media handles using pattern matching.

### Stage 7 — Country / Headquarters Lookup

**Module:** `core/enricher.py` → `fetch_country()`  
**Tool:** Apify Google Search Scraper  
**Query Pattern:** `"{company_name}" headquarters country city location`

A dedicated Google search retrieves snippets mentioning the company's location. These snippets are passed to the AI generator, which synthesizes them into a clean country name.

### Stage 8 — Firmographic Enrichment

**Module:** `core/enricher.py` → `fetch_firmographics()`  
**Tool:** Apify Google Search Scraper  
**Query Pattern:** `"{company_name}" funding total raised valuation crunchbase`

Funding data is extracted from Google snippets referencing Crunchbase, TechCrunch, and press releases. The module uses regex heuristics to parse dollar amounts (e.g., `$2.3B`, `$130K`) and employee counts from the results.

### Stage 9 — AI Pitch Generation

**Module:** `core/generator.py` → `generate_personalized_pitch()`  
**Tool:** OpenAI GPT-4o-mini with structured outputs  
**Output:** Pydantic `PitchAnalysis` object

This is the core intelligence layer. The system prompt describes Timidly Inc's audience (100K+ developers, startup operators) and lists the available sponsorship packages. The user prompt includes all enriched data: company name, tagline, funding, contact details, and website markdown.

**Self-Learning Mechanism:** Before generating, the module loads the last 5 entries from `learned_leads.json` and includes them in the system prompt as few-shot examples. This provides the model with concrete examples of successful pitch formats, outreach angles, and package recommendations — causing output quality to improve with each successive run.

**Structured Output Fields:**
| Field | Type | Description |
|-------|------|-------------|
| `why_pitch_fits` | `str` | Strategic reasoning for why this company is a good lead |
| `recommended_package` | `str` | Best sponsorship package from the catalog |
| `tailored_outreach_angle` | `str` | Personalized opening message for the decision-maker |
| `country_based_in` | `str` | Inferred headquarters country |
| `background_of_founders` | `str` | Synthesized founder/contact background |
| `contact_name` | `str` | Name of the key contact person or founder |
| `contact_title` | `str` | Job title of the contact person |
| `contact_linkedin` | `str` | LinkedIn profile URL of the contact |
| `contact_email` | `str` | Email address of the contact |
| `contact_phone` | `str` | Contact phone number for the company/founder |
| `funding` | `str` | Funding details and raised stage |
| `twitter_handle` | `str` | Company's or founder's Twitter/X username |

### Stage 10 — Memory Storage & Backfill

**Module:** `main.py` → `save_lead_to_memory()` & backfill logic  
**Storage:** `learned_leads.json`

Every successfully processed qualified lead (score $\ge 7$) is immediately appended to the local JSON database and final report. If the company already exists, it is updated.

If the requested lead limit has not been reached after discovery runs, the pipeline will sort the accumulated backup list of unqualified candidates (score $< 7$) by lead score descending and backfill the remaining slots to guarantee the exact target lead count is met. Backfilled leads are also stored in memory and exported.

The memory file serves three purposes:
1. **Few-shot training data** for the AI generator (Stage 9)
2. **Deduplication index** for future discovery runs (Stage 3)
3. **Instant cache** — if a learned lead is requested again, it is served directly from memory without making any API calls

### Stage 11 — Report Export

**Module:** `core/exporter.py`  
**Formats:** DOCX (Word), CSV, JSON

The DOCX report is formatted to match the style of the original prospect list: Calibri typography, navy blue headings, bold gray field labels, and italic taglines. Every lead occupies a full section with all 14 fields. The CSV is structured for direct CRM import. The JSON preserves the full data model for programmatic use.

### Stage 12 — Email Delivery

**Module:** `utils/mailer.py` → `send_leads_report()`  
**Tool:** Gmail SMTP with STARTTLS  
**Attachments:** DOCX + CSV

The DOCX and CSV files are attached to a plain-text email summarizing the number of leads generated and sent to the recipient address provided at runtime.

---

## External Services & API Usage

| Service | Actor / Endpoint | Purpose | Approx. Cost per Lead |
|---------|------------------|---------|----------------------|
| **Apify** | `apify/google-search-scraper` | Discovery, contact lookup, firmographics, country | ~$0.01–0.03 |
| **Apify** | `vdrmota/contact-info-scraper` | Email/phone extraction from websites | ~$0.01 |
| **Firecrawl** | `/v1/scrape` | Website → Markdown conversion | 1 credit per page |
| **OpenAI** | `gpt-4o-mini` | ICP query generation + pitch generation | ~$0.001–0.005 |
| **Gmail SMTP** | `smtp.gmail.com:587` | Email delivery | Free |

**Estimated cost per lead:** $0.03–0.08 (well within Apify's free $5/month tier for small batches).

---

## Self-Learning Feedback Loop

```
Run 1: Generates leads A, B, C → saves to learned_leads.json
                                              │
Run 2: Loads A, B, C as few-shot examples ◄───┘
        Generates leads D, E, F (higher quality pitches)
        Saves D, E, F → learned_leads.json now has A–F
                                              │
Run 3: Loads B, C, D, E, F as examples   ◄───┘
        Generates leads G, H, I (even higher quality)
        ...and so on
```

The model progressively learns:
- The **tone** and **length** of successful outreach angles
- Which **sponsorship packages** tend to be recommended for which company profiles
- How to frame **"why this company is a lead"** with concrete, specific reasoning
- The level of **founder background detail** expected in the output

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
