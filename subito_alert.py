#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -------------------
# CONFIGURAZIONE
# -------------------
GMAIL_USER = "senatore.isacco@gmail.com"
GMAIL_PASSWORD = "cstlbacjsedvzltq"  # App Password Gmail
RECIPIENT = GMAIL_USER
SEARCH_URL = "https://www.subito.it/annunci-lombardia/regalo/usato/bergamo/?q=&from=mysearches&order=datedesc"
SEEN_FILE = "seen.json"
EXCLUDE_KEYWORDS = ["cane", "cani", "gatto", "gatti", "cucciolo", "cuccioli", "animali"]
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SubitoAlert/1.0)"}

# -------------------
# FUNZIONI
# -------------------
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_announcements():
    print(f"Parsing URL: {SEARCH_URL}")
    r = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    ads = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("https://www.subito.it/") and "/annunci/" in href:
            title = a.get_text(strip=True)
            if not title:
                continue
            t = title.lower()
            if any(k in t for k in EXCLUDE_KEYWORDS):
                continue
            ads.append((title, href))
    print(f"Trovati {len(ads)} annunci totali dopo filtro animali")
    seen_urls = set()
    dedup = []
    for t, u in ads:
        if u not in seen_urls:
            dedup.append((t, u))
            seen_urls.add(u)
    return dedup

# -------------------
# MAIN
# -------------------
def main():
    print("Esecuzione script Subito Alert")
    seen = load_seen()
    new_ads = []
    for title, url in fetch_announcements():
        if url not in seen:
            new_ads.append((title, url))
            seen.add(url)
    save_seen(seen)

    if new_ads:
        body = "\n\n".join([f"{title}\n{url}" for title, url in new_ads])
        subject = f"Nuovi annunci 'In regalo' - Bergamo ({len(new_ads)})"
        print(f"Nuovi annunci trovati: {len(new_ads)}")
    else:
        body = "Nessun nuovo annuncio trovato in questa esecuzione."
        subject = "Subito Alert - Nessun nuovo annuncio"
        print("Nessun nuovo annuncio trovato")

    try:
        send_email(subject, body)
        print("Email inviata correttamente")
    except Exception as e:
        print("Invio email fallito:", e)

if __name__ == "__main__":
    main()
