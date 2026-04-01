from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from groq import Groq
from twilio.rest import Client
from dotenv import load_dotenv
import json
import os
from datetime import datetime

load_dotenv(override=True)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

def is_relevant(internship):
    prompt = f"""You are a filter for a job board. Decide if this internship or hackathon is relevant for a computer science or software engineering student.

Title: {internship['title']}
Company: {internship['company']}

Reply with only YES or NO."""

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content.strip().upper()
    return answer == "YES"

def scrape_unstop(page):
    print("Scraping Unstop...")
    internships = []
    try:
        page.goto("https://unstop.com/internship?quickApply=true&oppstatus=open")
        page.wait_for_timeout(8000)
        soup = BeautifulSoup(page.content(), "html.parser")

        # Get cards directly to keep title/company/link aligned
        cards = soup.find_all("a", href=True)
        listing_cards = [a for a in cards if a["href"].startswith("/internships/")]

        for card in listing_cards[:10]:
            title_tag = card.find("h3", class_="double-wrap")
            company_tag = card.find("p", class_="single-wrap")
            if title_tag and company_tag:
                internships.append({
                    "title": title_tag.text.strip(),
                    "company": company_tag.text.strip(),
                    "source": "Unstop",
                    "link": "https://unstop.com" + card["href"],
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"  Unstop error: {e}")
    print(f"  Found {len(internships)} listings")
    return internships

def scrape_devfolio(page):
    print("Scraping Devfolio...")
    hackathons = []
    try:
        page.goto("https://devfolio.co/hackathons/open")
        page.wait_for_timeout(12000)
        soup = BeautifulSoup(page.content(), "html.parser")

        # Real hackathon links are subdomains like hacktonix-26.devfolio.co
        seen = set()
        hackathon_links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if (href.endswith(".devfolio.co/") or href.endswith(".devfolio.co")) and href not in seen:
                seen.add(href)
                hackathon_links.append(href)

        titles = [h3.text.strip() for h3 in soup.find_all("h3")
                  if len(h3.text.strip()) > 3 and h3.text.strip() != "Applications open"]

        for i in range(min(len(titles), len(hackathon_links), 10)):
            hackathons.append({
                "title": titles[i],
                "company": "Devfolio",
                "source": "Devfolio",
                "link": hackathon_links[i],
                "date_scraped": datetime.now().strftime("%Y-%m-%d")
            })
    except Exception as e:
        print(f"  Devfolio error: {e}")
    print(f"  Found {len(hackathons)} listings")
    return hackathons

def scrape_google_careers(page):
    print("Scraping Google Careers...")
    jobs = []
    try:
        page.goto("https://careers.google.com/jobs/results/?category=SOFTWARE_ENGINEERING&employment_type=INTERN")
        page.wait_for_timeout(8000)
        soup = BeautifulSoup(page.content(), "html.parser")

        cards = soup.find_all("div", {"class": lambda c: c and "sMn82b" in c})
        for card in cards[:10]:
            title_tag = card.find("h3")
            link_tag = card.find("a", href=True)
            if title_tag and link_tag:
                jobs.append({
                    "title": title_tag.text.strip(),
                    "company": "Google",
                    "source": "Google Careers",
                    "link": "https://careers.google.com/" + link_tag["href"],  # ← fixed
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"  Google Careers error: {e}")
    print(f"  Found {len(jobs)} listings")
    return jobs

def scrape_microsoft_careers(page):
    print("Scraping Microsoft Careers...")
    jobs = []
    try:
        page.goto("https://careers.microsoft.com/v2/global/en/search.html?keywords=intern")
        page.wait_for_timeout(8000)
        soup = BeautifulSoup(page.content(), "html.parser")

        cards = soup.find_all("a", href=True)
        seen = set()
        for card in cards:
            href = card.get("href", "")
            if "/job/" in href and href not in seen:
                seen.add(href)
                title_tag = card.find("h2") or card.find("span")
                title = title_tag.text.strip() if title_tag else "Microsoft Internship"
                jobs.append({
                    "title": title,
                    "company": "Microsoft",
                    "source": "Microsoft Careers",
                    "link": href if href.startswith("http") else "https://careers.microsoft.com" + href,
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
                if len(jobs) >= 10:
                    break
    except Exception as e:
        print(f"  Microsoft Careers error: {e}")
    print(f"  Found {len(jobs)} listings")
    return jobs

def scrape_linkedin(page):
    print("Scraping LinkedIn...")
    jobs = []
    try:
        page.goto("https://www.linkedin.com/jobs/search/?keywords=software+intern&location=India&f_E=1")
        page.wait_for_timeout(8000)
        soup = BeautifulSoup(page.content(), "html.parser")

        cards = soup.find_all("div", class_="base-card")
        for card in cards[:10]:
            title_tag = card.find("h3")
            company_tag = card.find("h4")
            link_tag = card.find("a", href=True)
            if title_tag and company_tag:
                jobs.append({
                    "title": title_tag.text.strip(),
                    "company": company_tag.text.strip(),
                    "source": "LinkedIn",
                    "link": link_tag["href"].split("?")[0] if link_tag else "https://linkedin.com/jobs",
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
    except Exception as e:
        print(f"  LinkedIn error: {e}")
    print(f"  Found {len(jobs)} listings")
    return jobs

def scrape_mlh(page):
    print("Scraping MLH...")
    hackathons = []
    try:
        page.goto("https://mlh.io/seasons/2026/events")
        page.wait_for_timeout(6000)
        soup = BeautifulSoup(page.content(), "html.parser")

        skip = {"mlh.io", "dev.to", "sponsor", "my.mlh", "instagram",
                "tiktok", "linkedin", "youtube", "techtogether", "hackp.ac",
                "mlh.com", "events/prizes", "fellowship"}

        nav_words = {"attend", "prizes & freebies", "sign in", "for businesses",
                     "upcoming hackathons", "past hackathons", "about", "apply", "sponsor"}

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if not href.startswith("https://"):
                continue
            if any(s in href for s in skip):
                continue

            text = a.text.strip()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = None
            for line in lines:
                if (len(line) > 5 and
                    line.lower() not in nav_words and
                    "APR" not in line and
                    "MAY" not in line and
                    "JUN" not in line and
                    "In-Person" not in line and
                    "Online" not in line):
                    title = line
                    break

            if title:
                hackathons.append({
                    "title": title,
                    "company": "MLH",
                    "source": "MLH",
                    "link": href.split("?")[0],
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
                if len(hackathons) >= 10:
                    break
    except Exception as e:
        print(f"  MLH error: {e}")
    print(f"  Found {len(hackathons)} listings")
    return hackathons

def scrape_amazon(page):
    print("Scraping Amazon Jobs...")
    jobs = []
    try:
        page.goto("https://www.amazon.jobs/en/search?base_query=intern&category=software-development")
        page.wait_for_timeout(6000)
        soup = BeautifulSoup(page.content(), "html.parser")

        seen = set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            text = a.text.strip()
            if ("/en/jobs/" in href and 
                "Read more" not in text and 
                href not in seen and
                len(text) > 3):
                seen.add(href)
                jobs.append({
                    "title": text,
                    "company": "Amazon",
                    "source": "Amazon Jobs",
                    "link": "https://www.amazon.jobs" + href,
                    "date_scraped": datetime.now().strftime("%Y-%m-%d")
                })
                if len(jobs) >= 10:
                    break
    except Exception as e:
        print(f"  Amazon error: {e}")
    print(f"  Found {len(jobs)} listings")
    return jobs

def scrape_all():
    all_listings = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        all_listings += scrape_unstop(page)
        all_listings += scrape_devfolio(page)
        all_listings += scrape_google_careers(page)
        all_listings += scrape_microsoft_careers(page)
        all_listings += scrape_linkedin(page)
        all_listings += scrape_mlh(page)
        all_listings += scrape_amazon(page)  # ← new

        browser.close()
    return all_listings

def filter_internships(internships):
    print("\nFiltering with AI...")
    filtered = []
    for item in internships:
        if len(filtered) >= 15:  # ← cap at 15 to stay under Twilio limit
            break
        relevant = is_relevant(item)
        status = "✅ RELEVANT" if relevant else "❌ SKIPPED"
        print(f"  {status}: {item['title']} at {item['company']} [{item['source']}]")
        if relevant:
            filtered.append(item)
    return filtered

def send_whatsapp(internships):
    if not internships:
        print("No relevant internships to send.")
        return

    chunks = [internships[i:i+5] for i in range(0, len(internships), 5)]

    for idx, chunk in enumerate(chunks):
        message = f"🎯 *CareerScout AI ({idx+1}/{len(chunks)})*\n\n"
        for item in chunk:
            message += f"*{item['company']} is hiring!*\n"
            message += f"Role: {item['title'][:50]}\n"
            message += f"Source: {item['source']}\n"
            message += f"Apply here:\n{item['link']}\n\n"

        twilio_client.messages.create(
            from_=os.getenv("TWILIO_WHATSAPP_FROM"),
            to=os.getenv("TWILIO_WHATSAPP_TO"),
            body=message
        )
        print(f"✅ Sent batch {idx+1}/{len(chunks)} to WhatsApp!")
        
def save_results(internships):
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(internships, f, indent=2)
    print(f"Saved {len(internships)} filtered internships to results.json")
    

if __name__ == "__main__":
    results = scrape_all()
    print(f"\nTotal scraped: {len(results)} listings")
    filtered = filter_internships(results)
    save_results(filtered)
    send_whatsapp(filtered)
    print(f"\n✅ Done! {len(filtered)} relevant listings sent to WhatsApp.")