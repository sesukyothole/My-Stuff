import requests
import re
import socket
from datetime import datetime

UPSTREAM_URL = "https://iptv-scraper-re.vercel.app/nflwebcast/nflwebcast.m3u8"
EPG_URL = "http://drewlive24.duckdns.org:8081/merged3_epg.xml.gz"
OUTPUT_FILE = "NFL-Webcast.m3u"
FORCED_GROUP = "NFL"
FORCED_TVG_ID = "24.7.Dummy.us"

# Force IPv4 for all requests
def force_ipv4(host, port=0, family=0, type=0, proto=0, flags=0):
    return [(socket.AF_INET, socket.SOCK_STREAM, proto, "", (host, port))]
socket.getaddrinfo = force_ipv4

def inject_group_and_tvgid(extinf_line):
    extinf_line = re.sub(r'tvg-id="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'group-title="[^"]*"', '', extinf_line)
    extinf_line = re.sub(r'(#EXTINF:-1)\s+-1\s+', r'\1 ', extinf_line)
    extinf_line = extinf_line.replace(
        "#EXTINF:-1",
        f'#EXTINF:-1 tvg-id="{FORCED_TVG_ID}" group-title="{FORCED_GROUP}"',
        1
    )
    extinf_line = re.sub(r'\s+', ' ', extinf_line).strip()
    extinf_line = re.sub(r' ,', ',', extinf_line)
    return extinf_line

def main():
    print("[🔁] Fetching upstream playlist...")

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': '*/*',
        'Cache-Control': 'no-cache'
    }

    try:
        res = requests.get(UPSTREAM_URL, headers=headers, timeout=30)
        res.raise_for_status()
        lines = res.text.strip().splitlines()
        print(f"[✅] Upstream fetched: {len(lines)} lines.")
    except requests.exceptions.RequestException as e:
        print(f"[❌] Failed to fetch upstream: {e}")
        return

    output_lines = [
        f'#EXTM3U url-tvg="{EPG_URL}"',
        f'# Last forced update: {datetime.utcnow().isoformat()}Z'
    ]

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF:-1"):
            fixed_line = inject_group_and_tvgid(line)
            output_lines.append(fixed_line)
        else:
            output_lines.append(line)

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(output_lines) + "\n")
        print(f"[💾] Playlist saved to {OUTPUT_FILE}")
    except Exception as e:
        print(f"[❌] Failed to write playlist: {e}")

if __name__ == "__main__":
    main()
