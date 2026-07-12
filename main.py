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
    
    # Step 1: Discover & Process Loop
    final_leads = []
    backup_leads = []
    session_processed_names = set()
    iteration = 0
    max_iterations = 5
    
    while len(final_leads) < limit and iteration < max_iterations:
        iteration += 1
        needed = limit - len(final_leads)
        print(f"[PIPELINE] Loop iteration {iteration}: need {needed} more qualified leads.")
        
        # Request enough candidates to get needed qualified leads
        batch_limit = max(needed * 3, 5)
        companies = discover_companies("", limit=batch_limit, log_cb=print, exclude_names=session_processed_names)
        
        if not companies:
            print("[PIPELINE] No more target prospects discovered. Ending search.")
            break
            
        # Exclude them immediately in future iterations
        for comp in companies:
            session_processed_names.add(comp["company_name"].lower())
            
        # Filter
        companies = pre_qualify_companies_with_gpt(companies)
        print(f"Pre-qualification kept {len(companies)} candidates.")
        
        if len(companies) == 0:
            print("[PIPELINE] All candidates in this batch filtered out. Retrying...")
            continue
            
        for comp in companies:
            if len(final_leads) >= limit:
                break
                
            name = comp["company_name"]
            print(f"\n--- Processing: {name} (Got {len(final_leads)}/{limit}) ---")
            
            # Check memory cache
            cached_lead = get_lead_from_memory(name)
            if cached_lead:
                if cached_lead.get("lead_score", 0) < 7:
                    print(f"[MEMORY] Skipping cached lead {name} as its score ({cached_lead.get('lead_score')}/10) is below qualification.")
                    continue
                    
                # Fetch recent tweets if not present
                if not cached_lead.get("recent_tweets"):
                    print(f"[MEMORY] Cache hit for {name} but no recent tweets. Fetching...")
                    twitter_url = cached_lead.get("twitter", "Not listed")
                    twitter_handle = extract_handle_from_twitter_url(twitter_url)
                    if not twitter_handle or twitter_handle.lower() == "not listed":
                        twitter_handle = search_twitter_handle(name)
                    if twitter_handle:
                        recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=cached_lead.get("tagline"))
                        cached_lead["recent_tweets"] = recent_tweets
                        cached_lead["twitter"] = f"https://x.com/{twitter_handle}"
                        save_lead_to_memory(cached_lead)
                        
                print(f"[MEMORY] Loaded qualified lead details for {name} from cache.")
                if "recent_tweets" not in cached_lead:
                    cached_lead["recent_tweets"] = []
                final_leads.append(cached_lead)
                continue
                
            try:
                clean_name = "".join(c for c in name if c.isalnum()).lower()
                website = comp.get("website", f"https://{clean_name}.com")
                tagline = comp.get("tagline", "")
                
                # 2.1 Find Contact
                print(f"[{name}] Searching LinkedIn for decision-maker...")
                contact = find_contact_person(name, "Founder OR CEO OR 'Head of Marketing' OR 'Partnerships'")
                
                # 2.2 Scrape Website
                print(f"[{name}] Crawling landing page via Firecrawl: {website}...")
                markdown_content = scrape_website_content(website)
                
                # 2.3 Extract contact info
                print(f"[{name}] Scraping contact details (email, phone, handles)...")
                contact_details = extract_contact_info(name, website, contact.get("name"))
                
                # 2.3.5 Twitter
                print(f"[{name}] Checking Twitter/X presence...")
                twitter_url = contact_details.get("twitter", "Not listed")
                twitter_handle = extract_handle_from_twitter_url(twitter_url)
                if not twitter_handle or twitter_handle.lower() == "not listed":
                    twitter_handle = search_twitter_handle(name)
                    
                recent_tweets = []
                if twitter_handle:
                    print(f"[{name}] Twitter handle discovered: @{twitter_handle}. Fetching recent tweets...")
                    recent_tweets = scrape_recent_tweets(twitter_handle, limit=5, company_name=name, tagline=tagline)
                    contact_details["twitter"] = f"https://x.com/{twitter_handle}"
                else:
                    print(f"[{name}] No Twitter handle found.")
                    
                # 2.4 Country
                print(f"[{name}] Scraping location data...")
                country_snippets = fetch_country(name)
                
                # 2.5 Firmographics
                print(f"[{name}] Scraping firmographics (funding/employees)...")
                firmographics = fetch_firmographics(name)
                firmographics["country_search_snippets"] = country_snippets
                
                # 2.6 Generate pitch & score
                print(f"[{name}] Running lead qualification & OpenAI pitch engine...")
                ai_pitch = generate_personalized_pitch(
                    company_name=name,
                    tagline=tagline,
                    website_markdown=markdown_content,
                    firmographics=firmographics,
                    contact_info=contact,
                    recent_tweets=recent_tweets
                )
                
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
                if not resolved_phone or "not found" in resolved_phone.lower() or resolved_phone == "+1 (650) 456-7890":
                    resolved_phone = ""
                    
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
                
                if ai_pitch.lead_score < 7:
                    print(f"[PIPELINE] Lead {name} has score {ai_pitch.lead_score}/10 (below threshold of 7). Storing in backup list.")
                    backup_leads.append(lead_record)
                    continue
                    
                save_lead_to_memory(lead_record)
                final_leads.append(lead_record)
                print(f"[OK] Successfully processed {name}. Lead Score: {ai_pitch.lead_score}/10")
            except Exception as e:
                print(f"[FAIL] Error processing lead {name}: {e}")
                
    # Backfill if we didn't reach the target count with qualified leads
    if len(final_leads) < limit and backup_leads:
        print(f"[PIPELINE] Could not find enough qualified leads (score >= 7). Backfilling from the best backup candidates...")
        backup_leads.sort(key=lambda x: x["lead_score"], reverse=True)
        needed = limit - len(final_leads)
        for b_lead in backup_leads[:needed]:
            save_lead_to_memory(b_lead)
            final_leads.append(b_lead)
            print(f"[BACKFILL] Backfilled candidate {b_lead['company_name']} with score {b_lead['lead_score']}/10.")
            
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
        limit_str = input("How many leads do you want to generate (max 50)? ").strip()
        while not limit_str.isdigit() or int(limit_str) < 1 or int(limit_str) > 50:
            if limit_str.isdigit() and int(limit_str) > 50:
                print("Sorry, the limit is 50.")
            limit_str = input("Please enter a valid number (1-50): ").strip()
        limit = int(limit_str)
    else:
        if limit < 1 or limit > 50:
            print("Sorry, the limit is 50. Setting limit to 50.")
            limit = 50
        
    run_pipeline(email, limit)

if __name__ == "__main__":
    main()
