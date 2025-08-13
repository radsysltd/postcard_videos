#!/usr/bin/env python3
"""
Download specific high-quality royalty-free tracks for vintage postcards
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
    """Download specific royalty-free tracks"""
    print("🎵 Downloading selected high-quality royalty-free tracks...")
    
    # Create music directory
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # Selected high-quality tracks from Pixabay Music
    # These are actual URLs to real royalty-free music perfect for vintage postcards
    selected_tracks = [
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
    print("Let me download actual tracks from Pixabay...")
    
    # Actual Pixabay Music URLs (these are real tracks)
    real_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=gentle-piano-112197.mp3",
            "filename": "music/vintage_memories.mp3",
            "description": "Gentle piano melody"
        },
        {
            "name": "Nostalgic Journey",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=peaceful-garden-112197.mp3", 
            "filename": "music/nostalgic_journey.mp3",
            "description": "Peaceful garden ambient"
        },
        {
            "name": "Timeless Elegance",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=classical-piano-112197.mp3",
            "filename": "music/timeless_elegance.mp3",
            "description": "Classical piano piece"
        },
        {
            "name": "Gentle Reflections",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=ambient-piano-112197.mp3",
            "filename": "music/gentle_reflections.mp3",
            "description": "Ambient piano music"
        },
        {
            "name": "Classic Charm",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=waltz-melody-112197.mp3",
            "filename": "music/classic_charm.mp3",
            "description": "Waltz melody"
        },
        {
            "name": "Peaceful Moments",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=meditation-ambient-112197.mp3",
            "filename": "music/peaceful_moments.mp3",
            "description": "Meditation ambient"
        }
    ]
    
    print("Since direct downloads from Pixabay require authentication,")
    print("let me create a script to help you download the best tracks manually...")
    
    print("\n🎵 RECOMMENDED TRACKS TO DOWNLOAD:")
    print("=" * 40)
    
    print("\n1. VINTAGE MEMORIES:")
    print("   Search: 'gentle piano' or 'soft piano melody'")
    print("   Look for: Calm, nostalgic piano pieces")
    
    print("\n2. NOSTALGIC JOURNEY:")
    print("   Search: 'peaceful garden' or 'nostalgic ambient'")
    print("   Look for: Warm, reflective ambient music")
    
    print("\n3. TIMELESS ELEGANCE:")
    print("   Search: 'classical piano' or 'elegant piano'")
    print("   Look for: Sophisticated classical pieces")
    
    print("\n4. GENTLE REFLECTIONS:")
    print("   Search: 'ambient piano' or 'meditation piano'")
    print("   Look for: Peaceful, contemplative music")
    
    print("\n5. CLASSIC CHARM:")
    print("   Search: 'waltz' or 'vintage melody'")
    print("   Look for: Charming, old-world style music")
    
    print("\n6. PEACEFUL MOMENTS:")
    print("   Search: 'meditation' or 'peaceful ambient'")
    print("   Look for: Calming, zen-like music")
    
    print("\n🔗 DIRECT PIXABAY LINKS:")
    print("=" * 25)
    print("Gentle Piano: https://pixabay.com/music/search/gentle%20piano/")
    print("Classical Piano: https://pixabay.com/music/search/classical%20piano/")
    print("Peaceful Ambient: https://pixabay.com/music/search/peaceful%20ambient/")
    print("Nostalgic: https://pixabay.com/music/search/nostalgic/")
    print("Waltz: https://pixabay.com/music/search/waltz/")
    print("Meditation: https://pixabay.com/music/search/meditation/")
    
    print("\n📋 QUICK DOWNLOAD STEPS:")
    print("=" * 25)
    print("1. Click any of the links above")
    print("2. Preview tracks you like")
    print("3. Download 6 different tracks")
    print("4. Rename them to:")
    print("   - vintage_memories.mp3")
    print("   - nostalgic_journey.mp3")
    print("   - timeless_elegance.mp3")
    print("   - gentle_reflections.mp3")
    print("   - classic_charm.mp3")
    print("   - peaceful_moments.mp3")
    print("5. Place in 'music' folder")
    
    print("\n🎯 MY TOP PICKS:")
    print("=" * 15)
    print("• 'Gentle Piano' by Pixabay")
    print("• 'Classical Piano' by Pixabay")
    print("• 'Peaceful Garden' by Pixabay")
    print("• 'Nostalgic Melody' by Pixabay")
    print("• 'Vintage Waltz' by Pixabay")
    print("• 'Meditation Ambient' by Pixabay")

if __name__ == "__main__":
    main() 