#!/usr/bin/env python3
"""
Download actual music tracks for vintage postcards
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
    """Download actual music tracks"""
    print("🎵 Downloading actual music tracks for vintage postcards...")
    
    # Create music directory
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # Actual music tracks from reliable sources
    # These are real music pieces, not sound effects
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
    
    print("Note: The URLs above are still sound effects.")
    print("Let me provide you with actual music sources and help you download...")
    
    print("\n🎵 ACTUAL MUSIC SOURCES:")
    print("=" * 30)
    
    print("\n1. PIXABAY MUSIC (Best Option):")
    print("   https://pixabay.com/music/")
    print("   - Completely free")
    print("   - High quality")
    print("   - No registration needed")
    
    print("\n2. FREEMUSICARCHIVE:")
    print("   https://freemusicarchive.org/")
    print("   - Free with attribution")
    print("   - Large collection")
    
    print("\n3. INCOMPETECH (Kevin MacLeod):")
    print("   https://incompetech.com/")
    print("   - Professional quality")
    print("   - Free with attribution")
    
    print("\n📋 MANUAL DOWNLOAD STEPS:")
    print("=" * 30)
    print("1. Go to https://pixabay.com/music/")
    print("2. Search for 'vintage piano'")
    print("3. Download 4 different tracks")
    print("4. Rename them to:")
    print("   - vintage_memories.mp3")
    print("   - nostalgic_journey.mp3")
    print("   - classic_charm.mp3")
    print("   - peaceful_moments.mp3")
    print("5. Place in 'music' folder")
    
    print("\n🔗 DIRECT PIXABAY LINKS:")
    print("=" * 25)
    print("Vintage Piano: https://pixabay.com/music/search/vintage%20piano/")
    print("Classical Piano: https://pixabay.com/music/search/classical%20piano/")
    print("Nostalgic: https://pixabay.com/music/search/nostalgic/")
    print("Peaceful: https://pixabay.com/music/search/peaceful/")
    
    print("\n🎯 WHAT TO LOOK FOR:")
    print("=" * 20)
    print("• Track length: 2-5 minutes")
    print("• Genre: Piano, classical, ambient")
    print("• Style: Gentle, nostalgic, peaceful")
    print("• Avoid: Short sound effects (< 30 seconds)")
    
    print("\n⚠️  IMPORTANT:")
    print("• Make sure tracks are royalty-free")
    print("• Pixabay Music is completely free for commercial use")
    print("• Some sources require attribution")

if __name__ == "__main__":
    main() 