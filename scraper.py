"""
Job Listings Scraper
Scrapes job listings from Indeed based on keyword and location.
Author: Raj (Hemraj Adhikari)
"""

import requests
from bs4 import BeautifulSoup
import csv
import json
import os
import time
import logging
from datetime import datetime
from config import SEARCH_KEYWORD, SEARCH_LOCATION, MAX_PAGES, OUTPUT_FORMAT, DELAY_BETWEEN_REQUESTS

# ── Logging setup ──────────────────────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}


def build_url(keyword: str, location: str, start: int = 0) -> str:
    """Build Indeed search URL."""
    base = "https://www.indeed.com/jobs"
    params = f"?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
    return base + params


def parse_jobs(soup: BeautifulSoup) -> list[dict]:
    """Extract job listings from BeautifulSoup object."""
    jobs = []

    job_cards = soup.find_all("div", class_="job_seen_beacon")
    if not job_cards:
        # Fallback: try alternate card class
        job_cards = soup.find_all("div", {"class": lambda c: c and "jobsearch-SerpJobCard" in c})

    for card in job_cards:
        try:
            # Job title
            title_el = card.find("h2", class_="jobTitle")
            title = title_el.get_text(strip=True) if title_el else "N/A"

            # Company name
            company_el = card.find("span", {"data-testid": "company-name"})
            if not company_el:
                company_el = card.find("span", class_="companyName")
            company = company_el.get_text(strip=True) if company_el else "N/A"

            # Location
            location_el = card.find("div", {"data-testid": "text-location"})
            if not location_el:
                location_el = card.find("div", class_="companyLocation")
            location = location_el.get_text(strip=True) if location_el else "N/A"

            # Salary (optional)
            salary_el = card.find("div", {"data-testid": "attribute_snippet_testid"})
            salary = salary_el.get_text(strip=True) if salary_el else "Not listed"

            # Job URL
            link_el = card.find("a", href=True)
            job_url = "https://www.indeed.com" + link_el["href"] if link_el else "N/A"

            # Posted date
            date_el = card.find("span", {"data-testid": "myJobsStateDate"})
            if not date_el:
                date_el = card.find("span", class_="date")
            posted = date_el.get_text(strip=True) if date_el else "N/A"

            jobs.append({
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "posted": posted,
                "url": job_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        except Exception as e:
            logger.warning(f"Error parsing a job card: {e}")
            continue

    return jobs


def scrape_jobs(keyword: str, location: str, max_pages: int = 3) -> list[dict]:
    """Main scraping function — iterates through pages."""
    all_jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(max_pages):
        start = page * 10
        url = build_url(keyword, location, start)
        logger.info(f"Scraping page {page + 1}: {url}")

        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed on page {page + 1}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = parse_jobs(soup)

        if not jobs:
            logger.info("No more jobs found. Stopping.")
            break

        logger.info(f"Found {len(jobs)} jobs on page {page + 1}")
        all_jobs.extend(jobs)

        # Respectful delay between requests
        if page < max_pages - 1:
            logger.info(f"Waiting {DELAY_BETWEEN_REQUESTS}s before next request...")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_jobs


def save_results(jobs: list[dict], fmt: str = "csv"):
    """Save results to CSV or JSON."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    keyword_slug = SEARCH_KEYWORD.replace(" ", "_").lower()

    if fmt == "json":
        filepath = f"output/jobs_{keyword_slug}_{timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    else:
        filepath = f"output/jobs_{keyword_slug}_{timestamp}.csv"
        if jobs:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
                writer.writeheader()
                writer.writerows(jobs)

    logger.info(f"Results saved to: {filepath}")
    return filepath


def main():
    logger.info("=" * 60)
    logger.info("Job Listings Scraper — Starting")
    logger.info(f"Keyword : {SEARCH_KEYWORD}")
    logger.info(f"Location: {SEARCH_LOCATION}")
    logger.info(f"Pages   : {MAX_PAGES}")
    logger.info("=" * 60)

    jobs = scrape_jobs(SEARCH_KEYWORD, SEARCH_LOCATION, MAX_PAGES)

    if not jobs:
        logger.warning("No jobs scraped. Check if Indeed blocked the request or update selectors.")
        return

    logger.info(f"\nTotal jobs scraped: {len(jobs)}")
    save_results(jobs, OUTPUT_FORMAT)

    # Preview in terminal
    print("\n--- PREVIEW (first 3 results) ---")
    for job in jobs[:3]:
        print(f"\n  Title   : {job['title']}")
        print(f"  Company : {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Salary  : {job['salary']}")
        print(f"  Posted  : {job['posted']}")
        print(f"  URL     : {job['url']}")


if __name__ == "__main__":
    main()
