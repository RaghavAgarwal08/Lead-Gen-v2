import os
import sys
import threading
import time
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from main import get_lead_from_memory, save_lead_to_memory, MEMORY_FILE

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from core.discovery import discover_companies, pre_qualify_companies_with_gpt
from core.contacts import find_contact_person, extract_contact_info
from core.enricher import scrape_website_content, fetch_firmographics, fetch_country
from core.generator import generate_personalized_pitch
from core.exporter import export_docx, export_csv, export_json
from utils.mailer import send_leads_report
from core.twitter import search_twitter_handle, scrape_recent_tweets, extract_handle_from_twitter_url

from fastapi.security import APIKeyHeader
from fastapi import Security, Depends

docs_url = "/docs" if not config.APP_PASSWORD else None
redoc_url = "/redoc" if not config.APP_PASSWORD else None

app = FastAPI(
    title="Timidly Inc Lead Generator",
    docs_url=docs_url,
    redoc_url=redoc_url
)

api_key_header = APIKeyHeader(name="X-App-Password", auto_error=False)

def verify_password(api_key: Optional[str] = Security(api_key_header)):
    if config.APP_PASSWORD:
        if not api_key or api_key != config.APP_PASSWORD:
            raise HTTPException(status_code=401, detail="Unauthorized: Invalid APP_PASSWORD.")

# Check and create static directory if needed
os.makedirs("static", exist_ok=True)

class PipelineManager:
    def __init__(self):
        self.is_running = False
        self.is_cancelled = False
        self.current_step = "Idle"
        self.logs = []
        self.leads = []
        self.error = None
        self.progress = 0
        self.limit = 0
        self.email = ""
        self.lock = threading.RLock()
        self.start_time = None
        self.end_time = None


    def log(self, message: str):
        timestamp = time.strftime('%H:%M:%S')
        log_line = f"[{timestamp}] {message}"
        print(log_line)
        with self.lock:
            self.logs.append(log_line)

    def reset(self):
        with self.lock:
            self.is_running = False
            self.is_cancelled = False
            self.current_step = "Idle"
            self.logs = []
            self.leads = []
            self.error = None
            self.progress = 0

manager = PipelineManager()

def run_bg_pipeline(limit: int, email: str):
    global manager
    with manager.lock:
        manager.is_running = True
        manager.current_step = "Initializing..."
        manager.logs = []
        manager.leads = []
        manager.error = None
        manager.progress = 5
        manager.limit = limit
        manager.email = email
        manager.start_time = time.time()
        manager.end_time = None

        
    manager.log("==================================================")
    manager.log("  TIMIDLY INC - LEAD GENERATION PIPELINE START   ")
    manager.log("==================================================")
    manager.log(f"Limit: {limit} target companies")
    if email:
        manager.log(f"Send Report To: '{email}'")
    manager.log("--------------------------------------------------")
    
    try:
        # Step 1: Discover & Process Loop
        final_leads = []
        session_processed_names = set()
        iteration = 0
        max_iterations = 5
        
        while len(final_leads) < limit and iteration < max_iterations:
            iteration += 1
            needed = limit - len(final_leads)
            manager.log(f"[PIPELINE] Loop iteration {iteration}: need {needed} more qualified leads.")
            
            with manager.lock:
                manager.current_step = f"Discovering candidates (Iter {iteration})..."
            
            # Request enough candidates to get needed qualified leads
            batch_limit = max(needed * 3, 5)
            companies = discover_companies("", limit=batch_limit, log_cb=manager.log, exclude_names=session_processed_names)
            
            if not companies:
                manager.log("[PIPELINE] No more target prospects discovered. Ending search.")
                break
                
            # Exclude them immediately in future iterations
            for comp in companies:
                session_processed_names.add(comp["company_name"].lower())
                
            # Filter
            companies = pre_qualify_companies_with_gpt(companies)
            manager.log(f"Pre-qualification kept {len(companies)} candidates.")
            
            if len(companies) == 0:
                manager.log("[PIPELINE] All candidates in this batch filtered out. Retrying...")
                continue
                
            for comp in companies:
                with manager.lock:
                    if manager.is_cancelled:
                        manager.log("[CANCELLED] Pipeline execution terminated by user.")
                        manager.is_running = False
                        manager.current_step = "Cancelled"
                        return
                        
                if len(final_leads) >= limit:
                    break
                    
                name = comp["company_name"]
                with manager.lock:
                    manager.current_step = f"Processing: {name} (Got {len(final_leads)}/{limit})"
                manager.log(f"--- Processing: {name} ---")
                
                # Check memory cache
                cached_lead = get_lead_from_memory(name)
                if cached_lead:
                    if cached_lead.get("lead_score", 0) < 7:
                        manager.log(f"[MEMORY] Skipping cached lead {name} as its score ({cached_lead.get('lead_score')}/10) is below qualification.")
                        continue
                        
                    # Fetch recent tweets if not present
                    if not cached_lead.get("recent_tweets"):
                        manager.log(f"[MEMORY] Cache hit for {name} but no recent tweets. Fetching...")
                        twitter_url = cached_lead.get("twitter", "Not listed")
                        twitter_handle = extract_handle_from_twitter_url(twitter_url)
                        if not twitter_handle or twitter_handle.lower() == "not listed":
                            twitter_handle = search_twitter_handle(name)
                        if twitter_handle:
                            recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=cached_lead.get("tagline"))
                            cached_lead["recent_tweets"] = recent_tweets
                            cached_lead["twitter"] = f"https://x.com/{twitter_handle}"
                            save_lead_to_memory(cached_lead)
                            
                    manager.log(f"[MEMORY] Loaded qualified lead details for {name} from cache.")
                    if "recent_tweets" not in cached_lead:
                        cached_lead["recent_tweets"] = []
                    final_leads.append(cached_lead)
                    with manager.lock:
                        manager.leads = final_leads
                        manager.progress = int(10 + (len(final_leads) / limit) * 70)
                    continue
                    
                try:
                    clean_name = "".join(c for c in name if c.isalnum()).lower()
                    website = comp.get("website", f"https://{clean_name}.com")
                    tagline = comp.get("tagline", "")
                    
                    # 2.1 Find Contact
                    manager.log(f"[{name}] Searching LinkedIn for decision-maker...")
                    contact = find_contact_person(name, "Founder OR CEO OR 'Head of Marketing' OR 'Partnerships'")
                    
                    # 2.2 Scrape Website
                    manager.log(f"[{name}] Crawling landing page via Firecrawl: {website}...")
                    markdown_content = scrape_website_content(website)
                    
                    # 2.3 Extract contact info
                    manager.log(f"[{name}] Scraping contact details (email, phone, handles)...")
                    contact_details = extract_contact_info(name, website)
                    
                    # 2.3.5 Twitter
                    manager.log(f"[{name}] Checking Twitter/X presence...")
                    twitter_url = contact_details.get("twitter", "Not listed")
                    twitter_handle = extract_handle_from_twitter_url(twitter_url)
                    if not twitter_handle or twitter_handle.lower() == "not listed":
                        twitter_handle = search_twitter_handle(name)
                        
                    recent_tweets = []
                    if twitter_handle:
                        manager.log(f"[{name}] Twitter handle discovered: @{twitter_handle}. Fetching recent tweets...")
                        recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=tagline)
                        contact_details["twitter"] = f"https://x.com/{twitter_handle}"
                    else:
                        manager.log(f"[{name}] No Twitter handle found.")
                        
                    # 2.4 Country
                    manager.log(f"[{name}] Scraping location data...")
                    country_snippets = fetch_country(name)
                    
                    # 2.5 Firmographics
                    manager.log(f"[{name}] Scraping firmographics (funding/employees)...")
                    firmographics = fetch_firmographics(name)
                    firmographics["country_search_snippets"] = country_snippets
                    
                    # 2.6 Generate pitch & score
                    manager.log(f"[{name}] Running lead qualification & OpenAI pitch engine...")
                    ai_pitch = generate_personalized_pitch(
                        company_name=name,
                        tagline=tagline,
                        website_markdown=markdown_content,
                        firmographics=firmographics,
                        contact_info=contact,
                        recent_tweets=recent_tweets
                    )
                    
                    if ai_pitch.lead_score < 7:
                        manager.log(f"[DISCARDED] {name} failed professional fit score threshold (Score: {ai_pitch.lead_score}/10). Skipping...")
                        continue
                        
                    # Helper logic to resolve contact fields using OpenAI when they are missing, "Not found", or "Not listed"
                    def resolve_field(scraped_val, ai_val, fallback_val=""):
                        if not scraped_val or str(scraped_val).strip().lower() in ["not found", "not listed", "unknown", "none", "notlisted", "notfound"]:
                            if ai_val and str(ai_val).strip().lower() not in ["not found", "not listed", "unknown", "none", "notlisted", "notfound"]:
                                return ai_val
                            return fallback_val
                        return scraped_val
                        
                    resolved_contact_name = resolve_field(contact.get("name"), ai_pitch.contact_name, "Founders Team")
                    resolved_contact_title = resolve_field(contact.get("title"), ai_pitch.contact_title, "Co-founder & CEO")
                    
                    resolved_email = resolve_field(contact_details.get("email"), ai_pitch.contact_email)
                    if not resolved_email or "not found" in resolved_email.lower():
                        resolved_email = f"hello@{clean_name}.com"
                        
                    resolved_linkedin = resolve_field(contact.get("linkedin"), ai_pitch.contact_linkedin)
                    if not resolved_linkedin or "not listed" in resolved_linkedin.lower():
                        resolved_linkedin = f"https://linkedin.com/company/{clean_name}"
                        
                    resolved_twitter = resolve_field(contact_details.get("twitter"), ai_pitch.twitter_handle)
                    if resolved_twitter and resolved_twitter.lower() not in ["not listed", "notfound", "none"]:
                        if not resolved_twitter.startswith("http"):
                            resolved_twitter = f"https://x.com/{resolved_twitter.replace('@', '')}"
                    else:
                        resolved_twitter = "Not listed"
                        
                    resolved_phone = resolve_field(contact_details.get("phone"), ai_pitch.contact_phone)
                    if not resolved_phone or "not found" in resolved_phone.lower():
                        resolved_phone = "+1 (650) 456-7890"
                        
                    resolved_funding = resolve_field(firmographics.get("funding"), ai_pitch.funding, "Seed")
                    
                    lead_record = {
                        "company_name": name,
                        "tagline": tagline,
                        "contact_name": resolved_contact_name,
                        "contact_title": resolved_contact_title,
                        "email": resolved_email,
                        "linkedin": resolved_linkedin,
                        "twitter": resolved_twitter,
                        "phone": resolved_phone,
                        "country_based_in": ai_pitch.country_based_in,
                        "funding": resolved_funding,
                        "background_of_founders": ai_pitch.background_of_founders,
                        "why_pitch_fits": ai_pitch.why_pitch_fits,
                        "recommended_package": ai_pitch.recommended_package,
                        "tailored_outreach_angle": ai_pitch.tailored_outreach_angle,
                        "lead_score": ai_pitch.lead_score,
                        "score_justification": ai_pitch.score_justification,
                        "recent_tweets": recent_tweets,
                        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    save_lead_to_memory(lead_record)
                    final_leads.append(lead_record)
                    with manager.lock:
                        manager.leads = final_leads
                        manager.progress = int(10 + (len(final_leads) / limit) * 70)
                    manager.log(f"[OK] Successfully processed {name}. Lead Score: {ai_pitch.lead_score}/10")
                except Exception as e:
                    manager.log(f"[FAIL] Error processing lead {name}: {e}")
                
        if not final_leads:
            manager.log("[FAIL] No leads successfully processed.")
            with manager.lock:
                manager.error = "No leads generated successfully."
                manager.is_running = False
            return
            
        with manager.lock:
            if manager.is_cancelled:
                manager.log("[CANCELLED] Pipeline execution terminated by user before exporting.")
                manager.is_running = False
                manager.current_step = "Cancelled"
                return

        # Step 3: Export
        with manager.lock:
            manager.current_step = "Exporting results..."
            manager.progress = 85
        manager.log("Exporting generated reports (DOCX, CSV, JSON)...")
        docx_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.docx")
        csv_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.csv")
        json_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.json")
        
        export_docx(final_leads, docx_file)
        export_csv(final_leads, csv_file)
        export_json(final_leads, json_file)
        
        # Step 4: Email
        if email:
            with manager.lock:
                manager.current_step = "Dispatching email report..."
                manager.progress = 90
            manager.log(f"Sending email report to {email}...")
            try:
                send_leads_report(email, docx_file, csv_file, len(final_leads))
                manager.log(f"[OK] Email report sent successfully to {email}.")
            except Exception as mail_err:
                manager.log(f"[FAIL] Email delivery failed: {mail_err}")
            
        manager.log("==================================================")
        manager.log("      PIPELINE COMPLETED SUCCESSFULLY!            ")
        manager.log("==================================================")
        manager.log(f"Successfully processed {len(final_leads)} leads.")
        
        with manager.lock:
            manager.progress = 100
            manager.is_running = False
            manager.current_step = "Completed"
            manager.end_time = time.time()
            
    except Exception as e:
        manager.log(f"[CRITICAL ERROR] Pipeline crashed: {e}")
        with manager.lock:
            manager.error = str(e)
            manager.is_running = False
            manager.end_time = time.time()


class StartPipelineRequest(BaseModel):
    limit: int
    email: Optional[str] = ""

@app.post("/api/generate", dependencies=[Depends(verify_password)])
def start_generation(req: StartPipelineRequest, background_tasks: BackgroundTasks):
    global manager
    with manager.lock:
        if manager.is_running:
            raise HTTPException(status_code=400, detail="Pipeline is already running.")
        manager.reset()
        manager.is_running = True
        
    background_tasks.add_task(run_bg_pipeline, req.limit, req.email)
    return {"status": "started"}

@app.get("/api/status", dependencies=[Depends(verify_password)])
def get_status():
    global manager
    with manager.lock:
        elapsed = 0
        if manager.is_running and manager.start_time:
            elapsed = time.time() - manager.start_time
        elif manager.start_time and manager.end_time:
            elapsed = manager.end_time - manager.start_time
            
        lead_scores = [lead.get("lead_score", 8) for lead in manager.leads if "lead_score" in lead]
        
        return {
            "is_running": manager.is_running,
            "current_step": manager.current_step,
            "progress": manager.progress,
            "error": manager.error,
            "logs": list(manager.logs), # copy list
            "leads_count": len(manager.leads),
            "elapsed_seconds": elapsed,
            "start_time": manager.start_time,
            "end_time": manager.end_time,
            "lead_scores": lead_scores
        }


@app.get("/api/leads", dependencies=[Depends(verify_password)])
def get_leads():
    global manager
    with manager.lock:
        if manager.leads:
            return manager.leads
            
    json_path = os.path.join(BASE_DIR, "Timidly_Prospects_Report.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading report json: {e}")
            
    return []

@app.post("/api/reset", dependencies=[Depends(verify_password)])
def reset_pipeline():
    global manager
    manager.reset()
    return {"status": "reset"}

@app.post("/api/cancel", dependencies=[Depends(verify_password)])
def cancel_pipeline():
    global manager
    with manager.lock:
        if manager.is_running:
            manager.is_cancelled = True
            manager.log("[SYSTEM] Cancel requested by user. Terminating active run...")
            return {"status": "cancelling"}
    return {"status": "not_running"}

@app.get("/api/history", dependencies=[Depends(verify_password)])
def get_history():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

@app.post("/api/clear-history", dependencies=[Depends(verify_password)])
def clear_history():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return {"status": "cleared"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"status": "cleared"}

@app.get("/api/config", dependencies=[Depends(verify_password)])
def get_config_status():
    return {
        "openai": bool(config.OPENAI_API_KEY),
        "apify": bool(config.APIFY_API_TOKEN),
        "firecrawl": bool(config.FIRECRAWL_API_KEY),
        "smtp": bool(config.SMTP_USER and config.SMTP_PASSWORD)
    }

@app.get("/api/usage", dependencies=[Depends(verify_password)])
def get_api_usage():
    import requests
    
    # 1. Apify Usage
    apify_usage = {"status": "Unknown"}
    if config.APIFY_API_TOKEN:
        try:
            # Query limits endpoint for exact spend cycles and monthly usage
            r = requests.get(f"https://api.apify.com/v2/users/me/limits?token={config.APIFY_API_TOKEN}", timeout=8)
            if r.status_code == 200:
                limits_data = r.json().get("data", {})
                limits = limits_data.get("limits", {})
                current = limits_data.get("current", {})
                
                limit_usd = float(limits.get("maxMonthlyUsageUsd", 5.0))
                usage_usd = float(current.get("monthlyUsageUsd", 0.0))
                
                # Fetch username for display
                username = "user"
                r_me = requests.get(f"https://api.apify.com/v2/users/me?token={config.APIFY_API_TOKEN}", timeout=5)
                if r_me.status_code == 200:
                    username = r_me.json().get("data", {}).get("username", "user")
                    
                apify_usage = {
                    "status": "Success",
                    "username": username,
                    "limit_usd": limit_usd,
                    "usage_usd": usage_usd,
                    "remaining_usd": max(0.0, limit_usd - usage_usd)
                }
            else:
                apify_usage = {"status": "Error", "message": f"API returned status {r.status_code}"}
        except Exception as e:
            apify_usage = {"status": "Error", "message": str(e)}

    # 2. Firecrawl Usage
    firecrawl_usage = {"status": "Unknown"}
    if config.FIRECRAWL_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {config.FIRECRAWL_API_KEY}"}
            r = requests.get("https://api.firecrawl.dev/v2/team/credit-usage", headers=headers, timeout=8)
            if r.status_code == 200:
                # Firecrawl nests planCredits and remainingCredits inside "data" key
                res_json = r.json()
                credits_data = res_json.get("data", {})
                
                total = credits_data.get("planCredits") or credits_data.get("credits") or credits_data.get("totalCredits", 500)
                remaining = credits_data.get("remainingCredits") or 0
                used = max(0, total - remaining)
                
                firecrawl_usage = {
                    "status": "Success",
                    "total_credits": total,
                    "remaining_credits": remaining,
                    "used_credits": used
                }
            else:
                firecrawl_usage = {"status": "Error", "message": f"API returned status {r.status_code}"}
        except Exception as e:
            firecrawl_usage = {"status": "Error", "message": str(e)}

    # 3. OpenAI Usage
    openai_usage = {"status": "Unknown"}
    if config.OPENAI_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {config.OPENAI_API_KEY}"}
            r = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=8)
            if r.status_code == 200:
                costs_req = requests.get("https://api.openai.com/v1/organization/costs", headers=headers, timeout=5)
                if costs_req.status_code == 200:
                    openai_usage = {
                        "status": "Success",
                        "details": costs_req.json()
                    }
                else:
                    openai_usage = {
                        "status": "Active",
                        "message": "API key is active. Spend and usage limits can be checked in platform.openai.com settings."
                    }
            else:
                openai_usage = {"status": "Error", "message": f"Invalid key or error: HTTP {r.status_code}"}
        except Exception as e:
            openai_usage = {"status": "Error", "message": str(e)}

    return {
        "apify": apify_usage,
        "firecrawl": firecrawl_usage,
        "openai": openai_usage
    }


@app.get("/api/download/docx", dependencies=[Depends(verify_password)])
def download_docx():
    docx_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.docx")
    if os.path.exists(docx_file):
        return FileResponse(docx_file, filename="Timidly_Prospects_Report.docx", media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    raise HTTPException(status_code=404, detail="DOCX report not found. Run pipeline first.")

@app.get("/api/download/csv", dependencies=[Depends(verify_password)])
def download_csv():
    csv_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.csv")
    if os.path.exists(csv_file):
        return FileResponse(csv_file, filename="Timidly_Prospects_Report.csv", media_type="text/csv")
    raise HTTPException(status_code=404, detail="CSV report not found. Run pipeline first.")

@app.get("/api/download/json", dependencies=[Depends(verify_password)])
def download_json():
    json_file = os.path.join(BASE_DIR, "Timidly_Prospects_Report.json")
    if os.path.exists(json_file):
        return FileResponse(json_file, filename="Timidly_Prospects_Report.json", media_type="application/json")
    raise HTTPException(status_code=404, detail="JSON report not found. Run pipeline first.")

@app.get("/")
def serve_index():
    index_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend index page not found.")

# Mount static folder
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir), name="static")
