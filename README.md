# Health Research Journal

A private local web app that turns scattered health content into an organized, searchable library. Hosted on a Raspberry Pi 4. AI summaries powered by Gemini API.

---

## What it does

- **Submit** article links, screenshots, PDFs, or pasted text
- **Extracts** the text automatically (article scraping, OCR, PDF parsing)
- **Summarizes** using Gemini AI into three reading levels:
  - Key bullet points
  - Detailed plain-language explanation
  - ELI5 (simple explanation for non-scientists)
  - Limitations & cautions
- **Stores** everything in a local SQLite database
- **Search** your library by keyword, tag, or source type

---

## Quick Start

### 1. Install system dependencies

On Raspberry Pi OS (or Debian/Ubuntu):

```bash
sudo apt update
sudo apt install -y tesseract-ocr python3-pip python3-venv
```

### 2. Clone the repo and set up Python environment

```bash
git clone <your-repo-url>
cd Health_research_Journal
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Get a free Gemini API key

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with a Google account (free)
3. Click **Create API key**
4. Copy the key

### 4. Configure your environment

Edit the `.env` file:

```bash
nano .env
```

Fill in:
```
GEMINI_API_KEY=your-actual-api-key-here
SECRET_KEY=some-long-random-string
```

To generate a random `SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Run the app

```bash
python run.py
```

Then open your browser to: **http://localhost:8000**

### 6. Log in

Default credentials (change immediately after first login):
- Username: `admin`
- Password: `changeme`

---

## Running on your Pi (from another device on your network)

Start the server:
```bash
python run.py
```

From any other device on the same Wi-Fi:
```
http://<pi-ip-address>:8000
```

Find your Pi's IP:
```bash
hostname -I
```

---

## Running as a background service

Create `/etc/systemd/system/health-journal.service`:

```ini
[Unit]
Description=Health Research Journal
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/Health_research_Journal
ExecStart=/home/pi/Health_research_Journal/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable health-journal
sudo systemctl start health-journal
```

---

## Project structure

```
app/
├── main.py           # App startup, DB init, default user seed
├── config.py         # Settings loaded from .env
├── database.py       # SQLAlchemy + SQLite
├── models.py         # DB tables: users, items, summaries, tags, notes
├── auth.py           # Password hashing, login, default user seed
├── routes/
│   ├── web.py        # Page routes (dashboard, login, upload form)
│   ├── upload.py     # POST handlers for link/file/text intake
│   ├── items.py      # Item detail, notes, tags, delete, re-summarize
│   └── search.py     # Keyword + tag + type search
└── services/
    ├── article_extractor.py   # URL -> clean article text
    ├── ocr_service.py         # Screenshot -> text (Tesseract)
    ├── pdf_service.py         # PDF -> text (PyMuPDF)
    ├── gemini_service.py      # Gemini API client
    └── summarizer.py          # Orchestrates extraction -> AI -> save
```

---

## Version roadmap

**v1 (current):** Local login, link/screenshot/PDF/text intake, Gemini summaries, search

**v2:** Tags, notes, improved search, reprocess button, topic grouping

**v3:** X thread handling, YouTube transcripts, batch uploads, export

---

## Swapping the AI backend

`gemini_service.py` exposes a single `summarize(text: str) -> SummaryResult` function. To use a different model or API, replace that file without touching anything else.
