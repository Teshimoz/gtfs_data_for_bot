  #!/usr/bin/env python3
import time
import smtplib
import traceback
from email.message import EmailMessage
from pathlib import Path

import pandas as pd
import gspread
import requests
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

# === CONFIG ===
BASE_PATH = "/home/pi/Documents/15minutes/gtfs_server/gtfs_data_for_bot/"

FILES = {
    "bus_data.csv": "bus_data",
    "lrt_data.csv": "lrt_data",
    "train_data.csv": "train_data",
}

SPREADSHEET_ID = Path(
    "/home/pi/Documents/15minutes/gtfs_server/sheet_id.txt"
).read_text().strip()
CREDS_FILE = "/home/pi/creds/google_service_account.json"

# --- Notifications ---
# Telegram: put the bot token and your chat id in these files (one line each)
TELEGRAM_TOKEN_FILE = "/home/pi/creds/telegram_token_bus_watcher.txt"
TELEGRAM_CHAT_ID_FILE = "/home/pi/creds/telegram_chat_id.txt"

# Email (optional): set USE_EMAIL = True and fill in the details.
# For Gmail use an "App Password", not your normal password.
USE_EMAIL = False
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "you@gmail.com"
SMTP_PASSWORD_FILE = "/home/pi/creds/smtp_password.txt"
EMAIL_TO = "you@gmail.com"


# ---------------------------
# Notification helpers
# ---------------------------
def send_telegram(text):
    try:
        token = Path(TELEGRAM_TOKEN_FILE).read_text().strip()
        chat_id = Path(TELEGRAM_CHAT_ID_FILE).read_text().strip()
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": text},
            timeout=15,
        )
        r.raise_for_status()
    except Exception as e:
        print(f"Telegram send failed: {e}")


def send_email(subject, body):
    if not USE_EMAIL:
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = EMAIL_TO
        msg.set_content(body)
        password = Path(SMTP_PASSWORD_FILE).read_text().strip()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.login(SMTP_USER, password)
            s.send_message(msg)
    except Exception as e:
        print(f"Email send failed: {e}")


def notify(subject, body):
    print(body)
    send_telegram(f"{subject}\n\n{body}")
    send_email(subject, body)


# ---------------------------
# Upload logic
# ---------------------------
def safe_update(worksheet, values, retries=5):
    for i in range(retries):
        try:
            worksheet.update(values)
            return
        except APIError:
            print(f"Retry {i+1}/{retries} due to APIError")
            time.sleep(2 ** i)  # exponential backoff
    raise Exception("Failed after retries")


def upload_csv(spreadsheet, csv_file, worksheet_name):
    t_start = time.perf_counter()

    df = pd.read_csv(BASE_PATH + csv_file)
    df = df.fillna("")
    rows, cols = df.shape

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        raise Exception(f"Worksheet '{worksheet_name}' not found")

    worksheet.clear()
    safe_update(worksheet, [df.columns.tolist()] + df.values.tolist())

    elapsed = time.perf_counter() - t_start
    print(f"Uploaded {csv_file} -> {worksheet_name} ({rows}x{cols}, {elapsed:.2f}s)")
    return {"name": worksheet_name, "rows": rows, "cols": cols, "secs": elapsed}


def main():
    t0 = time.perf_counter()
    results = []

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)

        for csv_file, worksheet_name in FILES.items():
            results.append(upload_csv(spreadsheet, csv_file, worksheet_name))
            time.sleep(1)

    except Exception as e:
        lines = [f"- {r['name']}: {r['rows']:,} rows x {r['cols']:,} cols, {r['secs']:.1f}s" for r in results]
        body = (
            f"Error: {e}\n\n"
            + ("Completed before failure:\n" + "\n".join(lines) + "\n\n" if lines else "")
            + traceback.format_exc()[-1500:]
        )
        notify("❌ GTFS upload FAILED", body)
        raise

    total = time.perf_counter() - t0
    lines = [f"- {r['name']}: {r['rows']:,} rows x {r['cols']:,} cols, {r['secs']:.1f}s" for r in results]
    body = "\n".join(lines) + f"\n\nTotal: {total:.1f}s"
    notify("✅ GTFS upload OK", body)


if __name__ == "__main__":
    main()
