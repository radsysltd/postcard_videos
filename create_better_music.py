#!/usr/bin/env python3
"""
Create high-quality royalty-free background music for the postcard video creator
"""

import numpy as np
import wave
import struct
import os
import random

def create_note(frequency, duration, sample_rate=44100, wave_type='sine', envelope=True):
    """Create a musical note with envelope"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create base waveform
    if wave_type == 'sine':
        audio = np.sin(2 * np.pi * frequency * t)
    elif wave_type == 'triangle':
        audio = 2 * np.arcsin(np.sin(2 * np.pi * frequency * t)) / np.pi
    elif wave_type == 'square':
        audio = np.sign(np.sin(2 * np.pi * frequency * t)) * 0.5
    elif wave_type == 'sawtooth':
        audio = 2 * (t * frequency - np.floor(0.5 + t * frequency)) * 0.3
    else:
        audio = np.sin(2 * np.pi * frequency * t)
    
    # Apply envelope if requested
    if envelope:
        attack = min(0.1, duration * 0.1)
        release = min(0.2, duration * 0.2)
        sustain = 0.7
        
        attack_samples = int(attack * sample_rate)
        release_samples = int(release * sample_rate)
        sustain_samples = len(audio) - attack_samples - release_samples
        
        if sustain_samples > 0:
            # Create envelope
            envelope = np.ones(len(audio))
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
            envelope[attack_samples:attack_samples+sustain_samples] = sustain
            envelope[attack_samples+sustain_samples:] = np.linspace(sustain, 0, release_samples)
            audio *= envelope
    
    return audio

def create_chord(frequencies, duration, sample_rate=44100, wave_type='sine'):
    """Create a chord from multiple frequencies"""
    chord = np.zeros(int(sample_rate * duration))
    for freq in frequencies:
        note = create_note(freq, duration, sample_rate, wave_type)
        chord += note
    return chord / len(frequencies)  # Normalize

def create_vintage_memories():
    """Create 'Vintage Memories' - beautiful piano-like melody"""
    sample_rate = 44100
    duration = 60
    
    # C major scale with beautiful progression
    scale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C major
    melody = [
        (0, 1.5), (1, 1.5), (2, 1.5), (4, 1.5),  # C, D, E, G
        (6, 1.5), (5, 1.5), (4, 1.5), (3, 1.5),  # B, A, G, F
        (2, 1.5), (1, 1.5), (0, 1.5), (-1, 1.5), # E, D, C, rest
    ]
    
    audio = np.array([])
    for note_idx, note_duration in melody:
        if note_idx >= 0:
            freq = scale[note_idx]
            # Create rich piano-like sound
            note = create_note(freq, note_duration, sample_rate, 'triangle')
            note += 0.3 * create_note(freq * 2, note_duration, sample_rate, 'sine')
            note += 0.15 * create_note(freq * 3, note_duration, sample_rate, 'sine')
        else:
            note = np.zeros(int(sample_rate * note_duration))
        
        audio = np.concatenate([audio, note])
    
    # Repeat with variations
    base_audio = audio.copy()
    for i in range(3):
        if i == 1:  # Add harmony
            harmony = np.roll(base_audio, int(sample_rate * 0.5))
            audio = np.concatenate([audio, (base_audio + harmony * 0.4) * 0.8])
        else:
            audio = np.concatenate([audio, base_audio])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply fade
    fade_samples = int(sample_rate * 4)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def create_nostalgic_journey():
    """Create 'Nostalgic Journey' - warm strings-like melody"""
    sample_rate = 44100
    duration = 60
    
    # G major scale - warm and nostalgic
    scale = [196.00, 220.00, 246.94, 261.63, 293.66, 329.63, 369.99, 392.00]  # G major
    melody = [
        (0, 2), (2, 2), (4, 2), (5, 2),  # G, B, D, E
        (4, 2), (3, 2), (2, 2), (1, 2),  # D, C#, B, A
        (0, 2), (6, 2), (5, 2), (4, 2),  # G, F#, E, D
        (-1, 2),  # Rest
    ]
    
    audio = np.array([])
    for note_idx, note_duration in melody:
        if note_idx >= 0:
            freq = scale[note_idx]
            # Create warm string-like sound
            note = create_note(freq, note_duration, sample_rate, 'sine')
            note += 0.5 * create_note(freq * 1.5, note_duration, sample_rate, 'sine')
            note += 0.25 * create_note(freq * 2.5, note_duration, sample_rate, 'sine')
        else:
            note = np.zeros(int(sample_rate * note_duration))
        
        audio = np.concatenate([audio, note])
    
    # Repeat with layering
    base_audio = audio.copy()
    for i in range(3):
        if i == 1:  # Add lower octave
            lower_octave = base_audio * 0.6
            audio = np.concatenate([audio, lower_octave])
        else:
            audio = np.concatenate([audio, base_audio])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply fade
    fade_samples = int(sample_rate * 5)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def create_timeless_elegance():
    """Create 'Timeless Elegance' - classical-inspired melody"""
    sample_rate = 44100
    duration = 60
    
    # D major scale - elegant and classical
    scale = [146.83, 164.81, 185.00, 196.00, 220.00, 246.94, 277.18, 293.66]  # D major
    melody = [
        (0, 1.5), (2, 1.5), (4, 1.5), (6, 1.5),  # D, F#, A, C#
        (7, 1.5), (6, 1.5), (5, 1.5), (4, 1.5),  # D, C#, B, A
        (3, 1.5), (2, 1.5), (1, 1.5), (0, 1.5),  # G, F#, E, D
        (-1, 1.5),  # Rest
    ]
    
    audio = np.array([])
    for note_idx, note_duration in melody:
        if note_idx >= 0:
            freq = scale[note_idx]
            # Create classical sound with rich harmonics
            note = create_note(freq, note_duration, sample_rate, 'triangle')
            note += 0.6 * create_note(freq * 2, note_duration, sample_rate, 'sine')
            note += 0.3 * create_note(freq * 3, note_duration, sample_rate, 'sine')
            note += 0.15 * create_note(freq * 4, note_duration, sample_rate, 'sine')
        else:
            note = np.zeros(int(sample_rate * note_duration))
        
        audio = np.concatenate([audio, note])
    
    # Repeat with counterpoint
    base_audio = audio.copy()
    for i in range(3):
        if i == 1:  # Add counterpoint
            counterpoint = np.roll(base_audio, int(sample_rate * 1.5))
            audio = np.concatenate([audio, (base_audio + counterpoint * 0.5) * 0.7])
        else:
            audio = np.concatenate([audio, base_audio])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply fade
    fade_samples = int(sample_rate * 3)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def create_gentle_reflections():
    """Create 'Gentle Reflections' - ambient-like melody"""
    sample_rate = 44100
    duration = 60
    
    # Create ambient pad with slow progression
    base_freq = 220.00  # A3
    audio = np.array([])
    
    for i in range(20):  # 20 segments
        # Vary frequency slightly for ambient effect
        freq = base_freq * (1 + 0.05 * np.sin(i * 0.3))
        
        # Create ambient pad with multiple layers
        note = create_note(freq, 3, sample_rate, 'sine', envelope=False)
        note += 0.3 * create_note(freq * 1.25, 3, sample_rate, 'sine', envelope=False)
        note += 0.2 * create_note(freq * 1.75, 3, sample_rate, 'sine', envelope=False)
        note += 0.1 * create_note(freq * 2.25, 3, sample_rate, 'sine', envelope=False)
        
        # Add slow modulation
        t = np.linspace(0, 3, len(note))
        modulation = 0.1 * np.sin(2 * np.pi * 0.1 * t)
        note *= (1 + modulation)
        
        audio = np.concatenate([audio, note])
    
    # Repeat to fill duration
    while len(audio) < sample_rate * duration:
        audio = np.concatenate([audio, audio[:sample_rate * 6]])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply very gentle fade
    fade_samples = int(sample_rate * 8)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def create_classic_charm():
    """Create 'Classic Charm' - waltz-like melody"""
    sample_rate = 44100
    duration = 60
    
    # C major scale for waltz
    scale = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C major
    melody = [
        (0, 1), (2, 1), (4, 1), (0, 1),  # C, E, G, C
        (3, 1), (5, 1), (6, 1), (5, 1),  # F, A, B, A
        (4, 1), (2, 1), (1, 1), (0, 1),  # G, E, D, C
        (-1, 1),  # Rest
    ]
    
    audio = np.array([])
    for note_idx, note_duration in melody:
        if note_idx >= 0:
            freq = scale[note_idx]
            # Create waltz sound
            note = create_note(freq, note_duration, sample_rate, 'triangle')
            note += 0.4 * create_note(freq * 2, note_duration, sample_rate, 'sine')
            note += 0.2 * create_note(freq * 3, note_duration, sample_rate, 'sine')
        else:
            note = np.zeros(int(sample_rate * note_duration))
        
        audio = np.concatenate([audio, note])
    
    # Repeat with waltz rhythm
    base_audio = audio.copy()
    for i in range(4):
        if i == 1:  # Add bass line
            bass = np.roll(base_audio, int(sample_rate * 0.5)) * 0.3
            audio = np.concatenate([audio, (base_audio + bass) * 0.8])
        else:
            audio = np.concatenate([audio, base_audio])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply fade
    fade_samples = int(sample_rate * 2)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def create_peaceful_moments():
    """Create 'Peaceful Moments' - meditation-like melody"""
    sample_rate = 44100
    duration = 60
    
    # Create peaceful meditation melody
    base_freq = 196.00  # G3
    audio = np.array([])
    
    for i in range(15):  # 15 segments
        # Very slow, peaceful progression
        freq = base_freq * (1 + 0.02 * np.sin(i * 0.2))
        
        # Create meditation sound
        note = create_note(freq, 4, sample_rate, 'sine', envelope=False)
        note += 0.2 * create_note(freq * 1.5, 4, sample_rate, 'sine', envelope=False)
        note += 0.1 * create_note(freq * 2.25, 4, sample_rate, 'sine', envelope=False)
        
        # Add very slow modulation
        t = np.linspace(0, 4, len(note))
        modulation = 0.05 * np.sin(2 * np.pi * 0.05 * t)
        note *= (1 + modulation)
        
        audio = np.concatenate([audio, note])
    
    # Repeat to fill duration
    while len(audio) < sample_rate * duration:
        audio = np.concatenate([audio, audio[:sample_rate * 8]])
    
    audio = audio[:int(sample_rate * duration)]
    
    # Apply very gentle fade
    fade_samples = int(sample_rate * 10)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return audio, sample_rate

def save_audio(audio, sample_rate, filename):
    """Save audio as WAV file"""
    # Normalize audio
    audio = audio / np.max(np.abs(audio))
    
    # Convert to 16-bit integers
    audio_int = (audio * 32767).astype(np.int16)
    
    # Save as WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int.tobytes())

def main():
    """Create all music files"""
    print("Creating high-quality royalty-free background music...")
    
    # Create music directory if it doesn't exist
    if not os.path.exists('music'):
        os.makedirs('music')
    
    # Create all music tracks
    tracks = [
        ("Vintage Memories", create_vintage_memories),
        ("Nostalgic Journey", create_nostalgic_journey),
        ("Timeless Elegance", create_timeless_elegance),
        ("Gentle Reflections", create_gentle_reflections),
        ("Classic Charm", create_classic_charm),
        ("Peaceful Moments", create_peaceful_moments)
    ]
    
    for track_name, create_func in tracks:
        print(f"Creating {track_name}...")
        audio, sample_rate = create_func()
        filename = f"music/{track_name.replace(' ', '_').lower()}.wav"
        save_audio(audio, sample_rate, filename)
        print(f"✅ Saved {filename}")
    
    print("\n🎵 All high-quality music tracks created successfully!")
    print("Files created in 'music' directory:")
    for track_name, _ in tracks:
        filename = f"music/{track_name.replace(' ', '_').lower()}.wav"
        print(f"- {filename}")

if __name__ == "__main__":
    main() 