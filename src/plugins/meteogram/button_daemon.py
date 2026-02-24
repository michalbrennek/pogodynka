#!/usr/bin/env python3
"""Button daemon for Inky Impression 7.3" — controls meteogram display mode.

Buttons (GPIO): A=5, B=6, C=16, D=24
  A = show synoptic chart
  B = show meteogram
  C = force refresh now
  D = (reserved)

Writes mode to a state file and triggers InkyPi refresh via its web API.
"""
import json
import logging
import os
import signal
import time

import requests
from gpiozero import Button

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("button_daemon")

STATE_FILE = "/usr/local/inkypi/src/plugins/meteogram/button_state.json"
INKYPI_URL = "http://localhost:80/update_now"
PLUGIN_ID = "meteogram"

BUTTONS = {
    5: "synoptic",
    6: "meteogram",
    16: "refresh",
    24: "reserved",
}


def read_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"mode": "auto"}


def write_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    logger.info(f"State: {state}")


def trigger_inkypi_refresh():
    """Call InkyPi's web API to force a display refresh."""
    try:
        resp = requests.post(INKYPI_URL, data={"plugin_id": PLUGIN_ID}, timeout=60)
        logger.info(f"InkyPi refresh: {resp.status_code}")
    except Exception as e:
        logger.error(f"Failed to trigger InkyPi refresh: {e}")


def handle_button(btn):
    pin = btn.pin.number
    action = BUTTONS.get(pin, "unknown")
    logger.info(f"Button press: pin={pin} action={action}")

    if action == "synoptic":
        write_state({"mode": "synoptic"})
        trigger_inkypi_refresh()
    elif action == "meteogram":
        write_state({"mode": "meteogram"})
        trigger_inkypi_refresh()
    elif action == "refresh":
        trigger_inkypi_refresh()


def main():
    logger.info("Button daemon starting")
    write_state(read_state())  # ensure state file exists

    buttons = []
    for pin in BUTTONS:
        b = Button(pin=pin, pull_up=True, bounce_time=0.3)
        b.when_pressed = handle_button
        buttons.append(b)
        logger.info(f"Listening on GPIO {pin} ({BUTTONS[pin]})")

    signal.pause()


if __name__ == "__main__":
    main()
