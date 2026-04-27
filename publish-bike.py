#!/usr/bin/env python3
"""
Publish a bike from the Rückenwind sales page to kleinanzeigen.de.

Setup (one-time):
  1. Run: .venv/bin/python -m kleinanzeigen_bot create-config
     → Edit the generated config.yaml with your kleinanzeigen.de login credentials.
  2. The default ad_files pattern ("./**/ad_*.yaml") will find generated ads automatically.

Usage:
  python3 publish-bike.py <bike-share-url>
  python3 publish-bike.py --dry-run <bike-share-url>

Example:
  python3 publish-bike.py "https://rueckenwind.github.io/salesbikes.html#bike-rennrad-bianchi"
  python3 publish-bike.py --dry-run "https://rueckenwind.github.io/salesbikes.html#bike-rennrad-bianchi"
"""

import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1yetJyZLSLszZaw6icMQaUiUlQHiFO_B1beAT-HNcHJQ"
    "/gviz/tq?tqx=out:json"
)
API_KEY = "AIzaSyC0x2Bbiq1YclQJtMBhBjZfrqYW-vdhBJQ"
ZIPCODE = "12047"
CATEGORY_BASE = "210/217"

SCRIPT_DIR = Path(__file__).resolve().parent
FOOTER_FILE = SCRIPT_DIR / "ad-footer.txt"
ADS_DIR = SCRIPT_DIR / "kleinanzeigen-ads"
VENV_PYTHON = SCRIPT_DIR / ".venv" / "bin" / "python"


def slugify(name):
    """Replicate the JS slug: 'bike-' + name.replace(/\\W+/g, '-').toLowerCase()"""
    return "bike-" + re.sub(r"\W+", "-", name, flags=re.ASCII).lower()


def fetch_sheet():
    """Fetch and parse the Google Sheet data."""
    req = urllib.request.Request(SHEET_URL)
    with urllib.request.urlopen(req) as resp:
        text = resp.read().decode("utf-8")
    start = text.index("(")
    end = text.rindex(")")
    data = json.loads(text[start + 1 : end])
    return data["table"]["rows"]


def find_bike(rows, bike_id):
    """Find the bike row matching the given slug ID."""
    for row in rows:
        cells = row.get("c", [])
        name = cells[1]["v"] if cells[1] else None
        if not name:
            continue
        if slugify(name) == bike_id:
            price = cells[2]["v"] if cells[2] else 0
            desc = cells[3]["v"] if cells[3] else ""
            folder_url = cells[4]["v"] if len(cells) > 4 and cells[4] else None
            bike_type = cells[6]["v"].strip().lower() if len(cells) > 6 and cells[6] else ""
            bike_art = cells[7]["v"].strip().lower() if len(cells) > 7 and cells[7] else "herren"
            return {
                "name": name,
                "price": price,
                "description": desc,
                "folder_url": folder_url,
                "bike_type": bike_type,
                "bike_art": bike_art,
            }
    return None


def extract_folder_id(url):
    """Extract Google Drive folder ID from a folder URL."""
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def fetch_drive_images(folder_url):
    """List image files in a Google Drive folder via the Drive API."""
    folder_id = extract_folder_id(folder_url)
    if not folder_id:
        return []
    api_url = (
        f"https://www.googleapis.com/drive/v3/files"
        f"?q=%27{folder_id}%27+in+parents+and+mimeType+contains+%27image%27"
        f"&key={API_KEY}"
        f"&fields=files(id,name)"
        f"&orderBy=name"
    )
    req = urllib.request.Request(api_url)
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("files", [])


def download_image(file_id, dest_path):
    """Download a single image from Google Drive."""
    url = (
        f"https://www.googleapis.com/drive/v3/files/{file_id}"
        f"?alt=media&key={API_KEY}"
    )
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        with open(dest_path, "wb") as f:
            f.write(resp.read())


def yaml_escape(s):
    """Escape a string for use as a YAML double-quoted value."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def generate_ad_yaml(bike, image_paths):
    """Generate the kleinanzeigen-bot ad YAML config."""
    footer = FOOTER_FILE.read_text(encoding="utf-8").strip() if FOOTER_FILE.exists() else ""
    description = bike["description"].rstrip()
    if footer:
        description += "\n\n" + footer
    indented_desc = textwrap.indent(description, "  ")

    images_lines = ""
    for img in image_paths:
        images_lines += f'\n  - "images/{img.name}"'

    # Build category and special_attributes
    bike_art = bike.get("bike_art", "herren")
    bike_type = bike.get("bike_type", "")
    category = f"{CATEGORY_BASE}/{bike_art}"

    special_attrs = f"special_attributes:\n  art_s: {bike_art}\n  versand_s: nein\n"
    if bike_type:
        special_attrs += f"  type_s: {bike_type}\n"

    return (
        f'active: true\n'
        f'type: OFFER\n'
        f'title: "{yaml_escape(bike["name"])}"\n'
        f'description: |\n'
        f'{indented_desc}\n'
        f'category: {category}\n'
        f'{special_attrs}'
        f'price: {int(bike["price"])}\n'
        f'price_type: FIXED\n'
        f'shipping_type: PICKUP\n'
        f'sell_directly: false\n'
        f'contact:\n'
        f'  zipcode: "{ZIPCODE}"\n'
        f'images:{images_lines}\n'
    )


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("Usage: python3 publish-bike.py [--dry-run] <bike-share-url>")
        print()
        print("The URL is the share link from the bike sales page, e.g.:")
        print('  python3 publish-bike.py "https://example.com/salesbikes.html#bike-rennrad-bianchi"')
        print()
        print("Options:")
        print("  --dry-run  Generate the ad config without publishing")
        sys.exit(1)

    url = args[0]

    # Extract bike ID from URL hash or accept a bare ID
    parsed = urlparse(url)
    bike_id = parsed.fragment
    if not bike_id:
        if url.startswith("bike-"):
            bike_id = url
        else:
            print(f"Error: URL must contain a #bike-xxx hash fragment.")
            print(f"Got: {url}")
            sys.exit(1)

    # Remove trailing hyphen if present (from trailing non-word chars in name)
    bike_id = bike_id.rstrip("-")

    print(f"Looking up: {bike_id}")
    print()

    # Fetch sheet data and find the bike
    rows = fetch_sheet()
    bike = find_bike(rows, bike_id)
    if not bike:
        print(f"Error: No bike found matching '{bike_id}'")
        print()
        print("Available bikes:")
        for row in rows:
            cells = row.get("c", [])
            name = cells[1]["v"] if cells[1] else "(unnamed)"
            sid = slugify(name)
            print(f"  {sid}  ->  {name}")
        sys.exit(1)

    print(f"  Name:  {bike['name']}")
    print(f"  Price: {int(bike['price'])} EUR")
    print()

    # Create ad directory
    ad_dir = ADS_DIR / bike_id
    images_dir = ad_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Download images
    image_paths = []
    if bike["folder_url"]:
        files = fetch_drive_images(bike["folder_url"])
        print(f"Downloading {len(files)} image(s)...")
        for f in files:
            dest = images_dir / f["name"]
            if dest.exists():
                print(f"  . {f['name']} (cached)")
            else:
                download_image(f["id"], dest)
                print(f"  + {f['name']}")
            image_paths.append(dest)
    else:
        print("No image folder linked for this bike.")
    print()

    # Generate the ad YAML config
    yaml_content = generate_ad_yaml(bike, image_paths)
    yaml_path = ad_dir / f"ad_{bike_id}.yaml"
    yaml_path.write_text(yaml_content, encoding="utf-8")
    print(f"Ad config written to: {yaml_path}")

    if dry_run:
        print()
        print("--- Ad config preview ---")
        print(yaml_content)
        print("Run without --dry-run to publish.")
    else:
        # Build a temporary config that only sees this one ad file,
        # so we don't accidentally publish leftover ads from dry runs.
        main_config = SCRIPT_DIR / "config.yaml"
        if not main_config.exists():
            print("Error: config.yaml not found. Run this first:")
            print("  .venv/bin/python -m kleinanzeigen_bot create-config")
            sys.exit(1)

        config_text = main_config.read_text(encoding="utf-8")
        # Replace or append ad_files to point only at this ad.
        # The field can be a scalar or a YAML list (key + indented "- ..." lines),
        # so we match the key line and any following indented lines.
        ad_pattern = str(yaml_path)
        if re.search(r'^ad_files\s*:', config_text, re.MULTILINE):
            config_text = re.sub(
                r'^ad_files\s*:.*(?:\n[ \t]+.*)*',
                f'ad_files:\n  - "{ad_pattern}"',
                config_text, count=1, flags=re.MULTILINE,
            )
        else:
            config_text += f'\nad_files:\n  - "{ad_pattern}"\n'

        # Disable incognito mode — the kleinanzeigen Business portal UI
        # shown in private windows is not supported by kleinanzeigen-bot.
        if re.search(r'^  use_private_window\s*:', config_text, re.MULTILINE):
            config_text = re.sub(
                r'^(  use_private_window\s*:).*',
                r'\1 false',
                config_text, count=1, flags=re.MULTILINE,
            )

        tmp_config = SCRIPT_DIR / "_publish_config.yaml"
        tmp_config.write_text(config_text, encoding="utf-8")

        print()
        print("Publishing to kleinanzeigen.de...")
        try:
            result = subprocess.run(
                [str(VENV_PYTHON), "-m", "kleinanzeigen_bot", "publish",
                 "--ads=new", f"--config={tmp_config}", "--workspace-mode=portable"],
                cwd=SCRIPT_DIR,
            )
            if result.returncode == 0:
                print("Done!")
            else:
                print(f"kleinanzeigen-bot exited with code {result.returncode}")
                sys.exit(result.returncode)
        finally:
            tmp_config.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
