import asyncio
import os
import datetime
from telegram import Bot
from playwright.async_api import async_playwright

# Telegram-Konfiguration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# Suchparameter
STARTORT = "Cottbus Hbf"
FRUEHESTES_DATUM = datetime.date.today()
LETZTES_DATUM = FRUEHESTES_DATUM + datetime.timedelta(days=7)
MIN_UMSATZ = 400
MAX_AUFTRAEGE_PRO_TAG = 3
ABFAHRT_FRUEHESTENS = datetime.time(5, 0)
ANKUNFT_SPAETESTENS = datetime.time(19, 0)
TAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]


async def finde_passende_auftraege():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # ✅ Richtiger Login-Link
        await page.goto("https://portal.onlogist.com/secure/login")

        # Login durchführen
        await page.fill("input[name=email]", os.getenv("ONLOGIST_EMAIL"))
        await page.fill("input[name=password]", os.getenv("ONLOGIST_PASSWORD"))
        await page.click("button[type=submit]")

        # Warten auf Weiterleitung zu "Aufträge finden"
        await page.wait_for_url("**/secure/dashboard", timeout=15000)

        # Navigiere zu "Aufträge finden"
        await page.goto("https://portal.onlogist.com/secure/order-search")

        # Warten auf die Seite
        await page.wait_for_selector("[data-testid='order-card']", timeout=10000)

        # Aufträge extrahieren
        alle_auftraege = await page.locator("[data-testid='order-card']").all()
        passende_auftraege = []

        for auftrag in alle_auftraege:
            text = await auftrag.inner_text()
            if STARTORT.lower() in text.lower():
                try:
                    umsatz_text = text.split("€")[0].split()[-1].replace(".", "").replace(",", ".")
                    umsatz = float(umsatz_text)
                    if umsatz >= MIN_UMSATZ:
                        passende_auftraege.append(text)
                except:
                    continue

        await browser.close()
        return passende_auftraege


async def sende_nachricht(text):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)


async def hauptfunktion():
    await sende_nachricht("🚀 Starte automatische Suche nach Onlogist-Aufträgen...")

    auftraege = await finde_passende_auftraege()
    if not auftraege:
        await sende_nachricht("❌ Es wurden keine passenden Aufträge gefunden.")
        return

    await sende_nachricht(f"✅ {len(auftraege)} passende Aufträge gefunden:")
    for auftrag in auftraege:
        await sende_nachricht(f"📦 Auftrag:\n{auftrag}")


if __name__ == "__main__":
    asyncio.run(hauptfunktion())
