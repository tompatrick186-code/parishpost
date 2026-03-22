"""
Parish Post — Find UK parish councils via DuckDuckGo
Outputs parishes.csv with name, email, website, county
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
from urllib.parse import urlparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}

COUNTIES = [
    "Oxfordshire", "Cambridgeshire", "Suffolk", "Norfolk", "Devon",
    "Somerset", "Wiltshire", "Gloucestershire", "Worcestershire", "Shropshire",
    "Herefordshire", "Derbyshire", "Lincolnshire", "Yorkshire", "Kent",
    "Sussex", "Hampshire", "Dorset", "Cheshire", "Lancashire",
]


def ddg_search(query):
    results = []
    url = "https://html.duckduckgo.com/html/"
    data = {"q": query, "kl": "uk-en"}

    for attempt in range(3):
        resp = requests.post(url, data=data, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            break
        time.sleep(random.uniform(10, 20))

    if resp.status_code != 200:
        return results

    soup = BeautifulSoup(resp.text, "html.parser")
    for a in soup.select("a.result__url"):
        href = a.get("href", "")
        if href and href.startswith("http"):
            results.append(href)

    return results[:10]


def extract_email_from_site(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resp.text)
        for email in emails:
            if any(x in email.lower() for x in ["clerk", "parish", "council", "info", "contact", "admin"]):
                return email.lower()
        if emails:
            return emails[0].lower()
    except Exception:
        pass

    domain = urlparse(url).netloc.replace("www.", "")
    return f"clerk@{domain}"


def find_parishes(output_file="parishes.csv"):
    found = []
    seen_domains = set()

    for county in COUNTIES:
        print(f"Searching {county}...")
        queries = [
            f"parish council clerk {county} contact email",
            f"parish council {county} clerk email",
            f"village parish council {county} newsletter",
        ]

        for query in queries:
            urls = ddg_search(query)
            for url in urls:
                domain = urlparse(url).netloc
                if domain in seen_domains:
                    continue
                if not any(x in url.lower() for x in ["parish", "village", "council", "pc.", "-pc", "towncouncil"]):
                    continue

                seen_domains.add(domain)
                name = domain.replace("www.", "").replace(".gov.uk", "").replace(".org.uk", "").replace("-", " ").replace(".", " ").title()
                email = extract_email_from_site(url)

                found.append({
                    "name": name,
                    "website": url,
                    "email": email,
                    "county": county,
                    "emailed": "no",
                })
                print(f"  Found: {name} — {email}")

            time.sleep(random.uniform(6, 10))

    fieldnames = ["name", "website", "email", "county", "emailed"]
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(found)

    print(f"\nDone — {len(found)} parishes saved to {output_file}")


if __name__ == "__main__":
    find_parishes()
