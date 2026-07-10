import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# SMTP Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Creator Packages for Timidly Inc (SomitraSR's Company)
CREATOR_PACKAGES = {
    "linkedin_post": "LinkedIn Sponsored Post ($500)",
    "newsletter_ad": "Newsletter Ad ($199)",
    "dual_impact": "Dual Impact Package (LinkedIn Post + Newsletter Ad) ($600)",
    "sponsored_reel": "Instagram Sponsored Reel ($1,200)",
    "bundle": "Sponsored Reel + X Sponsored Thread bundle ($1,500)"
}
