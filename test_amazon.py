from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.amazon.jobs/en/search?base_query=intern&category=software-development")
    page.wait_for_timeout(6000)
    soup = BeautifulSoup(page.content(), "html.parser")

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.text.strip()[:50]
        if text and len(text) > 5:
            print(f"{text} -> {href}")
    browser.close()