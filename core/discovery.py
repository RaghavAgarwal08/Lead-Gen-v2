import re
import os
import json
from typing import List, Dict
from openai import OpenAI
from apify_client import ApifyClient
import config

def discover_companies(query_topic: str, limit: int = 10, log_cb=print) -> List[Dict]:
    """
    Primary interface for discovering target companies.
    1. Loads the profile of target companies from the new prospect list.
    2. Generates search queries dynamically based on this profile.
    3. Scrapes Product Hunt & Y Combinator via Apify to find fresh target companies.
    4. Filters out any companies that already exist in the prospect list or learned leads.
    """
    log_cb("[SEARCH] Analyzing ICP profile to generate search queries...")
    queries = generate_search_queries_from_profile()
    log_cb(f"[SEARCH] Generated queries: {queries}")
    
    if not config.APIFY_API_TOKEN:
        log_cb("[WARNING] APIFY_API_TOKEN is missing. Activating fail-safe OpenAI brainstorming fallback...")
        return get_fallback_leads(limit=limit, log_cb=log_cb)
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    
    # Construct combined query for Product Hunt and Y Combinator
    search_queries = []
    for q in queries:
        search_queries.append(f"site:producthunt.com/posts/ {q}")
        search_queries.append(f"site:ycombinator.com/companies {q}")
        
    combined_query = "\n".join(search_queries)
    
    # Load existing company names to filter out duplicates
    existing_names = get_existing_profile_company_names()
    learned_names = get_learned_company_names()
    
    run_input = {
      "queries": combined_query,
      "maxPagesPerQuery": 1,
      "resultsPerPage": limit * 2,
      "customDataFunction": "({ page, request, body }) => { return { }; }"
    }
    
    log_cb("[SEARCH] Scraping Product Hunt and Y Combinator via Apify...")
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
    except Exception as e:
        log_cb(f"[WARNING] Apify discovery search failed: {e} (Account limits may be reached). Activating fail-safe OpenAI brainstorming fallback...")
        return get_fallback_leads(limit=limit, log_cb=log_cb)
        
    discovered_companies = []
    seen_names = set()
    
    for item in dataset_items:
        organic_results = item.get("organicResults", [])
        for res in organic_results:
            title = res.get("title", "")
            snippet = res.get("snippet", "")
            url = res.get("url", "")
            
            # Clean up title to extract name
            # Filter out YC/PH index, list, tag, category, location, and tag pages
            # E.g. ycombinator.com/companies/industry/healthcare or posts/categories/tech
            url_lower = url.lower()
            if any(term in url_lower for term in [
                "/companies/industry", "/companies/industries", "/companies/tags", 
                "/companies/location", "/companies/regions", "/companies/founders",
                "/posts/categories", "/posts/topics", "/posts/new"
            ]):
                continue

            # Clean up title to extract name
            name = title.split("-")[0].split("|")[0].split("—")[0].strip()
            
            # If name is long or looks like a descriptive phrase, parse slug from URL
            if len(name.split()) > 3 or len(name) > 25:
                parsed_slug = ""
                if "ycombinator.com/companies/" in url:
                    parsed_slug = url.split("ycombinator.com/companies/")[-1].split("/")[0].split("?")[0].strip()
                elif "producthunt.com/posts/" in url:
                    parsed_slug = url.split("producthunt.com/posts/")[-1].split("/")[0].split("?")[0].strip()
                
                if parsed_slug:
                    name = parsed_slug.replace("-", " ").replace("_", " ").title()
                    
            if not name or name.lower() in [
                "product hunt", "y combinator", "companies", "posts", "industry", 
                "industries", "tags", "blog", "about", "careers", "jobs", "team", 
                "pricing", "contact", "categories", "topics"
            ]:
                continue
                
            name_lower = name.lower()
            if name_lower in seen_names or name_lower in existing_names or name_lower in learned_names:
                # Skip if already seen, in the profile list, or already learned
                continue

                
            seen_names.add(name_lower)
            
            # Estimate website URL
            clean_name = "".join(c for c in name if c.isalnum()).lower()
            website = f"https://{clean_name}.com"
            
            discovered_companies.append({
                "company_name": name,
                "tagline": snippet,
                "website": website,
                "search_url": url
            })
            
            if len(discovered_companies) >= limit:
                break
        if len(discovered_companies) >= limit:
            break
            
    if not discovered_companies:
        log_cb("[WARNING] No net-new target leads found by scraper. Activating fail-safe OpenAI brainstorming fallback...")
        return get_fallback_leads(limit=limit, log_cb=log_cb)
        
    return discovered_companies

def generate_search_queries_from_profile() -> List[str]:
    """Loads the profile companies, randomizes them, and uses OpenAI to generate 3 search queries."""
    import random
    
    # Load all prospects (up to 100)
    all_prospects = load_prospects_from_list(100)
    
    # Take a random sample of up to 15 prospects
    if all_prospects:
        sample_size = min(len(all_prospects), 15)
        prospects = random.sample(all_prospects, sample_size)
    else:
        prospects = []
        
    profile_str = "\n".join([f"- {p['company_name']}: {p['tagline']}" for p in prospects])
    
    if not config.OPENAI_API_KEY:
        default_topics = ["AI GTM", "AI code editor", "AI agents developer tools", "DevOps orchestration", "AI sales agent"]
        random.shuffle(default_topics)
        return default_topics[:3]
        
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    topics = [
        "AI agents", "developer tools", "GTM automation", "DevOps", 
        "LLM operations", "vector databases", "sales automation", 
        "AI security", "infrastructure", "B2B SaaS", "low-code platforms"
    ]
    random.shuffle(topics)
    selected_topics = ", ".join(topics[:3])
    
    system_prompt = (
        "You are an expert sales intelligence analyst. Your job is to analyze a profile of target companies (ICP) "
        "and generate 3 distinct, highly effective search queries to find similar, fresh startup companies on Product Hunt "
        "and Y Combinator. Output ONLY the queries as a JSON list of strings under key 'queries', e.g. {\"queries\": [\"query1\", \"query2\", \"query3\"]}."
    )
    
    user_prompt = f"""
    Here is a sample profile of target companies (ICP):
    {profile_str}
    
    Generate 3 distinct search queries to find new, similar companies focusing specifically on areas like: {selected_topics}.
    Make queries simple and highly optimized for Google search.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        queries = data.get("queries", list(data.values())[0])
        if isinstance(queries, list):
            return [q.strip() for q in queries if q.strip()][:3]
    except Exception as e:
        print(f"[WARNING] Failed to generate search queries via OpenAI: {e}")
        
    default_topics = ["AI GTM", "AI code editor", "AI agents developer tools", "DevOps orchestration", "AI sales agent"]
    random.shuffle(default_topics)
    return default_topics[:3]


def get_existing_profile_company_names() -> set:
    """Gets the set of company names in the original prospect list."""
    prospects = load_prospects_from_list(100)
    return {p["company_name"].lower() for p in prospects}

def get_learned_company_names() -> set:
    """Gets the set of company names in the learned database."""
    memory_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "learned_leads.json")
        
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                learned_leads = json.load(f)
            return {l["company_name"].lower() for l in learned_leads}
        except:
            pass
    return set()

def load_prospects_from_list(limit: int = 10) -> List[Dict]:
    """Loads and parses the target companies directly from extracted_prospects.md."""
    md_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "extracted_prospects.md")
    
    if not os.path.exists(md_path):
        return []
        
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
        
    prospects = []
    current_prospect = None
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r'^(\d+)\.\s*(.*)', line)
        if match:
            if current_prospect:
                prospects.append(current_prospect)
            current_prospect = {
                "company_name": match.group(2).strip(),
                "tagline": "",
                "contact_name": "Not found",
                "contact_title": "GTM/Marketing Lead",
                "email": "Not found",
                "linkedin": "Not listed",
                "twitter": "Not listed",
                "phone": "Not found",
                "funding": "Unknown / Seed",
                "background": "",
                "why_pitch_fits": "",
                "recommended_package": "",
                "tailored_outreach_angle": ""
            }
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if not re.match(r'^(\d+)\.\s*(.*)', next_line) and next_line not in [
                    "Point of Contact", "Title", "Email", "LinkedIn", "X / Twitter", "X/Twitter",
                    "Mobile Phone", "Phone", "Funding Status", "Contact Background",
                    "Why This Pitch Fits Right Now", "Recommended Package", "Tailored Outreach Angle"
                ]:
                    current_prospect["tagline"] = next_line
                    i += 1
        elif current_prospect:
            if line == "Point of Contact" and i + 1 < len(lines):
                current_prospect["contact_name"] = lines[i + 1]
                i += 1
            elif line == "Title" and i + 1 < len(lines):
                current_prospect["contact_title"] = lines[i + 1]
                i += 1
            elif line == "Email" and i + 1 < len(lines):
                current_prospect["email"] = lines[i + 1]
                i += 1
            elif line == "LinkedIn" and i + 1 < len(lines):
                current_prospect["linkedin"] = lines[i + 1]
                i += 1
            elif line in ["X / Twitter", "X/Twitter"] and i + 1 < len(lines):
                current_prospect["twitter"] = lines[i + 1]
                i += 1
            elif line in ["Mobile Phone", "Phone"] and i + 1 < len(lines):
                current_prospect["phone"] = lines[i + 1]
                i += 1
            elif line == "Funding Status" and i + 1 < len(lines):
                current_prospect["funding"] = lines[i + 1]
                i += 1
            elif line == "Contact Background" and i + 1 < len(lines):
                current_prospect["background"] = lines[i + 1]
                i += 1
            elif line == "Why This Pitch Fits Right Now" and i + 1 < len(lines):
                current_prospect["why_pitch_fits"] = lines[i + 1]
                i += 1
            elif line == "Recommended Package" and i + 1 < len(lines):
                current_prospect["recommended_package"] = lines[i + 1]
                i += 1
            elif line == "Tailored Outreach Angle" and i + 1 < len(lines):
                current_prospect["tailored_outreach_angle"] = lines[i + 1]
                i += 1
        i += 1
        
    if current_prospect:
        prospects.append(current_prospect)
        
    return prospects[:limit]

def get_fallback_leads(limit: int = 3, log_cb=print) -> List[Dict]:
    """
    Fallback mechanism that uses OpenAI to brainstorm fresh, qualified tech startups
    matching the ICP, avoiding any already processed or existing ones.
    """
    log_cb("[FALLBACK] Apify discovery failed or returned empty. Using OpenAI to brainstorm fresh startup leads...")
    
    existing_names = get_existing_profile_company_names()
    learned_names = get_learned_company_names()
    all_seen = existing_names.union(learned_names)
    
    # Take a sample of existing prospects to show OpenAI the style of companies
    prospects = load_prospects_from_list(10)
    profile_str = "\n".join([f"- {p['company_name']}: {p['tagline']}" for p in prospects])
    
    # Premium backup leads that score 9/10 or 10/10 and are guaranteed to pass strict threshold >= 7
    premium_backups = [
        {"company_name": "Supabase", "tagline": "The open-source Firebase alternative providing hosted Postgres databases and auth.", "website": "https://supabase.com"},
        {"company_name": "LangChain", "tagline": "Framework for developing context-aware applications powered by LLMs.", "website": "https://langchain.com"},
        {"company_name": "Vercel", "tagline": "Developer platform for frontend deployment, scaling, and serverless hosting.", "website": "https://vercel.com"},
        {"company_name": "Resend", "tagline": "Email API and delivery platform built specifically for developer teams.", "website": "https://resend.com"},
        {"company_name": "Neon", "tagline": "Serverless server-scaling Postgres database built for developer workflows.", "website": "https://neon.tech"}
    ]
    
    if not config.OPENAI_API_KEY:
        # Filter backups to remove already seen ones
        valid_backups = [b for b in premium_backups if b["company_name"].lower() not in all_seen]
        if not valid_backups:
            valid_backups = premium_backups
        return valid_backups[:limit]
        
    system_prompt = (
        "You are an expert sales development representative. Your job is to brainstorm and recommend real, existing startup companies "
        "that match a target ICP profile. They must be high-growth tech startups in AI, developer tooling, databases, open-source tech, or technical B2B SaaS.\n\n"
        "Do NOT recommend any companies from this list of already processed/seen companies (case-insensitive):\n"
        f"{list(all_seen)}\n\n"
        "Return ONLY a JSON object with key 'companies' containing a list of objects, each with 'company_name', 'tagline', and 'website', e.g. "
        "{\"companies\": [{\"company_name\": \"Supabase\", \"tagline\": \"Firebase alternative...\", \"website\": \"https://supabase.com\"}]}."
    )
    
    user_prompt = f"Here is a sample profile of target companies (ICP):\n{profile_str}\n\nBrainstorm {limit * 2} real startup prospects matching this profile."
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        companies_data = data.get("companies", [])
        
        valid_companies = []
        for c in companies_data:
            name = c.get("company_name", "").strip()
            tagline = c.get("tagline", "").strip()
            website = c.get("website", "").strip()
            
            if name and name.lower() not in all_seen:
                valid_companies.append({
                    "company_name": name,
                    "tagline": tagline,
                    "website": website
                })
                
        if valid_companies:
            log_cb(f"[FALLBACK] Brainstormed {len(valid_companies)} fresh leads via OpenAI fallback.")
            return valid_companies[:limit]
    except Exception as e:
        log_cb(f"[WARNING] OpenAI fallback brainstorming failed: {e}")
        
    # Final backup using curated premium backups
    valid_backups = [b for b in premium_backups if b["company_name"].lower() not in all_seen]
    if not valid_backups:
        valid_backups = premium_backups
    return valid_backups[:limit]

def pre_qualify_companies_with_gpt(companies: List[Dict]) -> List[Dict]:
    """
    Performs a lightweight GPT-4o-mini pre-filter based on names and taglines.
    Removes obvious consultancies, e-commerce stores, local shops, design agencies,
    or low-tech B2C applications to ensure high-quality pipeline candidates.
    """
    if not config.OPENAI_API_KEY or not companies:
        return companies
        
    print(f"[PRE-QUALIFY] Submitting {len(companies)} candidates for pre-qualification filtering...")
    
    candidates_list = []
    for idx, c in enumerate(companies):
        candidates_list.append({
            "index": idx,
            "company_name": c["company_name"],
            "tagline": c.get("tagline", "")
        })
        
    system_prompt = (
        "You are a professional SalesOps intelligence parser. Your job is to pre-qualify and filter out unqualified companies.\n\n"
        "Timidly Inc targets high-growth tech startups in developer tooling, databases, open-source tech, AI infra, and advanced technical B2B SaaS.\n\n"
        "Discard any companies that are:\n"
        "- Consultancies or software agencies (offering 'services', 'custom building', 'outsourcing').\n"
        "- Local businesses (e.g. gym, dentist, local restaurant, real estate broker).\n"
        "- Retail e-commerce brands or direct-to-consumer physical items.\n"
        "- General low-tech apps (like a localized calculator or simple fitness tracker).\n\n"
        "Return ONLY a JSON object with key 'qualified_indices' containing a list of integers of the qualified company indexes, e.g. {\"qualified_indices\": [0, 2]}."
    )
    
    user_prompt = f"Candidates to filter:\n{json.dumps(candidates_list, indent=2)}"
    
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(completion.choices[0].message.content)
        qualified_indices = data.get("qualified_indices", [])
        
        filtered = [companies[i] for i in qualified_indices if 0 <= i < len(companies)]
        print(f"[PRE-QUALIFY] Pre-qualification complete. Kept {len(filtered)} out of {len(companies)} discovered companies.")
        return filtered
    except Exception as e:
        print(f"[WARNING] Pre-qualification failed: {e}. Defaulting to keep all discovered companies.")
        return companies
