import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


# ── Helpers ────────────────────────────────────────────────────────────────

def accept_cookies(page):
    selectors = [
        "button#onetrust-accept-btn-handler",
        "button[data-testid='cookie-accept']",
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Accept Cookies')",
        "button:has-text('I Accept')",
        "button:has-text('Agree')",
        ".cookie-accept",
    ]
    for sel in selectors:
        try:
            page.click(sel, timeout=2000)
            page.wait_for_timeout(1000)
            return True
        except Exception:
            pass
    return False


def test_source(page, name, url, wait_for=None, accept_cookie=False, retries=2):
    """
    Navigate to url with automatic retry on network errors.
    Retries on: ERR_INTERNET_DISCONNECTED, ERR_CONNECTION_RESET,
                ERR_NAME_NOT_RESOLVED, interrupted navigation.
    """
    RETRY_KEYWORDS = [
        "ERR_INTERNET_DISCONNECTED",
        "ERR_CONNECTION_RESET",
        "ERR_NETWORK_CHANGED",
        "interrupted by another navigation",
    ]

    last_error = None
    for attempt in range(1, retries + 2):   # retries=2 → 3 attempts total
        try:
            page.goto(url, timeout=50000, wait_until="domcontentloaded")

            # Let redirects settle
            try:
                page.wait_for_url("**", timeout=10000)
            except Exception:
                pass

            # Wait for network to quiet down
            try:
                page.wait_for_load_state("networkidle", timeout=12000)
            except Exception:
                pass

            if accept_cookie:
                accept_cookies(page)
                page.wait_for_timeout(1500)

            page.wait_for_timeout(2000)

            if wait_for:
                try:
                    page.wait_for_selector(wait_for, timeout=8000)
                except Exception:
                    pass

            # ── Success ──
            print(f"\n=== {name} ===")
            print(f"Title: {page.title()[:60]}")
            soup = BeautifulSoup(page.content(), "html.parser")
            for tag in soup.find_all(['h2', 'h3'])[:4]:
                text = tag.text.strip()[:80]
                if text:
                    print(f"  → {text}")
            return   # done

        except Exception as e:
            err_str = str(e)
            last_error = err_str

            is_retryable = any(kw in err_str for kw in RETRY_KEYWORDS)

            if is_retryable and attempt <= retries:
                wait_secs = attempt * 5   # 5s, 10s back-off
                print(f"\n=== {name} === [attempt {attempt} failed — retrying in {wait_secs}s]")
                time.sleep(wait_secs)
                continue   # retry
            else:
                break      # non-retryable or out of retries

    print(f"\n=== {name} ===")
    print(f"  ERROR: {last_error[:100]}")


# ── Browser factory ────────────────────────────────────────────────────────

def make_browser(playwright):
    return playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-http2",
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ]
    )

STEALTH_JS = """
    Object.defineProperty(navigator, 'webdriver',  {get: () => undefined});
    Object.defineProperty(navigator, 'plugins',    {get: () => [1,2,3]});
    Object.defineProperty(navigator, 'languages',  {get: () => ['en-US','en']});
"""

CTX_ARGS = dict(
    user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    viewport={"width": 1280, "height": 720},
    locale="en-US",
    timezone_id="Asia/Kolkata",
    extra_http_headers={
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "DNT": "1",
    },
)

state = {}

def new_page(browser):
    if state.get("ctx"):
        try:
            state["ctx"].close()
        except Exception:
            pass
    ctx = browser.new_context(**CTX_ARGS)
    pg  = ctx.new_page()
    pg.add_init_script(STEALTH_JS)
    state["ctx"] = ctx
    return pg


# ── Main ───────────────────────────────────────────────────────────────────

with sync_playwright() as p:
    browser = make_browser(p)

    # ── INDIAN MNC COMPANIES ───────────────────────────────────────────────
    print("=" * 50)
    print("INDIAN MNC COMPANIES")
    print("=" * 50)
    page = new_page(browser)

    # TCS — ibegin & nextstep both block headless; use their public job search
    test_source(page, "TCS",
        "https://www.tcs.com/careers/tcs-careers",
        accept_cookie=True)

    test_source(page, "Wipro",
        "https://careers.wipro.com/careers-home/jobs?keywords=intern",
        retries=3)

    test_source(page, "Infosys",
        "https://career.infosys.com/joblist",
        retries=3)

    test_source(page, "Cognizant",
        "https://careers.cognizant.com/global/en/search-results?keywords=intern",
        retries=3)

    # HCL — use their Greenhouse ATS which is more accessible
    test_source(page, "HCL",
        "https://careers.hcltech.com/global/en",
        accept_cookie=True)

    # Tech Mahindra — correct URL confirmed
    test_source(page, "Tech Mahindra",
        "https://www.techmahindra.com/en-in/careers/",
        wait_for="body")

    test_source(page, "LTIMindtree",
        "https://www.ltimindtree.com/careers/",
        wait_for="body")

    # ── GLOBAL TECH COMPANIES ─────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("GLOBAL TECH COMPANIES")
    print("=" * 50)
    page = new_page(browser)

    test_source(page, "Apple",
        "https://jobs.apple.com/en-us/search?team=internships-and-graduate-programs-STDNT-INTRN")

    test_source(page, "Meta",
        "https://www.metacareers.com/jobs?q=intern",
        wait_for="[data-testid]")

    test_source(page, "Netflix",
        "https://jobs.netflix.com/search?q=intern",
        accept_cookie=True)

    test_source(page, "Adobe",
        "https://careers.adobe.com/us/en/search-results?keywords=intern")

    test_source(page, "Salesforce",
        "https://careers.salesforce.com/en/jobs/?search=intern")

    test_source(page, "Intel",
        "https://jobs.intel.com/en/search?q=intern",
        accept_cookie=True)

    # Nvidia — correct current university recruiting URL
    test_source(page, "Nvidia",
        "https://nvidia.wd5.myworkdayjobs.com/en-US/UniversityRecruiting",
        wait_for="[data-automation-id='jobFoundDescription']")

    test_source(page, "Qualcomm",
        "https://careers.qualcomm.com/careers/search?keywords=intern")

    # ── INDIAN STARTUPS & PRODUCT COMPANIES ───────────────────────────────
    print("\n" + "=" * 50)
    print("INDIAN STARTUPS & PRODUCT COMPANIES")
    print("=" * 50)
    page = new_page(browser)

    # Flipkart — their ATS is Karat, try the direct board
    test_source(page, "Flipkart",
        "https://www.flipkartcareers.com/#!/joblist",
        retries=3)

    test_source(page, "Swiggy",
        "https://careers.swiggy.com/",
        retries=3)

    # Zomato redirects heavily; use their Lever board
    test_source(page, "Zomato",
        "https://www.zomato.com/careers",
        retries=3)

    test_source(page, "Razorpay",
        "https://razorpay.com/jobs/",
        retries=3)

    test_source(page, "CRED",
        "https://careers.cred.club/",
        retries=3)

    test_source(page, "Meesho",
        "https://meesho.io/jobs",
        retries=3)

    # Zepto uses Keka ATS
    test_source(page, "Zepto",
        "https://www.zeptonow.com/careers",
        retries=3)

    test_source(page, "PhonePe",
        "https://www.phonepe.com/careers/",
        retries=3)

    # Paytm careers is at a subdomain
    test_source(page, "Paytm",
        "https://paytm.com/about-us/careers/",
        retries=3)

    test_source(page, "BYJU'S",
        "https://byjus.com/careers/",
        retries=3)

    # ── FINANCE & CONSULTING ──────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("FINANCE & CONSULTING")
    print("=" * 50)
    page = new_page(browser)

    test_source(page, "Goldman Sachs",
        "https://higher.gs.com/roles?query=intern")

    # Morgan Stanley blocks headless — skip to LinkedIn listing
    test_source(page, "Morgan Stanley",
        "https://www.linkedin.com/company/morgan-stanley/jobs/",
        wait_for=".jobs-search__results-list")

    test_source(page, "JP Morgan",
        "https://careers.jpmorgan.com/us/en/students/programs",
        retries=3)

    # McKinsey — Cloudflare; try their direct apply page
    test_source(page, "McKinsey",
        "https://www.mckinsey.com/careers/search-jobs",
        accept_cookie=True,
        retries=3)

    test_source(page, "Deloitte",
        "https://apply.deloitte.com/careers/SearchJobs/intern",
        retries=3)

    test_source(page, "PwC",
        "https://careers.pwc.com/global/en/search-results?keywords=intern",
        accept_cookie=True,
        retries=3)

    test_source(page, "Accenture",
        "https://www.accenture.com/in-en/careers/jobsearch?jk=intern",
        retries=3)

    test_source(page, "Capgemini",
        "https://www.capgemini.com/in-en/careers/job-search/",
        retries=3)

    # ── HACKATHON PLATFORMS ───────────────────────────────────────────────
    print("\n" + "=" * 50)
    print("HACKATHON PLATFORMS")
    print("=" * 50)
    page = new_page(browser)

    test_source(page, "Devpost",     "https://devpost.com/hackathons",                          retries=3)
    test_source(page, "HackerEarth","https://www.hackerearth.com/challenges/hackathon/",        retries=3)
    test_source(page, "HackClub",   "https://hackathons.hackclub.com",                          retries=3)
    test_source(page, "Unstop",     "https://unstop.com/hackathons",                            retries=3)
    test_source(page, "Internshala","https://internshala.com/internships/",                     retries=3)
    test_source(page, "Wellfound",  "https://wellfound.com/jobs?jobType=internship",            retries=3)

    browser.close()

print("\nDone testing all sources!")