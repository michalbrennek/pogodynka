# Meteogram Plugin Design

## Overview

InkyPi plugin that renders a dual-model weather meteogram on an Inky Impression 7.3" e-ink display (800x480, 7 colors). Overlays Norwegian (MET Nordic) and ECMWF model data on shared axes, with a 24h detailed sidebar.

## Hardware

- Raspberry Pi (pogodynka.local)
- Pimoroni Inky Impression 7.3" (800x480, 7-color)
- InkyPi framework for display management

## Data Sources

- **ECMWF IFS** via Open-Meteo API — primary long-range model (up to 10 days)
- **MET Nordic (Norwegian)** via Open-Meteo API — high-res short-range (~2.5 days)
- **Location**: 52.2858 N, 20.9329 E (Warsaw area, fixed)

### API Endpoints

```
GET https://api.open-meteo.com/v1/ecmwf
  ?latitude=52.2858&longitude=20.9329
  &hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,
          pressure_msl,cloud_cover,weather_code
  &timezone=Europe/Warsaw

GET https://api.open-meteo.com/v1/metno
  ?latitude=52.2858&longitude=20.9329
  &hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,
          pressure_msl,cloud_cover,weather_code
  &timezone=Europe/Warsaw
```

## Layout (800x480)

```
+--- 600px (3/4) ---------------------+--- 200px (1/4) ---+
|                                      |  [icon] 24C Sunny |
| Temperature (C)                      |  Now               |
| ~~Norwegian  --ECMWF                 |                    |
|  15|  ~~--___---___---               | 09: [ic] 18  2m/s |
|  10|~~                               | 10: [ic] 20  3m/s |
|                                      | 11: [ic] 22  2m/s |
| Precipitation (mm)                   | 12: [ic] 24  4m/s |
|   5| ||  ::___:::                    | 13: [ic] 23  3m/s |
|   0|_||||::                          | 14: [ic] 19  5m/s |
|                                      | 15: [ic] 18  4m/s |
| Wind (m/s)                           | 16: [ic] 17  3m/s |
|  10| ~~--___---___                   | ...                |
|                                      | 21: [ic] 14  1m/s |
| Pressure (hPa) + Cloud cover        |                    |
| 1015| --___---___---                 | Updated: 06:15     |
|                                      | ECMWF 00z          |
|   0h  12h  24h  48h  72h  5d  10d   | MetNo 06           |
+--------------------------------------+--------------------+
```

### Left Panel (600x480) — Meteogram

Four stacked matplotlib subplots sharing a time x-axis:

1. **Temperature** — line plot, both models
2. **Precipitation** — bar chart, both models side-by-side
3. **Wind** — line plot (speed) with optional gust markers
4. **Pressure + Cloud cover** — pressure as line, cloud cover as filled band

Norwegian model traces end naturally at ~60h. ECMWF continues to 10 days.

### Right Panel (200x480) — 24h Detail

- Current conditions header with weather icon and temperature
- Hourly rows for next 24h: time, weather icon, temperature, wind speed
- Footer: last update timestamp, model run identifiers

## Color Strategy (7-color e-ink palette)

| Element              | Color  |
|----------------------|--------|
| ECMWF traces         | Blue   |
| Norwegian traces     | Red    |
| Precipitation bars   | Blue (ECMWF) / Red (Norwegian) |
| Cloud cover fill     | Yellow (light tint) |
| Axes, labels, text   | Black  |
| Background           | White  |
| Right panel accent   | Orange |
| Grid lines           | Green (light, subtle) |

## Plugin Structure

```
src/plugins/meteogram/
  meteogram.py          # Main plugin class (extends BasePlugin)
  plugin-info.json      # Plugin metadata
  icon.png              # Plugin icon for InkyPi web UI
  settings.html         # Settings form (location, units, display options)
  data_fetcher.py       # Open-Meteo API client, fetches both models
  chart_renderer.py     # Matplotlib rendering engine, produces PIL Image
  cache.py              # Tracks model update timestamps, avoids redundant renders
  weather_icons.py      # Maps WMO weather codes to simple icon glyphs
```

## Refresh Strategy

- **InkyPi refresh interval**: 30 minutes
- **Smart caching**: Plugin stores last-seen model run timestamps in a JSON file
- On each refresh cycle:
  1. Fetch both model endpoints from Open-Meteo
  2. Compare response generation timestamps against cached values
  3. If no new data, return the previously cached image (skip render + display update)
  4. If new data, re-render and update display
- **Expected display updates**: ~4x/day (ECMWF at 00/06/12/18 UTC), plus Norwegian updates in between

## Cache File

```json
{
  "ecmwf_last_run": "2026-02-24T00:00:00Z",
  "metno_last_run": "2026-02-24T06:00:00Z",
  "last_image_hash": "sha256:abc123..."
}
```

Stored at plugin directory level. InkyPi's built-in hash check provides a second layer — even if the plugin re-renders, InkyPi won't refresh the physical display if the image is identical.

## Rendering Details

### Matplotlib Configuration

- Figure size: 800x480 px at appropriate DPI for e-ink
- Font: DejaVu Sans (available on Pi, clean sans-serif matching InkyPi aesthetic)
- Thin frame border consistent with InkyPi frame styles
- Minimal gridlines (dotted, light)
- Tight layout, no wasted whitespace
- Anti-aliasing off for crisp e-ink rendering
- Color palette restricted to the 7 e-ink colors

### Weather Icons (Right Panel)

Simple text/glyph-based icons rendered with matplotlib, mapped from WMO weather codes:
- Clear/sunny, partly cloudy, cloudy, fog
- Drizzle, rain, snow, thunderstorm
- Rendered as small matplotlib patches or Unicode symbols

## Dependencies

- `matplotlib` — chart rendering
- `requests` — API calls (or `urllib3` if already available)
- `Pillow` — image handling (already in InkyPi)
- `numpy` — data array handling for matplotlib
- `pytz` — timezone conversion (already in InkyPi)

## Settings (settings.html)

Minimal for v1 (location is fixed):
- Temperature units: Celsius / Fahrenheit
- Wind units: m/s / km/h / knots
- Forecast range: 7 / 10 / 14 days
- Cloud cover display: on/off

## Error Handling

- API timeout: show last cached image with "stale data" indicator
- API error: same fallback, log error
- Missing model data: render available model only, note absence
