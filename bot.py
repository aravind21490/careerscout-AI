
"""
bot.py — CareerScout AI Telegram Bot
Handles all user-facing commands. Run with: python bot.py
"""

import os
import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from db import (
    init_db, save_subscriber, remove_subscriber,
    is_subscribed, get_preferences, save_preferences, subscriber_count
)
from formatter import build_jobs_message, build_hackathons_message

# ── Load token ────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set.")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ── Helpers ───────────────────────────────────────────────────────────────────

def send_chunks(chat_id, chunks: list[str]):
    """Send a list of chunked messages safely."""
    for chunk in chunks:
        try:
            bot.send_message(chat_id, chunk, parse_mode="Markdown",
                             disable_web_page_preview=True)
        except Exception as e:
            print(f"[BOT] Failed to send chunk to {chat_id}: {e}")


def get_jobs_data():
    try:
        from scraper import scrape_unstop
        return scrape_unstop()
    except ImportError:
        # Demo data — replace with your actual scraper
        return [
            {
                "title": "Software Engineer Intern",
                "company": "Google",
                "location": "Bangalore / Remote",
                "stipend": "₹80,000/month",
                "deadline": "30 Apr 2025",
                "link": "https://careers.google.com",
                "tags": ["Python", "ML", "2025"]
            },
            {
                "title": "Product Management Intern",
                "company": "Flipkart",
                "location": "Bangalore",
                "stipend": "₹50,000/month",
                "deadline": "15 May 2025",
                "link": "https://flipkartcareers.com",
                "tags": ["Product", "Analytics"]
            }
        ]


def get_hackathons_data():
    """Import your hackathon scraper here."""
    try:
        from scraper import fetch_all_hackathons
        return fetch_all_hackathons()
    except ImportError:
        return [
            {
                "name": "Smart India Hackathon 2025",
                "organizer": "Govt. of India",
                "mode": "Hybrid",
                "prize": "₹1,00,000",
                "deadline": "10 May 2025",
                "link": "https://sih.gov.in",
                "tags": ["AI", "Social Impact"]
            }
        ]


# ── Command Handlers ───────────────────────────────────────────────────────────

@bot.message_handler(commands=["start"])
def cmd_start(msg: Message):
    name = msg.from_user.first_name or "there"
    text = (
        f"👋 Hey *{name}!* Welcome to *CareerScout AI* 🚀\n\n"
        "I hunt down the best internships & hackathons daily using AI — "
        "so you don't have to.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "*📋 Commands*\n"
        "/jobs          — Latest AI-filtered internships\n"
        "/hackathons    — Upcoming hackathons\n"
        "/subscribe     — Get daily updates automatically\n"
        "/unsubscribe   — Stop daily updates\n"
        "/filter        — Set your domain preferences\n"
        "/status        — Your subscription status\n"
        "/help          — Full guide\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Start with /jobs to see today's listings! 🎯"
    )
    bot.send_message(msg.chat.id, text)


@bot.message_handler(commands=["help"])
def cmd_help(msg: Message):
    text = (
        "🤖 *CareerScout AI — Help Guide*\n\n"
        "*How it works:*\n"
        "I scrape Unstop, Internshala, LinkedIn & more every day, "
        "then use Groq AI to filter only the best matches.\n\n"
        "*Commands:*\n"
        "• /jobs — Top internships (AI filtered)\n"
        "• /hackathons — Live hackathon listings\n"
        "• /subscribe — Daily 10:30 AM IST digest\n"
        "• /unsubscribe — Pause updates\n"
        "• /filter — Set domain (ML, Web, PM, etc.)\n"
        "• /status — See your preferences\n\n"
        "*Tips:*\n"
        "• Use /filter to get more relevant results\n"
        "• Listings refresh every 24 hours\n"
        "• Share this bot: @YourBotUsername\n\n"
        "_Built by @YourHandle with ❤️_"
    )
    bot.send_message(msg.chat.id, text)


@bot.message_handler(commands=["jobs"])
def cmd_jobs(msg: Message):
    bot.send_message(msg.chat.id, "🔍 Fetching today's internships...")
    jobs = get_jobs_data()
    chunks = build_jobs_message(jobs)
    send_chunks(msg.chat.id, chunks)
    bot.send_message(
        msg.chat.id,
        f"✅ Found *{len(jobs)}* listings today!\n\n"
        "_Use /subscribe to get this daily at 10:30 AM IST_ 🔔"
    )


@bot.message_handler(commands=["hackathons"])
def cmd_hackathons(msg: Message):
    bot.send_message(msg.chat.id, "🔍 Fetching hackathons...")
    hacks = get_hackathons_data()
    chunks = build_hackathons_message(hacks)
    send_chunks(msg.chat.id, chunks)


@bot.message_handler(commands=["subscribe"])
def cmd_subscribe(msg: Message):
    user = msg.from_user
    if is_subscribed(user.id):
        bot.send_message(msg.chat.id,
            "✅ You're already subscribed!\n"
            "You'll get daily updates at *10:30 AM IST*.\n\n"
            "Use /unsubscribe to stop.")
        return

    save_subscriber(user.id, user.username, user.first_name)
    count = subscriber_count()
    bot.send_message(msg.chat.id,
        f"🎉 *Subscribed successfully!*\n\n"
        f"You'll receive daily internship & hackathon digests at *10:30 AM IST*.\n\n"
        f"👥 You're subscriber *#{count}*!\n\n"
        f"_Use /filter to personalise your results_ ⚙️")


@bot.message_handler(commands=["unsubscribe"])
def cmd_unsubscribe(msg: Message):
    if not is_subscribed(msg.from_user.id):
        bot.send_message(msg.chat.id, "ℹ️ You're not subscribed yet. Use /subscribe to start.")
        return

    remove_subscriber(msg.from_user.id)
    bot.send_message(msg.chat.id,
        "😢 You've been *unsubscribed*.\n\n"
        "You won't receive daily updates anymore.\n"
        "Use /subscribe anytime to come back!")


@bot.message_handler(commands=["filter"])
def cmd_filter(msg: Message):
    markup = InlineKeyboardMarkup(row_width=3)
    domains = ["ML/AI", "Web Dev", "App Dev", "Data Science",
               "Product", "Design", "DevOps", "Cybersecurity", "All"]
    buttons = [InlineKeyboardButton(d, callback_data=f"domain:{d}") for d in domains]
    markup.add(*buttons)
    bot.send_message(msg.chat.id,
        "⚙️ *Set Your Domain Preference*\n\n"
        "I'll prioritise listings matching your domain:",
        reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("domain:"))
def handle_domain_filter(call):
    domain = call.data.split(":")[1]
    prefs = get_preferences(call.from_user.id)
    prefs["domain"] = domain
    save_preferences(call.from_user.id, prefs)
    bot.answer_callback_query(call.id, f"✅ Domain set to {domain}")
    bot.edit_message_text(
        f"✅ Preference saved: *{domain}*\n\n"
        "_Your next /jobs results will be filtered for this domain._",
        call.message.chat.id,
        call.message.message_id
    )


@bot.message_handler(commands=["status"])
def cmd_status(msg: Message):
    uid = msg.from_user.id
    subscribed = is_subscribed(uid)
    prefs = get_preferences(uid)
    domain = prefs.get("domain", "All (not set)")

    status_icon = "✅ Active" if subscribed else "❌ Not subscribed"
    text = (
        f"📊 *Your CareerScout Status*\n\n"
        f"Subscription: {status_icon}\n"
        f"Domain filter: `{domain}`\n"
        f"User ID: `{uid}`\n\n"
        f"_Use /filter to change domain | /subscribe to activate_"
    )
    bot.send_message(msg.chat.id, text)


@bot.message_handler(func=lambda m: True)
def fallback(msg: Message):
    bot.send_message(msg.chat.id,
        "🤔 I didn't understand that. Try /help to see available commands.")


# ── Entry Point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("[BOT] CareerScout AI bot is running...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
