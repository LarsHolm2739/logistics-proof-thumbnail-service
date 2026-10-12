import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from src.logistics_thumbnails import ShipmentEvent, thumbnail_plan


def test_exception_event_keeps_large_review_image():
    event = ShipmentEvent("SHP-9", "exception", b"scan", "exception.jpg")
    assert thumbnail_plan(event) == {"status": "review", "width": 1600, "height": 1200}
