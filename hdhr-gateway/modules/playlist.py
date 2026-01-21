"""
M3U playlist generator module.
"""

import os
import config


def generate_playlist(lineup_json, device_ip):
    """
    Generate M3U playlist from HDHomeRun lineup data.
    
    Args:
        lineup_json (list): Channel lineup data
        device_ip (str): Device IP address
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not lineup_json:
        print("No lineup data provided")
        return False
    
    try:
        # Ensure output directory exists
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        
        # Build M3U content
        m3u_lines = ['#EXTM3U']
        
        for channel in lineup_json:
            # Filter for enabled channels only (DRM=false typically means enabled)
            if channel.get('DRM', False):
                continue
            
            # Extract channel information
            guide_name = channel.get('GuideName', 'Unknown')
            guide_number = channel.get('GuideNumber', '')
            channel_url = channel.get('URL', '')
            
            # If URL is not provided, construct it
            if not channel_url:
                # Extract channel number from GuideNumber (e.g., "10.1" -> "v10.1")
                if guide_number:
                    channel_url = f"http://{device_ip}:5004/auto/v{guide_number}"
                else:
                    continue  # Skip if no guide number or URL
            
            # Format #EXTINF line with tvg attributes
            extinf = f'#EXTINF:-1 tvg-id="{guide_number}" tvg-name="{guide_name}" tvg-chno="{guide_number}",{guide_name}'
            
            m3u_lines.append(extinf)
            m3u_lines.append(channel_url)
        
        # Write to file
        output_path = os.path.join(config.OUTPUT_DIR, 'playlist.m3u')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_lines))
        
        channel_count = (len(m3u_lines) - 1) // 2  # Subtract header, divide by 2 (extinf + url)
        print(f"Playlist generated: {channel_count} channels written to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error generating playlist: {e}")
        return False
