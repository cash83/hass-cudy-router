# Cudy Router Integration for Home Assistant (AC1200 Optimized)

This is an enhanced custom integration for Cudy routers, specifically optimized and tested for the **Cudy AC1200 (WR1200)** model. 

While based on original work for the WR3600, this version features a completely rewritten `parser.py` to handle the specific HTML structure of AC1200 firmware and introduces several new dedicated sensors for better network monitoring.

## 🚀 Enhanced Features & Sensors

Beyond basic device tracking, this integration now provides dedicated entities for comprehensive network analysis:

### **Network Performance**
* **Download Speed:** `sensor.download_speed` — Real-time aggregate download throughput.
* **Upload Speed:** `sensor.upload_speed` — Real-time aggregate upload throughput.
* **Total Data:** `sensor.download_total` & `sensor.upload_total` — Accumulative data counters since last router reboot.

### **Traffic Analysis**
* **Top Downloader:** `sensor.top_downloader` — Identifies the device (Hostname or IP) currently consuming the most download bandwidth.
* **Top Uploader:** `sensor.top_uploader` — Identifies the device currently consuming the most upload bandwidth.
* **Device Count:** `sensor.device_count` — A numeric sensor showing the total number of currently connected clients.

### **System Health & Info**
* **Uptime:** `sensor.connected_time` — How long the router has been running.
* **Firmware & HW:** `sensor.firmware_version` and `sensor.hardware_version` for easy version tracking.
* **IP Info:** `sensor.lan_ip_address` — Monitoring the local gateway address.

## 🛠 Installation

1. Open your Home Assistant `config/custom_components` directory.
2. Create a folder named `cudy_router`.
3. Copy all files from this repository into that folder.
   - The structure should look like:
     ```
     custom_components/
       cudy_router/
         __init__.py
         config_flow.py
         const.py
         coordinator.py
         device_tracker.py
         manifest.json
         parser.py
         router.py
         sensor.py
         strings.json
         translations/
           en.json
     ```
4. **Restart Home Assistant.**

## ⚙️ Configuration

1. Navigate to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for **Cudy Router**.
4. Enter the router's IP address (default: `192.168.10.1`), username (`admin`), and password.
5. The integration will automatically discover the router and populate all sensors.

## 📋 Data Attributes
The `sensor.connected_devices` entity stores a full JSON list of clients in its attributes, allowing for advanced dashboarding (Markdown/Flex-Table):
* `hostname`: The name assigned to the device.
* `ip`: Current local IP address.
* `mac`: Unique hardware address.
* `connection`: Connection type (`wired` or `wireless`).
* `signal`: Wireless signal strength percentage.
* `online_time`: Session duration.

## ⚠️ Notes for AC1200 Users
The AC1200 model is a standard Wi-Fi router. Therefore, LTE-specific sensors (SIM status, 4G signal strength, Cell bands) are intentionally disabled or unavailable to keep your entity list clean.

## Credits
Based on the original work by [armendkadrija](https://github.com/armendkadrija/hass-cudy-router-wr3600).
Optimized for AC1200 HTML parsing and extended sensor support.
