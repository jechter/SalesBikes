# SalesBikes

A simple, static website for a bicycle co-op that repairs donated bikes and gives them to refugees and people in need. Special or higher-value bikes (e.g. road bikes) are sold to cover the co-op's operating costs. This site lists the bikes currently for sale.

## How it works

- Bike inventory is managed in a **Google Sheet** (published to the web).
- The site fetches data from the sheet at page load using Google's Visualization API (`/gviz/tq?tqx=out:json`).
- Only bikes with status "available" are displayed.
- There is no backend — this is a purely client-side, single-page site that can be hosted anywhere (GitHub Pages, Netlify, etc.).

## Google Sheet structure

The sheet is at: `https://docs.google.com/spreadsheets/d/1V_8ExLOLyxVXeImMNdwBGJ9EKeqKqVVZPl_8DVevNC4`

Expected columns (0-indexed):

| Column | Field       | Description                          |
|--------|-------------|--------------------------------------|
| 0      | (unused/ID) | Row identifier or internal use       |
| 1      | Name        | Bike name / model                    |
| 2      | Price       | Price in euros                       |
| 3      | Description | Short text describing the bike       |
| 4      | Image URL   | URL to a photo of the bike           |
| 5      | Status      | "available", "sold", etc.            |

## Tech stack

- Single HTML file with inline CSS and JavaScript
- No build step, no dependencies, no framework
- Vanilla JS `fetch()` to pull data from the Google Sheet

## Design goals

- Keep it simple: co-op volunteers with limited tech skills should be able to update inventory by editing the Google Sheet.
- The site should look appealing and be easy to browse on both desktop and mobile.
- Prices are displayed in euros (€).
- Sold or reserved bikes are hidden from the listing automatically.
