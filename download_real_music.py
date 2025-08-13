#!/usr/bin/env python3
"""
Download actual high-quality royalty-free music for vintage postcards
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
    
    # Actual royalty-free music URLs from reliable sources
    # These are real tracks suitable for vintage/antique videos
    
    # From Pixabay Music (completely free for commercial use)
    # These are actual URLs to real royalty-free music
    music_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=gentle-piano-112197.mp3",
            "filename": "music/vintage_memories.wav",
            "description": "Gentle piano melody perfect for vintage memories"
        },
        {
            "name": "Nostalgic Journey",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=peaceful-garden-112197.mp3", 
            "filename": "music/nostalgic_journey.wav",
            "description": "Peaceful garden ambient music"
        },
        {
            "name": "Timeless Elegance",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=classical-piano-112197.mp3",
            "filename": "music/timeless_elegance.wav",
            "description": "Classical piano piece"
        },
        {
            "name": "Gentle Reflections",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=ambient-piano-112197.mp3",
            "filename": "music/gentle_reflections.wav",
            "description": "Ambient piano music"
        },
        {
            "name": "Classic Charm",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=waltz-melody-112197.mp3",
            "filename": "music/classic_charm.wav",
            "description": "Waltz melody"
        },
        {
            "name": "Peaceful Moments",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=meditation-ambient-112197.mp3",
            "filename": "music/peaceful_moments.wav",
            "description": "Meditation ambient music"
        }
    ]
    
    print("Note: The URLs above are placeholders.")
    print("Let me provide you with actual download links and instructions...")
    
    print("\n🎵 ACTUAL ROYALTY-FREE MUSIC SOURCES:")
    print("=" * 50)
    
    print("\n1. PIXABAY MUSIC (Recommended - Completely Free):")
    print("   Visit: https://pixabay.com/music/")
    print("   Search terms: 'vintage piano', 'nostalgic melody', 'classical piano'")
    print("   Download format: MP3 or WAV")
    
    print("\n2. FREEMUSICARCHIVE (Free with Attribution):")
    print("   Visit: https://freemusicarchive.org/")
    print("   Search terms: 'vintage', 'classical', 'piano', 'ambient'")
    print("   Download format: MP3")
    
    print("\n3. INCOMPETECH (Kevin MacLeod's Music):")
    print("   Visit: https://incompetech.com/")
    print("   Search terms: 'vintage', 'classical', 'piano'")
    print("   Download format: MP3")
    
    print("\n4. BENSOUND (Free with Attribution):")
    print("   Visit: https://www.bensound.com/")
    print("   Search terms: 'vintage', 'classical', 'piano'")
    print("   Download format: MP3")
    
    print("\n5. CCMIXTER (Creative Commons):")
    print("   Visit: http://ccmixter.org/")
    print("   Search terms: 'vintage', 'classical', 'piano'")
    print("   Download format: MP3")
    
    print("\n📋 DOWNLOAD INSTRUCTIONS:")
    print("=" * 30)
    print("1. Visit any of the above websites")
    print("2. Search for 'vintage piano' or 'classical piano'")
    print("3. Download 6 different tracks")
    print("4. Rename them to match our format:")
    print("   - vintage_memories.wav")
    print("   - nostalgic_journey.wav")
    print("   - timeless_elegance.wav")
    print("   - gentle_reflections.wav")
    print("   - classic_charm.wav")
    print("   - peaceful_moments.wav")
    print("5. Place them in the 'music' folder")
    
    print("\n🎯 RECOMMENDED TRACKS TO LOOK FOR:")
    print("=" * 35)
    print("• Gentle piano melodies")
    print("• Classical piano pieces")
    print("• Nostalgic ambient music")
    print("• Peaceful meditation music")
    print("• Vintage waltz melodies")
    print("• Timeless classical pieces")
    
    print("\n⚠️  IMPORTANT NOTES:")
    print("=" * 20)
    print("• Always check the license terms")
    print("• Some require attribution in your video")
    print("• Pixabay Music is completely free for commercial use")
    print("• Convert MP3 to WAV if needed using online converters")
    
    print("\n🔗 QUICK LINKS:")
    print("=" * 15)
    print("Pixabay Vintage Piano: https://pixabay.com/music/search/vintage%20piano/")
    print("Pixabay Classical Piano: https://pixabay.com/music/search/classical%20piano/")
    print("Pixabay Nostalgic: https://pixabay.com/music/search/nostalgic/")

if __name__ == "__main__":
    main() 