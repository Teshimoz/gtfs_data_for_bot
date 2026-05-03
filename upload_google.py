import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time
import gspread
from gspread.exceptions import APIError


# ---------------------------
# Timer utils
# ---------------------------
t0 = time.perf_counter()
last = t0

# === CONFIG ===
BASE_PATH = "/home/pi/Documents/15minutes/gtfs_server/gtfs_data_for_bot/"

FILES = {
   
    "stops_by_city.csv": "stops_by_city",
     "routes_by_city.csv": "routes_by_city",
     "global_data.csv": "global_data",
}

SPREADSHEET_ID = "1cqCKAW-kyk1UJVB4WawtG5pi6UaCh1D4flEw8RSHj6E"
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
        except APIError as e:
            print(f"Retry {i+1}/{retries} due to APIError")
            time.sleep(2 ** i)  # exponential backoff
    raise Exception("Failed after retries")



def upload_csv(spreadsheet, csv_file, worksheet_name):
    path = BASE_PATH + csv_file

    df = pd.read_csv(path)
    
    # replace NaN
    df = df.fillna("")

    try:
        print(f"---{worksheet_name}---")
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        raise Exception(f"Worksheet '{worksheet_name}' not found")

    # overwrite content
    worksheet.clear()
    safe_update(worksheet, [df.columns.tolist()] + df.values.tolist())

    print(f"Uploaded {csv_file} → {worksheet_name}")


def main():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    # ONE spreadsheet
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # MULTIPLE tabs inside it
    for csv_file, worksheet_name in FILES.items():
        upload_csv(spreadsheet, csv_file, worksheet_name)
        
        log(f"Uploaded {worksheet_name}")

        time.sleep(1)
    
    print(f"All data uploaded")


if __name__ == "__main__":
    main()
