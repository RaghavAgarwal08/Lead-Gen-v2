import re
from typing import List, Dict, Any
from apify_client import ApifyClient
import config

def extract_handle_from_twitter_url(url: str) -> str:
    """Extracts the Twitter handle from a URL or raw handle string."""
    if not url or url in ["Not listed", "Not found", "Unknown"]:
        return None
    url = url.strip()
    
    # Handle simple @username
    if url.startswith("@"):
        return url[1:]
    
    # Remove query params
    url = url.split("?")[0]
    
    # Match twitter.com/username or x.com/username
    match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', url, re.IGNORECASE)
    if match:
        handle = match.group(1)
        # Filter out common routing paths
        if handle.lower() not in ["search", "home", "explore", "status", "i", "share", "intent", "privacy", "tos"]:
            return handle
    
    # Fallback: if it's a clean alphanumeric handle
    if re.match(r'^[a-zA-Z0-9_]+$', url):
        if url.lower() not in ["notlisted", "notfound", "unknown"]:
            return url
        
    return None

def search_twitter_handle(company_name: str) -> str:
    """Searches Google via Apify to discover the company's Twitter/X handle."""
    print(f"[TWITTER] Searching Google for Twitter profile of '{company_name}'...")
    if not config.APIFY_API_TOKEN:
        return None
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    query = f'"{company_name}" (site:twitter.com OR site:x.com)'
    
    run_input = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": 3,
    }
    
    try:
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
        for item in dataset_items:
            organic_results = item.get("organicResults", [])
            for res in organic_results:
                url = res.get("url", "")
                handle = extract_handle_from_twitter_url(url)
                if handle:
                    print(f"[TWITTER] Discovered handle @{handle} for {company_name}")
                    return handle
    except Exception as e:
        print(f"[WARNING] Apify Google search for Twitter failed: {e}")
        
    return None

def scrape_recent_tweets(twitter_handle: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Scrapes recent tweets for a given Twitter handle using the apidojo/tweet-scraper on Apify, with Google Search fallback."""
    print(f"[TWITTER] Scraping recent tweets for handle: @{twitter_handle}...")
    if not config.APIFY_API_TOKEN:
        print("[WARNING] APIFY_API_TOKEN is missing. Skipping Twitter scraping.")
        return []
        
    client = ApifyClient(config.APIFY_API_TOKEN)
    tweets = []
    
    # 1. Try apidojo/tweet-scraper first
    try:
        run_input = {
            "twitterHandles": [twitter_handle],
            "maxItems": limit,
            "sort": "Latest",
            "tweetLanguage": "en"
        }
        run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run.default_dataset_id).list_items().items
        
        for item in dataset_items:
            text = item.get("full_text") or item.get("text")
            if text:
                text = " ".join(text.split())
                tweets.append({
                    "text": text,
                    "created_at": item.get("created_at", ""),
                    "likes": item.get("favorite_count", 0),
                    "retweets": item.get("retweet_count", 0)
                })
        if tweets:
            print(f"[TWITTER] Scraped {len(tweets)} tweets for @{twitter_handle} via apidojo/tweet-scraper")
            return tweets
    except Exception as e:
        print(f"[WARNING] Apify Twitter Scraper failed for @{twitter_handle}: {e}")

    # 2. Fallback to Google Search scraping if no tweets returned (e.g. Free plan restriction)
    if not tweets:
        print(f"[TWITTER] Falling back to Google Search scraper for @{twitter_handle}...")
        try:
            # Query site:x.com or site:twitter.com
            query = f"site:x.com {twitter_handle} inurl:status"
            run_input = {
                "queries": query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": 10,
            }
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            dataset_items = client.dataset(run.default_dataset_id).list_items().items
            for item in dataset_items:
                organic_results = item.get("organicResults", [])
                for res in organic_results:
                    url = res.get("url", "")
                    if f"/{twitter_handle.lower()}/status/" in url.lower() or f"/{twitter_handle.lower()}/statuses/" in url.lower():
                        title = res.get("title", "")
                        desc = res.get("description", "")
                        
                        # Clean title a bit
                        title_clean = title.split(" on Twitter: ")[-1].split(" on X: ")[-1].strip()
                        if title_clean.startswith('"') and title_clean.endswith('"'):
                            title_clean = title_clean[1:-1].strip()
                            
                        text = desc if desc else title_clean
                        if text.endswith("...Read more"):
                            text = text[:-12].strip()
                            
                        # If description is too short, combine with title
                        if len(text) < 40 and title_clean and title_clean != text:
                            text = f"{title_clean} - {text}"
                            
                        tweets.append({
                            "text": text,
                            "created_at": "Recent",
                            "likes": 0,
                            "retweets": 0
                        })
                        if len(tweets) >= limit:
                            break
                if len(tweets) >= limit:
                    break
            print(f"[TWITTER] Scraped {len(tweets)} tweets for @{twitter_handle} via Google Search fallback")
        except Exception as google_err:
            print(f"[WARNING] Google Search fallback for Twitter failed: {google_err}")
            
    return tweets

