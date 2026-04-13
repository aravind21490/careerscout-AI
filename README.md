<div align="center">

<h1>🎯 CareerScout AI</h1>

<p><strong>An AI-powered internship and hackathon finder that automatically scrapes multiple job portals, filters relevant opportunities using LLM, and delivers personalized results to your Telegram every day — completely free.</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-llama--3.1--8b-F55036?style=flat-square&logo=openai&logoColor=white)](https://groq.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://telegram.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Daily%20Automation-2088FF?style=flat-square&logo=github-actions&logoColor=white)](https://github.com/features/actions)
[![Playwright](https://img.shields.io/badge/Playwright-Scraping-45ba4b?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## 🚀 Features

- **Multi-source scraping** — Unstop, Devfolio, Google Careers, LinkedIn, Amazon Jobs, MLH
- **AI filtering** — Groq LLM filters only CS/SWE relevant listings
- **Daily automation** — GitHub Actions runs every day at 9:30 AM IST
- **Telegram delivery** — Results sent directly to your Telegram
- **ATS Resume Optimizer** — Upload resume, get match score + cover letter

---

## 🛠️ Tech Stack

| Component | Tool |
|---|---|
| Scraping | Playwright + BeautifulSoup |
| AI Filter | Groq (`llama-3.1-8b-instant`) |
| Delivery | Telegram Bot API |
| Automation | GitHub Actions |
| Resume Parser | PyMuPDF |
| Language | Python |

---

## 📸 How It Works

```
GitHub Actions (9:30 AM IST daily)
         ↓
Scrape 6 sources (50+ listings)
         ↓
Groq AI filters relevant listings
         ↓
Top 15 results saved to results.json
         ↓
Telegram Bot sends 3 messages
```

---

## 📂 Project Structure

```
careerscout-AI/
│
├── .github/
│   └── workflows/              # GitHub Actions automation
│
├── scraper/                    # Platform-specific scrapers
│
├── frontend/                   # Frontend UI
│
├── main.py                     # Main pipeline entry point
├── main_api.py                 # FastAPI backend
├── bot.py                      # Telegram bot handler
├── broadcast.py                # Broadcast messages to subscribers
├── ai_filter_v2.py             # Groq LLM filtering logic
├── ats.py                      # ATS Resume Optimizer
├── formatter.py                # Job/hackathon message formatter
├── scraper.py                  # Core scraper logic
├── db.py                       # SQLite subscriber database
├── results.json                # Latest scraped results
├── supabase_schema.sql         # Supabase DB schema
├── requirements.txt
├── Procfile
└── .env
```

---

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/aravind21490/careerscout-AI.git
cd careerscout-AI
```

### 2. Install dependencies

```bash
pip install playwright beautifulsoup4 groq python-dotenv requests pymupdf
playwright install chromium
```

### 3. Create `.env` file

```env
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### 4. Run manually

```bash
python main.py
```

### 5. ATS Resume Optimizer

```bash
python ats.py
```

---

## 🤖 Telegram Bot Setup

1. Open Telegram → search **@BotFather**
2. Send `/newbot` and follow the steps
3. Copy the **bot token**
4. Search **@userinfobot** to get your **Chat ID**
5. Add both to your `.env` file

---

## ⚡ GitHub Actions Setup

1. Fork this repository
2. Go to **Settings → Secrets → Actions**
3. Add these secrets:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Go to **Actions** tab → **Run workflow**

The scraper will now run automatically every day at **9:30 AM IST**!

---

## 📊 Sources

| Source | Type |
|---|---|
| Unstop | Internships |
| Devfolio | Hackathons |
| Google Careers | Internships |
| LinkedIn | Internships |
| Amazon Jobs | Internships |
| MLH | Hackathons |

---

## 🧠 AI Resume Optimizer

1. Upload your resume PDF
2. Paste any job description
3. Get **ATS match score** (0–100)
4. See **missing keywords**
5. Get **improvement suggestions**
6. Auto-generated **cover letter**

---

## 👨‍💻 Author

**Aravind Rampelly**

- GitHub: [@aravind21490](https://github.com/aravind21490)

---

## 📄 License

MIT License — free to use and modify!
