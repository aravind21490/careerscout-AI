"""
CareerScout AI — Upgraded AI Filter (Gen AI Course Edition)
============================================================
Demonstrates:
  1. Prompt Chaining   — multi-step LLM pipeline (extract → score → recommend)
  2. Structured Output — JSON responses via system prompt
  3. Persona Prompting — system prompt with role definition
  4. Chain-of-Thought  — step-by-step reasoning in prompts

Drop this file into your careerscout-AI project and replace
your existing filter call with `chain_filter(listing)`.
"""

import json
import os
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"

# ─── User Profile (customize this) ──────────────────────────────────────────
USER_PROFILE = {
    "skills": ["Python", "Machine Learning", "Web Scraping", "FastAPI", "React"],
    "interests": ["AI/ML", "Automation", "Full Stack", "Data Engineering"],
    "level": "undergraduate student",
    "looking_for": ["internship", "hackathon", "open source contribution"],
}


# ─── STEP 1: Extraction Chain ────────────────────────────────────────────────
def step1_extract(listing: dict) -> dict:
    """
    Chain Step 1 — Extract structured info from raw listing.
    Converts messy scraped text into clean fields.
    """
    system_prompt = """You are a career data extraction engine.
Your job is to extract structured information from job/internship/hackathon listings.
Always respond with ONLY valid JSON. No explanation, no markdown, no backticks.

JSON format:
{
  "title": "string",
  "type": "internship | hackathon | job | unknown",
  "skills_required": ["skill1", "skill2"],
  "domain": "string (e.g. AI/ML, Web Dev, Data Science)",
  "deadline": "string or null",
  "location": "string (Remote / City / Hybrid)",
  "stipend_or_prize": "string or null",
  "experience_level": "beginner | intermediate | advanced | any"
}"""

    user_prompt = f"""Extract structured information from this listing:

Title: {listing.get('title', 'N/A')}
Description: {listing.get('description', 'N/A')}
Stipend/Pay: {listing.get('stipend', 'N/A')}
Deadline: {listing.get('deadline', 'N/A')}
Source: {listing.get('source', 'N/A')}
Link: {listing.get('link', 'N/A')}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,  # Low temp for structured extraction
    )

    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return partial data
        return {"title": listing.get("title", ""), "type": "unknown", "skills_required": []}


# ─── STEP 2: Relevance Scoring Chain ─────────────────────────────────────────
def step2_score(extracted: dict, profile: dict) -> dict:
    """
    Chain Step 2 — Score relevance using extracted data + user profile.
    Uses chain-of-thought to reason before scoring.
    """
    system_prompt = """You are a career relevance scoring engine for a student developer.
You receive a structured job/internship listing and a student profile.
Think step by step, then output ONLY valid JSON. No markdown, no explanation outside JSON.

JSON format:
{
  "relevance_score": <integer 0-10>,
  "skill_match_count": <integer>,
  "matched_skills": ["skill1", "skill2"],
  "reasoning": "2-3 sentence explanation of score",
  "red_flags": ["any concerns or null"],
  "recommended": <true | false>
}

Score 7+ means recommend. Be strict — only high quality matches should score 7+."""

    user_prompt = f"""Student Profile:
- Skills: {', '.join(profile['skills'])}
- Interests: {', '.join(profile['interests'])}
- Level: {profile['level']}
- Looking for: {', '.join(profile['looking_for'])}

Listing Details:
{json.dumps(extracted, indent=2)}

Think step by step about skill overlap, domain match, and experience level fit. Then respond with JSON."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"relevance_score": 0, "recommended": False, "reasoning": "Parse error"}


# ─── STEP 3: Message Generation Chain ────────────────────────────────────────
def step3_message(extracted: dict, score: dict) -> str:
    """
    Chain Step 3 — Generate a Telegram-ready notification message.
    Only called if step2 recommends the listing.
    """
    system_prompt = """You are CareerScout AI, a helpful career assistant bot.
Generate a short, punchy Telegram notification for a matched opportunity.
Use emojis. Max 5 lines. Be enthusiastic but not cringe.
Plain text only — no JSON, no markdown headers."""

    user_prompt = f"""Create a Telegram notification for this matched opportunity:

Title: {extracted.get('title')}
Type: {extracted.get('type')}
Domain: {extracted.get('domain')}
Skills: {', '.join(extracted.get('skills_required', []))}
Location: {extracted.get('location')}
Stipend/Prize: {extracted.get('stipend_or_prize')}
Why it matched: {score.get('reasoning')}
Match Score: {score.get('relevance_score')}/10"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,  # Higher temp for creative message
    )

    return response.choices[0].message.content.strip()


# ─── MAIN CHAIN RUNNER ────────────────────────────────────────────────────────
def chain_filter(listing: dict, profile: dict = USER_PROFILE) -> dict:
    """
    Runs the full 3-step prompt chain on a single listing.

    Returns:
        {
            "recommended": bool,
            "score": int,
            "extracted": dict,
            "scoring": dict,
            "telegram_message": str or None,
            "link": str,
            "source": str,
            "stipend": str or None,
            "deadline": str or None,
        }
    """
    print(f"\n🔗 Chain started for: {listing.get('title', 'Unknown')}")

    # Step 1 — Extract
    print("  ⛏️  Step 1: Extracting structured data...")
    extracted = step1_extract(listing)
    print(f"  ✅ Extracted: {extracted.get('type')} | Domain: {extracted.get('domain')}")

    # Step 2 — Score
    print("  🧠  Step 2: Scoring relevance...")
    scoring = step2_score(extracted, profile)
    score = scoring.get("relevance_score", 0)
    recommended = scoring.get("recommended", False)
    print(f"  ✅ Score: {score}/10 | Recommended: {recommended}")
    print(f"  💬 Reasoning: {scoring.get('reasoning', '')}")

    # Step 3 — Message (only if recommended)
    telegram_message = None
    if recommended:
        print("  📨  Step 3: Generating Telegram message...")
        telegram_message = step3_message(extracted, scoring)
        print(f"  ✅ Message ready")
    else:
        print("  ⏭️  Step 3: Skipped (not recommended)")

    return {
        "recommended": recommended,
        "score": score,
        "extracted": extracted,
        "scoring": scoring,
        "telegram_message": telegram_message,
        # ✅ FIX: pass through original scraper fields so main_api.py can use them
        "link":     listing.get("link", ""),
        "source":   listing.get("source", ""),
        "stipend":  listing.get("stipend"),
        "deadline": listing.get("deadline"),
    }


# ─── BATCH FILTER ─────────────────────────────────────────────────────────────
def batch_chain_filter(listings: list, profile: dict = USER_PROFILE) -> list:
    """
    Runs chain_filter on a list of listings.
    Returns only recommended ones, sorted by score.
    """
    results = []
    for listing in listings:
        result = chain_filter(listing, profile)
        if result["recommended"]:
            results.append(result)

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"\n🎯 {len(results)}/{len(listings)} listings recommended after chain filtering")
    return results


# ─── TEST / DEMO ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Sample listings to test the chain
    test_listings = [
        {
            "title": "ML Intern - Computer Vision",
            "description": "Looking for a Python developer with ML experience to work on real-time object detection using YOLO and OpenCV. Remote internship, 3 months, ₹15,000/month stipend.",
            "source": "Unstop",
            "link": "https://unstop.com/example1",
            "stipend": "₹15,000/month",
            "deadline": None,
        },
        {
            "title": "Smart India Hackathon 2025 - AI Track",
            "description": "Build AI-powered solutions for real government problems. 36-hour hackathon. Prize pool ₹1,00,000. Open to all undergraduate students.",
            "source": "Devfolio",
            "link": "https://devfolio.co/example2",
            "stipend": None,
            "deadline": "April 30",
        },
        {
            "title": "Java Backend Developer - 3 Years Experience",
            "description": "Looking for experienced Java Spring Boot developer with 3+ years. Not suitable for freshers.",
            "source": "LinkedIn",
            "link": "https://linkedin.com/example3",
            "stipend": None,
            "deadline": None,
        },
    ]

    print("=" * 60)
    print("CareerScout AI — Prompt Chain Demo")
    print("=" * 60)

    recommended = batch_chain_filter(test_listings)

    print("\n" + "=" * 60)
    print("FINAL RECOMMENDED LISTINGS:")
    print("=" * 60)
    for r in recommended:
        print(f"\n📌 {r['extracted'].get('title')} | Score: {r['score']}/10")
        print(f"🔗 {r['link']}")
        print(f"💰 Stipend: {r['stipend']} | ⏰ Deadline: {r['deadline']}")
        if r["telegram_message"]:
            print(f"\n📱 Telegram Message:\n{r['telegram_message']}")
        print("-" * 40)