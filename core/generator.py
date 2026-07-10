import json
import os
from openai import OpenAI
from pydantic import BaseModel, Field
import config

class PitchAnalysis(BaseModel):
    why_pitch_fits: str = Field(
        description="Reasoning why this company is a great fit for Timidly Inc's creator sponsorship campaigns right now."
    )
    recommended_package: str = Field(
        description="The specific creator packages (from config.CREATOR_PACKAGES) recommended for them."
    )
    tailored_outreach_angle: str = Field(
        description="A highly personalized message pitch or email opening line referencing their profile/product."
    )
    country_based_in: str = Field(
        description="The country where this company/startup is based or headquartered (e.g. 'United States', 'Germany', 'United Kingdom')."
    )
    background_of_founders: str = Field(
        description="Detailed background context about the founders/point of contact, including their work experience, education, or achievements."
    )
    lead_score: int = Field(
        description="Lead fit score out of 10 (integer from 1 to 10) evaluating how well this company aligns with Timidly Inc's Ideal Customer Profile (ICP). Higher is better. Based on the fact that Timidly Inc targets high-growth tech startups in AI, developer tools, database, GTM, and SaaS space who sell to builders, developers, or founders."
    )
    score_justification: str = Field(
        description="A short 1-2 sentence justification for the lead score out of 10."
    )

def generate_personalized_pitch(
    company_name: str,
    tagline: str,
    website_markdown: str,
    firmographics: dict,
    contact_info: dict,
    recent_tweets: list = None
) -> PitchAnalysis:
    """Uses OpenAI's structured outputs to generate personalized outreach and fit scores."""
    print(f"[AI] Generating AI pitch and lead score for {company_name}...")
    
    if not config.OPENAI_API_KEY:
        # Fallback values
        return PitchAnalysis(
            why_pitch_fits="Timidly Inc's audience reaches technical founders and builders who would love this tool.",
            recommended_package="Newsletter ad ($199)",
            tailored_outreach_angle=f"Hi {contact_info.get('name', 'there')}, loved what you are building at {company_name}!",
            country_based_in="United States",
            background_of_founders=contact_info.get("title", "") + " with experience at " + company_name,
            lead_score=8,
            score_justification="Fallback score: Appears to align with technical audience based on domain name."
        )
        
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    available_packages_str = "\n".join([f"- {k}: {v}" for k, v in config.CREATOR_PACKAGES.items()])
    
    # Load learned leads as few-shot examples (Self-Learning Mechanism)
    learned_examples_str = ""
    memory_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "learned_leads.json")
    if os.path.exists(memory_file):
        try:
            with open(memory_file, 'r', encoding='utf-8') as f:
                learned_leads = json.load(f)
            # Take the last 5 learned leads to optimize context window and training quality
            examples = learned_leads[-5:]
            if examples:
                learned_examples_str = "\n\nHere are examples of successfully generated leads from past runs. Study them to generate even better, more tailored pitches and angles matching this style:\n"
                for ex in examples:
                    learned_examples_str += (
                        f"\nCompany: {ex.get('company_name')}\n"
                        f"- Why Fit: {ex.get('why_pitch_fits')}\n"
                        f"- Outreach Angle: {ex.get('tailored_outreach_angle')}\n"
                        f"- Country: {ex.get('country_based_in')}\n"
                        f"- Recommended Package: {ex.get('recommended_package')}\n"
                        f"- Founder Background: {ex.get('background_of_founders')}\n"
                        f"- Lead Score: {ex.get('lead_score', 8)}/10\n"
                        "---"
                    )
        except Exception as e:
            print(f"[WARNING] Could not load learned leads memory: {e}")
            
    system_prompt = (
        "You are an expert sales strategist and growth marketer for Timidly Inc (led by SomitraSR). "
        "Timidly Inc is a premium content brand reaching over 100K+ developers, software engineering builders, "
        "and startup operators on LinkedIn, X/Twitter, Instagram, and a highly engaged weekly newsletter.\n\n"
        "Your task is to analyze the target startup company details, their landing page, their funding/firmographics stage, "
        "their point of contact, and their recent tweets to write a highly tailored pitch recommendation and evaluate their "
        "lead score out of 10.\n\n"
        "Lead Scoring Criteria (out of 10):\n"
        "- 9-10: Perfect fit. High-growth tech startup in developer tooling, databases, open-source tech, or AI, selling directly to builders/developers, with active funding (Series A-D or YC-backed).\n"
        "- 7-8: Great fit. Mid-stage tech/AI startup, selling to general startup operators/founders, or possessing good organic traction.\n"
        "- 5-6: Moderate fit. B2B SaaS without developer angle or lower relevance to software engineering builders.\n"
        "- 1-4: Poor fit. Non-tech company, consultancy, localized business, or extremely early bootstrapped with no budget.\n\n"
        f"Available Sponsorship Packages:\n{available_packages_str}"
        f"{learned_examples_str}"
    )
    
    recent_tweets_str = ""
    if recent_tweets:
        recent_tweets_str = "\nRecent Tweets from Company/Founder/Key Execs:\n"
        for t in recent_tweets:
            recent_tweets_str += f"- {t.get('text')} (Likes: {t.get('likes')}, Retweets: {t.get('retweets')})\n"
            
    user_prompt = f"""
    Analyze the following lead data:
    
    - Company Name: {company_name}
    - Company Description: {tagline}
    - Funding/Firmographics: {json_serialize(firmographics)}
    - Contact Name: {contact_info.get('name')}
    - Contact Job Title: {contact_info.get('title')}
    - Contact LinkedIn: {contact_info.get('linkedin')}
    {recent_tweets_str}
    
    Website Landing Page Text:
    ---
    {website_markdown[:4000]}
    ---
    
    Generate the pitch analysis output in the requested JSON structure, including lead_score (integer 1-10) and score_justification. Keep descriptions professional and highly tailored.
    """
    
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=PitchAnalysis
        )
        return completion.choices[0].message.parsed
    except Exception as e:
        print(f"[WARNING] OpenAI Generation failed: {e}")
        return PitchAnalysis(
            why_pitch_fits="Timidly Inc reaches developers who build products. Startups in this vertical need early traction.",
            recommended_package=config.CREATOR_PACKAGES.get("newsletter_ad", "Newsletter Ad ($199)"),
            tailored_outreach_angle=f"Hi {contact_info.get('name', 'there')}, noticed your launch on Product Hunt. Let's collaborate!",
            country_based_in="United States",
            background_of_founders=contact_info.get("title", "") + " with experience at " + company_name,
            lead_score=8,
            score_justification="Fallback score applied due to API error during processing."
        )

def json_serialize(obj):
    try:
        return json.dumps(obj)
    except:
        return str(obj)
