"""
CareerScout AI v2 — Scraper
============================
Sources: Internshala, Unstop, Devfolio, MLH, LinkedIn, Google Careers
Exports:  run_all_scrapers() → list of listing dicts
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json, time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


# ── Helper ───────────────────────────────────────────────────────────────────
def safe_get(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  ⚠️  GET failed for {url}: {e}")
        return None


# ── 1. Internshala ───────────────────────────────────────────────────────────
def scrape_internshala():
    print("🔍 Scraping Internshala...")
    results = []
    r = safe_get("https://internshala.com/internships/")
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_="internship_meta")
    for card in cards[:10]:
        try:
            title   = card.find("a", class_="job-title-href")
            title   = title.text.strip() if title else "Internship"
            company = card.find("p", class_="company-name")
            company = company.text.strip() if company else "Unknown"
            stipend = card.find("span", class_="stipend")
            stipend = stipend.text.strip() if stipend else "Not disclosed"
            loc     = card.find("div", class_="locations")
            loc     = loc.get_text(strip=True) if loc else "India"
            posted  = card.find("div", class_="status-info")
            posted  = posted.get_text(strip=True) if posted else None
            link_tag = card.find("a", class_="job-title-href")
            link    = "https://internshala.com" + link_tag["href"] if link_tag else "https://internshala.com/internships"
            results.append({
                "title": title,
                "description": f"{title} at {company}. Stipend: {stipend}. Location: {loc}.",
                "location": loc, "stipend": stipend, "deadline": posted,
                "source": "Internshala", "link": link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception as e:
            print(f"  Card error: {e}")
    print(f"  ✅ {len(results)} from Internshala")
    return results


# ── 2. Unstop ────────────────────────────────────────────────────────────────
def scrape_unstop():
    print("🔍 Scraping Unstop...")
    results = []
    r = safe_get("https://unstop.com/competitions")
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_="double-wrap")
    for card in cards[:10]:
        try:
            title = card.find("h3")
            title = title.text.strip() if title else "Opportunity"
            desc  = card.find("p", class_="single-wrap")
            desc  = desc.text.strip() if desc else ""
            link_tag = card.find_parent("a")
            link  = "https://unstop.com" + link_tag["href"] if link_tag and link_tag.get("href") else "https://unstop.com"
            results.append({
                "title": title, "description": desc or title,
                "location": "Online", "source": "Unstop", "link": link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception as e:
            print(f"  Card error: {e}")
    print(f"  ✅ {len(results)} from Unstop")
    return results


# ── 3. Devfolio ──────────────────────────────────────────────────────────────
def scrape_devfolio():
    print("🔍 Scraping Devfolio...")
    results = []
    r = safe_get("https://devfolio.co/hackathons")
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("a", href=True)
    seen = set()
    for tag in cards:
        href = tag.get("href", "")
        # Only actual hackathon subdomains, not nav links
        if "devfolio.co" not in href or href in seen:
            continue
        if any(x in href for x in ["/hackathons", "/api", "/u/", "/login"]):
            continue
        seen.add(href)
        title_el = tag.find(["h2", "h3", "h4"])
        title = title_el.text.strip() if title_el else href.split("//")[-1].split(".")[0].title()
        results.append({
            "title": title + " Hackathon",
            "description": f"Hackathon on Devfolio: {title}",
            "location": "Online", "source": "Devfolio", "link": href,
            "date_scraped": datetime.now().strftime("%Y-%m-%d"),
        })
        if len(results) >= 8:
            break
    print(f"  ✅ {len(results)} from Devfolio")
    return results


# ── 4. MLH (Major League Hacking) ────────────────────────────────────────────
def scrape_mlh():
    print("🔍 Scraping MLH...")
    results = []
    r = safe_get("https://mlh.io/seasons/2025/events")
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    events = soup.find_all("div", class_="event")
    for event in events[:10]:
        try:
            title = event.find("h3", class_="event-name")
            title = title.text.strip() if title else "MLH Hackathon"
            # Clean noise like emoji/icons from title
            title = " ".join(w for w in title.split() if w.isascii())
            date  = event.find("p", class_="event-date")
            date  = date.text.strip() if date else ""
            loc   = event.find("p", class_="event-location")
            loc   = loc.text.strip() if loc else "Online"
            link_tag = event.find("a", class_="event-link")
            link  = link_tag["href"] if link_tag else "https://mlh.io"
            results.append({
                "title": title or "MLH Hackathon",
                "description": f"MLH hackathon. Date: {date}. Location: {loc}",
                "location": loc, "deadline": date, "source": "MLH", "link": link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception as e:
            print(f"  Card error: {e}")
    print(f"  ✅ {len(results)} from MLH")
    return results


# ── 5. LinkedIn (public search, no auth) ─────────────────────────────────────
def scrape_linkedin():
    print("🔍 Scraping LinkedIn...")
    results = []
    url = "https://www.linkedin.com/jobs/search/?keywords=AI+ML+internship+India&location=India&f_E=1"
    r = safe_get(url)
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("div", class_="base-card")
    for card in cards[:10]:
        try:
            title   = card.find("h3", class_="base-search-card__title")
            title   = title.text.strip() if title else "Job"
            company = card.find("h4", class_="base-search-card__subtitle")
            company = company.text.strip() if company else "Company"
            loc     = card.find("span", class_="job-search-card__location")
            loc     = loc.text.strip() if loc else "India"
            link_tag = card.find("a", class_="base-card__full-link")
            link    = link_tag["href"].split("?")[0] if link_tag else "https://linkedin.com/jobs"
            results.append({
                "title": title,
                "description": f"{title} at {company}. Location: {loc}",
                "location": loc, "source": "LinkedIn", "link": link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception as e:
            print(f"  Card error: {e}")
    print(f"  ✅ {len(results)} from LinkedIn")
    return results


# ── 6. Google Careers ─────────────────────────────────────────────────────────
def scrape_google_careers():
    print("🔍 Scraping Google Careers...")
    results = []
    url = "https://careers.google.com/jobs/results/?q=intern&location=India"
    r = safe_get(url)
    if not r:
        return results
    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.find_all("li", class_="lLd3Je")
    for card in cards[:8]:
        try:
            title = card.find("h3", class_="QJPWVe")
            title = title.text.strip() if title else "Google Internship"
            loc   = card.find("span", class_="r0wTof")
            loc   = loc.text.strip() if loc else "India"
            link_tag = card.find("a")
            link  = "https://careers.google.com" + link_tag["href"] if link_tag and not link_tag["href"].startswith("http") else (link_tag["href"] if link_tag else "https://careers.google.com")
            results.append({
                "title": title, "description": f"{title} at Google. Location: {loc}",
                "location": loc, "source": "Google Careers", "link": link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        except Exception as e:
            print(f"  Card error: {e}")
    print(f"  ✅ {len(results)} from Google Careers")
    return results


# ── MAIN EXPORT ───────────────────────────────────────────────────────────────
def run_all_scrapers():
    """
    Runs all scrapers and returns a combined deduplicated list.
    This is the function imported by main_api.py.
    """
    print("\n" + "="*50)
    print("CareerScout AI — Running all scrapers")
    print("="*50)

    all_results = []
    scrapers = [
        scrape_internshala,
        scrape_unstop,
        scrape_devfolio,
        scrape_mlh,
        scrape_linkedin,
        scrape_google_careers,
    ]

    for scraper in scrapers:
        try:
            results = scraper()
            all_results.extend(results)
        except Exception as e:
            print(f"  ❌ Scraper failed: {e}")
        time.sleep(1)  # Be polite to servers

    # Deduplicate by link
    seen_links = set()
    unique = []
    for item in all_results:
        link = item.get("link", "")
        if link and link not in seen_links:
            seen_links.add(link)
            unique.append(item)

    print(f"\n🎯 Total: {len(unique)} unique listings from {len(scrapers)} sources")
    return unique


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    results = run_all_scrapers()
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Saved {len(results)} listings to results.json")
    print("\nSample:")
    for r in results[:3]:
        print(f"  [{r['source']}] {r['title']} — {r.get('location', 'N/A')}")