# Pogodynka - Project Context

## Development Environment

- **Python**: `C:\Users\michal\AppData\Local\Programs\Python\Python312\python.exe`
- **Run tests**: `PYTHONPATH=src /c/Users/michal/AppData/Local/Programs/Python/Python312/python.exe -m pytest tests/ -v`
- **Source root**: `src/` (must be on PYTHONPATH for imports like `plugins.meteogram.*`)

## Raspberry Pi (pogodynka.local)

- **SSH user**: `michal` (not `pi`)
- **SSH key**: `~/.ssh/id_ed25519_pogodynka`
- **Deploy path**: `/usr/local/inkypi/src/plugins/meteogram/`
- **Service**: `sudo systemctl restart inkypi`
- **Deploy workflow**: SCP files to `/tmp/`, then `sudo cp` to deploy path (requires sudo for /usr/local)
- **OS**: Debian Trixie Lite 64-bit
- **Display**: Pimoroni Inky Impression 7.3" (800x480, 7-color e-ink)
- **Font**: DejaVu Sans — supports basic Unicode (arrows U+2190-2199, geometric shapes) but NOT emoji (U+1Fxxx)

## GitHub

- **Repo**: `michalbrennek/pogodynka`
- **SSH alias**: `github-pogodynka` (uses `id_ed25519_pogodynka` deploy key)
- **No Claude attribution** in commits — user explicitly requested this

## Architecture

- InkyPi plugin framework: `BasePlugin.generate_image(settings, device_config) -> PIL.Image`
- Data: Open-Meteo API (ECMWF + ICON-EU models), MET Norway API (moonrise/moonset)
- Rendering: matplotlib (Agg backend) + PIL for right panel
- Layout: 65/35 split — left meteogram charts (GridSpec 5 rows), right sidebar (24h hourly detail)
- Smart caching via `MeteogramCache` (JSON) — skips render if model generation_time unchanged

## E-ink 7-color Palette

- Blue (#0000FF) = ECMWF, Red (#FF0000) = ICON-EU
- Green (#00FF00) = grid, Orange (#FF8C00) = cloud shading + accents
- Black (#000000) = text, White (#FFFFFF) = background
- Yellow (#FFFF00) = available but poor visibility on white background

## Key Constraints

- NaN handling: use `float('nan')` for line-plotted fields (matplotlib breaks lines), `0.0` for bars, `0` for weather_code
- `_trim_trailing_nan()` removes trailing all-NaN forecast hours
- Emoji characters don't render on Pi — use plain ASCII labels (SR/SS/MR/MS) and geometric Unicode symbols for moon phases
- Precipitation probability only available from ICON-EU, not ECMWF
