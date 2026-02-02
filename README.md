# Cudy Router Integration for Home Assistant

A modern, fully UI-configured Home Assistant integration for Cudy routers.

The integration is designed to work across AC and AX generations by automatically detecting router capabilities and adjusting parsing, scaling, and data interpretation accordingly.

WARNING:
This is a custom integration (not part of Home Assistant Core).
Home Assistant will display a warning about custom integrations — this is expected.

---

## KEY FEATURES

- UI Config Flow (no YAML required)
- Options Flow (change scan interval & tracked devices without re-adding)
- Multi-language UI (English & Polish included)
- Safe reboot action (button + service)

---

## SUPPORTED DEVICES

Implementation is based on emulators data published on https://support.cudy.com. All devices from this page have initial support.

There might be some errors due to differences in admin panel files and request - please report any in https://github.com/emce/hass-cudy-router/issues


## INSTALLATION

### IMPORTANT:
Integration domain: cudy_router
Folder name: hass_cudy_router

### MANUAL INSTALLATION

1. Open Home Assistant config directory:
   `config/custom_components/`
2. Create folder:
   `hass_cudy_router/`
3. Copy repository files from `custom_components/hass_cudy_router` to this folder
4. Restart Home Assistant.

---

## CONFIGURATION

### INITIAL SETUP

1. `Settings` -> `Devices & Services`
2. Add `Integration`
3. Search for "Cudy Router"
4. Enter:
   - Protocol _(http / https)_
   - Router IP _(default: 192.168.10.1)_
   - Username _(optional for some router - put `admin` just in case)_
   - Password

## OPTIONS (POST-SETUP)
After setup, click Configure on the integration to adjust:

- Scan interval (seconds)
- Tracked device MAC list (device_tracker)

---

## Rebooting

### BUTTON ENTITY (RECOMMENDED)

- Entity: button.cudy_router_reboot
- Available on the router device page
- Manual action (safe UX)

### SERVICE CALL
service: `cudy_router.reboot`

With multiple routers:
```
service: cudy_router.reboot
data:
entry_id: YOUR_CONFIG_ENTRY_ID
```
---

## Contribution

All contributions are welcome - general rules are applied. There is many models of Cudy brand - use `base_` classes to add new ones. Also for tests.

### TRANSLATIONS

Included:
- English
- Polish

To add another language:

1. Copy translations/en.json
2. Rename to <lang>.json
3. Translate values only (keys must remain unchanged)

---

## CREDITS

Based on original work by:
https://github.com/armendkadrija/hass-cudy-router-wr3600

Extended with:

- Modern Home Assistant architecture
- UI configuration & options flow
- Device tracker & reboot actions
- Full automated test coverage
