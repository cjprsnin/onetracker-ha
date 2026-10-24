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

## Lovelace cards

### Summary (stock)

```yaml
type: entities
title: Packages
show_header_toggle: false
entities:
  - entity: sensor.onetracker_active_packages
    name: In transit
  - entity: sensor.onetracker_delivered_packages
    name: Delivered
```

### Active package list (Markdown)

```yaml
type: markdown
title: Active packages
content: |
  {% set pkgs = state_attr('sensor.onetracker_active_packages', 'packages') or [] %}
  {% if pkgs | length == 0 %}
  No active packages 📦
  {% else %}
  {% for p in pkgs %}
  **{{ p.description }}**
  {% if p.retailer %}· {{ p.retailer }}{% endif %}
  {% if p.carrier %}· {{ p.carrier }}{% endif %}

  {% if p.status_text %}{{ p.status_text }}{% else %}{{ p.status }}{% endif %}
  {% if p.location %} · {{ p.location }}{% endif %}
  {% if p.eta %} · ETA {{ p.eta[:10] }}{% endif %}

  {% if not loop.last %}
  ---
  {% endif %}
  {% endfor %}
  {% endif %}
```

### Mushroom template (requires [Mushroom](https://github.com/piitaya/lovelace-mushroom) from HACS)

```yaml
type: custom:mushroom-template-card
primary: "{{ states('sensor.onetracker_active_packages') }} active"
secondary: >-
  {% set pkgs = state_attr('sensor.onetracker_active_packages', 'packages') or [] %}
  {% if pkgs | length == 0 %}Nothing in transit
  {% else %}{{ pkgs | map(attribute='description') | list | join(', ') }}{% endif %}
icon: mdi:package-variant-closed
icon_color: "{{ 'orange' if states('sensor.onetracker_active_packages') | int > 0 else 'grey' }}"
tap_action:
  action: more-info
  entity: sensor.onetracker_active_packages
```

More single-card variants are in [`examples/lovelace-card.yaml`](examples/lovelace-card.yaml).

### Full dashboard view template

Ready-made view with summary + active list + recent delivered:

1. Open a dashboard → **Edit** → ⋮ → **Raw configuration editor**
2. Under `views:`, paste the block from [`examples/dashboard-view.yaml`](examples/dashboard-view.yaml)
3. Save

### Delivery notification blueprint

1. **Settings → Automations & scenes → Blueprints → Import blueprint**
2. Paste:  
   `https://github.com/cjprsnin/onetracker-ha/blob/main/blueprints/automation/onetracker_package_delivered.yaml`
3. Create an automation from the blueprint and pick your notify service

## Notes

- Polls the OneTracker API every 5 minutes
- Uses the public OneTracker API (`https://api.onetracker.app`)
- Version: 0.1.0
