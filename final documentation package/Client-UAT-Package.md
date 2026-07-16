# Client User Acceptance Testing (UAT) Package

Welcome to the User Acceptance Testing (UAT) Package for the Timidly Inc Lead Intelligence Platform. This guide is designed to walk you, the client, through testing and verifying that the delivered software works exactly as requested and satisfies your business requirements before final project sign-off.

---

## 1. Purpose
User Acceptance Testing (UAT) is the final phase of software validation. As the business owner, you will run the application in a real-world scenario to confirm it performs all functions (discovering target leads, enrichment, AI-based scoring, and document exports) correctly. Successful completion of this testing packet serves as the formal approval to conclude the project and mark it as delivered.

---

## 2. Scope of Testing
The testing process covers the following areas of the application:
*   **Access Control**: Gated login modal screen protecting administrative controls.
*   **Discovery Interface**: Input parameter settings (target lead limit and email address) and execution controls.
*   **Activity Console**: Real-time console logs displaying search query results, API connections, and scoring logs.
*   **Prospect Directory Grid**: Qualified lead lists, company information cards, and status tags.
*   **Lead Inspector Drawer**: Detailed lead profiles, decision-maker contacts, funding stages, and customized AI pitches.
*   **Exports & Delivery**: Standard file downloads (CSV, DOCX, JSON) and automated email attachment delivery.

*Intentionally Excluded*:
*   Testing on mobile phone screens (the dashboard is designed for desktop monitors and tablets).
*   Testing performance limits above 50 leads per run on free billing plans.

---

## 3. Testing Instructions
To execute these test cases:
*   **Time Commitment**: Approximately 15–20 minutes.
*   **Required Browser**: Google Chrome or Mozilla Firefox (latest versions).
*   **Required Device**: Desktop computer, laptop, or tablet.
*   **Prerequisites**: Active internet connection and access to the web dashboard hosted on Render at [https://lead-gen-v2.onrender.com/](https://lead-gen-v2.onrender.com/) (or a local server running at `http://127.0.0.1:8000`).
*   **Required Credentials**: The platform access password (e.g. `123456` or your configured password).

---

## 4. Acceptance Criteria
The system will be deemed accepted for production sign-off when:
1.  Access to all API endpoints and dashboard views is blocked unless the correct password is entered.
2.  The pipeline successfully scrapes targets from Product Hunt or Y Combinator and applies two-stage AI filters.
3.  The pipeline attempts to gather high-scoring qualified prospects (>= 7.0 score). If they are insufficient to meet the target count, the best backup candidates (below 7.0) are backfilled to meet the exact lead limit requested, and are displayed in the directory grid.
4.  All lead details render safely without executing script tags (sanitized against web injections).
5.  Report downloads (DOCX, CSV, JSON) export correctly with formatted data tables.

---

## 5. Feature Validation Checklist

### Feature 1: Platform Authentication Gate (Dashboard Lock)
*   **Purpose**: Protects the dashboard and API routes from unauthorized public access.
*   **Preconditions**: `APP_PASSWORD` is configured in the environment settings.
*   **Test Procedure**:
    1. Open your browser and navigate to `http://127.0.0.1:8000` (or your Render URL).
    2. Confirm that a blur-background login modal overlay blocks the dashboard.
    3. Enter an incorrect password (e.g., `invalid123`) and click **Unlock Platform**.
    4. Observe the warning response, confirm the dashboard remains locked, and the modal stays active.
    5. Enter the correct password (e.g., `123456`) and click **Unlock Platform**.
*   **Expected Result**: The dashboard unlocks immediately, displaying the lead lists and controls.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Comments / Client Feedback*:
\
\
\

---

### Feature 2: Real-Time Execution Console & Progress Logs
*   **Purpose**: Displays the live progress of the search pipeline.
*   **Preconditions**: Successfully unlocked the dashboard.
*   **Test Procedure**:
    1. Enter a valid email address and set the lead count limit to `3`.
    2. Click **Generate Leads**.
    3. Observe the loading indicators and watch the scrolling progress console window.
*   **Expected Result**: A scrolling stream of timestamped logs appears, showing queries, scraping actions, and scoring ratings.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Comments / Client Feedback*:
\
\
\

---

### Feature 3: Prospect Information Inspector
*   **Purpose**: Opens a side panel to display detailed company metrics, contacts, and custom pitches.
*   **Preconditions**: Leads list contains at least one company card.
*   **Test Procedure**:
    1. Locate a company name card in the directory list.
    2. Click on the company card.
    3. Verify that the side inspector drawer slides open displaying contacts, LinkedIn URL, country, and pitch.
    4. Click the **Back to Directory** button.
*   **Expected Result**: Details panel opens with structured information, and closes cleanly returning you to the main directory.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Comments / Client Feedback*:
\
\
\

---

### Feature 4: Multi-Format Exporter
*   **Purpose**: Exports qualified leads to CSV, DOCX, or JSON formats.
*   **Preconditions**: At least one lead exists in the directory.
*   **Test Procedure**:
    1. Locate the **Reports & Downloads** section in the sidebar.
    2. Click **Download Word Report (DOCX)**. Verify the file downloads to your computer.
    3. Click **Download CSV**. Verify the file downloads.
    4. Open the downloaded files and check their table structures.
*   **Expected Result**: Files download instantly and open cleanly in MS Word/Excel showing consistent prospect profiles.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Comments / Client Feedback*:
\
\
\

---

### Feature 5: Credentials & Settings Configuration Form
*   **Purpose**: Allows secure updating of environment credentials (API keys, email logins) directly from the browser settings dashboard.
*   **Preconditions**: Successfully unlocked the dashboard.
*   **Test Procedure**:
    1. Click on the **API Credentials** menu item in the sidebar.
    2. Confirm that the form fields load showing masked placeholders of your active keys (e.g. `sk-proj-...` or `fc-...`).
    3. Enter a new key (e.g. your `RESEND_API_KEY`) in the Resend API Key field.
    4. Click **Save Credentials**.
    5. Verify the confirmation alert: "Credentials updated successfully!"
*   **Expected Result**: Values are updated in memory immediately and written to your local `.env` file.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Comments / Client Feedback*:
\
\
\

---

## 6. End-to-End Business Workflow Validation

### Workflow 1: Standard Discovery & Scoring Workflow
*   **Objective**: Run a complete pipeline search to find, enrich, score, and deliver qualified leads.
*   **Steps**:
    1. Log in to the dashboard.
    2. Enter your email address in the configuration field.
    3. Type `5` in the "Number of Leads to Generate" input field and click **Produce Leads**.
    4. Verify that a confirmation modal displays the count of 5 and the entered email address.
    5. Click **OK** on the confirmation dialog.
    6. Wait for the logs to declare: `[INFO] Pipeline Completed. Reports sent.`
    7. Check your email inbox for a message from the platform with the DOCX and CSV attachments.
*   **Expected Outcome**: The pipeline runs to completion, displays qualified leads in the grid, and delivers the report files as email attachments.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Notes*:
\
\
\

---

### Workflow 2: Administrative Security Locking & Re-entry
*   **Objective**: Verify manual session locking and token expiration protection.
*   **Steps**:
    1. On the dashboard sidebar, click the red **Lock Dashboard** button.
    2. Confirm the prompt: "Are you sure you want to lock the dashboard?"
    3. Verify that you are immediately redirected back to the password modal and the dashboard is hidden.
    4. Attempt to access `http://127.0.0.1:8000/api/leads` directly in another browser tab.
*   **Expected Outcome**: The UI locks immediately, and raw API endpoints reject direct connections with a `401 Unauthorized` message.

| Result | Checkbox |
| :--- | :--- |
| **Pass** | ☐ |
| **Fail** | ☐ |
| **N/A** | ☐ |

*Notes*:
\
\
\

---

## 7. Integration Validation
The application interacts directly with external APIs. Verify that each integration responds correctly:

*   **OpenAI GPT-4o-mini API**:
    *   *Purpose*: Generating search queries, pre-qualification filtering, and fit-scoring.
    *   *Validation Step*: Observe the logs during a lead search. Check if queries are generated (e.g. `[INFO] Generated queries...`) and scores are computed.
    *   *Expected Result*: Logs confirm AI scoring (e.g. `Score: 8.2/10`) and populate structured pitches.
*   **Apify Scrapers**:
    *   *Purpose*: Scrapes Product Hunt, Y Combinator, LinkedIn, and target homepages.
    *   *Validation Step*: Verify that the console logs trace search progress: `[INFO] Scraping Google Search for Product Hunt posts...`
    *   *Expected Result*: Target companies and contact links are successfully extracted.
*   **Firecrawl Crawler**:
    *   *Purpose*: Scrapes target homepages into Markdown.
    *   *Validation Step*: Check logs for landing page crawls: `[INFO] Crawling landing page content via Firecrawl...`
    *   *Expected Result*: Landing page structures are downloaded and formatted for AI processing.
*   **SMTP / Resend Email service**:
    *   *Purpose*: Emails report files to your inbox.
    *   *Validation Step*: Check email inbox after a search run completes.
    *   *Expected Result*: Email arrives containing the generated report files.

---

## 8. Data Validation
Confirm that business data is parsed and persisted accurately:
*   **Scored Lead Accuracy**: Look at the scores inside the dashboard cards. Confirm they are calculated using the 4-Dimensional criteria (Audience, Budget, Relevance, Traction).
*   **Duplicate Prevention**: Re-run a search. Confirm that previously processed companies are listed as `[DUPLICATE] Skipped` in the console logs and do not re-appear.
*   **HTML Injection Prevention**: Review leads with descriptions containing special characters (like `<`, `>`, `&`). Verify that they are rendered correctly as plain text on the dashboard and do not trigger layout breaks or script popups.

---

## 9. User Experience Validation
Please rate the visual design and usability of the admin dashboard client (Scale of 1 to 5):

*   **Navigation & Tabs**: Is the sidebar navigation easy to use? (1 = Confusing, 5 = Intuitive)
    *   *Rating*: [ ]
*   **Usability & Responsiveness**: Does the interface adjust smoothly to screen adjustments? (1 = Broken layouts, 5 = Fluid)
    *   *Rating*: [ ]
*   **Visual Aesthetics**: Rate the premium glassmorphism, fonts, and dark mode colors. (1 = Poor, 5 = Excellent)
    *   *Rating*: [ ]

---

## 10. Performance Validation
Confirm that dashboard rendering is responsive:
*   **Page Load Time**: The dashboard should initialize in under 2 seconds.
*   **Log Streaming**: Real-time console messages should update smoothly without freezing the browser interface.
*   **Action Responsiveness**: Clicking on tab menus or lead cards should display data drawers instantly.

---

## 11. Error Handling Validation
Verify that the system responds gracefully when encountering issues:
*   **Trigger Invalid Password**: Try to submit an empty password field.
    *   *Expected response*: Modals remain locked, displaying a clear warning indicator.
*   **Unavailable Third-Party Scraper**: If Firecrawl fails, check logs.
    *   *Expected response*: The pipeline skips the error log gracefully and uses Google Snippets, ensuring the run completes successfully.

---

## 12. Security & Permissions Validation
*   **Direct API Access Restriction**: Try accessing `http://127.0.0.1:8000/api/leads` (or your Render server equivalent) in an incognito window.
    *   *Expected response*: Returns a blank page or a raw JSON message: `{"detail":"Unauthorized"}`.
*   **Locked Sessions**: Refresh the page after logging out. Confirm the login overlay blocks access.

---

## 13. Regression Validation
Confirm that all core functions continue to operate after migrating the server from Vercel to Render:
*   [ ] Dashboard login modal functions correctly.
*   [ ] Background pipeline launches and finishes without server timeouts.
*   [ ] Local database caching (`learned_leads.json`) updates correctly in place.
*   [ ] File reports download cleanly.

---

## 14. Known Limitations
Please keep the following constraints in mind during testing:
*   **Storage Lifespan on Render**: Unless a Render Persistent Volume is attached to the path `/app/learned_leads.json`, the local memory database will reset back to its initial state when Render rebuilds the application container during a new deployment.
*   **API Usage Allowances**: Running large batch requests will deplete free monthly quotas on OpenAI, Apify, and Firecrawl. Check credit configurations if scrapers return empty lists.

---

## 15. Defect Reporting
If you identify a bug during testing, please fill out this form and share it with the development team:

| Field | Description |
| :--- | :--- |
| **Issue Title** | Brief summary of the bug (e.g. "Download DOCX button fails with 404"). |
| **Feature Area** | (e.g. Login, Pipeline, Inspector, Exports) |
| **Steps to Reproduce** | 1. Navigate to... <br>2. Click on... <br>3. Enter... |
| **Expected Behavior** | What the application should have done. |
| **Actual Behavior** | What the application actually did (include error codes if visible). |
| **Environment Details** | (e.g. Chrome Version 120, MacOS, Render Live Server) |
| **Severity Level** | **Critical** (blocks workflow) / **Major** (workaround exists) / **Minor** (cosmetic) |

---

## 16. Client Feedback
Please share your overall experience and future ideas:

*   **Overall Satisfaction Rating** (1 = Unsatisfied, 5 = Delighted): [ ]
*   **Requested Improvements / Cosmetic Changes**:
    \
    \
    \
*   **Future Feature Requests**:
    \
    \
    \

---

## 17. Formal Acceptance

**Project Name:** Timidly Inc AI Lead Generation Pipeline  
**Deliverable Version:** v2.0.0  
**Client Representative:** SomitraSR (Timidly Inc)  

### Acceptance Decision:
*   [ ] **Accepted**: The system meets all requirements and is approved for production sign-off.
*   [ ] **Accepted with Comments**: The system is approved, subject to completing the minor improvements documented in the feedback section.
*   [ ] **Rejected**: The system requires additional corrections before sign-off can be granted.

**Signature:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  
**Date:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_  

---

## 18. Appendix

### Glossary of Business Terms
*   **UAT (User Acceptance Testing)**: Final operational testing performed by the client.
*   **ICP (Ideal Customer Profile)**: The description of target startups that represent ideal leads.
*   **Enrichment**: Gathering additional public data (such as emails, founders, funding) for a lead.
*   **XSS (Cross-Site Scripting)**: A security vulnerability where malicious scripts are executed in a user's browser via unsanitized data inputs.

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
