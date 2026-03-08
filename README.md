# Health Research Journal

A private local web app that turns scattered health content into an organized, searchable library. Hosted on a Raspberry Pi. AI summaries powered by Gemini API.

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

## Hardware

This app runs on either a **Raspberry Pi 3 Model B** or **Raspberry Pi 4**.

The Pi 3B (1GB RAM) is perfectly capable — the app is lightweight. FastAPI + SQLite + Gemini API calls use well under 512MB in normal use. OCR (Tesseract) is CPU-intensive but runs fine for occasional household use.

---

## Setting Up on a Fresh Raspberry Pi 3 (Recommended — clean slate)

### Step 1: Flash the OS

Use **[Raspberry Pi Imager](https://www.raspberrypi.com/software/)** (free, runs on Windows/Mac/Linux):

1. Download and open Raspberry Pi Imager
2. **Choose Device:** Raspberry Pi 3
3. **Choose OS:** Raspberry Pi OS Lite (64-bit) — under "Raspberry Pi OS (other)"
   - Lite = no desktop, runs headless. Saves RAM for the app.
4. **Choose Storage:** your SD card
5. Click the **gear icon** (Advanced Options) before writing:
   - Enable SSH
   - Set a username and password (e.g. user: `pi`, password: your choice)
   - Configure your Wi-Fi network name and password
6. Write the card, insert into Pi, power on

### Step 2: SSH into the Pi

From your laptop (same Wi-Fi network):

```bash
ssh pi@raspberrypi.local
```

If that doesn't resolve, find the Pi's IP from your router's device list, then:

```bash
ssh pi@<ip-address>
```

### Step 3: Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 4: Install system dependencies

```bash
sudo apt install -y tesseract-ocr python3-venv git
```

- `tesseract-ocr` — required for OCR on screenshots
- `python3-venv` — required to create an isolated Python environment
- `git` — to clone the repo

### Step 5: Clone the repo

```bash
cd ~
git clone https://github.com/NathanaelP/Health_research_Journal.git
cd Health_research_Journal
```

### Step 6: Create a Python virtual environment

**Important:** Always use a venv — never `sudo pip install`. The venv keeps all app packages isolated from the system.

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

This will take several minutes on the Pi 3 — it's compiling some packages for ARM. Let it run.

### Step 7: Get a free Gemini API key

1. Go to [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with a Google account (free)
3. Click **Create API key**
4. Copy the key

### Step 8: Configure your environment

```bash
nano .env
```

Fill in your values:

```
GEMINI_API_KEY=paste-your-key-here
SECRET_KEY=paste-a-long-random-string-here
```

To generate a good `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and paste it as your `SECRET_KEY`.

Press `Ctrl+O` to save, `Ctrl+X` to exit nano.

### Step 9: Test run

```bash
source venv/bin/activate
python run.py
```

You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

From your phone or laptop on the same Wi-Fi, open:
```
http://raspberrypi.local:8000
```

Log in with:
- Username: `admin`
- Password: `changeme`

**Change this password** after your first login.

Press `Ctrl+C` to stop the test run.

### Step 10: Run as a background service (auto-starts on boot)

```bash
sudo nano /etc/systemd/system/health-journal.service
```

Paste this (adjust the username if yours isn't `pi`):

```ini
[Unit]
Description=Health Research Journal
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/Health_research_Journal
ExecStart=/home/pi/Health_research_Journal/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PATH=/home/pi/Health_research_Journal/venv/bin

[Install]
WantedBy=multi-user.target
```

Save and exit, then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable health-journal
sudo systemctl start health-journal
sudo systemctl status health-journal
```

You should see `active (running)`. The app will now start automatically every time the Pi boots.

### Step 11: Find your Pi's address

```bash
hostname -I
```

Access from any device on your home network:
```
http://<that-ip-address>:8000
```

You may want to set a static IP for the Pi in your router settings so the address doesn't change.

---

## Updating the app

When new code is pushed to the repo:

```bash
cd ~/Health_research_Journal
git pull
sudo systemctl restart health-journal
```

---

## Useful service commands

```bash
# Check if it's running
sudo systemctl status health-journal

# View live logs
journalctl -u health-journal -f

# Restart after config change
sudo systemctl restart health-journal

# Stop
sudo systemctl stop health-journal
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
