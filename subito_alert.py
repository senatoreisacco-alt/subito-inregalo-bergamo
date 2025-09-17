#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# === CONFIG (legge da env, fallback su valore di default dove sensato) ===
SEARCH_URL = os.environ.get("SEARCH_URL", "https://www.subito.it/annunci-lombardia/regalo/usato/bergamo/?q=&from=mysearches&order=datedesc")
SEEN_FILE = os.environ.get("SEEN_FILE", "seen.json")
GMAIL_USER = os.environ.get("GMAIL_USER", "senatore.isacco@gmail.com")
GMAIL_PASSWORD = os.environ.get("cstl bacj sedv zltq")  # **obbligatoria** (App Password)
RECIPIENT = os.environ.get("RECIPIENT", GMAIL_USER)

# parole da escludere (animali)
EXCLUDE_KEYWORDS = ["cani", "gatti", "cuccioli", "gatto", "cane", "criceti", "conigli", "uccelli", "pesci", "cavalli", "pet", "gabbia", "guinzaglio", "cuccia", "acquario", "gattin"]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; SubitoAlert/1.0)"}

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
        except Exception:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def fetch_announcements():
    resp = requests.get(SEARCH_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    ads = []
    # fallback generico: cerca link dentro della pagina che sembrano annunci
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("https://www.subito.it/") and "/annunci/" in href:
            title = a.get_text(strip=True)
            if not title:
                continue
            t = title.lower()
            if any(k in t for k in EXCLUDE_KEYWORDS):
                continue
            ads.append((t, href))

    # deduplica preservando ordine
    seen_urls = set()
    dedup = []
    for t, u in ads:
        if u not in seen_urls:
            dedup.append((t, u))
            seen_urls.add(u)
    return dedup

def main():
    if not GMAIL_PASSWORD:
        print("ERRORE: la variabile d'ambiente GMAIL_PASSWORD non è settata.")
        return

    seen = load_seen()
    new_ads = []

    for title, url in fetch_announcements():
        if url not in seen:
            new_ads.append((title, url))
            seen.add(url)

    if new_ads:
        body = "\n\n".join([f"{title}\n{url}" for title, url in new_ads])
        subject = f"Nuovi annunci 'In regalo' - Bergamo ({len(new_ads)})"
        try:
            send_email(subject, body)
            print(f"Inviata email con {len(new_ads)} annunci.")
        except Exception as e:
            print("Invio email fallito:", e)
    else:
        print("Nessun nuovo annuncio trovato.")

    save_seen(seen)

if __name__ == "__main__":
    main()
