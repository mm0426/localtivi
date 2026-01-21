# HDHR-Gateway

**HDHomeRun to Tivimate Bridge**

A lightweight Python application that automatically discovers your local HDHomeRun device, generates an M3U playlist, and fetches Electronic Program Guide (EPG) data in XMLTV format. These files are served via HTTP for easy import into Tivimate or any IPTV player.

## Features

- **Zero Configuration**: Auto-discovery of HDHomeRun devices on your local network
- **Standards Compliant**: Generates valid Extended M3U and XMLTV files
- **Automatic Updates**: Periodically refreshes EPG data in the background (every 4 hours)
- **Easy Integration**: Serve files via HTTP for direct URL import in Tivimate
- **Docker Support**: Ready-to-use Docker container for easy deployment

## Requirements

- Python 3.9 or higher
- HDHomeRun device on your local network
- Network access to `api.hdhomerun.com` for EPG data

## Installation

### Option 1: Standard Python Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python app.py
   ```

### Option 2: Docker Installation (Recommended)

1. Build the Docker image:
   ```bash
   docker build -t hdhr-gateway .
   ```
2. Run the container:
   ```bash
   docker run -d --name hdhr-gateway --network=host hdhr-gateway
   ```

   Or use docker-compose:
   ```bash
   docker-compose up -d
   ```

   **Note**: `--network=host` is required for UDP broadcast discovery to work properly.

## Configuration

Edit `config.py` to customize settings:

```python
UDP_IP = "255.255.255.255"      # Broadcast IP for device discovery
UDP_PORT = 65001                 # HDHomeRun discovery port
HTTP_PORT = 5000                 # Web server port
EPG_UPDATE_INTERVAL_HOURS = 4    # How often to refresh EPG data
OUTPUT_DIR = "static"            # Directory for generated files
```

## Usage

Once the application is running, access the following URLs:

- **Status Page**: `http://localhost:5000/`
- **M3U Playlist**: `http://localhost:5000/playlist.m3u`
- **XMLTV EPG**: `http://localhost:5000/epg.xml`
- **Manual Refresh**: `POST http://localhost:5000/refresh`

## Tivimate Configuration

1. Open **Tivimate** on your Android TV
2. Go to **Settings** > **Playlists** > **Add Playlist**
3. Select **M3U Playlist**
4. Enter URL: `http://<YOUR_SERVER_IP>:5000/playlist.m3u`
5. Proceed to **EPG Source**
6. Enter URL: `http://<YOUR_SERVER_IP>:5000/epg.xml`
7. Set **Time Offset** to 0

Replace `<YOUR_SERVER_IP>` with the IP address of the machine running HDHR-Gateway.

## How It Works

1. **Device Discovery**: On startup, the app broadcasts a UDP packet to discover HDHomeRun devices. If that fails, it falls back to the cloud API.
2. **Data Retrieval**: Once discovered, it fetches:
   - Channel lineup from `http://<HDHR_IP>/lineup.json`
   - Device authentication from `http://<HDHR_IP>/discover.json`
3. **File Generation**:
   - **Playlist**: Converts lineup JSON to M3U format with proper tvg-* attributes
   - **EPG**: Downloads XMLTV guide data from SiliconDust's API using DeviceAuth
4. **Serving**: Flask web server hosts the files and provides a status endpoint
5. **Background Updates**: APScheduler automatically refreshes EPG data every 4 hours

## Troubleshooting

### Device Not Found
- Ensure your HDHomeRun is powered on and connected to the same network
- Check firewall settings allow UDP broadcast on port 65001
- Verify network connectivity to `api.hdhomerun.com`

### Files Not Generated
- Check console output for error messages
- Try manually refreshing: `curl -X POST http://localhost:5000/refresh`
- Verify the `static/` directory exists and is writable

### Docker Networking Issues
- Use `--network=host` mode for proper UDP broadcast discovery
- If using bridge mode, ensure proper port mapping: `-p 5000:5000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Status page with device information |
| GET | `/playlist.m3u` | Download M3U playlist |
| GET | `/epg.xml` | Download XMLTV EPG file |
| POST | `/refresh` | Manually trigger data refresh |

## Project Structure

```
hdhr-gateway/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── modules/
│   ├── __init__.py
│   ├── device.py       # Device discovery and data retrieval
│   ├── playlist.py     # M3U playlist generator
│   └── epg.py          # XMLTV EPG generator
└── static/             # Generated files output directory
    ├── playlist.m3u
    └── epg.xml
```

## License

This project is provided as-is for personal use. HDHomeRun is a trademark of SiliconDust Engineering Ltd.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
