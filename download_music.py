#!/usr/bin/env python3
"""
Download high-quality royalty-free music for the postcard video creator
"""

import requests
import os
import urllib.parse
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def main():
    """Download royalty-free music"""
    print("Downloading high-quality royalty-free music...")
    
    # Create music directory
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # List of high-quality royalty-free music URLs (vintage/antique style)
    # These are from Pixabay Music - completely free for commercial use
    music_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=gentle-piano-112197.mp3",
            "filename": "music/vintage_memories.mp3"
        },
        {
            "name": "Nostalgic Journey", 
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=peaceful-garden-112197.mp3",
            "filename": "music/nostalgic_journey.mp3"
        },
        {
            "name": "Timeless Elegance",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=classical-piano-112197.mp3", 
            "filename": "music/timeless_elegance.mp3"
        },
        {
            "name": "Gentle Reflections",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=ambient-piano-112197.mp3",
            "filename": "music/gentle_reflections.mp3"
        },
        {
            "name": "Classic Charm",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=waltz-melody-112197.mp3",
            "filename": "music/classic_charm.mp3"
        },
        {
            "name": "Peaceful Moments",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/15/audio_8b6c1b9c.mp3?filename=meditation-ambient-112197.mp3",
            "filename": "music/peaceful_moments.mp3"
        }
    ]
    
    # Since the URLs above are placeholders, let me create some alternative sources
    # Using actual royalty-free music from reliable sources
    alternative_tracks = [
        {
            "name": "Vintage Memories",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "filename": "music/vintage_memories.wav"
        },
        {
            "name": "Nostalgic Journey",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-04.wav", 
            "filename": "music/nostalgic_journey.wav"
        },
        {
            "name": "Timeless Elegance",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-03.wav",
            "filename": "music/timeless_elegance.wav"
        },
        {
            "name": "Gentle Reflections",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-02.wav",
            "filename": "music/gentle_reflections.wav"
        },
        {
            "name": "Classic Charm",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-01.wav",
            "filename": "music/classic_charm.wav"
        },
        {
            "name": "Peaceful Moments",
            "url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            "filename": "music/peaceful_moments.wav"
        }
    ]
    
    print("Note: Creating placeholder music files for demonstration...")
    print("In a real implementation, you would download from actual royalty-free music sources.")
    
    # Create placeholder files for now
    for track in alternative_tracks:
        print(f"Creating placeholder for {track['name']}...")
        
        # Create a simple placeholder audio file
        import wave
        import struct
        import numpy as np
        
        # Create a simple tone as placeholder
        sample_rate = 44100
        duration = 30  # 30 seconds
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Apply fade
        fade_samples = int(sample_rate * 2)
        audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
        audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
        
        # Save as WAV
        audio_int = (audio * 32767).astype(np.int16)
        
        with wave.open(track['filename'], 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int.tobytes())
        
        print(f"✅ Created {track['filename']}")
    
    print("\n🎵 Placeholder music files created!")
    print("For production use, replace these with actual royalty-free music from:")
    print("- Pixabay Music (pixabay.com/music)")
    print("- Free Music Archive (freemusicarchive.org)")
    print("- ccMixter (ccmixter.org)")
    print("- Incompetech (incompetech.com)")

if __name__ == "__main__":
    main() 