import requests
import json
import config
from apify_client import ApifyClient
from firecrawl import FirecrawlApp

def scrape_website_content(url: str) -> str:
    """Scrapes the landing page and returns markdown content using Firecrawl."""
    print(f"[WEBSITE] Scraping website content via Firecrawl: {url}...")
    if not config.FIRECRAWL_API_KEY:
        return "Firecrawl API key is missing. Could not fetch page context."
        
    try:
        app = FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)
        scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
        return scrape_result.get('markdown', 'No markdown content returned.')
    except Exception as e:
        print(f"[WARNING] Firecrawl failed: {e}. Falling back to metadata search...")
        return f"Could not fetch full site. URL: {url}"

def fetch_firmographics(company_name: str) -> dict:
    """Queries Google via Apify to retrieve funding and employee size context."""
    print(f"[FIRMOGRAPHICS] Retrieving funding and company size context for {company_name}...")
    if not config.APIFY_API_TOKEN:
        return {"funding": "Unknown / Self-funded", "employees": "1-10"}
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    query = f'"{company_name}" funding total raised valuation crunchbase'
    
    run_input = {
      "queries": query,
      "maxPagesPerQuery": 1,
      "resultsPerPage": 3,
    }
    
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
    except Exception as e:
        print(f"[WARNING] Apify firmographics scraper failed: {e}")
        return {"funding": "Unknown / Self-funded", "employees": "1-10"}
        
    snippets = []
    for item in dataset_items:
        organic_results = item.get("organicResults", [])
        for res in organic_results:
            snippets.append(res.get("snippet", ""))
            
    combined_snippets = " ".join(snippets)
    
    # Simple heuristics to parse funding
    funding = "Unknown / Seed"
    if "raised" in combined_snippets.lower() or "funding" in combined_snippets.lower():
        # Match dollar values e.g. $130k, $2.3B, $100M
        matches = re_find_funding(combined_snippets)
        if matches:
            funding = f"Raised {', '.join(matches)}"
            
    # Simple heuristics to parse employee count
    employees = "10-50 employees"
    if "employees" in combined_snippets or "people" in combined_snippets:
        emp_match = re_find_employees(combined_snippets)
        if emp_match:
            employees = emp_match
            
    return {
        "funding": funding,
        "employees": employees,
        "search_snippets": combined_snippets
    }

def fetch_country(company_name: str) -> str:
    """Queries Google via Apify to retrieve headquarters/country context for the company."""
    print(f"[COUNTRY] Retrieving headquarters country context for {company_name}...")
    if not config.APIFY_API_TOKEN:
        return "Unknown"
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    query = f'"{company_name}" headquarters country city location'
    
    run_input = {
      "queries": query,
      "maxPagesPerQuery": 1,
      "resultsPerPage": 3,
    }
    
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
    except Exception as e:
        print(f"[WARNING] Apify country search failed: {e}")
        return "Unknown"
        
    snippets = []
    for item in dataset_items:
        organic_results = item.get("organicResults", [])
        for res in organic_results:
            snippets.append(res.get("snippet", ""))
            
    return " ".join(snippets)

def re_find_funding(text: str) -> list:
    import re
    return re.findall(r'\$[0-9.]+\s*[kMBmb]illion|\$[0-9.]+\s*[kMBmb]', text)

def re_find_employees(text: str) -> str:
    import re
    match = re.search(r'([0-9,+-]+)\s*(employees|people|workers)', text, re.IGNORECASE)
    return match.group(0) if match else None
