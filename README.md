# OneTracker for Home Assistant

Unofficial Home Assistant integration for [OneTracker](https://onetracker.app) package tracking.

Tracks your packages, exposes active/delivered counts as sensors, and fires an event when a package is delivered.

## Installation

### HACS (recommended)

1. In HACS → Integrations → ⋮ → **Custom repositories**
2. Add repository URL: `https://github.com/cjprsnin/onetracker-ha`
3. Category: **Integration**
4. Click **Add**
5. Search for **OneTracker** and install
6. Restart Home Assistant
7. Settings → Devices & services → **Add integration** → **OneTracker**
8. Sign in with your OneTracker email and password

### Manual

1. Copy `custom_components/onetracker` into your HA config folder (`/config/custom_components/`)
2. Restart Home Assistant
3. Add the integration as above

## Entities

| Entity | Description |
|--------|-------------|
| `sensor.onetracker_active_packages` | Number of packages not yet delivered |
| `sensor.onetracker_delivered_packages` | Number of delivered packages |

Both sensors include attributes:

- `packages` – list of package summaries
- `by_status` – counts grouped by tracking status

## Events

`onetracker_package_delivered` – fired when a package changes to delivered status.

Event data includes description, retailer, carrier, tracking_id, location, etc.

## Notes

- Polls the OneTracker API every 5 minutes
- Uses the public OneTracker API (`https://api.onetracker.app`)
- Version: 0.1.0
