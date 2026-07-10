# Usage Guide

> Step-by-step instructions to set up and run the Timidly Inc AI Lead Generation Pipeline.

---

## Prerequisites

- **Python 3.10+** (tested on 3.12)
- **pip** package manager
- A Gmail account with 2-Step Verification enabled (for email delivery)

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/lead-gen-v0.git
cd lead-gen-v0
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
| Package | Version | Purpose |
|---------|---------|---------|
| `python-dotenv` | 1.0.1 | Loads `.env` variables |
| `pydantic` | 2.13.4 | Structured AI output validation |
| `openai` | 2.44.0 | GPT-4o-mini API client |
| `apify-client` | 3.0.4 | Apify scraping platform client |
| `python-docx` | 1.1.2 | Word document generation |
| `requests` | 2.32.3 | HTTP requests |
| `firecrawl-py` | 1.0.0 | Website crawling API client |

---

## 3. Configure API Keys

Copy the environment template:

```bash
cp .env.example .env
```

Open `.env` in your editor and fill in each credential:

### Apify API Token
1. Go to [https://console.apify.com/](https://console.apify.com/) and create a free account
2. Navigate to **Settings → API tokens**
3. Copy your token and paste it:
```
APIFY_API_TOKEN="apify_api_xxxxxxxxxxxxxxxxxx"
```
> **Free tier:** $5/month of compute credits — enough for ~50–100 leads per month.

### OpenAI API Key
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Copy and paste:
```
OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxx"
```
> **Cost:** GPT-4o-mini is extremely affordable — approximately $0.001–0.005 per lead.

### Firecrawl API Key
1. Go to [https://firecrawl.dev/](https://firecrawl.dev/) and sign up
2. Navigate to **Dashboard → API Keys**
3. Copy and paste:
```
FIRECRAWL_API_KEY="fc-xxxxxxxxxxxxxxxxxx"
```
> **Free tier:** 500 credits on signup — 1 credit per page scraped.

### Gmail SMTP (for email delivery)
1. **Enable 2-Step Verification** on your Google account:  
   [https://myaccount.google.com/signinoptions/two-step-verification](https://myaccount.google.com/signinoptions/two-step-verification)
2. **Generate an App Password**:  
   [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Enter name: `Lead Gen Tool`
   - Click **Create**
   - Copy the 16-character password
3. Update `.env`:
```
SMTP_HOST="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="abcdefghijklmnop"
```
> Remove any spaces from the App Password.

---

## 4. Prepare the ICP Prospect List

The tool requires a reference prospect list that defines your Ideal Customer Profile. Two files are needed:

- **`data/New Prospect List.docx`** — Your master prospect document in Word format
- **`data/extracted_prospects.md`** — A parsed markdown version

If you update the Word document, re-generate the markdown:
```bash
python -c "
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile('data/New Prospect List.docx') as z:
    root = ET.fromstring(z.read('word/document.xml'))
    ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    paras = []
    for p in root.iter(f'{{{ns}}}p'):
        texts = [n.text for n in p.iter(f'{{{ns}}}t') if n.text]
        if texts: paras.append(''.join(texts))
with open('data/extracted_prospects.md', 'w', encoding='utf-8') as f:
    for p in paras: f.write(p + '\n\n')
print(f'Extracted {len(paras)} paragraphs')
"
```

---

## 5. Running the Pipeline

### Interactive Mode (recommended)

```bash
python main.py
```

You will be prompted:
```
Enter the email address to send the leads report to: your-email@gmail.com
How many leads do you want to generate? 5
```

### Command-Line Mode

```bash
python main.py --email "your-email@gmail.com" --limit 5
```

### CLI Arguments

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--email` | string | *(prompted)* | Recipient email for the report |
| `--limit` | integer | *(prompted)* | Number of new leads to generate |

---

## 6. Output Files

After the pipeline completes, three files are saved to the project root:

| File | Format | Purpose |
|------|--------|---------|
| `Timidly_Prospects_Report.docx` | Word | Formatted report matching the ICP prospect list style |
| `Timidly_Prospects_Report.csv` | CSV | Flat file for CRM import (HubSpot, Salesforce, etc.) |
| `Timidly_Prospects_Report.json` | JSON | Machine-readable format for programmatic use |

If email delivery is configured, the DOCX and CSV are also sent as attachments to the specified email address.

---

## 7. Self-Learning Memory

The tool maintains a local file called `learned_leads.json` that stores every lead ever processed.

**Benefits:**
- **Instant cache hits** — If you request a company that was already processed, it loads instantly from memory (no API calls, no credits used)
- **Improved AI quality** — Past leads are fed as few-shot examples to GPT-4o-mini, so pitches get better with each run
- **Automatic deduplication** — Companies in the memory file are excluded from future discovery searches

**To reset the memory** (start fresh):
```bash
echo [] > learned_leads.json
```

---

## 8. Troubleshooting

### "APIFY_API_TOKEN is not set"
Your `.env` file is missing or the token field is empty. Verify the file exists and contains the correct token.

### "Firecrawl failed: DNS resolution failed"
The inferred website URL is wrong (e.g., the company's domain doesn't match its name). The pipeline will continue with reduced context — the AI pitch will still be generated using firmographic data.

### "SMTP: Username and Password not accepted"
Your Gmail App Password is incorrect or 2-Step Verification is not enabled. Re-generate the App Password following the instructions in Section 3.

### "No leads were successfully processed"
All discovered companies either already exist in the ICP list / learned memory, or the Apify free tier credits are exhausted. Check your usage at [https://console.apify.com/billing](https://console.apify.com/billing).

### Thread exceptions (`impit.TimeoutException`)
These are non-fatal log-streaming timeouts from the Apify client. They appear as warnings in the console but do not affect pipeline results — the scraper runs complete successfully on the server side.

---

## 9. Cost Estimates

| Leads per Run | Apify | OpenAI | Firecrawl | Total |
|:---:|:---:|:---:|:---:|:---:|
| 1 | ~$0.04 | ~$0.01 | 1 credit | ~$0.05 |
| 5 | ~$0.20 | ~$0.03 | 5 credits | ~$0.25 |
| 10 | ~$0.40 | ~$0.05 | 10 credits | ~$0.50 |
| 50 | ~$2.00 | ~$0.25 | 50 credits | ~$2.50 |

The Apify free tier ($5/month) comfortably supports 10–25 leads per run for regular use.
