"""
formatter.py — Formats job/hackathon dicts into Telegram-ready Markdown strings.
Keeps messages under Telegram's 4096-char limit by chunking if needed.
"""

MAX_MSG_LEN = 4000  # safe limit under Telegram's 4096


def format_job(job: dict) -> str:
    """Format a single job listing."""
    title    = job.get("title", "Untitled")
    company  = job.get("company", "Unknown Company")
    location = job.get("location", "Remote / Not specified")
    stipend  = job.get("stipend", "Not disclosed")
    deadline = job.get("deadline", "Rolling")
    link     = job.get("link", "#")
    tags     = job.get("tags", [])

    tag_line = "  ".join([f"`{t}`" for t in tags]) if tags else ""

    return (
        f"💼 *{title}*\n"
        f"🏢 {company}\n"
        f"📍 {location}\n"
        f"💰 {stipend}\n"
        f"⏰ Deadline: {deadline}\n"
        f"{tag_line}\n"
        f"🔗 [Apply Now]({link})\n"
    )


def format_hackathon(hack: dict) -> str:
    """Format a single hackathon listing."""
    name      = hack.get("name", "Untitled")
    organizer = hack.get("organizer", "Unknown")
    mode      = hack.get("mode", "Online")
    prize     = hack.get("prize", "Not disclosed")
    deadline  = hack.get("deadline", "TBA")
    link      = hack.get("link", "#")
    tags      = hack.get("tags", [])

    tag_line = "  ".join([f"`{t}`" for t in tags]) if tags else ""

    return (
        f"🏆 *{name}*\n"
        f"🎙️ {organizer}\n"
        f"💻 Mode: {mode}\n"
        f"🎁 Prize: {prize}\n"
        f"⏰ Deadline: {deadline}\n"
        f"{tag_line}\n"
        f"🔗 [Register Now]({link})\n"
    )


def build_jobs_message(jobs: list) -> list[str]:
    """Returns a list of message strings (chunked) for all jobs."""
    header = "🎯 *Today's Internship Picks — CareerScout AI*\n\n"
    return _chunk_messages(header, jobs, format_job)


def build_hackathons_message(hacks: list) -> list[str]:
    """Returns a list of message strings (chunked) for all hackathons."""
    header = "🏆 *Upcoming Hackathons — CareerScout AI*\n\n"
    return _chunk_messages(header, hacks, format_hackathon)


def _chunk_messages(header: str, items: list, formatter) -> list[str]:
    """Chunk a list of items into Telegram-safe message blocks."""
    if not items:
        return [header + "_No results found right now. Check back tomorrow!_"]

    chunks = []
    current = header

    for i, item in enumerate(items, 1):
        block = f"*#{i}*\n" + formatter(item) + "─" * 30 + "\n\n"
        if len(current) + len(block) > MAX_MSG_LEN:
            chunks.append(current)
            current = block
        else:
            current += block

    if current:
        chunks.append(current)

    return chunks
