from apify_client import ApifyClient
from typing import Dict, Any
import config
import re

def find_contact_person(company_name: str, query_topic: str) -> Dict[str, str]:
    """
    Finds the name and LinkedIn profile of a decision-maker at the target company
    using Google Search via Apify.
    """
    print(f"[CONTACT] Finding decision-maker for {company_name}...")
    
    if not config.APIFY_API_TOKEN:
        return {"name": "Not found", "title": "GTM/Marketing Lead", "linkedin": "Not listed"}
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    
    # We search Google for a LinkedIn profile of a decision-maker
    search_query = f'site:linkedin.com/in/ "{company_name}" (Founder OR CEO OR "Head of Marketing" OR "Partnerships")'
    
    run_input = {
      "queries": search_query,
      "maxPagesPerQuery": 1,
      "resultsPerPage": 3,
    }
    
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
    except Exception as e:
        print(f"[WARNING] Apify contact search failed: {e}")
        return {"name": "Not found", "title": "GTM/Marketing Lead", "linkedin": "Not listed"}
        
    for item in dataset_items:
        organic_results = item.get("organicResults", [])
        if organic_results:
            first_res = organic_results[0]
            title = first_res.get("title", "")
            url = first_res.get("url", "")
            
            # Example title: "Bruno Estrella - Head of Marketing - Clay | LinkedIn"
            # Extract name and title
            parts = title.split("-")
            name = parts[0].strip() if len(parts) > 0 else "Decision Maker"
            contact_title = parts[1].strip() if len(parts) > 1 else "Marketing/Partnerships Lead"
            
            # Clean name from site branding
            name = name.split("|")[0].split(" - ")[0].strip()
            
            return {
                "name": name,
                "title": contact_title,
                "linkedin": url
            }
            
    return {"name": "Not found", "title": "GTM/Marketing Lead", "linkedin": "Not listed"}

def extract_contact_info(company_name: str, domain: str) -> Dict[str, str]:
    """
    Extracts emails, phone numbers, and social URLs from the company's website
    using the Apify Contact Info Scraper.
    """
    print(f"[EMAIL] Scraping contact info from website for {company_name} ({domain})...")
    
    # Simple heuristic fallback if domain is not provided
    if not domain or domain == "Not found":
        # Guess domain
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
        domain = f"https://{clean_name}.com"
        
    if not domain.startswith("http"):
        domain = f"https://{domain}"
        
    if not config.APIFY_API_TOKEN:
        return {"email": "Not found", "phone": "Not found", "twitter": "Not listed"}
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    
    run_input = {
        "startUrls": [{"url": domain}],
        "maxDepth": 1,
        "maxPagesPerCrawl": 5
    }
    
    try:
        run = client.actor("vdrmota/contact-info-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
    except Exception as e:
        print(f"[WARNING] Apify website scraping failed: {e}")
        # Guess email as fallback
        clean_name = re.sub(r'[^a-zA-Z0-9]', '', company_name).lower()
        return {
            "email": f"hello@{clean_name}.com",
            "phone": "Not found",
            "twitter": "Not listed"
        }
        
    emails = []
    phones = []
    twitters = []
    
    for item in dataset_items:
        # Extract emails
        for e in item.get("emails", []):
            if e not in emails:
                emails.append(e)
        # Extract phones
        for p in item.get("phones", []):
            if p not in phones:
                phones.append(p)
        # Extract twitter links
        for t in item.get("twitter", []):
            if t not in twitters:
                twitters.append(t)
                
    return {
        "email": emails[0] if emails else f"info@{domain.split('//')[-1]}",
        "phone": phones[0] if phones else "Not found",
        "twitter": twitters[0] if twitters else "Not listed"
    }
