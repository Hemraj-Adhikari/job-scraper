#  Job Listings Web Scraper

A Python-based web scraper that extracts job listings from Indeed based on keyword and location. Results are saved to **CSV or JSON** with automatic logging.

##  Features

- Scrape job title, company, location, salary, posted date & URL
- Multi-page scraping with configurable page count
- Export to **CSV** or **JSON**
- Auto-generated timestamped logs
- Respectful request delay (no rate-limit abuse)
- Clean config file — no hardcoding needed


##  Sample Output (CSV)

| title | company | location | salary | posted | url | scraped_at |
|-------|---------|----------|--------|--------|-----|------------|
| IT Support Admin | TechCorp | Kathmandu | $30K | 2 days ago | https://... | 2024-06-10 |

##  Disclaimer

This tool is for **educational purposes only**. Always respect a website's `robots.txt` and Terms of Service. Do not use for commercial data harvesting.

## 🛠️ Tech Stack

- Python 3.10+
- [requests](https://docs.python-requests.org/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)

## 👤 Author

**Hemraj Adhikari (Raj)**  
IT Officer & Cloud Infrastructure Specialist  
 [hemrajadhikari.info.np](https://hemrajadhikari.info.np)  
💼 [LinkedIn](https://linkedin.com/in/hemrajadhikari)

---

> ⭐ If you found this useful, consider giving it a star!
