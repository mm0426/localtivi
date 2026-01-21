"""
HDHR-Gateway: HDHomeRun to Tivimate Bridge
Main application entry point.
"""

from flask import Flask, send_from_directory, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import config
from modules import device, playlist, epg

app = Flask(__name__)

# Global state
device_ip = None
device_auth = None


@app.route('/')
def status():
    """Return application status page."""
    return jsonify({
        'status': 'HDHR Gateway Running',
        'device_found': device_ip is not None,
        'device_ip': device_ip
    })


@app.route('/playlist.m3u')
def serve_playlist():
    """Serve the generated M3U playlist."""
    try:
        return send_from_directory(config.OUTPUT_DIR, 'playlist.m3u')
    except FileNotFoundError:
        return jsonify({
            'error': 'Playlist not found',
            'message': 'Try triggering a refresh via POST /refresh'
        }), 404


@app.route('/epg.xml')
def serve_epg():
    """Serve the generated XMLTV EPG file."""
    try:
        return send_from_directory(config.OUTPUT_DIR, 'epg.xml')
    except FileNotFoundError:
        return jsonify({
            'error': 'EPG not found',
            'message': 'Try triggering a refresh via POST /refresh'
        }), 404


@app.route('/refresh', methods=['POST'])
def refresh():
    """Manually trigger data refresh."""
    success = update_data()
    return jsonify({'success': success})


def update_data():
    """
    Update playlist and EPG data.
    
    Returns:
        bool: True if successful, False otherwise
    """
    global device_ip, device_auth
    
    print("\n--- Starting data update ---")
    
    # 1. Discover device (if not already found)
    if not device_ip or not device_auth:
        print("Discovering device...")
        device_ip, device_auth = device.discover_device()
        
        if not device_ip:
            print("ERROR: Could not discover HDHomeRun device")
            return False
    
    # 2. Get lineup and generate playlist
    print("Fetching channel lineup...")
    lineup_data = device.get_lineup(device_ip)
    
    if lineup_data:
        print("Generating playlist...")
        playlist_success = playlist.generate_playlist(lineup_data, device_ip)
    else:
        print("ERROR: Failed to fetch lineup data")
        playlist_success = False
    
    # 3. Update EPG
    if device_auth:
        print("Updating EPG data...")
        epg_success = epg.update_epg(device_auth)
    else:
        print("ERROR: No DeviceAuth available for EPG update")
        epg_success = False
    
    success = playlist_success and epg_success
    
    if success:
        print("--- Data update completed successfully ---\n")
    else:
        print("--- Data update completed with errors ---\n")
    
    return success


def initialize_app():
    """Initialize the application on startup."""
    global device_ip, device_auth
    
    print("=" * 50)
    print("Initializing HDHR-Gateway...")
    print("=" * 50)
    
    # Ensure output directory exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Discover device and generate initial data
    print("\nPerforming initial data generation...")
    initial_success = update_data()
    
    if not initial_success:
        print("\nWARNING: Initial data generation failed!")
        print("The server will start, but files may not be available.")
        print("Check your network connection and HDHomeRun device.")
    
    # Setup background scheduler for EPG updates
    print(f"\nSetting up background scheduler (updates every {config.EPG_UPDATE_INTERVAL_HOURS} hours)...")
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=update_data,
        trigger='interval',
        hours=config.EPG_UPDATE_INTERVAL_HOURS,
        id='epg_update'
    )
    scheduler.start()
    print("Background scheduler started")
    
    print("=" * 50)
    print(f"Server starting on http://0.0.0.0:{config.HTTP_PORT}")
    print("=" * 50)
    print(f"\nAccess URLs:")
    print(f"  Playlist: http://localhost:{config.HTTP_PORT}/playlist.m3u")
    print(f"  EPG:      http://localhost:{config.HTTP_PORT}/epg.xml")
    print(f"  Status:   http://localhost:{config.HTTP_PORT}/")
    print(f"  Refresh:  POST http://localhost:{config.HTTP_PORT}/refresh")
    print()


if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=config.HTTP_PORT, debug=True)
