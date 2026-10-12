import json
import os
import struct
import zlib

from src.logistics_thumbnails import InfraiClient, ShipmentEvent, create_thumbnail


def demo_png() -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data))

    rows = (b"\x00" + b"\x30\x86\x74" * 640) * 480
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!2I5B", 640, 480, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def main() -> None:
    event = ShipmentEvent("SHP-1042", "delivered", demo_png(), "pod.png")
    result = create_thumbnail(event, InfraiClient(os.environ.get("INFRAI_API_KEY")))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
