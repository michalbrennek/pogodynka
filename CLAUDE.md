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
- **Button daemon**: `sudo systemctl restart pogodynka-buttons`
- **Deploy workflow**: SCP files to `/tmp/`, then `sudo cp` to deploy path (requires sudo for /usr/local)
- **InkyPi web API**: port 80, refresh endpoint `POST /update_now` with `plugin_id=meteogram`
- **OS**: Debian Trixie Lite 64-bit
- **Display**: Pimoroni Inky Impression 7.3" (800x480, 7-color e-ink)
- **Buttons**: GPIO 5=A(synoptic), 6=B(meteogram), 16=C(refresh), 24=D(reserved)
- **Font**: DejaVu Sans — supports basic Unicode (arrows U+2190-2199, geometric shapes, U+2600-2602) but NOT emoji (U+1Fxxx), NOT U+26C5

## GitHub

- **Repo**: `michalbrennek/pogodynka`
- **SSH alias**: `github-pogodynka` (uses `id_ed25519_pogodynka` deploy key)
- **No Claude attribution** in commits — user explicitly requested this

## Architecture

- InkyPi plugin framework: `BasePlugin.generate_image(settings, device_config) -> PIL.Image`
- Data fetching: Open-Meteo API (ECMWF + ICON-EU + Best Match models), MET Norway API (moonrise/moonset), weathercharts.org (UKMO synoptic)
- Rendering: matplotlib (Agg backend) + PIL for right panel
- Layout: 65/35 split — left panel (meteogram or synoptic chart), right sidebar (24h hourly detail)
- Display modes: auto (even hours=synoptic, odd=meteogram), synoptic, meteogram — controlled by button_state.json
- Button daemon: standalone systemd service, writes state file, triggers InkyPi refresh via POST /update_now
- Smart caching via `MeteogramCache` (JSON) — skips render if model generation_time unchanged

## E-ink 7-color Palette

- Blue (#0000FF) = ECMWF, Red (#FF0000) = ICON-EU / thunderstorm icons
- Green (#00FF00) = grid, Orange (#FF8C00) = cloud shading + clear sky icon
- Black (#000000) = text / cloud icons, White (#FFFFFF) = background
- Blue icons for rain/snow/drizzle, Red icons for thunderstorms
- Yellow (#FFFF00) = available but poor visibility on white background

## Key Constraints

- NaN handling: use `float('nan')` for line-plotted fields (matplotlib breaks lines), `0.0` for bars, `0` for weather_code
- `_trim_trailing_nan()` removes trailing all-NaN forecast hours
- Emoji characters don't render on Pi — use plain ASCII labels (SR/SS/MR/MS) and geometric Unicode symbols for moon phases
- Precipitation probability only available from Best Match endpoint (not ICON-EU single model, not ECMWF)
- Synoptic chart from weathercharts.org (UKMO B&W fax chart, ~80KB GIF)
- Right panel sidebar uses "Best Match" model data (has real precipitation probability from ensemble)
