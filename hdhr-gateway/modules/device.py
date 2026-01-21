"""
Device discovery and data retrieval module for HDHomeRun devices.
"""

import socket
import requests
import config


def discover_device():
    """
    Discover HDHomeRun device on the local network.
    
    Returns:
        tuple: (device_ip, device_auth) or (None, None) if not found
    """
    # Try UDP broadcast discovery first
    device_ip = _discover_via_udp()
    
    # Fallback to cloud API if UDP fails
    if not device_ip:
        print("UDP discovery failed, trying cloud API...")
        device_ip = _discover_via_cloud_api()
    
    if device_ip:
        print(f"Device found at: {device_ip}")
        device_auth = get_device_auth(device_ip)
        return device_ip, device_auth
    
    print("No HDHomeRun device found")
    return None, None


def _discover_via_udp():
    """
    Attempt to discover device via UDP broadcast.
    
    Returns:
        str: Device IP address or None
    """
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(3)  # 3 second timeout
        
        # Send discovery packet
        message = b'\x00\x02\x00\x0c\x01\x04\x00\x00\x00\x01\x02\x04\x00\x00\x00\x01'
        sock.sendto(message, (config.UDP_IP, config.UDP_PORT))
        
        # Wait for response
        try:
            data, addr = sock.recvfrom(1024)
            sock.close()
            return addr[0]
        except socket.timeout:
            sock.close()
            return None
            
    except Exception as e:
        print(f"UDP discovery error: {e}")
        return None


def _discover_via_cloud_api():
    """
    Discover device via HDHomeRun cloud API.
    
    Returns:
        str: Device IP address or None
    """
    try:
        response = requests.get('http://ipv4-api.hdhomerun.com/discover', timeout=5)
        if response.status_code == 200:
            data = response.json()
            # API returns list of devices, take the first one
            if data and len(data) > 0:
                return data[0].get('LocalIP')
    except Exception as e:
        print(f"Cloud API discovery error: {e}")
    
    return None


def get_device_auth(ip):
    """
    Fetch DeviceAuth string from the device.
    
    Args:
        ip (str): Device IP address
        
    Returns:
        str: DeviceAuth string or None
    """
    try:
        url = f"http://{ip}/discover.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            device_auth = data.get('DeviceAuth')
            if device_auth:
                print(f"DeviceAuth retrieved: {device_auth}")
                return device_auth
            else:
                print("DeviceAuth not found in discover.json")
        else:
            print(f"Failed to fetch discover.json: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching DeviceAuth: {e}")
    
    return None


def get_lineup(ip):
    """
    Fetch channel lineup from the device.
    
    Args:
        ip (str): Device IP address
        
    Returns:
        list: JSON list of channels or None
    """
    try:
        url = f"http://{ip}/lineup.json"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            lineup = response.json()
            print(f"Lineup retrieved: {len(lineup)} channels found")
            return lineup
        else:
            print(f"Failed to fetch lineup.json: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Error fetching lineup: {e}")
    
    return None
