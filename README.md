# Pogodynka - Dual-Model Weather Meteogram for InkyPi

A weather meteogram plugin for [InkyPi](https://github.com/fatihak/InkyPi) that overlays ECMWF and DWD ICON-EU model forecasts on a Pimoroni Inky Impression 7.3" e-ink display, with synoptic chart switching via physical buttons.

## Features

- **Dual-model overlay** — ECMWF (long-range, 10 days) and DWD ICON-EU (7km European resolution) on the same axes
- **Meteorologist view** — 4 stacked panels: temperature + feels-like, precipitation + humidity, wind + direction arrows, pressure + cloud cover
- **Synoptic chart** — UKMO surface pressure analysis from [weathercharts.org](https://www.weathercharts.org/), alternating with meteogram on even/odd hours
- **Physical buttons** — Inky Impression buttons switch between synoptic chart (A), meteogram (B), and force refresh (C)
- **24h sidebar** — hourly detail with colored weather icons, temperature/feels-like, wind direction + speed, precipitation mm and probability %
- **Astronomical data** — moon phase, sunrise/sunset, moonrise/moonset
- **Smart caching** — only refreshes the e-ink display when model data actually updates
- **7-color e-ink** — designed for the Inky Impression's 7-color palette

## Layout

```
+--- 65% left panel -------+--- 35% sidebar ----------+
| Meteogram (odd hours)    | Now: 2/0°C Overcast      |
|  or                      | Moon: ◐ First Quarter     |
| Synoptic chart (even)    | SR 06:45  SS 17:22       |
|                          | Time Wx °C/feel m/s mm % |
| Temp + feels-like        | 09:00 ☁  2/0   ↓ 5 0.1 79|
| Precip + humidity        | 10:00 ☂  3/1   ← 4 0.2 45|
| Wind + direction arrows  | ...                      |
| Pressure + cloud cover   |                          |
+---------------------------+--------------------------+
```

## Physical Buttons

The Inky Impression 7.3" has 4 buttons (GPIO 5, 6, 16, 24):

| Button | Action |
|--------|--------|
| A (top) | Show synoptic chart |
| B | Show meteogram |
| C | Force refresh |
| D | Reserved |

A separate `pogodynka-buttons` systemd service listens for button presses and triggers InkyPi display updates via its web API.

## Hardware

- Raspberry Pi (Zero 2W, 3, 4, or 5)
- [Pimoroni Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3) (800x480, 7-color)

## Data Sources

- [Open-Meteo ECMWF API](https://open-meteo.com/en/docs/ecmwf-api) — temperature, wind, pressure, cloud cover (free, no API key)
- [Open-Meteo DWD ICON-EU API](https://open-meteo.com/en/docs/dwd-api) — European regional model overlay (free, no API key)
- [Open-Meteo Best Match API](https://open-meteo.com/en/docs) — sidebar data with precipitation probability (free, no API key)
- [MET Norway Sunrise API](https://api.met.no/weatherapi/sunrise/3.0/) — moonrise/moonset data
- [WeatherCharts.org](https://www.weathercharts.org/) — UKMO surface pressure analysis (B&W fax chart)

## Built on

This project is a plugin for **[InkyPi](https://github.com/fatihak/InkyPi)** by [@fatihak](https://github.com/fatihak) — an open-source e-ink display framework for Raspberry Pi. InkyPi provides the web interface, plugin architecture, display management, and scheduling that this plugin relies on.

## License

MIT
