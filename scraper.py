import os
import time
from datetime import date, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import gspread


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

BASE_URL = os.getenv(
    "SEARCHIQS_BASE_URL",
    "https://www.searchiqs.com/CTASH/"
)

# Set this to the authorized search endpoint supplied by the
# assignment organizer.
SEARCH_URL = os.getenv(
    "SEARCHIQS_SEARCH_URL",
    ""
)

GOOGLE_CREDENTIALS = os.getenv(
    "GOOGLE_CREDENTIALS",
    "credentials.json"
)

GOOGLE_SHEET_NAME = os.getenv(
    "GOOGLE_SHEET_NAME",
    "Ashford Land Records"
)

DAYS_BACK = 80

REQUEST_DELAY = 1.0


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "Authorized-LandRecords-Client/1.0",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9"
})


# ============================================================
# DATE FUNCTIONS
# ============================================================

def get_date_range():
    """
    Calculate:

    From Date = current date - 80 days
    To Date   = current date
    """

    today = date.today()

    from_date = today - timedelta(days=DAYS_BACK)

    return (
        from_date.strftime("%m/%d/%Y"),
        today.strftime("%m/%d/%Y")
    )


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_text(value):
    if not value:
        return ""

    return " ".join(value.split())


# ============================================================
# GET PAGE
# ============================================================

def get_page(url, params=None):

    try:

        response = session.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        time.sleep(REQUEST_DELAY)

        return response.text

    except requests.RequestException as error:

        print("Request failed:")
        print(error)

        return None


# ============================================================
# SEARCH
# ============================================================

def search_land_records(from_date, to_date):

    if not SEARCH_URL:

        raise RuntimeError(
            "SEARCHIQS_SEARCH_URL is not configured. "
            "Set it to the authorized search endpoint "
            "provided by the assignment organizer."
        )

    params = {

        # These parameter names are examples.
        # Replace them with the actual authorized
        # endpoint parameters supplied by the organizer.

        "document_group": "Land Records",

        "from_date": from_date,

        "to_date": to_date,

        "page": 1
    }

    return get_page(
        SEARCH_URL,
        params=params
    )


# ============================================================
# PARSE RECORDS
# ============================================================

def parse_records(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    records = []

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Replace this selector with the actual result-row
    # selector from the authorized Ashford HTML/API response.
    # --------------------------------------------------------

    rows = soup.select(
        "table.results tbody tr"
    )

    for row in rows:

        cells = row.find_all("td")

        values = [
            clean_text(cell.get_text(" ", strip=True))
            for cell in cells
        ]

        if len(values) < 8:
            continue

        record = {

            "Party 1": values[0],

            "Party 2": values[1],

            "Type": values[2],

            "Book-Page": values[3],

            "Date": values[4],

            "Description": values[5],

            "Additional Description": values[6],

            "Related": values[7]
        }

        records.append(record)

    return records


# ============================================================
# FIND NEXT PAGE
# ============================================================

def get_next_page(html, current_url):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # Replace this selector with the actual pagination
    # selector from the authorized response.

    next_link = soup.select_one(
        "a.next-page"
    )

    if not next_link:
        return None

    href = next_link.get("href")

    if not href:
        return None

    return urljoin(
        current_url,
        href
    )


# ============================================================
# SCRAPE ALL PAGES
# ============================================================

def scrape_all_pages(first_html):

    all_records = []

    html = first_html

    current_url = SEARCH_URL

    page_number = 1

    while html:

        print(
            f"Scraping page {page_number}..."
        )

        records = parse_records(html)

        print(
            f"Records found: {len(records)}"
        )

        all_records.extend(records)

        next_url = get_next_page(
            html,
            current_url
        )

        if not next_url:
            break

        current_url = next_url

        html = get_page(
            current_url
        )

        page_number += 1

    return all_records


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(records):

    unique_records = {}

    for record in records:

        key = (

            record.get("Party 1", ""),

            record.get("Party 2", ""),

            record.get("Type", ""),

            record.get("Book-Page", ""),

            record.get("Date", "")
        )

        unique_records[key] = record

    return list(
        unique_records.values()
    )


# ============================================================
# GOOGLE SHEETS
# ============================================================

def export_to_google_sheet(records):

    print(
        "\nConnecting to Google Sheets..."
    )

    client = gspread.service_account(
        filename=GOOGLE_CREDENTIALS
    )

    try:

        spreadsheet = client.open(
            GOOGLE_SHEET_NAME
        )

    except gspread.SpreadsheetNotFound:

        print(
            "Sheet not found. Creating new sheet..."
        )

        spreadsheet = client.create(
            GOOGLE_SHEET_NAME
        )

    worksheet = spreadsheet.sheet1

    worksheet.clear()

    headers = [

        "Party 1",

        "Party 2",

        "Type",

        "Book-Page",

        "Date",

        "Description",

        "Additional Description",

        "Related"
    ]

    rows = [
        headers
    ]

    for record in records:

        rows.append([

            record.get(
                "Party 1",
                ""
            ),

            record.get(
                "Party 2",
                ""
            ),

            record.get(
                "Type",
                ""
            ),

            record.get(
                "Book-Page",
                ""
            ),

            record.get(
                "Date",
                ""
            ),

            record.get(
                "Description",
                ""
            ),

            record.get(
                "Additional Description",
                ""
            ),

            record.get(
                "Related",
                ""
            )
        ])

    worksheet.update(
        "A1",
        rows
    )

    # --------------------------------------------------------
    # Read access
    #
    # Use this only if the assignment permits a public
    # read-only sheet.
    # --------------------------------------------------------

    spreadsheet.share(
        None,
        perm_type="anyone",
        role="reader"
    )

    print(
        "\nGoogle Sheet URL:"
    )

    print(
        spreadsheet.url
    )

    return spreadsheet.url


# ============================================================
# MAIN
# ============================================================

def main():

    if not SEARCH_URL:
        print("SEARCHIQS_SEARCH_URL is not configured.")
        print("Create a .env file or set the environment variable before running the scraper.")
        print("Example: SEARCHIQS_SEARCH_URL=https://example.com/search")
        return

    print("=" * 60)

    print(
        "SEARCHIQS ASHFORD LAND RECORD SCRAPER"
    )

    print("=" * 60)

    # --------------------------------------------------------
    # 1. Dynamic dates
    # --------------------------------------------------------

    from_date, to_date = get_date_range()

    print(
        f"\nFrom Date : {from_date}"
    )

    print(
        f"To Date   : {to_date}"
    )

    # --------------------------------------------------------
    # 2. Search
    # --------------------------------------------------------

    print(
        "\nSearching Land Records..."
    )

    html = search_land_records(
        from_date,
        to_date
    )

    if not html:

        print(
            "No response received."
        )

        return

    # --------------------------------------------------------
    # 3. Scrape all pages
    # --------------------------------------------------------

    records = scrape_all_pages(
        html
    )

    print(
        f"\nTotal scraped records: {len(records)}"
    )

    # --------------------------------------------------------
    # 4. Remove duplicates
    # --------------------------------------------------------

    records = remove_duplicates(
        records
    )

    print(
        f"Unique records: {len(records)}"
    )

    # --------------------------------------------------------
    # 5. Google Sheets
    # --------------------------------------------------------

    if records:

        sheet_url = export_to_google_sheet(
            records
        )

        print(
            "\nFinished successfully."
        )

        print(
            f"Sheet: {sheet_url}"
        )

    else:

        print(
            "\nNo records found."
        )


# ============================================================
# PROGRAM ENTRY
# ============================================================

if __name__ == "__main__":
    main()