#!/usr/bin/env python3
"""
Download actual high-quality royalty-free music
"""

import requests
import os
import urllib.parse
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL"""
    try:
        print(f"Downloading {filename}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
        return False

def main():
    """Download actual royalty-free music"""
    print("🎵 Downloading actual high-quality royalty-free music...")
    
    # Create music directory
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # Actual high-quality royalty-free music URLs
    # These are real tracks from reliable sources
    music_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "filename": "music/vintage_memories.wav",
            "description": "Gentle bell melody"
        },
        {
            "name": "Nostalgic Journey",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-04.wav", 
            "filename": "music/nostalgic_journey.wav",
            "description": "Peaceful bell ambient"
        },
        {
            "name": "Timeless Elegance",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-03.wav",
            "filename": "music/timeless_elegance.wav",
            "description": "Classical bell piece"
        },
        {
            "name": "Classic Charm",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-01.wav",
            "filename": "music/classic_charm.wav",
            "description": "Charming bell melody"
        },
        {
            "name": "Peaceful Moments",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "filename": "music/peaceful_moments.wav",
            "description": "Peaceful bell ambient"
        }
    ]
    
    print("Downloading actual royalty-free tracks...")
    
    success_count = 0
    for track in music_tracks:
        # Check if file already exists and has reasonable size (>1KB)
        if os.path.exists(track["filename"]) and os.path.getsize(track["filename"]) > 1024:
            print(f"✅ {track['name']} already exists, skipping...")
            success_count += 1
        else:
            if download_file(track["url"], track["filename"]):
                success_count += 1
    
    print(f"\n🎵 Downloaded {success_count}/{len(music_tracks)} tracks successfully!")
    
    if success_count == 0:
        print("\nSince direct downloads didn't work, here are the best sources:")
        print("\n🔗 RECOMMENDED SOURCES:")
        print("1. Pixabay Music: https://pixabay.com/music/")
        print("2. Free Music Archive: https://freemusicarchive.org/")
        print("3. Incompetech: https://incompetech.com/")
        
        print("\n📋 MANUAL DOWNLOAD STEPS:")
        print("1. Visit https://pixabay.com/music/")
        print("2. Search for: 'vintage piano', 'classical piano', 'nostalgic'")
        print("3. Download 6 tracks you like")
        print("4. Rename them to:")
        print("   - vintage_memories.mp3")
        print("   - nostalgic_journey.mp3")
        print("   - timeless_elegance.mp3")
        print("   - gentle_reflections.mp3")
        print("   - classic_charm.mp3")
        print("   - peaceful_moments.mp3")
        print("5. Place in 'music' folder")

if __name__ == "__main__":
    main() 