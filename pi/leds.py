"""ExecStopPost of pnp-expo.service: strip dark after a clean stop, calm
orange after a crash or watchdog kill -- visible from the booth while
systemd restarts the game."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))
from config import LED_DOWN  # noqa: E402
from hw import Leds          # noqa: E402

Leds().close((0, 0, 0) if os.environ.get("SERVICE_RESULT") == "success" else LED_DOWN)
