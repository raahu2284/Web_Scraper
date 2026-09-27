SearchIQS Ashford Land Records Scraper

A Python-based scraper designed for the SearchIQS Ashford, Connecticut Land Records assignment. The application calculates a dynamic 80-day date range, retrieves authorized search results, handles pagination, extracts required record fields, removes duplicates, and exports the results to Google Sheets.

Important: The live SearchIQS terms currently restrict automated scraping. This project is intended to be used with an authorized SearchIQS endpoint, test environment, or HTML fixture provided by the assignment organizer. It does not use browser automation or bypass anti-bot/security controls.

Features
Python-based implementation
No Selenium, Playwright, Puppeteer, or browser automation
Dynamic date calculation
Searches the Land Records document group
Date range:
From: current date − 80 days
To: current date
Pagination support
Extracts:
Party 1
Party 2
Type
Book-Page
Date
Description
Additional Description
Related
Duplicate record removal
Google Sheets export
Read-only Google Sheet sharing
Environment-variable configuration
Basic HTTP error handling
Project Structure
searchiqs-scraper/
│
├── scraper.py
├── requirements.txt
├── .env
├── credentials.json
└── README.md
Requirements

Install:

Python 3.10+
Google Cloud service account
Google Sheets API enabled
Authorized SearchIQS endpoint/test data
Authorized US-based network/VPN if required by the assignment
