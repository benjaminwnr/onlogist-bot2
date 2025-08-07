import os
import zipfile
import glob
from bs4 import BeautifulSoup
from telegram import Bot
from datetime import datetime

# === CONFIG ===
MIN_VERGÜTUNG = 400     # Mindestumsatz pro Auftrag in €
STARTORT = "Cottbus"    # Nur Aufträge ab diesem Ort
TODAY = datetime.now().strftime("%d.%m.%Y")

# === TELEGRAM ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# === FUNKTIONEN ===

def extract_html_from_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall("unzipped")
    return glob.glob("unzipped/*.html")

def parse_html_file(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    return soup.find_all("tr")

def filter_auftraege(rows):
    results = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        
        datum = cells[1].get_text(strip=True)
        ort = cells[2].get_text(strip=True)
        vergütung_raw = cells[4].get_text(strip=True).replace("€", "").replace(",", ".")
        auftrag_id = cells[5].get_text(strip=True)

        try:
            vergütung = float(vergütung_raw)
        except ValueError:
            continue

        if STARTORT.lower() in ort.lower() and datum == TODAY and vergütung >= MIN_VERGÜTUNG:
            ergebnis = f"📦 Auftrag-ID: {auftrag_id}\n📍 Ort: {ort}\n💰 Vergütung: {vergütung:.2f} €\n📅 Datum: {datum}\n"
            results.append(ergebnis)
    return results

def send_telegram_nachricht(nachrichten_liste):
    if not nachrichten_liste:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="⚠️ Heute keine passenden Aufträge gefunden.")
    else:
        for nachricht in nachrichten_liste:
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=nachricht)

# === HAUPTFUNKTION ===

def main():
    print(f"📆 Starte Auftragssuche für {TODAY} in {STARTORT}...")

    try:
        zip_files = glob.glob("*.zip")
        if not zip_files:
            print("❌ Keine ZIP-Datei gefunden.")
            bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="❌ Keine ZIP-Datei zum Verarbeiten gefunden.")
            return

        html_files = extract_html_from_zip(zip_files[0])
        alle_rows = []
        for html_file in html_files:
            alle_rows.extend(parse_html_file(html_file))
        
        gefiltert = filter_auftraege(alle_rows)
        send_telegram_nachricht(gefiltert)

        print(f"✅ {len(gefiltert)} passende Aufträge gefunden und gesendet.")
        
    except Exception as e:
        fehler = f"❌ Fehler beim Verarbeiten:\n{str(e)}"
        print(fehler)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=fehler)

# === START ===
if __name__ == "__main__":
    main()
