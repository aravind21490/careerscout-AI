"""
CareerScout AI v2 — FastAPI Backend
=====================================
Routes:
  GET  /jobs               → fetch all filtered jobs from Supabase
  POST /run                → trigger scrape + AI filter pipeline manually
  POST /resume             → upload resume, get ATS score + keywords
  GET  /health             → health check
  POST /telegram/webhook   → Telegram webhook (handles all bot commands)

Telegram Commands:
  /start       → subscribe + welcome message
  /subscribe   → same as /start
  /unsubscribe → remove from subscribers
  /stop        → same as /unsubscribe
  /jobs        → latest 5 internships
  /hackathons  → latest 5 hackathons
  /filter      → set domain preference (AI/ML, Web Dev, etc.)
  /status      → subscriber count
  /help        → full guide

Run locally:
  pip install fastapi uvicorn supabase groq pymupdf python-dotenv
  uvicorn main_api:app --reload --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os, json, tempfile, requests
from datetime import datetime

load_dotenv(override=True)

# ── Supabase client ──────────────────────────────────────────────────────────
from supabase import create_client
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# ── Groq client ──────────────────────────────────────────────────────────────
from groq import Groq
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.1-8b-instant"

# ── Telegram config ──────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="CareerScout AI",
    description="AI-powered internship & hackathon finder",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════════════════════
# TELEGRAM HELPERS
# ════════════════════════════════════════════════════════════════════════════
def send_telegram(chat_id: str, text: str):
    """Send a plain text message to a single Telegram chat_id."""
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        return r.ok
    except Exception as e:
        print(f"  ❌ Telegram send failed for {chat_id}: {e}")
        return False


def send_telegram_keyboard(chat_id: str, text: str, keyboard: list):
    """Send a message with inline keyboard buttons."""
    try:
        r = requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": keyboard
            }
        }, timeout=10)
        return r.ok
    except Exception as e:
        print(f"  ❌ Telegram keyboard send failed for {chat_id}: {e}")
        return False


def get_all_subscribers() -> list:
    """
    Fetch all subscribers from Supabase with their domain preference.
    Returns list of dicts: [{chat_id, domain}, ...]
    """
    subscribers = []
    own_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if own_id:
        subscribers.append({"chat_id": own_id, "domain": "All"})
    try:
        result = supabase.table("telegram_users").select("chat_id, domain").execute()
        own_ids = {s["chat_id"] for s in subscribers}
        for row in result.data:
            if str(row["chat_id"]) not in own_ids:
                subscribers.append({
                    "chat_id": str(row["chat_id"]),
                    "domain": row.get("domain") or "All"
                })
    except Exception as e:
        print(f"  ⚠️  Could not fetch telegram_users: {e}")
    return subscribers


def smart_broadcast(job_domain: str, message: str):
    """
    ✅ Send job only to subscribers whose domain matches.
    Users with domain=All receive everything.
    Users with a specific domain only receive matching jobs.
    """
    subscribers = get_all_subscribers()
    print(f"  📢 Smart broadcast [{job_domain}] to {len(subscribers)} subscribers...")
    success = 0
    skipped = 0
    for sub in subscribers:
        user_domain = sub.get("domain", "All")
        if user_domain == "All" or user_domain == job_domain:
            if send_telegram(sub["chat_id"], message):
                success += 1
        else:
            skipped += 1
    print(f"  ✅ Sent: {success} | Skipped (domain mismatch): {skipped}")
    return success


def subscribe_user(chat_id: str, first_name: str, domain: str = "All"):
    """Save or update user in telegram_users table."""
    supabase.table("telegram_users").upsert({
        "chat_id": chat_id,
        "first_name": first_name,
        "domain": domain,
        "joined_at": datetime.utcnow().isoformat(),
    }, on_conflict="chat_id").execute()


def get_user_domain(chat_id: str) -> str:
    """Get user's preferred domain filter."""
    try:
        result = supabase.table("telegram_users").select("domain").eq("chat_id", chat_id).execute()
        if result.data:
            return result.data[0].get("domain", "All")
    except:
        pass
    return "All"


def format_job_card(job: dict) -> str:
    """Format a single job into a Telegram message card."""
    title    = job.get("title", "Unknown")
    domain   = job.get("domain", "")
    location = job.get("location", "")
    stipend  = job.get("stipend") or "Not disclosed"
    deadline = job.get("deadline") or "Not specified"
    score    = job.get("score", 0)
    link     = job.get("link", "")
    source   = job.get("source", "")

    return (
        f"📌 <b>{title}</b>\n"
        f"🏷️ {domain} | 📍 {location}\n"
        f"💰 {stipend}\n"
        f"⏰ {deadline}\n"
        f"⭐ Match Score: {score}/10 | 🔎 {source}\n"
        f"🔗 <a href='{link}'>Apply Now</a>"
    )


# ════════════════════════════════════════════════════════════════════════════
# COMMAND HANDLERS
# ════════════════════════════════════════════════════════════════════════════
def handle_start(chat_id: str, first_name: str):
    try:
        subscribe_user(chat_id, first_name)
        print(f"  ✅ Subscriber saved: {first_name} ({chat_id})")
    except Exception as e:
        print(f"  ⚠️  Could not save user: {e}")

    send_telegram(chat_id, (
        f"👋 Hey <b>{first_name}</b>! Welcome to <b>CareerScout AI</b> 🚀\n"
        f"I hunt down the best internships & hackathons daily using AI — so you don't have to.\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Commands</b>\n"
        f"/jobs          — Latest AI-filtered internships\n"
        f"/hackathons    — Upcoming hackathons\n"
        f"/subscribe     — Get daily updates automatically\n"
        f"/unsubscribe   — Stop daily updates\n"
        f"/filter        — Set your domain preferences\n"
        f"/status        — Your subscription status\n"
        f"/help          — Full guide\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Start with /jobs to see today's listings! 🎯"
    ))


def handle_subscribe(chat_id: str, first_name: str):
    try:
        subscribe_user(chat_id, first_name)
    except Exception as e:
        print(f"  ⚠️  Could not save user: {e}")
    send_telegram(chat_id, (
        f"✅ <b>{first_name}</b>, you're now subscribed to CareerScout AI!\n"
        f"You'll get daily AI-filtered internships & hackathons.\n\n"
        f"Use /filter to set your domain preference.\n"
        f"Use /unsubscribe to stop anytime."
    ))


def handle_unsubscribe(chat_id: str):
    try:
        supabase.table("telegram_users").delete().eq("chat_id", chat_id).execute()
    except:
        pass
    send_telegram(chat_id, "❌ You've been unsubscribed. Send /start anytime to resubscribe.")


def handle_jobs(chat_id: str):
    send_telegram(chat_id, "🔍 Fetching latest internships for you...")
    try:
        domain = get_user_domain(chat_id)
        query = supabase.table("jobs") \
            .select("*") \
            .eq("recommended", True) \
            .eq("type", "internship") \
            .order("score", desc=True) \
            .limit(5)

        if domain and domain != "All":
            query = query.eq("domain", domain)

        result = query.execute()
        jobs = result.data

        if not jobs:
            send_telegram(chat_id, (
                "😕 No internships found right now.\n"
                "Try /filter to change your domain, or check back after the daily pipeline runs!"
            ))
            return

        send_telegram(chat_id, f"🎯 <b>Top {len(jobs)} Internships</b>\n━━━━━━━━━━━━━━━━━━━━━")
        for job in jobs:
            send_telegram(chat_id, format_job_card(job))
        send_telegram(chat_id, "✅ Done! Use /hackathons to see hackathons.")

    except Exception as e:
        print(f"  ❌ handle_jobs error: {e}")
        send_telegram(chat_id, "❌ Something went wrong. Please try again later.")


def handle_hackathons(chat_id: str):
    send_telegram(chat_id, "🔍 Fetching latest hackathons for you...")
    try:
        result = supabase.table("jobs") \
            .select("*") \
            .eq("recommended", True) \
            .eq("type", "hackathon") \
            .order("score", desc=True) \
            .limit(5) \
            .execute()

        jobs = result.data

        if not jobs:
            send_telegram(chat_id, (
                "😕 No hackathons found right now.\n"
                "Check back after the daily pipeline runs!"
            ))
            return

        send_telegram(chat_id, f"🏆 <b>Top {len(jobs)} Hackathons</b>\n━━━━━━━━━━━━━━━━━━━━━")
        for job in jobs:
            send_telegram(chat_id, format_job_card(job))
        send_telegram(chat_id, "✅ Done! Use /jobs to see internships.")

    except Exception as e:
        print(f"  ❌ handle_hackathons error: {e}")
        send_telegram(chat_id, "❌ Something went wrong. Please try again later.")


def handle_filter(chat_id: str):
    keyboard = [
        [
            {"text": "🤖 AI/ML",          "callback_data": "filter_AI/ML"},
            {"text": "🌐 Web Dev",         "callback_data": "filter_Web Dev"},
        ],
        [
            {"text": "📊 Data Science",    "callback_data": "filter_Data Science"},
            {"text": "🔒 Cybersecurity",   "callback_data": "filter_Cybersecurity"},
        ],
        [
            {"text": "☁️ Cloud",           "callback_data": "filter_Cloud"},
            {"text": "🌍 All Domains",     "callback_data": "filter_All"},
        ],
    ]
    send_telegram_keyboard(
        chat_id,
        "🎯 <b>Choose your domain preference:</b>\nYou'll only receive listings matching this domain.",
        keyboard
    )


def handle_filter_callback(chat_id: str, domain: str):
    try:
        supabase.table("telegram_users").update({
            "domain": domain
        }).eq("chat_id", chat_id).execute()
        send_telegram(chat_id, (
            f"✅ Filter set to <b>{domain}</b>!\n"
            f"You'll now receive only {domain} listings.\n\n"
            f"Use /jobs to see current listings with your new filter."
        ))
    except Exception as e:
        print(f"  ❌ filter save error: {e}")
        send_telegram(chat_id, "❌ Could not save filter. Please try again.")


def handle_status(chat_id: str):
    count = len(get_all_subscribers())
    domain = get_user_domain(chat_id)
    send_telegram(chat_id, (
        f"📊 <b>CareerScout AI Status</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total subscribers: <b>{count}</b>\n"
        f"🎯 Your domain filter: <b>{domain}</b>\n"
        f"✅ You are subscribed\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Use /filter to change your domain preference."
    ))


def handle_help(chat_id: str):
    send_telegram(chat_id, (
        f"🤖 <b>CareerScout AI — Help Guide</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"I scrape 6+ platforms daily (Internshala, Unstop, LinkedIn, Devfolio, MLH, Google) "
        f"and use AI to filter only the best matches for student developers.\n\n"
        f"📋 <b>Commands</b>\n"
        f"/jobs          — Latest AI-filtered internships\n"
        f"/hackathons    — Upcoming hackathons\n"
        f"/subscribe     — Get daily updates automatically\n"
        f"/unsubscribe   — Stop daily updates\n"
        f"/filter        — Set your domain preferences\n"
        f"/status        — Your subscription status\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Pipeline runs daily at 4 AM UTC\n"
        f"Built with ❤️ using Python, Groq AI & FastAPI"
    ))


# ════════════════════════════════════════════════════════════════════════════
# ROUTE — POST /telegram/webhook
# ════════════════════════════════════════════════════════════════════════════
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()

    # ── Handle inline keyboard button presses (filter selection) ────────────
    if "callback_query" in body:
        cb         = body["callback_query"]
        chat_id    = str(cb["message"]["chat"]["id"])
        data       = cb.get("data", "")

        if data.startswith("filter_"):
            domain = data.replace("filter_", "")
            handle_filter_callback(chat_id, domain)

        # Answer callback to remove loading spinner on button
        requests.post(f"{TELEGRAM_API}/answerCallbackQuery", json={
            "callback_query_id": cb["id"]
        }, timeout=5)
        return {"ok": True}

    # ── Handle regular text messages ─────────────────────────────────────────
    message    = body.get("message", {})
    chat_id    = str(message.get("chat", {}).get("id", ""))
    text       = message.get("text", "").strip()
    first_name = message.get("chat", {}).get("first_name", "there")

    if not chat_id or not text:
        return {"ok": True}

    print(f"  📩 [{first_name}] {text}")

    if text == "/start":
        handle_start(chat_id, first_name)
    elif text == "/subscribe":
        handle_subscribe(chat_id, first_name)
    elif text in ["/stop", "/unsubscribe"]:
        handle_unsubscribe(chat_id)
    elif text == "/jobs":
        handle_jobs(chat_id)
    elif text == "/hackathons":
        handle_hackathons(chat_id)
    elif text == "/filter":
        handle_filter(chat_id)
    elif text == "/status":
        handle_status(chat_id)
    elif text == "/help":
        handle_help(chat_id)
    else:
        send_telegram(chat_id, (
            "🤔 I didn't understand that. Here's what I can do:\n\n"
            "/jobs — Latest internships\n"
            "/hackathons — Latest hackathons\n"
            "/filter — Set domain preference\n"
            "/status — Your subscription status\n"
            "/help — Full guide"
        ))

    return {"ok": True}


# ════════════════════════════════════════════════════════════════════════════
# ROUTE 1 — GET /jobs
# ════════════════════════════════════════════════════════════════════════════
@app.get("/jobs")
def get_jobs(limit: int = 20, type: str = None):
    query = supabase.table("jobs") \
        .select("*") \
        .eq("recommended", True) \
        .order("score", desc=True) \
        .limit(limit)

    if type:
        query = query.eq("type", type)

    result = query.execute()
    return {
        "count": len(result.data),
        "jobs": result.data
    }


# ════════════════════════════════════════════════════════════════════════════
# ROUTE 2 — POST /run
# ════════════════════════════════════════════════════════════════════════════
@app.post("/run")
def run_pipeline():
    from scraper import run_all_scrapers
    from ai_filter_v2 import batch_chain_filter

    print("🚀 Pipeline started...")

    listings = run_all_scrapers()
    print(f"📦 Scraped {len(listings)} listings")

    existing = supabase.table("jobs").select("link").execute()
    existing_links = {row["link"] for row in existing.data}
    new_listings = [l for l in listings if l.get("link") not in existing_links]
    print(f"🔍 {len(new_listings)} new listings after dedup")

    recommended = batch_chain_filter(new_listings)
    print(f"🤖 {len(recommended)} recommended by AI chain")

    saved = 0
    for r in recommended:
        job_domain = r["extracted"].get("domain", "")
        row = {
            "title":        r["extracted"].get("title", ""),
            "type":         r["extracted"].get("type", "unknown"),
            "domain":       job_domain,
            "skills":       r["extracted"].get("skills_required", []),
            "location":     r["extracted"].get("location", ""),
            "stipend":      r["extracted"].get("stipend_or_prize") or r.get("stipend"),
            "deadline":     r["extracted"].get("deadline") or r.get("deadline"),
            "score":        r["score"],
            "recommended":  True,
            "reasoning":    r["scoring"].get("reasoning", ""),
            "link":         r.get("link", ""),
            "source":       r.get("source", ""),
            "created_at":   datetime.utcnow().isoformat(),
            "telegram_msg": r.get("telegram_message", ""),
        }
        supabase.table("jobs").insert(row).execute()
        saved += 1

        if r.get("telegram_message"):
            msg = r["telegram_message"]
            link = r.get("link", "")
            if link:
                msg += f"\n\n🔗 <a href='{link}'>Apply Now</a>"
            smart_broadcast(job_domain, msg)

    return {
        "status": "success",
        "scraped": len(listings),
        "new": len(new_listings),
        "recommended": len(recommended),
        "saved": saved
    }


# ════════════════════════════════════════════════════════════════════════════
# ROUTE 3 — POST /resume
# ════════════════════════════════════════════════════════════════════════════
@app.post("/resume")
async def analyze_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files accepted")

    import fitz
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    doc = fitz.open(tmp_path)
    resume_text = " ".join(page.get_text() for page in doc)
    doc.close()
    os.unlink(tmp_path)

    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")

    system_prompt = """You are an ATS (Applicant Tracking System) expert and career coach.
Analyze resumes for tech internships and hackathons in India.
Always respond with ONLY valid JSON. No explanation, no markdown, no backticks.

JSON format:
{
  "ats_score": <integer 0-100>,
  "summary": "2-sentence overall assessment",
  "strong_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1", "keyword2"],
  "sections_found": ["Experience", "Projects", "Skills"],
  "sections_missing": ["Certifications", "Links"],
  "improvements": [
    {"priority": "high", "tip": "Add quantified achievements"},
    {"priority": "medium", "tip": "Include GitHub link"}
  ],
  "verdict": "strong | average | needs_work"
}"""

    user_prompt = f"""Analyze this resume for tech internship and hackathon applications in India.
Focus on: Python, ML, Web Dev, AI skills, project quality, and ATS compatibility.

Resume text:
{resume_text[:3000]}"""

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="AI response parse error")

    return result


# ════════════════════════════════════════════════════════════════════════════
# ROUTE 4 — GET /health
# ════════════════════════════════════════════════════════════════════════════
@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_api:app", host="0.0.0.0", port=8000, reload=True)