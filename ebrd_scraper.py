#!/usr/bin/env python3
"""
EBRD Job Scraper
Extracts job listings from EBRD careers website and generates RSS feed
Uses Selenium to handle JavaScript-rendered content
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import time

BASE_URL = "https://jobs.ebrd.com"
SEARCH_URL = f"{BASE_URL}/search/?q=&sortColumn=referencedate&sortDirection=desc"

def setup_driver():
    """Setup Chrome WebDriver with headless mode"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_jobs_with_selenium():
    """Fetch all job listings using Selenium"""
    print("Starting Chrome browser (headless mode)...")
    driver = setup_driver()
    all_jobs = []

    try:
        print(f"Loading EBRD jobs page...")
        driver.get(SEARCH_URL)

        # Wait for the page to load
        print("Waiting for page content to load...")
        time.sleep(5)  # Give JavaScript time to render

        # Wait for job listings to appear
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "searchResults"))
            )
            print("[OK] Job listings table found")
        except Exception as e:
            print(f"Warning: Timeout waiting for job listings table: {e}")

        # Get the page HTML
        html_content = driver.page_source

        # Save debug HTML
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("[OK] Saved debug HTML to debug_page.html")

        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the job listings table (searchResults class)
        table = soup.find('table', {'class': 'searchResults'})

        if not table:
            print("ERROR: Could not find job listings table")
            # Try to find any table
            all_tables = soup.find_all('table')
            print(f"Found {len(all_tables)} table(s) total")
            if all_tables:
                print("Table classes found:", [t.get('class') for t in all_tables])
            return []

        print("[OK] Job table found, parsing jobs...")

        # Find all job rows
        rows = table.find_all('tr', {'class': 'data-row'})

        if not rows:
            # Try alternative selectors
            rows = table.find_all('tr')
            rows = [r for r in rows if r.find('a')]  # Keep only rows with links

        print(f"Found {len(rows)} job rows")

        for row in rows:
            try:
                # Find the job title link
                link = row.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                job_url = link.get('href', '')

                # Make URL absolute
                if job_url.startswith('/'):
                    job_url = BASE_URL + job_url
                elif not job_url.startswith('http'):
                    job_url = BASE_URL + '/' + job_url

                # Find all cells in the row
                cells = row.find_all('td')

                # Extract location and date (if available)
                location = 'Not specified'
                posting_date = 'Not specified'

                if len(cells) >= 2:
                    location = cells[1].get_text(strip=True) if cells[1] else 'Not specified'
                if len(cells) >= 3:
                    posting_date = cells[2].get_text(strip=True) if cells[2] else 'Not specified'

                # Skip if we don't have essential info
                if not title or not job_url or title == '':
                    continue

                all_jobs.append({
                    'title': title,
                    'link': job_url,
                    'location': location,
                    'posting_date': posting_date
                })

            except Exception as e:
                print(f"Error parsing job row: {e}")
                continue

    finally:
        driver.quit()
        print("[OK] Browser closed")

    return all_jobs

def create_rss_feed(jobs):
    """Generate RSS 2.0 feed from job listings"""

    # Create RSS root
    rss = ET.Element('rss', version='2.0', attrib={'xmlns:atom': 'http://www.w3.org/2005/Atom'})

    # Create channel
    channel = ET.SubElement(rss, 'channel')

    # Channel metadata
    ET.SubElement(channel, 'title').text = 'EBRD Job Vacancies'
    ET.SubElement(channel, 'link').text = SEARCH_URL
    ET.SubElement(channel, 'description').text = 'Current job opportunities at the European Bank for Reconstruction and Development'
    ET.SubElement(channel, 'language').text = 'en'
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Add atom:link for feed validation
    atom_link = ET.SubElement(channel, 'atom:link')
    atom_link.set('href', 'https://cinfoposte.github.io/ebrd-jobs/ebrd_jobs.xml')
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    # Add job items
    for job in jobs:
        item = ET.SubElement(channel, 'item')

        # Title
        ET.SubElement(item, 'title').text = job['title']

        # Link
        ET.SubElement(item, 'link').text = job['link']

        # Description with location and posting date
        description = f"Location: {job['location']}\nPosting Date: {job['posting_date']}"
        ET.SubElement(item, 'description').text = description

        # Publication date (use current date as fallback)
        ET.SubElement(item, 'pubDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        # GUID (use job URL)
        guid = ET.SubElement(item, 'guid')
        guid.set('isPermaLink', 'true')
        guid.text = job['link']

    return rss

def prettify_xml(element):
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(element, encoding='utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

def main():
    """Main scraper function"""
    print("=" * 60)
    print("EBRD Job Scraper")
    print("=" * 60)

    # Fetch all jobs
    jobs = fetch_jobs_with_selenium()

    if not jobs:
        print("No jobs found!")
        return

    # Remove duplicates (by link)
    unique_jobs = []
    seen_links = set()
    for job in jobs:
        if job['link'] not in seen_links:
            unique_jobs.append(job)
            seen_links.add(job['link'])

    print(f"\nUnique jobs: {len(unique_jobs)}")

    # Create RSS feed
    print("\nGenerating RSS feed...")
    rss_feed = create_rss_feed(unique_jobs)

    # Save to file
    output_file = 'ebrd_jobs.xml'
    xml_content = prettify_xml(rss_feed)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print(f"\n[SUCCESS] RSS feed saved to: {output_file}")
    print(f"[SUCCESS] Total jobs in feed: {len(unique_jobs)}")
    print("\nSample jobs:")
    for i, job in enumerate(unique_jobs[:5], 1):
        print(f"{i}. {job['title']} - {job['location']}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == '__main__':
    main()
