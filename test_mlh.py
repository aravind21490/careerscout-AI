from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://mlh.io/seasons/2026/events")
    page.wait_for_timeout(6000)
    soup = BeautifulSoup(page.content(), "html.parser")

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if (href.startswith("https://") and
            "mlh.io" not in href and
            "dev.to" not in href and
            "sponsor" not in href and
            "my.mlh" not in href):
            h3 = a.find("h3")
            print(f"H3: {h3.text.strip() if h3 else 'NONE'} -> {href.split('?')[0]}")
    browser.close()