# EBRD Job Scraper

A Python script that extracts current job opportunities from the European Bank for Reconstruction and Development (EBRD) website and generates an RSS feed.

## Features

✓ Scrapes all job listings from EBRD careers website
✓ Extracts job title, location, and posting date
✓ Handles pagination automatically (fetches all pages)
✓ Saves data in RSS 2.0 format as `ebrd_jobs.xml`
✓ Removes duplicate listings

## Prerequisites

- Python 3.7 or higher

## Installation

1. Navigate to the project directory:
```bash
cd ebrd-scraper
```

2. Install required packages:
```bash
py -m pip install -r requirements.txt
```

## Usage

Run the scraper:

```bash
py ebrd_scraper.py
```

The script will:
1. Fetch all pages of job listings from EBRD
2. Extract job information (title, location, posting date)
3. Remove duplicates
4. Generate `ebrd_jobs.xml` RSS feed

## Output

The RSS feed `ebrd_jobs.xml` contains:

- **Job Title** - Full position title
- **Link** - URL to detailed job description
- **Location** - City and country
- **Posting Date** - When the job was posted

### Example RSS Feed Structure:

```xml
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>EBRD Job Vacancies</title>
    <link>https://jobs.ebrd.com/search/</link>
    <description>Current job opportunities at EBRD</description>
    <item>
      <title>Associate, Azure DevOps Engineer</title>
      <link>https://jobs.ebrd.com/job/...</link>
      <description>Location: London, GB
Posting Date: 05/02/2026</description>
    </item>
  </channel>
</rss>
```

## Technical Details

### Architecture

- **Requests**: HTTP library for fetching pages
- **BeautifulSoup**: HTML parser
- **Static HTML**: No JavaScript rendering needed (faster than Selenium)

### Data Structure

Jobs are extracted from HTML table with class `searchResultsTable`:
```html
<table class="searchResultsTable">
  <tr class="data-row">
    <td class="coljobtitle"><a href="...">Title</a></td>
    <td class="collocation">Location</td>
    <td class="coldate">Posting Date</td>
  </tr>
</table>
```

## Notes

- The script respects the server with 1-second delays between page requests
- Pagination: 25 jobs per page
- Safety limit: Maximum 10 pages (250 jobs)
- EBRD typically has 50-100 active job listings

## Source

**EBRD Jobs Website:** https://jobs.ebrd.com/search/

## License

This script is for informational purposes only. Please respect EBRD's terms of service.
