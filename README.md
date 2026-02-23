# Pogodynka - Dual-Model Weather Meteogram for InkyPi

A weather meteogram plugin for [InkyPi](https://github.com/fatihak/InkyPi) that overlays ECMWF and Norwegian (MET Nordic) model forecasts on a Pimoroni Inky Impression 7.3" e-ink display.

## Features

- **Dual-model overlay** — ECMWF (long-range, 10 days) and Norwegian MET Nordic (high-res, ~2.5 days) on the same axes
- **Meteorologist view** — 4 stacked panels: temperature, precipitation, wind, pressure + cloud cover
- **24h sidebar** — hourly detail with weather icons for quick reference
- **Smart caching** — only refreshes the e-ink display when model data actually updates
- **7-color e-ink** — designed for the Inky Impression's 7-color palette

## Layout

```
+--- 3/4 meteogram --------+--- 1/4 detail ---+
| Temp (ECMWF + MetNo)     | Now: 24C Sunny   |
| Precip (both models)     | 09: 18C 2m/s     |
| Wind (speed + gusts)     | 10: 20C 3m/s     |
| Pressure + Cloud cover   | ...              |
|  0h  12h  48h  5d  10d   | Updated: 06:15   |
+---------------------------+------------------+
```

## Hardware

- Raspberry Pi (Zero 2W, 3, 4, or 5)
- [Pimoroni Inky Impression 7.3"](https://shop.pimoroni.com/products/inky-impression-7-3) (800x480, 7-color)

## Data Sources

- [Open-Meteo ECMWF API](https://open-meteo.com/en/docs/ecmwf-api) — free, no API key required
- [Open-Meteo MET Norway API](https://open-meteo.com/en/docs/metno-api) — free, no API key required

## Built on

This project is a plugin for **[InkyPi](https://github.com/fatihak/InkyPi)** by [@fatihak](https://github.com/fatihak) — an open-source e-ink display framework for Raspberry Pi. InkyPi provides the web interface, plugin architecture, display management, and scheduling that this plugin relies on.

## License

MIT
