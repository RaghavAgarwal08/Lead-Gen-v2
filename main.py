import argparse
import sys
import os
import json
from datetime import datetime

# Add current folder to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.discovery import discover_companies, pre_qualify_companies_with_gpt
from core.contacts import find_contact_person, extract_contact_info
from core.enricher import scrape_website_content, fetch_firmographics, fetch_country
from core.generator import generate_personalized_pitch
from core.exporter import export_docx, export_csv, export_json
from utils.mailer import send_leads_report
from core.twitter import search_twitter_handle, scrape_recent_tweets, extract_handle_from_twitter_url


IS_VERCEL = bool(os.environ.get("VERCEL"))
if IS_VERCEL:
    MEMORY_FILE = "/tmp/learned_leads.json"
    # Bootstrap /tmp/learned_leads.json from committed file if not present
    if not os.path.exists(MEMORY_FILE):
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learned_leads.json")
        if os.path.exists(src):
            import shutil
            try:
                shutil.copy(src, MEMORY_FILE)
            except Exception as e:
                print(f"[VERCEL] Warning: Failed to copy learned_leads.json to /tmp: {e}")
else:
    MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "learned_leads.json")


def get_lead_from_memory(company_name: str) -> dict:
    """Retrieves a cached lead from memory if it exists and has all required fields."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                learned_leads = json.load(f)
            for l in learned_leads:
                if l.get("company_name", "").lower() == company_name.lower():
                    # Ensure it has the newly required fields
                    if "country_based_in" in l and "background_of_founders" in l and "lead_score" in l:
                        return l
        except:
            pass
    return None

def save_lead_to_memory(lead: dict):
    """Saves or updates a processed lead in the learned leads database (Self-Learning Memory)."""
    learned_leads = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                learned_leads = json.load(f)
        except:
            pass
            
    # Remove old record of same company if it exists
    for idx, l in enumerate(learned_leads):
        if l.get("company_name", "").lower() == lead.get("company_name", "").lower():
            learned_leads.pop(idx)
            break
            
    # Always insert at the top (index 0)
    learned_leads.insert(0, lead)
        
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(learned_leads, f, indent=4)
    except Exception as e:
        print(f"[WARNING] Failed to save lead to memory: {e}")

def run_pipeline(recipient_email: str, limit: int):
    print("==================================================")
    print("  TIMIDLY INC - LEAD GENERATION PIPELINE START   ")
    print("==================================================")
    print(f"Send Report To: '{recipient_email}'")
    print(f"Limit: {limit} target companies")
    print("--------------------------------------------------")
    
    # Step 1: Discover target companies directly from the ICP Prospect list
    companies = discover_companies("", limit=limit, log_cb=print)
    # Apply professional pre-qualification GPT filter
    companies = pre_qualify_companies_with_gpt(companies)
    print(f"Found {len(companies)} qualified target prospects to process after pre-filtering.")
    
    final_leads = []
    
    # Step 2: Iterate and Enrich each company
    for idx, comp in enumerate(companies, 1):
        name = comp["company_name"]
        print(f"\n[{idx}/{len(companies)}] Processing: {name}...")
        
        # Check Self-Learning Memory Cache
        cached_lead = get_lead_from_memory(name)
        if cached_lead:
            if cached_lead.get("lead_score", 0) < 7:
                print(f"[MEMORY] Skipping cached lead {name} as its score ({cached_lead.get('lead_score')}/10) is below the qualification threshold.")
                continue
                
            # If cached lead doesn't have recent tweets, let's fetch them now!
            if not cached_lead.get("recent_tweets"):
                print(f"[MEMORY] Cache hit for {name} but no recent tweets found. Fetching tweets...")
                twitter_url = cached_lead.get("twitter", "Not listed")
                twitter_handle = extract_handle_from_twitter_url(twitter_url)
                if not twitter_handle or twitter_handle.lower() == "not listed":
                    twitter_handle = search_twitter_handle(name)
                if twitter_handle:
                    recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=cached_lead.get("tagline"))
                    cached_lead["recent_tweets"] = recent_tweets
                    cached_lead["twitter"] = f"https://x.com/{twitter_handle}"
                    save_lead_to_memory(cached_lead)

            
            print(f"[MEMORY] Loaded learned lead details for {name} from cache.")
            if "recent_tweets" not in cached_lead:
                cached_lead["recent_tweets"] = []
            final_leads.append(cached_lead)
            continue
            
        try:
            # Guess website domain from name
            clean_name = "".join(c for c in name if c.isalnum()).lower()
            website = comp.get("website", f"https://{clean_name}.com")
            tagline = comp.get("tagline", "")
            
            # 2.1 Find Point of Contact on LinkedIn
            contact = find_contact_person(name, "Founder OR CEO OR 'Head of Marketing' OR 'Partnerships'")
            
            # 2.2 Scraping landing page content via Firecrawl
            markdown_content = scrape_website_content(website)
            
            # 2.3 Extract email, phone, and social handles
            contact_details = extract_contact_info(name, website)
            
            # 2.3.5 Twitter/X handle discovery and scraping using apidojo/tweet-scraper
            twitter_url = contact_details.get("twitter", "Not listed")
            twitter_handle = extract_handle_from_twitter_url(twitter_url)
            if not twitter_handle:
                twitter_handle = search_twitter_handle(name)
                
            recent_tweets = []
            if twitter_handle:
                recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=tagline)
                contact_details["twitter"] = f"https://x.com/{twitter_handle}"

            
            # 2.4 Retrieve headquarters/country search snippets
            country_snippets = fetch_country(name)
            
            # 2.5 Retrieve firmographics/funding info
            firmographics = fetch_firmographics(name)
            firmographics["country_search_snippets"] = country_snippets
            
            # 2.6 Generate AI pitch and recommended package (uses past learned examples)
            ai_pitch = generate_personalized_pitch(
                company_name=name,
                tagline=tagline,
                website_markdown=markdown_content,
                firmographics=firmographics,
                contact_info=contact,
                recent_tweets=recent_tweets
            )
            
            # Check strict professional qualification score threshold
            if ai_pitch.lead_score < 7:
                print(f"[DISCARDED] {name} failed professional fit score threshold (Score: {ai_pitch.lead_score}/10). Skipping...")
                continue
            
            # Compile the complete lead record using all enriched API data
            lead_record = {
                "company_name": name,
                "tagline": tagline,
                "contact_name": contact.get("name", "Not found"),
                "contact_title": contact.get("title", "GTM/Marketing Lead"),
                "email": contact_details.get("email", f"hello@{clean_name}.com"),
                "linkedin": contact.get("linkedin", "Not listed"),
                "twitter": contact_details.get("twitter", "Not listed"),
                "phone": contact_details.get("phone", "Not found"),
                "country_based_in": ai_pitch.country_based_in,
                "funding": firmographics.get("funding", "Unknown / Seed"),
                "background_of_founders": ai_pitch.background_of_founders,
                "why_pitch_fits": ai_pitch.why_pitch_fits,
                "recommended_package": ai_pitch.recommended_package,
                "tailored_outreach_angle": ai_pitch.tailored_outreach_angle,
                "lead_score": ai_pitch.lead_score,
                "score_justification": ai_pitch.score_justification,
                "recent_tweets": recent_tweets,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Learn the lead for future runs
            save_lead_to_memory(lead_record)
            final_leads.append(lead_record)
            print(f"[OK] successfully enriched, generated pitch, and learned lead for {name}")
            
        except Exception as e:
            print(f"[FAIL] Failed to process lead {name}: {e}")
            continue
            
    if not final_leads:
        print("[FAIL] No leads were successfully processed. Pipeline aborted.")
        return
        
    # Step 3: Export Files Locally
    docx_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Timidly_Prospects_Report.docx")
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Timidly_Prospects_Report.csv")
    json_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Timidly_Prospects_Report.json")
    
    export_docx(final_leads, docx_file)
    export_csv(final_leads, csv_file)
    export_json(final_leads, json_file)
    
    # Step 4: Send Report via Email
    if recipient_email:
        send_leads_report(recipient_email, docx_file, csv_file, len(final_leads))
        
    print("\n==================================================")
    print("      PIPELINE COMPLETED SUCCESSFULLY!            ")
    print("==================================================")
    print(f"Generated {len(final_leads)} leads. Files saved locally:")
    print(f" - {docx_file}")
    print(f" - {csv_file}")
    print(f" - {json_file}")
    print("==================================================")

def main():
    parser = argparse.ArgumentParser(description="Timidly Inc Lead Generator Script")
    parser.add_argument("--email", type=str, default=None, help="Email address to receive the report")
    parser.add_argument("--limit", type=int, default=None, help="Number of leads to retrieve")
    args = parser.parse_args()
    
    email = args.email
    if not email:
        email = input("Enter the email address to send the leads report to: ").strip()
        while not email:
            email = input("An email address is required: ").strip()
            
    limit = args.limit
    if not limit:
        limit_str = input("How many leads do you want to generate? ").strip()
        while not limit_str.isdigit():
            limit_str = input("Please enter a valid number: ").strip()
        limit = int(limit_str)
        
    run_pipeline(email, limit)

if __name__ == "__main__":
    main()
