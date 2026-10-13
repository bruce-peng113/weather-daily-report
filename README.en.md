# Weather Daily Report

A multi-city weather dashboard for apparel / e-commerce operations. It automatically pulls weather data, generates a visual dashboard, and pushes images to a Feishu (Lark) group.

> ⚠️ **Current version is China-only**: the data source is Amap Weather (Chinese cities only), the map is a China map, and the push channel is Feishu. A global/international version is planned but not yet available.

> Background: when you sell clothes, you have to watch the weather every day to decide what to stock and which items to promote. This tool automates the whole "watching the weather" routine — every morning it generates a daily report for 36+ cities and pushes it straight to your Feishu group, so you can see national hot/cold spots, cooling cities, and dressing advice at a glance.

## Features

- 🌡️ **Multi-city real-time weather**: Amap (Gaode) Weather API, supports 36+ core cities (customizable by region)
- 📊 **Visual dashboard**: China Meteorological Administration color scale (blue = cold → red = hot), weather emoji icons, 4-day temperature trend lines
- 🗺️ **China map heat layer**: province-average temperature coloring + dashed province/national boundaries and the nine-dash line (official Alibaba DataV GeoJSON)
- 📅 **Year-over-year comparison**: Open-Meteo free historical API to tell whether this year is colder or warmer
- 📱 **Feishu image push**: automatically screenshots the dashboard and sends the image to a group via a Feishu bot
- ⏰ **Schedulable automation**: works with any scheduler to run automatically every morning

## Preview

![Dashboard example](dashboard.png)

## Quick Start

### 1. Configure credentials

```bash
cp .env.example .env
# Edit .env and fill in your Amap key and Feishu credentials
```

### 2. Install dependencies

No `pip` install needed — only the Python standard library, plus Chrome (for screenshots).

### 3. Generate the dashboard

```bash
python3 gen_weather.py      # Pull weather data and generate data.json
open index.html             # Open the dashboard in a browser
```

### 4. Push to Feishu

```bash
python3 push_image.py       # Screenshot + send the image to a Feishu group
```

## Two credentials you need to apply for

| Credential | Where to get it |
|------------|-----------------|
| Amap Weather Key | https://lbs.amap.com/ → Console → App management → Create app → Add Key (choose "Web service") |
| Feishu bot | Feishu Open Platform → Custom app → Add the "Bot" capability → Enable permissions im:message + im:resource + im:chat |

## Project structure

```
weather-dashboard/
├── index.html          # Dashboard (data separated from layout)
├── gen_weather.py      # Pull data and generate data.json
├── push_image.py       # Screenshot + push image to Feishu
├── push_feishu.py      # Legacy text push (kept for reference)
├── china.json          # China map GeoJSON
├── .env.example        # Credential template
└── .gitignore
```

## Customization

- **City list**: edit `REGIONS` at the top of `gen_weather.py` (city name + adcode)
- **Dressing advice**: edit the `CLOTHING` dict at the top of `gen_weather.py`
- **Layout / colors**: edit `tempColor()`, `weatherIcon()`, `renderMap()` in `index.html`

## FAQ

- **Amap rate limiting**: the free key has a QPS limit; the script already includes retries + delays
- **Blank screenshot**: Chrome headless needs `--allow-file-access-from-files` for local files (already handled)
- **Feishu won't send images**: a group's "custom bot webhook" cannot send images — you must use a "custom app" with the im/v1/images upload API

## License

[MIT License](LICENSE)
