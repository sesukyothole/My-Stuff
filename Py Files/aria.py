import requests
import re

PLAYLIST_URL = "https://theariatv.github.io/aria.m3u"

ALLOWED_COUNTRIES = [
    "Australia", "Canada", "New Zealand", "United Kingdom", "United States"
]

# Optional: aliases so matching works even if group-title doesn't have the exact name
COUNTRY_ALIASES = {
    "Australia": ["Australia", "AUS"],
    "Canada": ["Canada", "CAN"],
    "New Zealand": ["New Zealand", "NZ"],
    "United Kingdom": ["United Kingdom", "UK", "Britain", "England"],
    "United States": ["United States", "USA", "US", "America"]
}

def fetch_playlist(url):
    r = requests.get(url)
    r.raise_for_status()
    return r.text.splitlines()

def force_group_title(line, country):
    # Remove any existing group-title attribute
    line = re.sub(r'\s*group-title="[^"]*"', '', line)
    line = re.sub(r'\s{2,}', ' ', line).strip()

    if line.startswith("#EXTINF:"):
        parts = line.split(",", 1)
        header = parts[0]
        title = parts[1] if len(parts) > 1 else ""

        # New forced group-title
        new_group = f'AriaPlus - {country}'
        header = header.strip() + f' group-title="{new_group}"'

        return f"{header},{title}"
    return line

def parse_and_filter(lines):
    output_lines = ["#EXTM3U"]
    keep_channel = False
    current_country = ""

    for line in lines:
        if line.startswith("#EXTINF"):
            country_match = re.search(r'group-title="([^"]+)"', line)
            country_text = country_match.group(1) if country_match else ""

            # Also include channel name in search
            title_text = line.split(",", 1)[1] if "," in line else ""
            search_area = (country_text + " " + title_text).lower()

            matched_country = ""
            for c, aliases in COUNTRY_ALIASES.items():
                if any(alias.lower() in search_area for alias in aliases):
                    matched_country = c
                    break

            if matched_country:
                line = force_group_title(line, matched_country)
                output_lines.append(line)
                keep_channel = True
                current_country = matched_country
            else:
                keep_channel = False
                current_country = ""
        elif line.startswith("http"):
            if keep_channel:
                output_lines.append(line)

    return "\n".join(output_lines)

if __name__ == "__main__":
    lines = fetch_playlist(PLAYLIST_URL)
    filtered_playlist = parse_and_filter(lines)
    with open("AriaPlus.m3u8", "w", encoding="utf-8") as f:
        f.write(filtered_playlist)
    print("✅ AriaPlus playlist updated with categorized group-titles per country.")
