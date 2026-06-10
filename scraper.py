"""
Job Listings Scraper
Scrapes job listings from Indeed & LinkedIn based on multiple keywords and location.
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
from config import (
    SEARCH_KEYWORDS, SEARCH_LOCATION, MAX_PAGES,
    OUTPUT_FORMAT, DELAY_BETWEEN_REQUESTS,
    SCRAPE_INDEED, SCRAPE_LINKEDIN
)

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


# ══════════════════════════════════════════════════════════════════════════════
# INDEED SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

def build_indeed_url(keyword: str, location: str, start: int = 0) -> str:
    base = "https://www.indeed.com/jobs"
    params = f"?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
    return base + params


def parse_indeed_jobs(soup: BeautifulSoup, keyword: str) -> list[dict]:
    jobs = []
    job_cards = soup.find_all("div", class_="job_seen_beacon")
    if not job_cards:
        job_cards = soup.find_all("div", {"class": lambda c: c and "jobsearch-SerpJobCard" in c})

    for card in job_cards:
        try:
            title_el = card.find("h2", class_="jobTitle")
            title = title_el.get_text(strip=True) if title_el else "N/A"

            company_el = card.find("span", {"data-testid": "company-name"})
            if not company_el:
                company_el = card.find("span", class_="companyName")
            company = company_el.get_text(strip=True) if company_el else "N/A"

            location_el = card.find("div", {"data-testid": "text-location"})
            if not location_el:
                location_el = card.find("div", class_="companyLocation")
            location = location_el.get_text(strip=True) if location_el else "N/A"

            salary_el = card.find("div", {"data-testid": "attribute_snippet_testid"})
            salary = salary_el.get_text(strip=True) if salary_el else "Not listed"

            link_el = card.find("a", href=True)
            job_url = "https://www.indeed.com" + link_el["href"] if link_el else "N/A"

            date_el = card.find("span", {"data-testid": "myJobsStateDate"})
            if not date_el:
                date_el = card.find("span", class_="date")
            posted = date_el.get_text(strip=True) if date_el else "N/A"

            jobs.append({
                "source": "Indeed",
                "keyword": keyword,
                "title": title,
                "company": company,
                "location": location,
                "salary": salary,
                "posted": posted,
                "url": job_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            logger.warning(f"[Indeed] Error parsing card: {e}")
            continue

    return jobs


def scrape_indeed(keyword: str, location: str, max_pages: int) -> list[dict]:
    all_jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(max_pages):
        start = page * 10
        url = build_indeed_url(keyword, location, start)
        logger.info(f"  [Indeed] Page {page + 1}: {url}")

        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"  [Indeed] Request failed: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = parse_indeed_jobs(soup, keyword)

        if not jobs:
            logger.info("  [Indeed] No more jobs found.")
            break

        logger.info(f"  [Indeed] Found {len(jobs)} jobs on page {page + 1}")
        all_jobs.extend(jobs)

        if page < max_pages - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_jobs


# ══════════════════════════════════════════════════════════════════════════════
# LINKEDIN SCRAPER
# ══════════════════════════════════════════════════════════════════════════════

def build_linkedin_url(keyword: str, location: str, start: int = 0) -> str:
    base = "https://www.linkedin.com/jobs/search/"
    params = f"?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&start={start}"
    return base + params


def parse_linkedin_jobs(soup: BeautifulSoup, keyword: str) -> list[dict]:
    jobs = []
    job_cards = soup.find_all("div", class_="base-card")

    for card in job_cards:
        try:
            title_el = card.find("h3", class_="base-search-card__title")
            title = title_el.get_text(strip=True) if title_el else "N/A"

            company_el = card.find("h4", class_="base-search-card__subtitle")
            company = company_el.get_text(strip=True) if company_el else "N/A"

            location_el = card.find("span", class_="job-search-card__location")
            location = location_el.get_text(strip=True) if location_el else "N/A"

            link_el = card.find("a", class_="base-card__full-link", href=True)
            job_url = link_el["href"] if link_el else "N/A"

            date_el = card.find("time")
            posted = date_el.get_text(strip=True) if date_el else "N/A"

            jobs.append({
                "source": "LinkedIn",
                "keyword": keyword,
                "title": title,
                "company": company,
                "location": location,
                "salary": "Not listed",
                "posted": posted,
                "url": job_url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            logger.warning(f"  [LinkedIn] Error parsing card: {e}")
            continue

    return jobs


def scrape_linkedin(keyword: str, location: str, max_pages: int) -> list[dict]:
    all_jobs = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(max_pages):
        start = page * 25  # LinkedIn uses 25 per page
        url = build_linkedin_url(keyword, location, start)
        logger.info(f"  [LinkedIn] Page {page + 1}: {url}")

        try:
            response = session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"  [LinkedIn] Request failed: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        jobs = parse_linkedin_jobs(soup, keyword)

        if not jobs:
            logger.info("  [LinkedIn] No more jobs found.")
            break

        logger.info(f"  [LinkedIn] Found {len(jobs)} jobs on page {page + 1}")
        all_jobs.extend(jobs)

        if page < max_pages - 1:
            time.sleep(DELAY_BETWEEN_REQUESTS)

    return all_jobs


# ══════════════════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ══════════════════════════════════════════════════════════════════════════════

def save_results(jobs: list[dict], fmt: str = "csv"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if fmt == "json":
        filepath = f"output/jobs_all_{timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
    else:
        filepath = f"output/jobs_all_{timestamp}.csv"
        if jobs:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
                writer.writeheader()
                writer.writerows(jobs)

    logger.info(f"Results saved → {filepath}")
    return filepath


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    all_jobs = []

    logger.info("=" * 60)
    logger.info("Job Listings Scraper — Starting")
    logger.info(f"Keywords : {', '.join(SEARCH_KEYWORDS)}")
    logger.info(f"Location : {SEARCH_LOCATION}")
    logger.info(f"Sources  : {'Indeed ' if SCRAPE_INDEED else ''}{'LinkedIn' if SCRAPE_LINKEDIN else ''}")
    logger.info("=" * 60)

    for keyword in SEARCH_KEYWORDS:
        logger.info(f"\n🔍 Keyword: '{keyword}'")

        if SCRAPE_INDEED:
            indeed_jobs = scrape_indeed(keyword, SEARCH_LOCATION, MAX_PAGES)
            all_jobs.extend(indeed_jobs)
            logger.info(f"  Indeed total: {len(indeed_jobs)} jobs")

        if SCRAPE_LINKEDIN:
            linkedin_jobs = scrape_linkedin(keyword, SEARCH_LOCATION, MAX_PAGES)
            all_jobs.extend(linkedin_jobs)
            logger.info(f"  LinkedIn total: {len(linkedin_jobs)} jobs")

        time.sleep(DELAY_BETWEEN_REQUESTS)  # pause between keywords

    if not all_jobs:
        logger.warning("No jobs scraped. Sites may have blocked the request.")
        return

    logger.info(f"\n✅ Total jobs scraped: {len(all_jobs)}")
    filepath = save_results(all_jobs, OUTPUT_FORMAT)

    # ── Terminal preview ──
    print("\n" + "=" * 60)
    print(f"TOTAL SCRAPED: {len(all_jobs)} jobs")
    print("=" * 60)

    # Group by keyword for summary
    from collections import Counter
    keyword_counts = Counter(j["keyword"] for j in all_jobs)
    source_counts = Counter(j["source"] for j in all_jobs)

    print("\n📊 By Keyword:")
    for kw, count in keyword_counts.items():
        print(f"   {kw:<25} → {count} jobs")

    print("\n🌐 By Source:")
    for src, count in source_counts.items():
        print(f"   {src:<25} → {count} jobs")

    print(f"\n💾 Saved to: {filepath}")

    print("\n--- PREVIEW (first 5 results) ---")
    for job in all_jobs[:5]:
        print(f"\n  [{job['source']}] [{job['keyword']}]")
        print(f"  Title   : {job['title']}")
        print(f"  Company : {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  Posted  : {job['posted']}")
        print(f"  URL     : {job['url'][:80]}...")


if __name__ == "__main__":
    main()
