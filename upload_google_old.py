import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
CSV_PATH = "/home/pi/Documents/15minutes/gtfs_server/gtfs_data_for_bot/routes_by_city.csv"
SPREADSHEET_NAME = "global_data"
WORKSHEET_NAME = "Sheet1"
CREDS_FILE = "/home/pi/creds/form-connect-389913-71d2a8a5a857.json"

def upload_csv_to_gsheet():
    # Load CSV
    df = pd.read_csv(CSV_PATH)

    # Auth
    scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=scopes)
    client = gspread.authorize(creds)

    # Open sheet
    sheet = client.open(SPREADSHEET_NAME)
    worksheet = sheet.worksheet(WORKSHEET_NAME)

    # Clear existing content
    worksheet.clear()

    # Upload data
    worksheet.update(
        [df.columns.values.tolist()] + df.values.tolist()
    )

if __name__ == "__main__":
    upload_csv_to_gsheet()
