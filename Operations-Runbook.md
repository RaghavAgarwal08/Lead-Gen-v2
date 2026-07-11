# Operations Runbook

This document is the operational guide for deploying, monitoring, maintaining, and recovering the Timidly Inc Lead Intelligence Platform in production. It is designed to enable an engineer to manage the system independently.

---

## 1. Purpose
This runbook defines the operational practices required to maintain and secure the Lead Intelligence Platform. It covers server configuration, external API interfaces, deployment on **Render**, log inspection, troubleshooting, incident recovery, and best practices. It applies specifically to the FastAPI web server (`app.py`), the background pipeline threads, and the admin dashboard client.

---

## 2. System Overview
The platform consists of:
*   **Web Server Backend**: A Python FastAPI service (`app.py`) exposing REST endpoints.
*   **Background Worker Threads**: Orchestrated by a singleton `PipelineManager` inside the web server process to run discovery, enrichment, and scoring.
*   **Frontend Dashboard**: A responsive static HTML/CSS/JS client served by FastAPI from the `/static` folder.
*   **Local Storage**: A flat JSON file cache (`learned_leads.json`) which tracks historical leads to prevent duplicate credit consumption and act as few-shot training.
*   **External API Integrations**:
    *   *OpenAI API* (GPT-4o-mini): Structured output parser for scoring and pitch generation.
    *   *Apify Platform*: Scrapes Product Hunt/YC search results and extracts target LinkedIn executive profiles.
    *   *Firecrawl API*: Web crawler that strips HTML and extracts landing pages to Markdown context.
    *   *Resend / Gmail SMTP*: Email delivery systems for reports dispatch.

---

## 3. Infrastructure
The production service runs on the **Render** cloud platform:
*   **Runtime Environment**: Python 3.12 Web Service.
*   **Continuous Deployment**: Auto-deployments trigger automatically when changes are pushed to the GitHub repository's `main` branch.
*   **Domain & SSL**: Hosted at a Render sub-domain or custom domain with automated Let's Encrypt TLS/SSL certificates managed by Render.
*   **Ephemeral Disk**: Render web services utilize container instances with ephemeral storage. File updates (including `learned_leads.json`) are reset during redeployments or container restarts unless a Persistent Volume is mounted.
*   **Secrets Manager**: Configurations are securely saved under Render's **Environment Variables** dashboard panel.

---

## 4. Environment Variables
To operate the platform, set the following parameters under Render's **Environment** tab:

| Variable Name | Required | Purpose / Role | Example Value | Backup Location |
| :--- | :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | **Yes** | OpenAI API authorization token. | `sk-proj-...` | Admin Vault |
| `APIFY_API_TOKEN` | **Yes** | Apify API token for running actors. | `apify_api_...` | Admin Vault |
| `FIRECRAWL_API_KEY` | **Yes** | Firecrawl landing page scraping key. | `fc-...` | Admin Vault |
| `APP_PASSWORD` | **Yes** | Dashboard security access password. | `my_secure_pass` | Secure Config |
| `RESEND_API_KEY` | No (Rec) | Resend HTTPS email API credential. | `re_...` | Admin Vault |
| `SMTP_HOST` | No | SMTP delivery host server. | `smtp.gmail.com` | Mail Config |
| `SMTP_PORT` | No | Port for STARTTLS/SSL email. | `587` | Mail Config |
| `SMTP_USER` | No | Gmail SMTP account name. | `auth@gmail.com` | Mail Config |
| `SMTP_PASSWORD` | No | Google App Password (16 chars). | `abcdedfghijkl` | Mail Config |

*Consequence of Missing Keys*:
*   Missing API keys will cause background pipelines to crash.
*   Missing `APP_PASSWORD` will open the admin dashboard to the public (development mode).
*   Missing email settings will skip automatic inbox dispatch.

---

## 5. Deployment Procedure
The service uses automated Git-integrated build triggers.

### Prerequisites
*   Passed local code quality checks.
*   Verified configuration changes in the environment parameters vault.

### Build & Deploy Instructions
1.  Commit and push updates to the GitHub repository:
    ```bash
    git add .
    git commit -m "feat: description of update"
    git push origin main
    ```
2.  Render will detect the `main` push and initialize the build container.
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `python -m uvicorn app:app --host 0.0.0.0 --port $PORT`
3.  **Verification (Smoke Tests)**:
    *   Access the live domain URL.
    *   Confirm the "Dashboard Locked" auth screen appears if `APP_PASSWORD` is set.
    *   Unlock the dashboard, confirm the green "Pipeline Idle" health indicator lights up, and check the logs tab.

---

## 6. Rollback Procedure
If a production deploy introduces syntax issues or configuration errors:
1.  **Revert via Dashboard**:
    *   Navigate to the **Render Dashboard → Web Service → Deployments**.
    *   Find the previous active deployment commit list.
    *   Click **Rollback** on the last stable container image.
2.  **Revert via Git** (if code fixes are required):
    *   Revert the commit locally:
        ```bash
        git revert HEAD
        git push origin main
        ```
    *   Render will re-build and replace the failing release.
3.  **Validate Rollback**:
    *   Check Render build logs to confirm uvicorn binds to `$PORT` successfully.
    *   Verify API routes load without returning `502 Bad Gateway` responses.

---

## 7. Startup Procedure
To spin up a new environment from scratch:

### Local Development environment
1.  Clone the repository and install requirements:
    ```bash
    git clone https://github.com/RaghavAgarwal08/Lead-Gen-v2.git
    cd Lead-Gen-v2
    pip install -r requirements.txt
    ```
2.  Configure `.env` using `.env.example`.
3.  Start the web dashboard:
    ```bash
    python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
    ```
4.  Open `http://127.0.0.1:8000` in your web browser.

### Production Environment (Render)
1.  Link your repository in your Render panel as a **Web Service**.
2.  Select environment `Python 3` and add the variables listed in Section 4.
3.  Deploy. Render will automatically expose the app via secure HTTPS port redirection.

---

## 8. Shutdown Procedure
*   **Local Shutdown**: Press `Ctrl+C` in the running terminal.
*   **Render Maintenance / Shutdown**:
    1.  Check the dashboard to ensure the pipeline status is "Idle". Stopping during a running process will abort the batch.
    2.  If scaling down, click **Suspend** in the Render service settings panel.
    3.  To spin up again, click **Resume**.

---

## 9. Monitoring
Operators should track the following indicators:

*   **Server Health**: Check the Render Dashboard metric pane for CPU (> 80% requires scaling) and memory usage (> 512MB free tier cap will trigger OOM container restarts).
*   **HTTP Response Metrics**: Monitor server logs for excessive `500 Internal Server Error` messages.
*   **API Credit Usage**:
    *   Monitor OpenAI usage dashboard: [platform.openai.com/usage](https://platform.openai.com/usage)
    *   Monitor Apify consumption settings: [console.apify.com/billing](https://console.apify.com/billing)
*   **Failure Notifications**: Look at stdout logs for `[ERROR]` or `[WARNING]` streams from Firecrawl or SMTP sockets.

---

## 10. Logging
Logs are printed directly to the standard output streams (stdout/stderr) and captured by Render's centralized logs tab.

*   **Uvicorn HTTP request logs**:
    ```
    INFO:     127.0.0.1:56836 - "GET /api/status HTTP/1.1" 200 OK
    ```
*   **Pipeline background thread logs**:
    ```
    [2026-07-12 01:23:45] [INFO] Discovering companies for query: site:producthunt.com/posts/ AI startup tools...
    [2026-07-12 01:24:12] [WARNING] Firecrawl failed: DNS resolution failed on domain. Skipping.
    ```
*   **Tracebacks**: Python exceptions print complete error traces. Search for `Traceback (most recent call last):` inside the Render logs tab.

---

## 11. Scheduled Jobs
This platform does not contain cron jobs or schedulers. Pipeline executions are strictly **on-demand**:
*   Triggered via the Web Admin Dashboard button (requests are received at `POST /api/generate`).
*   Triggered manually via CLI arguments using `python main.py`.

---

## 12. External Services

| Service | Protocol / API | Purpose | Timeout (sec) | Retry Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **OpenAI** | HTTP POST `/v1/chat/completions` | Structured scoring models. | 60 | Exponential backoff (3 attempts) |
| **Apify** | HTTP Client SDK / Runs API | Google search & contact scraping. | 300 | Automatic client timeouts |
| **Firecrawl** | HTTP POST `/v1/scrape` | Website Markdown crawling. | 90 | Skipped on failure (falls back to Google) |
| **Resend** | HTTP POST `/v1/emails` | Primary email sender. | 30 | Immediate failover to local SMTP |
| **SMTP** | SMTP over TLS (587/465) | Fallback email dispatch. | 30 | Skipped on authentication failure |

---

## 13. Backup Strategy
*   **What needs backup**: The database memory cache `learned_leads.json`.
*   **Render Ephemeral Caveat**: Because Render container disks are wiped on deployment builds, the database state resets unless a persistent volume is mounted.
*   **Backup Method**:
    *   *Manual*: Open the Admin Dashboard, navigate to reports, and click **Download JSON** to save a local backup copy of the leads.
    *   *Automated / Recommended*: Mount a Render Persistent Volume to the path `/app/learned_leads.json` inside your Render service parameters to persist database updates across builds.

---

## 14. Incident Response

### Incident: Scrapers Blocked (Empty Results)
*   **Symptom**: Pipeline logs show `[INFO] Discovery found 0 target prospects.`
*   **Diagnosis**: Apify is encountering CAPTCHA blocks or IP bans.
*   **Resolution**: Log in to Apify console, configure residential proxy settings in the Google Search Scraper setup, or update the mock query prompts.

### Incident: API Quota Exceeded (429 Rate Limit)
*   **Symptom**: Logs show `Error 429: OpenAI Rate Limit Exceeded` or `Apify insufficient credits`.
*   **Diagnosis**: API credit tier limit has been hit.
*   **Resolution**: Check billing status on target platforms and deposit credits.

### Incident: Authentication Failure (401 Lock Loop)
*   **Symptom**: Entering password returns `401 Unauthorized` in the console console and pops up the modal again.
*   **Diagnosis**: Env settings mismatch.
*   **Resolution**: Check the value of `APP_PASSWORD` in the Render environment settings. Click **Lock Dashboard** in the client to clear localStorage buffers before retrying.

---

## 15. Troubleshooting Guide

| Problem | Possible Cause | Diagnosis | Fix | Verification |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard returns 502 Bad Gateway** | FastAPI crashed on start. | Inspect Render logs for Python compilation errors. | Fix syntax or import errors and push fix. | Page opens successfully. |
| **Pipeline status stuck in "Processing"** | Thread crashed without clean state reset. | Refresh page, check logs for unhandled errors. | Click **Restart Web Service** on Render console. | Status returns to "Pipeline Idle". |
| **Email reports not delivered** | SMTP auth failure or Resend key invalid. | Search logs for `SMTPAuthenticationError` or `Resend API Error`. | Re-verify App Passwords or Resend key configurations. | Trigger a report download manually to check structure. |
| **"No leads processed" warning** | All found companies filtered as duplicates. | Inspect log details for duplicate skips. | Clean out duplicates in `learned_leads.json` if needed. | Fresh run processes new targets. |

---

## 16. Maintenance
*   **Dependency Updates**: Run `pip list --outdated` quarterly. Update `requirements.txt` to apply security updates for `fastapi` and `uvicorn`.
*   **Key Rotation**: Rotate Resend, Apify, and OpenAI secret keys every 180 days.
*   **History Cleanup**: If the memory database `learned_leads.json` grows beyond 5MB (which slows down GPT-4o-mini pre-prompt context loading), archive old leads and prune the JSON file structure.

---

## 17. Security Operations
*   **Credential Handling**: Never store credentials inside code. Always load parameters using `config.py` from Render environment variables.
*   **Dashboard Security Checks**: Verify that `APP_PASSWORD` is set to a complex string.
*   **XSS Protection Reviews**: Confirm that all new dashboard DOM elements are rendered using the `escapeHtml()` function in `static/app.js` to prevent HTML/Javascript injection.

---

## 18. Recovery Procedures
### Full System Reconstruction
If the hosting container fails completely:
1.  Provision a new Python Web Service on Render.
2.  Clone the repository from GitHub.
3.  Copy credentials from your secure vault to the Render Environment Variables tab.
4.  Re-deploy the container.
5.  If a backup is available, write the backed up `learned_leads.json` cache database into the persistent storage volume.

---

## 19. Operational Checklists

### Daily Check
*   [ ] Open the admin panel and confirm green health status.
*   [ ] Check Render console metrics for memory usage.

### Weekly Check
*   [ ] Log in to the dashboard and download a backup `JSON` report to save the current state of `learned_leads.json`.

### Monthly Check
*   [ ] Audit billing limits and remaining credit balances on Apify, Firecrawl, and OpenAI.

### Release Day Checklist
*   [ ] Run Python compilation checks locally.
*   [ ] Confirm all changes are pushed and successfully deployed.
*   [ ] Perform a manual smoke test login validation.

---

## 20. Escalation
If issues cannot be resolved:
1.  **Gather Diagnostics**:
    *   Export the last 100 lines of Render service logs.
    *   Take screenshot of any console error messages in browser Developer Tools.
2.  **Contact Support Contacts**:
    *   *Primary Systems Operator*: SomitraSR / Timidly Lead
    *   *External Integrations Lead*: Platform Engineer

---

## 21. Operational Best Practices
*   **Never Modify Production Storage directly**: Avoid manually editing raw JSON cache files inside Render instances.
*   **Observe Lead Limits**: Limit bulk generation queries on the web dashboard to max 20 leads per run to prevent API timeouts.
*   **Enforce HTTPS**: Always configure SSL/TLS encryption for production services.

---

## Document Navigation

*   [README.md](README.md) — Product Overview & Launch
*   [DOCUMENTATION_V1.md](DOCUMENTATION_V1.md) — User & Admin Operations Guide
*   [USAGE.md](USAGE.md) — Environment variables & CLI usage reference
*   [ARCHITECTURE.md](ARCHITECTURE.md) — Project layout & Module maps
*   [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) — Technical system design details
*   [WORKFLOW.md](WORKFLOW.md) — Pipeline data processing stages
*   [OWASP_TOP_10.md](OWASP_TOP_10.md) — Security remediations & Checklist
*   [Operations-Runbook.md](Operations-Runbook.md) — Operations & Troubleshooting runbook
*   [INTEGRATIONS_LIST.md](INTEGRATIONS_LIST.md) — API configurations & Cost structure
*   [LEAD_QUALIFICATION_CRITERIA.md](LEAD_QUALIFICATION_CRITERIA.md) — Fit scoring framework & Criteria
