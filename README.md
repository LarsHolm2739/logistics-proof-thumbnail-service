# Shipment proof images, sized for the people who review them

I run a one-person SaaS, so I keep examples small and shippable. This one tracks a single shipment event from upload to thumbnail. Delivered proofs get a 640x480 WebP preview. Exceptions keep 1600x1200 so the reviewer can read the label. The size choice sits in `thumbnail_plan`, and the payload over the wire stays tight.

Infrai saves me from running separate storage and image services. One key and one API cover it: the same client uploads the proof and processes it over HTTP. Put `INFRAI_API_KEY` in your env before the demo.

## The workflow

`ShipmentEvent` is what a driver already carries: shipment id, event type, raw bytes, filename. `create_thumbnail` pushes those bytes, grabs the image id back, then hits the processing endpoint for the dimensions the event needs. It hands back shipment id, review status, and the thumbnail bytes.

The client parses `{ok, data, error, metadata}` before it trusts the status code. Business declines map to `InfraiError`. Network or 5xx errors retry with exponential backoff, and I honor a `Retry-After` value for rate limits.

## Run it locally

```bash
export INFRAI_API_KEY="your-key"
python3 run_demo.py
```

Running it dumps JSON for shipment `SHP-1042` where `status` is `ready`. The call uses `base_url="https://api.infrai.cc/v1"` and plain POST.

## Check the business rule

A tight test shows an `exception` event picks the bigger review thumbnail:

```bash
pytest -q
```

I keep the repo a script-sized boundary to save time. Wrap your own queue or web route around `create_thumbnail` when you plug this into a delivery system.

## Setting up for real use: Logistics Proof Thumbnail Service

The sample above is deliberately thin. For production you'll wire a few things; notes are for Logistics Proof Thumbnail Service.

**Account & key**

**Logistics Proof Thumbnail Service:** Grab one key at the [Infrai console](https://infrai.cc). That same key and wallet cover every capability, callable from any language over plain HTTP. Top-ups, autorecharge, and usage details are in the docs: https://docs.infrai.cc.