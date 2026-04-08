from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_unstop():
    print("Scraping Unstop...")
    internships = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://unstop.com/internship?quickApply=true&oppstatus=open")
        page.wait_for_timeout(8000)
        
        content = page.content()
        soup = BeautifulSoup(content, "html.parser")
        
        titles = soup.find_all("h3", class_="double-wrap")
        companies = soup.find_all("p", class_="single-wrap")
        
        for i in range(min(len(titles), len(companies), 10)):
            internship = {
                "title":        titles[i].text.strip(),
                "company":      companies[i].text.strip(),
                "location":     "India",
                "stipend":      "Not disclosed",
                "deadline":     "Rolling",
                "tags":         ["Unstop"],
                "source":       "Unstop",
                "link":         "https://unstop.com/internship",
                "date_scraped": datetime.now().strftime("%Y-%m-%d"),
            }
            internships.append(internship)
    
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
        print(f"  {r['title']} at {r['company']}")

