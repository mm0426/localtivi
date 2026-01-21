"""
XMLTV EPG generator module.
"""

import os
import requests
import config


def update_epg(device_auth):
    """
    Fetch and save XMLTV EPG data.
    
    Args:
        device_auth (str): DeviceAuth string for API access
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not device_auth:
        print("No DeviceAuth provided")
        return False
    
    try:
        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # Construct API URL
        api_url = f"http://api.hdhomerun.com/api/xmltv?DeviceAuth={device_auth}"
        
        print(f"Fetching EPG data from SiliconDust API...")
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 200:
            # Get the raw XML content
            xml_content = response.text
            
            # Basic validation - check if content is not empty and looks like XML
            if not xml_content or len(xml_content) < 100:
                print("EPG data appears to be empty or invalid")
                return False
            
            if not xml_content.strip().startswith('<?xml'):
                print("EPG data does not appear to be valid XML")
                return False
            
            # Write to file
            output_path = os.path.join(config.OUTPUT_DIR, 'epg.xml')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            file_size = len(xml_content)
            print(f"EPG updated: {file_size} bytes written to {output_path}")
            return True
        else:
            print(f"Failed to fetch EPG data: HTTP {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"Network error fetching EPG: {e}")
        return False
    except Exception as e:
        print(f"Error updating EPG: {e}")
        return False
