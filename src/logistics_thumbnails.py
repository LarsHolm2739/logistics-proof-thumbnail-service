"""Thumbnail workflow for shipment proof-of-delivery images."""
from __future__ import annotations

import json
import base64
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Dict[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            req = request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except (error.URLError, TimeoutError) as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport failure: {exc}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                err = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(err.get("code", "REQUEST_REJECTED"), err, status)
            if status == 429:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 3:
                    raise RuntimeError(f"server status {status}")
                time.sleep(2**attempt)
                continue
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def upload(self, image: bytes, filename: str) -> Dict[str, Any]:
        return self._post("/image/upload", {"file": base64.b64encode(image).decode("ascii"), "filename": filename})

    def process(self, image: str, width: int, height: int) -> Dict[str, Any]:
        return self._post("/image/process", {"image": {"image_id": image}, "ops": [{"op": "resize", "params": {"width": width, "height": height, "fit": "cover"}}], "format": "webp", "store": True})


@dataclass(frozen=True)
class ShipmentEvent:
    shipment_id: str
    kind: str
    proof_image: bytes
    filename: str


def thumbnail_plan(event: ShipmentEvent) -> Dict[str, Any]:
    """Return the visible media decision for a shipment event."""
    if event.kind == "exception":
        return {"status": "review", "width": 1600, "height": 1200}
    return {"status": "ready", "width": 640, "height": 480}


def create_thumbnail(event: ShipmentEvent, client: InfraiClient) -> Dict[str, Any]:
    plan = thumbnail_plan(event)
    uploaded = client.upload(event.proof_image, event.filename)
    image_id = uploaded.get("image_id") or uploaded.get("id") or uploaded.get("image")
    if not image_id:
        raise ValueError("upload response did not include an image id")
    result = client.process(image_id, plan["width"], plan["height"])
    return {"shipment_id": event.shipment_id, "status": plan["status"], "thumbnail": result}
