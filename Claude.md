# SalesBikes

A simple, static website for a bicycle co-op that repairs donated bikes and gives them to refugees and people in need. Special or higher-value bikes (e.g. road bikes) are sold to cover the co-op's operating costs. This site lists the bikes currently for sale.

## How it works

- Bike inventory is managed in a **Google Sheet** (published to the web).
- The site fetches data from the sheet at page load using Google's Visualization API (`/gviz/tq?tqx=out:json`).
- Bike images are stored in Google Drive folders (one folder per bike), listed via the Drive API.
- There is no backend — this is a purely client-side, single-page site that can be hosted anywhere (GitHub Pages, Netlify, etc.).

## Google Sheet structure

The sheet is at: `https://docs.google.com/spreadsheets/d/1yetJyZLSLszZaw6icMQaUiUlQHiFO_B1beAT-HNcHJQ`

The first row contains headers. Expected columns (0-indexed):

| Column | Field        | Description                                    |
|--------|--------------|------------------------------------------------|
| 0      | Listing Date | Date the bike was listed                       |
| 1      | Title        | Bike name / model                              |
| 2      | Price        | Price in euros                                 |
| 3      | Description  | Short text describing the bike                 |
| 4      | Image links  | URL to a Google Drive folder containing photos |
| 5      | Status       | "available", "sold", etc.                      |

## Tech stack

- Single HTML file with inline CSS and JavaScript
- No build step, no dependencies, no framework
- Vanilla JS `fetch()` to pull data from the Google Sheet
- Google Drive API (with API key) to list images in Drive folders

## Design goals

- Keep it simple: co-op volunteers with limited tech skills should be able to update inventory by editing the Google Sheet.
- The site should look appealing and be easy to browse on both desktop and mobile.
- Prices are displayed in euros (EUR).
- Styling matches the main rueckenwind.berlin website (green #53a735, Arial/Trebuchet MS fonts).

## Publishing to kleinanzeigen.de

`publish-bike.py` cross-posts a bike listing from the sales site to kleinanzeigen.de.

- Uses [kleinanzeigen-bot](https://github.com/Second-Hand-Friends/kleinanzeigen-bot), installed from git into `.venv/`.
- Install or update the pinned version with `./update-kleinanzeigen-bot.sh`.
- The pinned revision is recorded in `requirements-kleinanzeigen.txt`; update it together with the revision in the updater script.
- Usage: `python3 publish-bike.py <bike-share-url>` (or `--dry-run` to preview without publishing).
- Requires `config.yaml` with kleinanzeigen.de login credentials (created via `.venv/bin/python -m kleinanzeigen_bot create-config`).
- Generated ad configs are stored in `kleinanzeigen-ads/<bike-id>/`.
- The ad description is appended with content from `ad-footer.txt`.
