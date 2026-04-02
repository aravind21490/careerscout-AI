# 🎯 CareerScout AI

An AI-powered internship and hackathon finder that automatically scrapes multiple job portals, filters relevant opportunities using LLM, and delivers personalized results to your Telegram every day — completely free.

## 🚀 Features

- **Multi-source scraping** — Unstop, Devfolio, Google Careers, LinkedIn, Amazon Jobs, MLH
- **AI filtering** — Groq LLM filters only CS/SWE relevant listings
- **Daily automation** — GitHub Actions runs every day at 9:30 AM IST
- **Telegram delivery** — Results sent directly to your Telegram
- **ATS Resume Optimizer** — Upload resume, get match score + cover letter

## 🛠️ Tech Stack

| Component | Tool |
|-----------|------|
| Scraping | Playwright + BeautifulSoup |
| AI Filter | Groq (llama-3.1-8b-instant) |
| Delivery | Telegram Bot API |
| Automation | GitHub Actions |
| Resume Parser | PyMuPDF |
| Language | Python |

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
```
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

## 🤖 Telegram Bot Setup

1. Open Telegram → search **@BotFather**
2. Send `/newbot` and follow steps
3. Copy the bot token
4. Search **@userinfobot** to get your Chat ID
5. Add both to `.env`

## ⚡ GitHub Actions Setup

1. Fork this repository
2. Go to **Settings → Secrets → Actions**
3. Add these secrets:
   - `GROQ_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Go to **Actions** tab → **Run workflow**

The scraper will now run automatically every day at 9:30 AM IST!

## 📊 Sources

| Source | Type |
|--------|------|
| Unstop | Internships |
| Devfolio | Hackathons |
| Google Careers | Internships |
| LinkedIn | Internships |
| Amazon Jobs | Internships |
| MLH | Hackathons |

## 🧠 AI Resume Optimizer

- Upload your resume PDF
- Paste any job description
- Get ATS match score (0-100)
- See missing keywords
- Get improvement suggestions
- Auto-generated cover letter

## 👨‍💻 Author

**Aravind Rampelly**
- GitHub: [@aravind21490](https://github.com/aravind21490)

## 📄 License

MIT License — free to use and modify!
