"""Configuration for the Amsterdam Culture Event Extractor."""

import os
from dotenv import load_dotenv

load_dotenv()

# Google OAuth
GMAIL_CREDENTIALS_FILE = "gmailcredentials.json"
TOKEN_FILE = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Google Sheets
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1NGqCZJggiif_6fQ9huqLk8tx-Kfw89YAdLUIhQkLrUU")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Supabase (optional)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Pipeline settings
DAYS_LOOKBACK = int(os.getenv("DAYS_LOOKBACK", "7"))
PROCESSED_IDS_FILE = "processed_ids.json"
