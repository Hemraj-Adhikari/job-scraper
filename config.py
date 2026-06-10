# ── Scraper Configuration ─────────────────────────────────────────────────────
# Edit these values before running

# Multiple job search keywords (scraper will run for EACH keyword)
SEARCH_KEYWORDS = [
    "Graphic Designer",
    "IT Support",
    "Web Developer",
    "UI UX Designer",
]

# Location to search (city, state or "remote")
SEARCH_LOCATION = "Kathmandu"

# Number of pages to scrape per keyword (each page = ~10 jobs)
MAX_PAGES = 3

# Output format: "csv" or "json"
OUTPUT_FORMAT = "csv"

# Delay in seconds between page requests (be respectful!)
DELAY_BETWEEN_REQUESTS = 3

# ── Sources to scrape ─────────────────────────────────────────────────────────
# Enable/disable sources
SCRAPE_INDEED = True
SCRAPE_LINKEDIN = True
