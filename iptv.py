import requests
import re
from datetime import datetime

# Playlist sources
playlist_urls = [
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLive.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DaddyLiveEvents.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/DrewAll.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/PlutoTV.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TVPass.m3u",
    "http://drewlive24.duckdns.org:8081/PPVLand.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/StreamEast.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/FSTV24.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/TheTVApp.m3u8",
    "http://drewlive24.duckdns.org:8081/Tims247.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/AriaPlus.m3u8",
    "http://drewlive24.duckdns.org:8081/Zuzz.m3u8",
    "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/SamsungTVPlus.m3u8",
]

EPG_URL = "https://tinyurl.com/DrewLive002-epg"
OUTPUT_FILE = "MergedPlaylist.m3u8"

# -------------------------
# Fetch playlist content
# -------------------------
def fetch_playlist(url):
    print(f"\n🔹 Fetching playlist: {url}")
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        print(f"✅ Successfully fetched: {url} ({len(res.content)} bytes)")
        return res.content.decode('utf-8', errors='ignore').splitlines()
    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return []

# -------------------------
# Parse channels from playlist
# -------------------------
def parse_playlist(lines, source_url="Unknown"):
    parsed_channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf_line = line
            headers = []
            i += 1
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                headers.append(lines[i].strip())
                i += 1
            if i < len(lines):
                url_line = lines[i].strip()
                i += 1
                if not url_line or url_line.lower() in ["*", "none", "null"]:
                    print(f"⚠️ Removed dead channel from {source_url}: {extinf_line}")
                    continue
                print(f"✅ Parsed channel from {source_url}: {extinf_line}")
                parsed_channels.append((extinf_line, tuple(headers), url_line))
        else:
            i += 1
    print(f"ℹ️ Total valid channels parsed from {source_url}: {len(parsed_channels)}")
    return parsed_channels

# -------------------------
# Write merged playlist
# -------------------------
def write_merged_playlist(channels):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"', ""]
    # Remove duplicates by URL
    unique_channels = {}
    for extinf, headers, url in channels:
        unique_channels[url] = (extinf, headers, url)

    sorted_channels = sorted(unique_channels.values(), key=lambda x: re.search(r',([^,]+)$', x[0]).group(1).lower())

    current_group = None
    total_channels_written = 0
    for extinf, headers, url in sorted_channels:
        group_match = re.search(r'group-title="([^"]+)"', extinf)
        group_name = group_match.group(1) if group_match else "Other"
        if group_name != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f'#EXTGRP:{group_name}')
            current_group = group_name
        lines.append(extinf)
        lines.extend(headers)
        lines.append(url)
        total_channels_written += 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n✅ Merged playlist written to {OUTPUT_FILE}.")
    print(f"📊 Total unique channels merged: {total_channels_written}")

# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    print(f"🕒 Starting merge at {datetime.now()}...")
    all_channels = []
    for url in playlist_urls:
        lines = fetch_playlist(url)
        parsed = parse_playlist(lines, source_url=url)
        all_channels.extend(parsed)

    write_merged_playlist(all_channels)
    print(f"🕒 Merge complete at {datetime.now()}")
