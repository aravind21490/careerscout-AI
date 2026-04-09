import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://unstop.com/",
}

def scrape_unstop():
    print("Scraping Unstop via API...")
    internships = []

    try:
        url = "https://unstop.com/api/public/opportunity/search-result"
        params = {
            "opportunity": "internship",
            "quickApply": "true",
            "oppstatus": "open",
            "page": 1,
            "size": 10,
        }

        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        data = response.json()

        opportunities = data.get("data", {}).get("data", [])

        for item in opportunities:
            org = item.get("organisation", {})
            title = item.get("title", "Internship")
            company = org.get("name", "Unknown Company")
            city = item.get("city", "India")
            stipend_min = item.get("stipendMin", "")
            stipend_max = item.get("stipendMax", "")
            deadline = item.get("deadline", "Rolling")
            slug = item.get("seoUrl", "")
            link = f"https://unstop.com/{slug}" if slug else "https://unstop.com/internships"

            if stipend_min and stipend_max:
                stipend = f"₹{stipend_min}–{stipend_max}/month"
            elif stipend_min:
                stipend = f"₹{stipend_min}/month"
            else:
                stipend = "Not disclosed"

            if deadline and deadline != "Rolling":
                try:
                    deadline = datetime.strptime(deadline[:10], "%Y-%m-%d").strftime("%d %b %Y")
                except:
                    pass

            internship = {
                "title":        title,
                "company":      company,
                "location":     city or "India",
                "stipend":      stipend,
                "deadline":     deadline or "Rolling",
                "tags":         ["Unstop"],
                "source":       "Unstop",
                "link":         link,
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            }
            internships.append(internship)

        print(f"Scraped {len(internships)} internships from Unstop API.")

    except Exception as e:
        print(f"Unstop API error: {e}")
        internships = scrape_unstop_html()

    return internships


def scrape_unstop_html():
    print("Falling back to HTML scraping...")
    internships = []
    try:
        url = "https://unstop.com/internships"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        titles    = soup.find_all("h3", class_="double-wrap")
        companies = soup.find_all("p",  class_="single-wrap")

        for i in range(min(len(titles), len(companies), 10)):
            internships.append({
                "title":        titles[i].text.strip(),
                "company":      companies[i].text.strip(),
                "location":     "India",
                "stipend":      "Not disclosed",
                "deadline":     "Rolling",
                "tags":         ["Unstop"],
                "source":       "Unstop",
                "link":         "https://unstop.com/internships",
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            })
        print(f"HTML fallback scraped {len(internships)} internships.")
    except Exception as e:
        print(f"HTML fallback error: {e}")

    return internships


def save_results(internships):
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(internships, f, indent=2)
    print(f"Saved {len(internships)} internships to results.json")


if __name__ == "__main__":
    results = scrape_unstop()
    save_results(results)
    print("\nSample results:")
    for r in results[:3]:
        print(f"  {r['title']} at {r['company']} — {r['stipend']}")