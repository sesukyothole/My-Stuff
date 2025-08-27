import requests
import re
from bs4 import BeautifulSoup
import os

BASE_URL = "https://ustvgo.kissreport.com"
CATEGORIES = [
    "local", "sport", "entertainment", "news",
    "movie", "comedy", "lifestyle"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

PLAYLIST_FILE = "USTVGO.m3u"

def extract_m3u8_from_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        matches = re.findall(r'(https://[^\s"]+\.m3u8)', resp.text)
        return matches[0] if matches else None
    except Exception as e:
        print(f"[❌] Failed to extract m3u8 from {url}: {e}")
        return None

def scrape_category(cat):
    print(f"[📺] Scraping category: {cat}")
    url = f"{BASE_URL}/category/{cat}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        links = soup.select("h3.entry-title a")
        channels = []

        for a in links:
            title = a.get_text(strip=True)
            href = a.get("href")
            print(f"  - {title}: {href}")
            m3u8_url = extract_m3u8_from_page(href)
            if m3u8_url:
                channels.append((title, m3u8_url))

        return channels
    except Exception as e:
        print(f"[❌] Failed to scrape category {cat}: {e}")
        return []

def load_existing_playlist(path):
    """Load existing playlist into dict: {title: (extinf_line, url)}"""
    if not os.path.isfile(path):
        return {}

    channels = {}
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for i in range(len(lines)):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            extinf_line = line
            url_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
            # Extract title from EXTINF (after last comma)
            title = extinf_line.split(",")[-1]
            channels[title] = (extinf_line, url_line)
    return channels

def force_group_title(extinf_line):
    # Replace or add group-title="USTVGO" in EXTINF line
    if 'group-title=' in extinf_line:
        return re.sub(r'group-title=".*?"', 'group-title="USTVGO"', extinf_line)
    else:
        return extinf_line.replace('#EXTINF:-1', '#EXTINF:-1 group-title="USTVGO"')

def main():
    existing_channels = load_existing_playlist(PLAYLIST_FILE)
    new_channels_raw = []

    for cat in CATEGORIES:
        new_channels_raw.extend(scrape_category(cat))

    # Merge preserving metadata, updating URLs, force group-title
    merged = {}

    # First, add all existing channels (metadata)
    for title, (extinf, url) in existing_channels.items():
        merged[title] = {"extinf": force_group_title(extinf), "url": url}

    # Update/add from newly scraped channels
    for title, url in new_channels_raw:
        if title in merged:
            # Update URL, keep metadata extinf (with forced group-title)
            merged[title]["url"] = url
        else:
            # New channel: create extinf line with forced group-title
            extinf_line = f'#EXTINF:-1 group-title="USTVGO",{title}'
            merged[title] = {"extinf": extinf_line, "url": url}

    # Sort alphabetically by title
    sorted_channels = dict(sorted(merged.items()))

    # Write to playlist file
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for title, data in sorted_channels.items():
            f.write(data["extinf"] + "\n")
            f.write(data["url"] + "\n")

    print(f"[✅] Saved {len(sorted_channels)} channels to {PLAYLIST_FILE}")

if __name__ == "__main__":
    main()
