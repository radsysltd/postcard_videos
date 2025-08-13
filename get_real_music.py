#!/usr/bin/env python3
"""
Get real music for vintage postcards
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
    """Get real music tracks"""
    print("🎵 Getting real music for vintage postcards...")
    
    # Create music directory
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # Let me try some actual music URLs from reliable sources
    # These are real music tracks, not sound effects
    music_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "filename": "music/vintage_memories.wav",
            "description": "This is still a sound effect - need real music"
        }
    ]
    
    print("I need to find actual music URLs. Let me provide you with the best sources...")
    
    print("\n🎵 BEST SOURCES FOR REAL MUSIC:")
    print("=" * 35)
    
    print("\n1. PIXABAY MUSIC (Recommended):")
    print("   https://pixabay.com/music/")
    print("   - Completely free for commercial use")
    print("   - High quality piano and classical music")
    print("   - No registration required")
    
    print("\n2. FREEMUSICARCHIVE:")
    print("   https://freemusicarchive.org/")
    print("   - Free with attribution")
    print("   - Large collection of vintage/classical music")
    
    print("\n3. INCOMPETECH (Kevin MacLeod):")
    print("   https://incompetech.com/")
    print("   - Professional quality")
    print("   - Free with attribution")
    
    print("\n📋 QUICK STEPS:")
    print("=" * 15)
    print("1. Visit https://pixabay.com/music/")
    print("2. Search: 'vintage piano', 'classical piano', 'nostalgic'")
    print("3. Download 4 tracks (2-5 minutes each)")
    print("4. Rename to: vintage_memories.mp3, nostalgic_journey.mp3, etc.")
    print("5. Place in 'music' folder")
    
    print("\n🔗 DIRECT LINKS:")
    print("=" * 15)
    print("Vintage Piano: https://pixabay.com/music/search/vintage%20piano/")
    print("Classical Piano: https://pixabay.com/music/search/classical%20piano/")
    print("Nostalgic: https://pixabay.com/music/search/nostalgic/")
    print("Peaceful: https://pixabay.com/music/search/peaceful/")
    
    print("\n🎯 WHAT TO LOOK FOR:")
    print("=" * 20)
    print("• Track length: 2-5 minutes (not 30-second effects)")
    print("• Genre: Piano, classical, ambient")
    print("• Style: Gentle, nostalgic, peaceful")
    print("• Quality: High-quality audio files")
    
    print("\n⚠️  IMPORTANT:")
    print("• Make sure tracks are royalty-free")
    print("• Pixabay Music is completely free")
    print("• Some sources require attribution")

if __name__ == "__main__":
    main() 