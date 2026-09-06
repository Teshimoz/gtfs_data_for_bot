import glob
import os
import re
import time

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

# ---------------------------
# Timer utils
# ---------------------------
t0 = time.perf_counter()
last = t0

# === CONFIG ===
TRAIN_DATA_DIR = "/home/pi/Documents/15minutes/gtfs_server/train_stop_times_data/"
TRAIN_FILE_PATTERN = "train_schedule_labeled__*.csv"
SPREADSHEET_ID = "1aFVQfvRR9CQXf1a12qjhkk2znz-WSenLr8L4F4gdEoQ"
CREDS_FILE = "/home/pi/creds/google_service_account.json"


def log(msg):
    global last
    now = time.perf_counter()
    print(f"{msg}: {now - last:.2f}s")
    last = now


def safe_update(worksheet, values, retries=5):
    for i in range(retries):
        try:
            worksheet.update(values)
            return
        except APIError:
            print(f"Retry {i+1}/{retries} due to APIError")
            time.sleep(2 ** i)  # exponential backoff
    raise Exception("Failed after retries")


def get_latest_train_file(data_dir, pattern):
    """Find the most recently dated train_schedule_labeled__YYYY-MM-DD.csv file."""
    matches = glob.glob(os.path.join(data_dir, pattern))
    if not matches:
        raise FileNotFoundError(f"No files matching '{pattern}' in {data_dir}")

    dated_files = []
    for path in matches:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(path))
        if m:
            dated_files.append((m.group(1), path))

    if not dated_files:
        raise FileNotFoundError(f"No dated files matching '{pattern}' in {data_dir}")

    dated_files.sort(key=lambda x: x[0])
    latest_date, latest_path = dated_files[-1]
    return latest_path, latest_date


def get_or_create_worksheet(spreadsheet, worksheet_name, rows=1000, cols=26):
    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{worksheet_name}' not found, creating it")
        return spreadsheet.add_worksheet(title=worksheet_name, rows=rows, cols=cols)


def upload_csv(spreadsheet, csv_path, worksheet_name):
    df = pd.read_csv(csv_path)
    df = df.fillna("")  # replace NaN

    print(f"---{worksheet_name}---")
    worksheet = get_or_create_worksheet(spreadsheet, worksheet_name)

    # overwrite content
    worksheet.clear()
    safe_update(worksheet, [df.columns.tolist()] + df.values.tolist())
    print(f"Uploaded {os.path.basename(csv_path)} → {worksheet_name}")


def main():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    csv_path, file_date = get_latest_train_file(TRAIN_DATA_DIR, TRAIN_FILE_PATTERN)
    log(f"Found latest file for {file_date}")

    upload_csv(spreadsheet, csv_path, worksheet_name=file_date)
    log(f"Uploaded {file_date}")

    print("All data uploaded")


if __name__ == "__main__":
    main()
