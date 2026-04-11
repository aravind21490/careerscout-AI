import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_unstop():
    print("Scraping Internshala...")
    internships = []
    try:
        url = "https://internshala.com/internships/ajax"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.find_all("div", class_="internship_meta")
        for card in cards[:10]:
            try:
                title    = card.find("h3").text.strip() if card.find("h3") else "Internship"
                company  = card.find("p", class_="company-name").text.strip() if card.find("p", class_="company-name") else "Unknown"
                stipend  = card.find("span", class_="stipend").text.strip() if card.find("span", class_="stipend") else "Not disclosed"
                loc      = card.find("a", class_="location_link")
                location = loc.text.strip() if loc else "India"
                link_tag = card.find_previous("a", class_="view_detail_button")
                link     = "https://internshala.com" + link_tag["href"] if link_tag else "https://internshala.com/internships"
                internships.append({
                    "title": title, "company": company, "location": location,
                    "stipend": stipend, "deadline": "Rolling", "tags": ["Internshala"],
                    "source": "Internshala", "link": link,
                    "date_scraped": datetime.now().strftime("%Y-%m-%d"),
                })
            except Exception as e:
                print(f"Card error: {e}")
        print(f"Scraped {len(internships)} internships.")
    except Exception as e:
        print(f"Scrape error: {e}")
    return internships

def save_results(internships):
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(internships, f, indent=2)

if __name__ == "__main__":
    results = scrape_unstop()
    save_results(results)
    for r in results[:3]:
        print(f"  {r['title']} at {r['company']} — {r['stipend']}")