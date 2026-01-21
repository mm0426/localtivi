# Design Specification: HDHR-Gateway (HDHomeRun to Tivimate Bridge)

## 1. Overview
**HDHR-Gateway** is a lightweight, standalone Python application designed to run on a local server (e.g., Raspberry Pi, Docker, or PC). It automatically discovers a local HDHomeRun device, generates a formatted M3U playlist, and fetches Electronic Program Guide (EPG) data to create an XMLTV file. These files are served via a built-in HTTP server for easy import into Tivimate.

### 1.1 Problem Statement
HDHomeRun devices provide raw streams and a proprietary guide format. Tivimate, a popular IPTV player, requires:
1.  **M3U Playlist:** A text file containing stream URLs and channel metadata.
2.  **XMLTV EPG:** A standardized XML file containing program schedules.

Native compatibility is limited. This application bridges that gap by "translating" HDHomeRun data into Tivimate-friendly formats.

### 1.2 Goals
* **Zero Configuration:** Auto-discovery of the HDHomeRun device on the local subnet.
* **Standards Compliance:** Generate valid Extended M3U (`#EXTM3U`) and XMLTV (`xmltv.dtd`) files.
* **Automation:** Periodically refresh guide data (EPG) in the background.
* **Accessibility:** Serve files via HTTP for direct URL import in Tivimate (e.g., `http://192.168.1.10:5000/playlist.m3u`).

---

## 2. Architecture

### 2.1 System Context
```mermaid
graph LR
    HDHR[HDHomeRun Device] -- JSON Lineup & Guide --> App[HDHR-Gateway App]
    App -- Serves HTTP --> TiviMate[Tivimate (Android TV)]
    App -- Periodic Updates --> App
````

### 2.2 Component Diagram

The application consists of four main modules:

1.  **Device Manager:** Handles discovery and communication with the HDHomeRun hardware.
2.  **Playlist Generator:** Converts HDHR JSON lineup to M3U format.
3.  **EPG Generator:** Fetches guide data from SiliconDust servers (via HDHR auth) and converts it to XMLTV.
4.  **Web Server:** A simple Flask/FastAPI server to host the generated files.

* * *

3\. Detailed Component Design
-----------------------------

### 3.1 Device Manager (`device.py`)

Responsible for locating the device and retrieving its dynamic configuration.

*   **Discovery Mechanism:**
    *   Broadcast UDP packet to `255.255.255.255` on port `65001`.
    *   Alternatively, query `http://ipv4-api.hdhomerun.com/discover`.
*   **Data Retrieval:**
    *   Fetch `http://<HDHR_IP>/discover.json` to get `DeviceID` and `LineupURL`.
    *   Fetch `http://<HDHR_IP>/lineup.json` to get the channel list.

### 3.2 Playlist Generator (`playlist.py`)

Responsible for creating the `playlist.m3u` file.

*   **Input:** JSON data from `/lineup.json`.
*   **Transformation Logic:**
    *   Iterate through enabled channels.
    *   Map `GuideName` to `tvg-name`.
    *   Map `GuideNumber` to `tvg-chno`.
    *   Construct Stream URL: `http://<HDHR_IP>:5004/auto/v<ChannelNumber>`.
*   **Output Format:**
    ```
    #EXTM3U
    #EXTINF:-1 tvg-id="10.1" tvg-name="NBC" tvg-chno="10.1" tvg-logo="[http://img.url](http://img.url)", NBC
    [http://192.168.1.50:5004/auto/v10.1](http://192.168.1.50:5004/auto/v10.1)
    ```

### 3.3 EPG Generator (`epg.py`)

Responsible for creating the `epg.xml` file.

*   **Strategy:**
    *   HDHomeRun devices do not host the full guide data locally. We must query the SiliconDust API using the device's `DeviceAuth` string found in `discover.json`.
    *   **API Endpoint:** `http://api.hdhomerun.com/api/xmltv?DeviceAuth=<AUTH_STRING>`
    *   _Alternative (if API fails):_ Scrape individual channel data if the device is a Legacy model, though the API is preferred for Modern (Gen 4/5) devices.
*   **Optimization:**
    *   Cache the XMLTV file to disk to prevent hitting the API too frequently.
    *   Refresh interval: Every 4-6 hours.

### 3.4 Web Server (`server.py`)

A lightweight web interface to serve the files.

*   **Routes:**
    *   `GET /playlist.m3u` -\> Returns generated M3U.
    *   `GET /epg.xml` -\> Returns generated XMLTV.
    *   `GET /` -\> Status page showing found device and last update time.
    *   `POST /refresh` -\> Manually triggers a data refresh.

* * *

4\. Data Flow
-------------

1.  **Startup:**
    *   `Device Manager` scans network -\> Finds HDHomeRun IP `192.168.1.50`.
    *   `Device Manager` requests `discover.json` -\> Gets `DeviceAuth`.
2.  **Generation Phase:**
    *   `Playlist Generator` fetches `lineup.json` -\> Writes `playlist.m3u`.
    *   `EPG Generator` uses `DeviceAuth` to request XMLTV data -\> Writes `epg.xml`.
3.  **Serving Phase:**
    *   User inputs `http://<APP_IP>:5000/playlist.m3u` into Tivimate.
    *   Tivimate requests the file -\> Server reads from disk -\> Returns file.

* * *

5\. Technology Stack & Dependencies
-----------------------------------

*   **Language:** Python 3.9+
*   **Core Libraries:**
    *   `requests` (HTTP calls)
    *   `flask` (Web Server)
    *   `apscheduler` (Background task scheduling for EPG updates)
    *   `xml.etree.ElementTree` (XML manipulation if raw parsing is needed)

* * *

6\. Implementation Plan
-----------------------

### 6.1 Directory Structure

```
hdhr-gateway/
├── app.py              # Main entry point & Flask app
├── config.py           # Configuration (Port, Update Interval)
├── requirements.txt    # Dependencies
├── modules/
│   ├── __init__.py
│   ├── device.py       # Discovery logic
│   ├── playlist.py     # M3U logic
│   └── epg.py          # XMLTV logic
└── static/             # output directory for generated files
    ├── playlist.m3u
    └── epg.xml
```

### 6.2 Configuration Variables (`config.py`)

```
UDP_IP = "255.255.255.255"
UDP_PORT = 65001
HTTP_PORT = 5000
EPG_UPDATE_INTERVAL_HOURS = 4
OUTPUT_DIR = "static"
```

7\. Tivimate Configuration Guide (User Instructions)
----------------------------------------------------

Once the application is running:

1.  Open **Tivimate** \> **Settings** \> **Playlists** \> **Add Playlist**.
2.  Select **M3U Playlist**.
3.  Enter URL: `http://<YOUR_PC_IP>:5000/playlist.m3u`.
4.  Proceed to **EPG Source**.
5.  Enter URL: `http://<YOUR_PC_IP>:5000/epg.xml`.
6.  Set **Time Offset** to 0 (The generated XMLTV should utilize UTC or standard offsets).
