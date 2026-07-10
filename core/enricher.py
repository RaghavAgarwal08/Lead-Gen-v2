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

def parse_firmographics_with_gpt(company_name: str, snippets: str) -> dict:
    """Uses OpenAI to accurately extract funding and employee details from search results."""
    if not config.OPENAI_API_KEY:
        return None
        
    from openai import OpenAI
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        prompt = (
            f"You are a sales intelligence extractor. Extract the total funding raised, last funding round details, "
            f"and employee count for the company '{company_name}' based on the following Google search snippets:\n\n"
            f"{snippets}\n\n"
            "Provide the response strictly as a JSON object with the following keys:\n"
            "- 'funding': a clean string describing total funding raised and stage (e.g. '$15M Series A', 'Seed - $2M', 'Bootstrapped', 'YC-backed - $500K'). "
            "Be as specific as possible. If the funding is not mentioned, write 'Seed - Unknown' or 'Bootstrapped'.\n"
            "- 'employees': employee size range (e.g. '11-50 employees', '51-200 employees').\n"
            "Return ONLY the raw JSON block without markdown formatting."
        )
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        res_text = completion.choices[0].message.content.strip()
        if res_text.startswith("```"):
            res_text = res_text.split("```")[1]
            if res_text.startswith("json"):
                res_text = res_text[4:]
            res_text = res_text.split("```")[0].strip()
        
        return json.loads(res_text)
    except Exception as e:
        print(f"[WARNING] AI firmographics extraction failed: {e}")
        return None

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
    
    # Try GPT extraction first
    gpt_firm = None
    if config.OPENAI_API_KEY:
        gpt_firm = parse_firmographics_with_gpt(company_name, combined_snippets)
        
    if gpt_firm:
        funding = gpt_firm.get("funding", "Unknown / Seed")
        employees = gpt_firm.get("employees", "10-50 employees")
    else:
        # Simple heuristics fallback to parse funding
        funding = "Unknown / Seed"
        if "raised" in combined_snippets.lower() or "funding" in combined_snippets.lower():
            matches = re_find_funding(combined_snippets)
            if matches:
                funding = f"Raised {', '.join(matches)}"
                
        # Simple heuristics fallback to parse employee count
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
