import logging
from datetime import datetime
from io import BytesIO
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from plugins.meteogram.data_fetcher import ModelData
from plugins.meteogram.weather_icons import wmo_to_icon, wmo_to_description

logger = logging.getLogger(__name__)

# E-ink 7-color palette
ECMWF_COLOR = "#0000FF"     # Blue
METNO_COLOR = "#FF0000"     # Red
CLOUD_COLOR = "#FFFF00"     # Yellow
GRID_COLOR = "#00FF00"      # Green
BG_COLOR = "#FFFFFF"        # White
TEXT_COLOR = "#000000"       # Black
ACCENT_COLOR = "#FF8C00"    # Orange

# Plot settings
DPI = 100
FONT_FAMILY = "DejaVu Sans"
FONT_SIZE_TITLE = 9
FONT_SIZE_LABEL = 7
FONT_SIZE_TICK = 6


def _parse_times(time_strings: list) -> list:
    return [datetime.fromisoformat(t) for t in time_strings]


def render_meteogram(
    ecmwf: ModelData,
    metno: Optional[ModelData],
    dimensions: tuple,
) -> Image.Image:
    """Render the left 3/4 meteogram panel with 4 stacked subplots."""
    total_w, total_h = dimensions
    left_w = int(total_w * 0.75)

    fig_w = left_w / DPI
    fig_h = total_h / DPI

    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.size": FONT_SIZE_LABEL,
        "axes.labelsize": FONT_SIZE_LABEL,
        "axes.titlesize": FONT_SIZE_TITLE,
        "xtick.labelsize": FONT_SIZE_TICK,
        "ytick.labelsize": FONT_SIZE_TICK,
        "figure.facecolor": BG_COLOR,
        "axes.facecolor": BG_COLOR,
        "text.antialiased": False,
        "lines.antialiased": False,
    })

    fig, axes = plt.subplots(4, 1, figsize=(fig_w, fig_h), dpi=DPI, sharex=True)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.08, hspace=0.25)

    ecmwf_times = _parse_times(ecmwf.times)
    metno_times = _parse_times(metno.times) if metno else []

    # --- Temperature ---
    ax_temp = axes[0]
    ax_temp.plot(ecmwf_times, ecmwf.temperature, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    if metno:
        ax_temp.plot(metno_times, metno.temperature, color=METNO_COLOR, linewidth=1.2, label="MetNo")
    ax_temp.set_ylabel("Temp (\u00b0C)")
    ax_temp.legend(loc="upper right", fontsize=FONT_SIZE_TICK, framealpha=0.8)
    ax_temp.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Precipitation ---
    ax_precip = axes[1]
    bar_width = 0.02  # in days
    ax_precip.bar(ecmwf_times, ecmwf.precipitation, width=bar_width,
                  color=ECMWF_COLOR, alpha=0.7, label="ECMWF")
    if metno:
        ax_precip.bar(metno_times, metno.precipitation, width=bar_width,
                      color=METNO_COLOR, alpha=0.7, label="MetNo")
    ax_precip.set_ylabel("Precip (mm)")
    ax_precip.set_ylim(bottom=0)
    ax_precip.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Wind ---
    ax_wind = axes[2]
    ax_wind.plot(ecmwf_times, ecmwf.wind_speed, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    ax_wind.plot(ecmwf_times, ecmwf.wind_gusts, color=ECMWF_COLOR, linewidth=0.5,
                 linestyle="--", alpha=0.5)
    if metno:
        ax_wind.plot(metno_times, metno.wind_speed, color=METNO_COLOR, linewidth=1.2, label="MetNo")
        ax_wind.plot(metno_times, metno.wind_gusts, color=METNO_COLOR, linewidth=0.5,
                     linestyle="--", alpha=0.5)
    ax_wind.set_ylabel("Wind (m/s)")
    ax_wind.set_ylim(bottom=0)
    ax_wind.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # --- Pressure + Cloud Cover ---
    ax_press = axes[3]
    ax_press.plot(ecmwf_times, ecmwf.pressure, color=ECMWF_COLOR, linewidth=1.2, label="ECMWF")
    if metno:
        ax_press.plot(metno_times, metno.pressure, color=METNO_COLOR, linewidth=1.2, label="MetNo")
    ax_press.set_ylabel("hPa")
    ax_press.grid(True, linestyle=":", linewidth=0.3, color=GRID_COLOR)

    # Cloud cover as filled area on secondary axis
    ax_cloud = ax_press.twinx()
    ax_cloud.fill_between(ecmwf_times, ecmwf.cloud_cover, alpha=0.15, color=CLOUD_COLOR)
    ax_cloud.set_ylabel("Cloud %", fontsize=FONT_SIZE_TICK)
    ax_cloud.set_ylim(0, 100)
    ax_cloud.tick_params(labelsize=FONT_SIZE_TICK)

    # X-axis formatting
    ax_press.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m\n%Hz"))
    ax_press.xaxis.set_major_locator(mdates.HourLocator(interval=12))
    plt.setp(ax_press.xaxis.get_majorticklabels(), rotation=0, ha="center")

    # Convert to PIL image
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=DPI, facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    left_img = Image.open(buf).convert("RGB")

    # Compose into full-size image (left 3/4)
    full_img = Image.new("RGB", dimensions, BG_COLOR)
    full_img.paste(left_img.resize((left_w, total_h)), (0, 0))

    return full_img


def render_right_panel(
    data: ModelData,
    width: int = 200,
    height: int = 480,
    model_info: str = "",
) -> Image.Image:
    """Render the right 1/4 sidebar with 24h hourly detail."""
    img = Image.new("RGB", (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
        font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_icon = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except (IOError, OSError):
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_icon = ImageFont.load_default()

    # Draw left border separator
    draw.line([(0, 0), (0, height)], fill=TEXT_COLOR, width=2)

    y = 8
    pad = 8

    # --- Current conditions header ---
    if data.times and data.weather_code and data.temperature:
        icon = wmo_to_icon(data.weather_code[0])
        desc = wmo_to_description(data.weather_code[0])
        temp = f"{data.temperature[0]:.0f}°C"

        draw.text((pad, y), f"{icon} {temp}", fill=TEXT_COLOR, font=font_large)
        y += 24
        draw.text((pad, y), desc, fill=ACCENT_COLOR, font=font_medium)
        y += 18

    # Separator line
    draw.line([(pad, y), (width - pad, y)], fill=TEXT_COLOR, width=1)
    y += 6

    # --- Hourly rows (next 24h) ---
    max_rows = min(24, len(data.times))
    row_h = min(16, (height - y - 50) // max_rows) if max_rows > 0 else 16

    for i in range(max_rows):
        if y + row_h > height - 45:
            break

        time_str = data.times[i]
        hour = time_str.split("T")[1][:5] if "T" in time_str else time_str
        icon = wmo_to_icon(data.weather_code[i]) if i < len(data.weather_code) else ""
        temp = f"{data.temperature[i]:.0f}°" if i < len(data.temperature) else ""
        wind = f"{data.wind_speed[i]:.0f}m/s" if i < len(data.wind_speed) else ""

        draw.text((pad, y), hour, fill=TEXT_COLOR, font=font_small)
        draw.text((pad + 40, y), icon, fill=TEXT_COLOR, font=font_icon)
        draw.text((pad + 60, y), temp, fill=TEXT_COLOR, font=font_small)
        draw.text((pad + 95, y), wind, fill=TEXT_COLOR, font=font_small)

        y += row_h

    # --- Footer with model info ---
    y = height - 40
    draw.line([(pad, y), (width - pad, y)], fill=TEXT_COLOR, width=1)
    y += 4

    now_str = datetime.now().strftime("Updated: %H:%M")
    draw.text((pad, y), now_str, fill=TEXT_COLOR, font=font_small)
    y += 14
    if model_info:
        draw.text((pad, y), model_info, fill=TEXT_COLOR, font=font_small)

    return img
