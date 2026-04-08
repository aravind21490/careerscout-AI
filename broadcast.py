"""
broadcast.py — Daily broadcast runner for CareerScout AI.
Called by GitHub Actions every morning.
"""

import os
import time
import telebot

from db import init_db, get_all_subscribers, subscriber_count
from formatter import build_jobs_message, build_hackathons_message

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set.")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")


def get_jobs():
    try:
        from scraper import fetch_all_jobs
        from filter import filter_jobs
        return filter_jobs(fetch_all_jobs())
    except ImportError:
        print("[BROADCAST] Warning: scraper/filter not found, using demo data.")
        return [
            {
                "title": "Software Engineer Intern",
                "company": "Google",
                "location": "Bangalore",
                "stipend": "₹80,000/month",
                "deadline": "30 Apr 2025",
                "link": "https://careers.google.com",
                "tags": ["Python", "ML"]
            }
        ]


def get_hackathons():
    try:
        from scraper import fetch_all_hackathons
        return fetch_all_hackathons()
    except ImportError:
        return []


def send_to_user(user_id: int, chunks: list[str]) -> bool:
    """Send all chunks to a user. Returns False if user blocked the bot."""
    for chunk in chunks:
        try:
            bot.send_message(
                user_id, chunk,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            time.sleep(0.05)  # respect Telegram rate limits (20 msg/s)
        except telebot.apihelper.ApiTelegramException as e:
            if "blocked" in str(e).lower() or "not found" in str(e).lower():
                print(f"[BROADCAST] User {user_id} has blocked the bot.")
                return False
            print(f"[BROADCAST] Error sending to {user_id}: {e}")
            return False
    return True


def broadcast():
    init_db()

    jobs      = get_jobs()
    hackathons = get_hackathons()
    subscribers = get_all_subscribers()
    total     = len(subscribers)

    print(f"[BROADCAST] Starting broadcast to {total} subscribers...")
    print(f"[BROADCAST] Jobs: {len(jobs)} | Hackathons: {len(hackathons)}")

    job_chunks  = build_jobs_message(jobs)
    hack_chunks = build_hackathons_message(hackathons) if hackathons else []

    success = 0
    failed  = 0

    for user_id in subscribers:
        ok = send_to_user(user_id, job_chunks)
        if ok and hack_chunks:
            send_to_user(user_id, hack_chunks)
        if ok:
            success += 1
        else:
            failed += 1

    # Summary log
    print(f"\n[BROADCAST] ✅ Done!")
    print(f"  Sent:   {success}/{total}")
    print(f"  Failed: {failed}/{total}")

    # Optional: send a summary to yourself (set ADMIN_CHAT_ID in secrets)
    admin_id = os.environ.get("ADMIN_CHAT_ID")
    if admin_id:
        try:
            bot.send_message(
                int(admin_id),
                f"📊 *Daily Broadcast Complete*\n\n"
                f"✅ Sent: {success}\n"
                f"❌ Failed: {failed}\n"
                f"📋 Jobs: {len(jobs)}\n"
                f"🏆 Hackathons: {len(hackathons)}\n"
                f"👥 Total subscribers: {total}",
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"[BROADCAST] Could not notify admin: {e}")


if __name__ == "__main__":
    broadcast()
