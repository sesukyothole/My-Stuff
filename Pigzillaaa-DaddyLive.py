import requests
import re
import time
from datetime import datetime

playlist_urls = [
    "https://raw.githubusercontent.com/pigzillaaa/daddylive/refs/heads/main/daddylive-channels.m3u8"
]

UDPTV_URL = "https://raw.githubusercontent.com/Drewski2423/DrewLive/refs/heads/main/UDPTV.m3u"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged3_epg.xml.gz"
OUTPUT_FILE = "Pigzillaaa-DaddyLive.m3u"

def fetch_playlist(url, retries=3, delay=5):
    """Fetch playlist with retries for non-GitHub raw URLs."""
    print(f"📡 Fetching playlist: {url}")
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.content.decode("utf-8", errors="ignore").splitlines()
        except Exception as e:
            print(f"❌ Attempt {attempt} failed for {url}: {e}")
            if "raw.githubusercontent.com" not in url and attempt < retries:
                print(f"⏳ Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                break
    print(f"❌ Failed to fetch {url}")
    return []

def extract_udptv_timestamp(lines):
    for line in lines:
        if line.strip().startswith("# Last forced update:"):
            print(f"✅ UDPTV timestamp found: {line.strip()}")
            return line.strip()
    print("⚠️ UDPTV timestamp not found.")
    return None

def parse_playlist(lines, source="Unknown"):
    parsed = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            metadata = []
            i += 1

            # Collect metadata lines
            while i < len(lines) and lines[i].strip().startswith("#") and not lines[i].strip().startswith("#EXTINF:"):
                metadata.append(lines[i].strip())
                i += 1

            # Expect a URL
            if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("#"):
                url = lines[i].strip()
                parsed.append((extinf, tuple(metadata), url))
                i += 1
            else:
                print(f"⚠️ Skipping orphaned EXTINF in {source}: {extinf}")
        else:
            i += 1

    print(f"✅ Parsed {len(parsed)} channels from {source}")
    return parsed

def write_merged_playlist(channels, udptv_timestamp):
    lines = [f'#EXTM3U url-tvg="{EPG_URL}"']
    if udptv_timestamp:
        lines.append(udptv_timestamp)
    lines.append("")

    def get_group_title(extinf):
        m = re.search(r'group-title="([^"]+)"', extinf)
        return m.group(1) if m else "Other"

    def get_channel_name(extinf):
        m = re.search(r',([^,]+)$', extinf)
        return m.group(1).strip() if m else ""

    sorted_channels = sorted(
        channels,
        key=lambda c: (get_group_title(c[0]).lower(), get_channel_name(c[0]).lower())
    )

    current_group = None
    for extinf, metadata, url in sorted_channels:
        group = get_group_title(extinf)
        if group != current_group:
            if current_group is not None:
                lines.append("")
            lines.append(f"#EXTGRP:{group}")
            current_group = group

        lines.append(extinf)
        lines.extend(metadata)
        lines.append(url)

    if lines and lines[-1] != "":
        lines.append("")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Merged playlist saved to {OUTPUT_FILE}")
    print(f"📺 Total channels: {len(channels)}")
    print(f"🕒 Saved at: {datetime.now()}")

if __name__ == "__main__":
    print(f"🚀 Starting merge at {datetime.now()}\n")

    all_channels = []

    # UDPTV first
    udptv_lines = fetch_playlist(UDPTV_URL)
    udptv_timestamp = extract_udptv_timestamp(udptv_lines)
    all_channels.extend(parse_playlist(udptv_lines, source="UDPTV"))

    # Others
    for url in playlist_urls:
        if url == UDPTV_URL:
            continue
        lines = fetch_playlist(url)
        all_channels.extend(parse_playlist(lines, source=url))

    write_merged_playlist(all_channels, udptv_timestamp)

    print(f"\n✅ Merge complete at {datetime.now()}")
