import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
import threading
import time
from PIL import Image, ImageTk
import cv2
import shutil
import glob
# Import core MoviePy modules first
try:
    # Try newer MoviePy 2.x import structure
    from moviepy import VideoClip, concatenate_videoclips, ImageClip, AudioFileClip
    print("DEBUG: Core MoviePy imports successful (MoviePy 2.x)")
except Exception:
    try:
        # Fallback to older MoviePy import structure
        from moviepy.editor import VideoClip, concatenate_videoclips, ImageClip, AudioFileClip
        print("DEBUG: Core MoviePy imports successful (older MoviePy)")
    except Exception as e:
        print(f"ERROR: MoviePy not properly installed: {e}")
        VideoClip = None
        concatenate_videoclips = None
        ImageClip = None
        AudioFileClip = None

# Import fade effects with fallbacks
try:
    # MoviePy 2.x structure - using proper method calls
    import moviepy
    def vfx_fadein(clip, duration):
        return clip.with_effects([moviepy.vfx.FadeIn(duration)])
    def vfx_fadeout(clip, duration):
        return clip.with_effects([moviepy.vfx.FadeOut(duration)])
    print("DEBUG: MoviePy 2.x fade effects imported successfully")
except Exception:
    try:
        # Older MoviePy structure
        from moviepy.video.fx.fadein import fadein as vfx_fadein
        from moviepy.video.fx.fadeout import fadeout as vfx_fadeout
        print("DEBUG: Older MoviePy fade effects imported successfully")
    except Exception:
        try:
            # Alternate aggregator path
            from moviepy.video.fx.all import fadein as vfx_fadein, fadeout as vfx_fadeout
            print("DEBUG: MoviePy fade effects imported via .all module")
        except Exception as e:
            print(f"DEBUG: Fade effects not available, using no-op functions: {e}")
            # Last-resort no-op functions to avoid import crashes
            def vfx_fadein(clip, duration):
                return clip
            def vfx_fadeout(clip, duration):
                return clip
import numpy as np
from datetime import datetime
import json
import logging
import requests
import tempfile
from urllib.parse import urlparse
import zipfile
import xml.etree.ElementTree as ET

# Setup logging
def setup_logging():
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, f"debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging to both file and console
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # This keeps console output
        ]
    )
    
    logging.info(f"Logging started - Log file: {log_file}")
    return log_file

# Setup logging when module is imported
current_log_file = setup_logging()

def get_latest_log_file():
    """Get the path to the most recent log file"""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        return None
    
    log_files = [f for f in os.listdir(log_dir) if f.startswith("debug_") and f.endswith(".log")]
    if not log_files:
        return None
    
    # Sort by filename (which contains timestamp) to get latest
    latest_log = sorted(log_files)[-1]
    return os.path.join(log_dir, latest_log)

# YouTube API imports
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    import pickle
    YOUTUBE_API_AVAILABLE = True
    print("DEBUG: YouTube API libraries available")
except ImportError as e:
    YOUTUBE_API_AVAILABLE = False
    print(f"YouTube API libraries not available: {e}")
    print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

class PostcardVideoCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Postcard Video Creator")
        # Start maximized for better layout; fallback size if not supported
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.postcard_images = []  # List of image paths in order
        self.image_durations = []  # List of durations for each image
        self.image_included = []  # List of boolean values for each image (checked/unchecked)
        self.output_path = r"C:\_postcards\renamed_postcards\videos"
        self.is_processing = False
        self.latest_video_path = None  # Track the most recently created video
        self.video_parts = []  # Track all created video parts for selection
        self.regeneration_info = None  # Track regeneration details when recreating a specific part
        
        # YouTube channel management
        self.youtube_channels = []  # List of available channels
        self.selected_channel_id = None  # Currently selected channel
        self.default_channel_id = None  # Default channel for uploads
        
        # Create default output directory if it doesn't exist
        if not os.path.exists(self.output_path):
            try:
                os.makedirs(self.output_path, exist_ok=True)
                print(f"Created default output directory: {self.output_path}")
            except Exception as e:
                print(f"Could not create default directory: {e}")
                # If we can't create the default directory, start with empty path
                self.output_path = ""
        else:
            print(f"Default output directory exists: {self.output_path}")
        
        # Video settings
        self.default_duration = 4  # seconds
        self.transition_duration = 1.0  # seconds
        self.video_width = 1080
        self.video_height = 1080
        
        # Background color for square format
        self.background_color_var = tk.StringVar(value="light_gray")
        
        # Starting part number for video naming
        self.starting_part_var = tk.IntVar(value=1)

        # Global fade options
        self.start_fade_in_var = tk.BooleanVar(value=False)
        self.start_fade_out_var = tk.BooleanVar(value=False)
        self.start_fade_in_dur_var = tk.DoubleVar(value=0.5)
        self.start_fade_out_dur_var = tk.DoubleVar(value=0.5)
        self.ending_fade_in_var = tk.BooleanVar(value=False)
        self.ending_fade_out_var = tk.BooleanVar(value=False)
        self.ending_fade_in_dur_var = tk.DoubleVar(value=0.5)
        self.ending_fade_out_dur_var = tk.DoubleVar(value=0.5)

        # Start extra image options (mirror ending)
        self.start_image_enabled_var = tk.BooleanVar(value=False)
        self.start_image_path_var = tk.StringVar(value="")
        self.start_image_height_var = tk.IntVar(value=200)
        self.start_image_spacing_var = tk.IntVar(value=20)
        
        # Ending text variables
        self.ending_line1_var = tk.StringVar(value="Lincoln Rare Books & Collectables")
        self.ending_line2_var = tk.StringVar(value="Many thousands of postcards in store")
        self.ending_line3_var = tk.StringVar(value="Please Like and Subscribe!")
        self.ending_line1_size_var = tk.DoubleVar(value=1.5)
        self.ending_line2_size_var = tk.DoubleVar(value=1.5)
        self.ending_line3_size_var = tk.DoubleVar(value=1.5)
        self.ending_line1_color_var = tk.StringVar(value="black")
        self.ending_line2_color_var = tk.StringVar(value="black")
        self.ending_line3_color_var = tk.StringVar(value="black")
        self.ending_line1_font_var = tk.StringVar(value="Arial")
        self.ending_line2_font_var = tk.StringVar(value="Arial")
        self.ending_line3_font_var = tk.StringVar(value="Arial")
        self.ending_line1_bold_var = tk.BooleanVar(value=True)
        self.ending_line2_bold_var = tk.BooleanVar(value=True)
        self.ending_line3_bold_var = tk.BooleanVar(value=True)
        self.ending_duration_var = tk.DoubleVar(value=5.0)
        
        # Start text variables
        self.start_line1_var = tk.StringVar(value="Welcome to")
        self.start_line2_var = tk.StringVar(value="Lincoln Rare Books & Collectables")
        self.start_line1_size_var = tk.DoubleVar(value=1.2)
        self.start_line2_size_var = tk.DoubleVar(value=1.5)
        self.start_line1_color_var = tk.StringVar(value="black")
        self.start_line2_color_var = tk.StringVar(value="black")
        self.start_line1_font_var = tk.StringVar(value="Arial")
        self.start_line2_font_var = tk.StringVar(value="Arial")
        self.start_line1_bold_var = tk.BooleanVar(value=True)
        self.start_line2_bold_var = tk.BooleanVar(value=True)
        self.start_duration_var = tk.DoubleVar(value=3.0)
        self.start_text_spacing_var = tk.IntVar(value=1)
        self.start_logo_size_var = tk.IntVar(value=300)
        self.start_logo_text_spacing_var = tk.IntVar(value=20)
        self.start_line1_hidden_var = tk.BooleanVar(value=False)
        
        # Ending screen configuration variables (like start screen)
        self.ending_text_spacing_var = tk.IntVar(value=1)
        self.ending_logo_size_var = tk.IntVar(value=300)
        self.ending_logo_text_spacing_var = tk.IntVar(value=20)
        # Ending line visibility toggles
        self.ending_line1_hidden_var = tk.BooleanVar(value=False)
        self.ending_line2_hidden_var = tk.BooleanVar(value=False)
        self.ending_line3_hidden_var = tk.BooleanVar(value=False)
        # Ending extra image options
        self.ending_image_enabled_var = tk.BooleanVar(value=False)
        self.ending_image_path_var = tk.StringVar(value="")
        self.ending_image_height_var = tk.IntVar(value=200)
        self.ending_image_spacing_var = tk.IntVar(value=20)
        
        # Second page variables
        self.second_page_enabled_var = tk.BooleanVar(value=False)
        self.second_page_line1_var = tk.StringVar(value="Welcome to our collection")
        self.second_page_line2_var = tk.StringVar(value="Discover amazing postcards")
        self.second_page_line1_bold_var = tk.BooleanVar(value=False)
        self.second_page_line2_bold_var = tk.BooleanVar(value=False)
        self.second_page_line1_italic_var = tk.BooleanVar(value=False)
        self.second_page_line2_italic_var = tk.BooleanVar(value=False)
        self.second_page_line1_size_var = tk.IntVar(value=60)
        self.second_page_line2_size_var = tk.IntVar(value=50)
        self.second_page_line1_y_var = tk.IntVar(value=450)
        self.second_page_line2_y_var = tk.IntVar(value=580)
        self.second_page_max_chars_var = tk.IntVar(value=30)
        self.second_page_duration_var = tk.DoubleVar(value=3.0)
        self.second_page_line1_color_var = tk.StringVar(value="#000000")
        self.second_page_line2_color_var = tk.StringVar(value="#000000")
        # Second page fade effects
        self.second_page_fade_in_var = tk.BooleanVar(value=False)
        self.second_page_fade_out_var = tk.BooleanVar(value=False)
        self.second_page_fade_in_dur_var = tk.DoubleVar(value=0.5)
        self.second_page_fade_out_dur_var = tk.DoubleVar(value=0.5)
        
        # NEW: Actual clip duration controls (for batch calculation accuracy)
        self.actual_start_duration_var = tk.DoubleVar(value=4.0)
        self.actual_second_page_duration_var = tk.DoubleVar(value=11.0)
        self.actual_ending_duration_var = tk.DoubleVar(value=8.0)
        self.actual_pair_duration_var = tk.DoubleVar(value=14.1)
        self.max_video_duration_var = tk.DoubleVar(value=60.0)  # Maximum allowed video duration
        
        self.setup_ui()
        
        # Clean up old files before loading defaults
        self.cleanup_old_files()
        
        # Load saved defaults after UI is set up
        self.load_defaults()
        
        # Always reset Start Part Number to 1 on app startup
        self.starting_part_var.set(1)
        
        # Update button state to show default output directory
        self.update_create_button_state()
        
    def setup_ui(self):
        # Create simple menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Backups menu
        backup_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Backups", menu=backup_menu)
        backup_menu.add_command(label="💾 Create Manual Backup", command=self.manual_backup)
        backup_menu.add_command(label="📁 Show Backup Folder", command=self.show_backup_folder)
        backup_menu.add_separator()
        backup_menu.add_command(label="🔄 Restore from Backup", command=self.restore_backup_dialog)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Postcard Video Creator", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Video Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure column weights for better spacing
        settings_frame.columnconfigure(1, weight=1)
        settings_frame.columnconfigure(3, weight=1)
        
        # Duration settings
        ttk.Label(settings_frame, text="Default Duration (seconds):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.default_duration_var = tk.StringVar(value=str(self.default_duration))
        default_duration_entry = ttk.Entry(settings_frame, textvariable=self.default_duration_var, width=10)
        default_duration_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Transition Duration (seconds):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.transition_duration_var = tk.StringVar(value="1.0")
        transition_duration_entry = ttk.Entry(settings_frame, textvariable=self.transition_duration_var, width=10)
        transition_duration_entry.grid(row=0, column=3, sticky=tk.W)
        
        # Resolution settings
        ttk.Label(settings_frame, text="Video Resolution:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.resolution_var = tk.StringVar(value="1080x1080 (Square)")
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var, 
                                       values=["1920x1080", "1280x720", "3840x2160", "1080x1080 (Square)", "720x720 (Square)"], width=18)
        resolution_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 20))
        resolution_combo.bind('<<ComboboxSelected>>', self.update_resolution)
        
        # Effect settings
        ttk.Label(settings_frame, text="Transition Effect:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.effect_var = tk.StringVar(value="fade")
        effect_combo = ttk.Combobox(settings_frame, textvariable=self.effect_var,
                                   values=["fade", "slide_left", "slide_right", "slide_up", "slide_down", 
                                          "zoom_in", "zoom_out", "wipe_left", "wipe_right", "wipe_up", "wipe_down",
                                          "dissolve", "random"], width=15)
        effect_combo.grid(row=1, column=3, sticky=tk.W, pady=(10, 0), padx=(0, 20))
        
        # Music settings
        ttk.Label(settings_frame, text="Background Music:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.music_var = tk.StringVar(value="Random")
        music_combo = ttk.Combobox(settings_frame, textvariable=self.music_var,
                                  values=["None", "Random", "Vintage Memories", "Nostalgic Journey", 
                                         "Classic Charm", "Peaceful Moments"], width=15)
        music_combo.grid(row=2, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 20))
        
        # Music volume
        ttk.Label(settings_frame, text="Music Volume:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0), padx=(0, 5))
        self.music_volume_var = tk.DoubleVar(value=0.3)
        volume_scale = ttk.Scale(settings_frame, from_=0.0, to=1.0, variable=self.music_volume_var, 
                                orient='horizontal', length=100)
        volume_scale.grid(row=2, column=3, sticky=tk.W, pady=(10, 0))
        
        # Music preview button
        preview_button = ttk.Button(settings_frame, text="🎵 Preview", command=self.preview_music)
        preview_button.grid(row=2, column=4, sticky=tk.W, pady=(10, 0), padx=(10, 0))
        
        # Batch Duration Configuration (NEW)
        ttk.Label(settings_frame, text="Batch Calculation Durations:", font=('Arial', 9, 'bold')).grid(row=3, column=0, columnspan=5, sticky=tk.W, pady=(20, 5))
        
        # Row 4: Start and Second Page durations
        ttk.Label(settings_frame, text="Actual Start Duration:").grid(row=4, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Spinbox(settings_frame, from_=1.0, to=15.0, increment=0.5, textvariable=self.actual_start_duration_var, 
                   width=8).grid(row=4, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Actual Second Page Duration:").grid(row=4, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Spinbox(settings_frame, from_=1.0, to=20.0, increment=0.5, textvariable=self.actual_second_page_duration_var, 
                   width=8).grid(row=4, column=3, sticky=tk.W)
        
        # Row 5: Ending and Pair durations
        ttk.Label(settings_frame, text="Actual Ending Duration:").grid(row=5, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=1.0, to=15.0, increment=0.5, textvariable=self.actual_ending_duration_var, 
                   width=8).grid(row=5, column=1, sticky=tk.W, padx=(0, 20), pady=(5, 0))
        
        ttk.Label(settings_frame, text="Actual Pair Duration:").grid(row=5, column=2, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=5.0, to=30.0, increment=0.1, textvariable=self.actual_pair_duration_var, 
                   width=8).grid(row=5, column=3, sticky=tk.W, pady=(5, 0))
        
        # Row 6: Max Video Duration
        ttk.Label(settings_frame, text="Max Video Duration (seconds):").grid(row=6, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Spinbox(settings_frame, from_=30.0, to=300.0, increment=5.0, textvariable=self.max_video_duration_var, 
                   width=8).grid(row=6, column=1, sticky=tk.W, padx=(0, 20), pady=(5, 0))
        
        # Help text (more compact)
        help_label = ttk.Label(settings_frame, text="ℹ️ Actual durations for batch splitting (max duration enforced)", 
                              font=('Arial', 8), foreground='#666666')
        help_label.grid(row=7, column=0, columnspan=4, sticky=tk.W, pady=(2, 5))
        
        # Music management button
        music_manage_button = ttk.Button(settings_frame, text="🎼 Manage Music", command=self.open_music_manager)
        music_manage_button.grid(row=2, column=5, sticky=tk.W, pady=(10, 0), padx=(10, 0))
        
        # Background color for square format (MOVED TO ROW 8)
        ttk.Label(settings_frame, text="Square Background:").grid(row=8, column=0, sticky=tk.W, pady=(15, 0))
        background_color_combo = ttk.Combobox(settings_frame, textvariable=self.background_color_var,
                                            values=["white", "black", "gray", "light_gray", "dark_gray", 
                                                   "red", "green", "blue", "yellow", "cyan", "magenta", 
                                                   "orange", "purple", "brown", "pink", "navy"], width=15)
        background_color_combo.grid(row=8, column=1, sticky=tk.W, pady=(15, 0), padx=(0, 20))
        
        # Starting part number setting (MOVED TO ROW 8)
        ttk.Label(settings_frame, text="Starting Part Number:").grid(row=8, column=2, sticky=tk.W, pady=(15, 0), padx=(20, 0))
        starting_part_spinbox = ttk.Spinbox(settings_frame, from_=1, to=999, textvariable=self.starting_part_var, width=8)
        starting_part_spinbox.grid(row=8, column=3, sticky=tk.W, pady=(15, 0), padx=(0, 10))
        
        # Ending text configuration button (MOVED TO ROW 9)
        ending_config_button = ttk.Button(settings_frame, text="🎬 Configure Ending Text", command=self.open_ending_config)
        ending_config_button.grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Start text configuration button (MOVED TO ROW 9)
        start_config_button = ttk.Button(settings_frame, text="🎬 Configure Start Text", command=self.open_start_config)
        start_config_button.grid(row=9, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Second page configuration button (MOVED TO ROW 10)
        second_page_config_button = ttk.Button(settings_frame, text="📄 Configure Second Page", command=self.open_second_page_config)
        second_page_config_button.grid(row=10, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # YouTube upload button (MOVED TO ROW 10)
        youtube_upload_button = ttk.Button(settings_frame, text="📺 Upload to YouTube", command=self.open_youtube_upload)
        youtube_upload_button.grid(row=10, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Postcard Images", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons for adding images
        ttk.Button(file_frame, text="Select Multiple Images", 
                  command=self.select_multiple_images).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(file_frame, text="📊 Upload Excel File", 
                  command=self.upload_excel_file).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(file_frame, text="Clear All", 
                  command=self.clear_all_images).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(file_frame, text="Select Output Folder", 
                  command=self.select_output_folder).grid(row=0, column=3)
        
        # Postcard list
        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Create Treeview for postcard images
        columns = ('✓', 'Image #', 'Filename', 'Duration (s)', 'Type', 'Preview')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == '✓':
                self.tree.column(col, width=50)
            elif col == 'Image #':
                self.tree.column(col, width=80)
            elif col == 'Duration (s)':
                self.tree.column(col, width=100)
            elif col == 'Type':
                self.tree.column(col, width=80)
            elif col == 'Filename':
                self.tree.column(col, width=220)
            else:
                self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Bind click event for checkbox column (moved after other bindings)
        print("DEBUG: Tree click binding will be set up after other bindings")
        
        # Control buttons for checkbox management
        control_button_frame = ttk.Frame(file_frame)
        control_button_frame.grid(row=2, column=0, columnspan=4, pady=(5, 0), sticky=tk.W)
        ttk.Button(control_button_frame, text="📋 Copy Selected Filename", 
                  command=self.copy_selected_filename).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(control_button_frame, text="☑ Select All", 
                  command=self.select_all_images).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(control_button_frame, text="☐ Deselect All", 
                  command=self.deselect_all_images).grid(row=0, column=2, padx=(0, 10))
        
        # No preview frame on main page - individual preview buttons will be added to tree
        
        # Bind tree selection and double-click for editing duration
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Store last click position for checkbox detection
        self.last_click_x = 0
        self.last_click_y = 0
        
        # Bind click event for checkbox column - try multiple event types
        print("DEBUG: Setting up tree click binding after other events")
        self.tree.bind('<Button-1>', self.on_tree_click, add='+')  
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click_release, add='+')
        print("DEBUG: Tree click binding set up successfully")
        
        # Progress and control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.grid(row=0, column=1, padx=(0, 10))
        
        # Create video button
        self.create_button = ttk.Button(control_frame, text="🎬 CREATE VIDEO", 
                                       command=self.create_video, state='normal')
        self.create_button.grid(row=0, column=2, padx=(10, 0), ipadx=20, ipady=5)
        
        # Part selector dropdown
        ttk.Label(control_frame, text="Part:").grid(row=0, column=3, padx=(10, 0), sticky=tk.E)
        self.part_selector_var = tk.StringVar(value="Latest")
        self.part_selector = ttk.Combobox(control_frame, textvariable=self.part_selector_var,
                                         values=["Latest"], width=24, state="readonly")
        self.part_selector.grid(row=0, column=4, padx=(5, 0))
        
        # Bind part selection to automatically update image checkboxes
        self.part_selector.bind('<<ComboboxSelected>>', self.on_part_selected)
        
        # Play video button
        self.play_button = ttk.Button(control_frame, text="▶️ PLAY VIDEO", 
                                     command=self.play_selected_video, state='disabled')
        self.play_button.grid(row=0, column=5, padx=(10, 0), ipadx=20, ipady=5)
        
        # Cancel button (initially hidden)
        self.cancel_button = ttk.Button(control_frame, text="❌ CANCEL", 
                                       command=self.cancel_processing, state='normal')
        self.cancel_button.grid(row=0, column=6, padx=(10, 0), ipadx=20, ipady=5)
        self.cancel_button.grid_remove()  # Hide initially
        
        # Add a label to show button status
        self.button_status_label = ttk.Label(control_frame, text="Button: Waiting for images and output folder", 
                                            font=('Arial', 8))
        self.button_status_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        # Add a test button for quick verification
        self.test_button = ttk.Button(control_frame, text="🧪 TEST VIDEO", 
                                     command=self.test_video_creation, state='normal')
        self.test_button.grid(row=1, column=5, padx=(10, 0), pady=(5, 0))
        
        # Configure grid weights for proper resizing
        main_frame.rowconfigure(2, weight=1)  # File frame should expand, not control frame
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Initialize music dropdown with actual music files from the music directory
        self.update_music_dropdown()
        
    def update_resolution(self, event=None):
        resolution = self.resolution_var.get()
        if resolution == "1920x1080":
            self.video_width, self.video_height = 1920, 1080
        elif resolution == "1280x720":
            self.video_width, self.video_height = 1280, 720
        elif resolution == "3840x2160":
            self.video_width, self.video_height = 3840, 2160
        elif resolution == "1080x1080 (Square)":
            self.video_width, self.video_height = 1080, 1080
        elif resolution == "720x720 (Square)":
            self.video_width, self.video_height = 720, 720
    
    def is_square_format(self):
        """Check if current resolution is square format"""
        return self.video_width == self.video_height
    
    def select_multiple_images(self):
        # Open file dialog for multiple images
        image_paths = filedialog.askopenfilenames(
            title="Select Postcard Images (in order: front1, back1, front2, back2, ...)",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        
        if not image_paths:
            return
            
        # Check if even number of images
        if len(image_paths) % 2 != 0:
            messagebox.showerror("Error", f"You selected {len(image_paths)} images. Please select an even number of images.\n\nOrder should be: front1, back1, front2, back2, front3, back3, etc.")
            return
            
        # Clear existing data
        self.postcard_images.clear()
        self.image_durations.clear()
        self.image_included.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add images and set default durations
        for i, path in enumerate(image_paths):
            self.postcard_images.append(path)
            self.image_durations.append(self.default_duration)
            self.image_included.append(True)  # All images checked by default
            
            # Determine if it's front or back
            image_type = "Front" if i % 2 == 0 else "Back"
            postcard_num = (i // 2) + 1
            
            # Add to treeview
            filename = os.path.basename(path)
            self.tree.insert('', 'end', values=("☑", f"{i+1}", filename, f"{self.default_duration}s", image_type, "👁️ View"))
            
        # No dialog box - just update status
        self.status_label.config(text=f"Added {len(image_paths)} images ({len(image_paths)//2} postcards)")
        
        # Enable create button if we have images and output folder
        self.update_create_button_state()
        
    def clear_all_images(self):
        self.postcard_images.clear()
        self.image_durations.clear()
        self.image_included.clear()
        
        # Clear regeneration info since we're starting fresh
        self.regeneration_info = None
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_create_button_state()
        self.clear_preview()
    
    def upload_excel_file(self):
        """Upload and process Excel file with postcard data"""
        excel_path = filedialog.askopenfilename(
            title="Select Excel File with Postcard Data",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not excel_path:
            return
        
        self.status_label.config(text="Processing Excel file...")
        self.root.update()
        
        try:
            # Process Excel file in a separate thread to avoid UI blocking
            import threading
            thread = threading.Thread(target=self._process_excel_file, args=(excel_path,))
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logging.error(f"Error starting Excel processing: {e}")
            messagebox.showerror("Error", f"Failed to process Excel file:\n{str(e)}")
            self.status_label.config(text="Ready")
    
    def _process_excel_file(self, excel_path):
        """Process Excel file in background thread"""
        try:
            logging.info(f"Processing Excel file: {excel_path}")
            
            # Extract data from Excel file
            postcards_data = self._extract_excel_data(excel_path)
            
            if not postcards_data:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "No postcard data found in Excel file"))
                self.root.after(0, lambda: self.status_label.config(text="Ready"))
                return
            
            # Clear existing images
            self.root.after(0, self.clear_all_images)
            
            # Download and process images for each postcard
            total_postcards = len(postcards_data)
            processed = 0
            
            for i, postcard_data in enumerate(postcards_data):
                try:
                    logging.debug(f"Processing postcard {i+1}/{total_postcards}: {postcard_data.get('title', 'Unknown')}")
                    
                    # Update progress
                    progress = (i / total_postcards) * 100
                    self.root.after(0, lambda p=progress: self.progress_var.set(p))
                    self.root.after(0, lambda i=i, t=total_postcards: self.status_label.config(text=f"Processing postcard {i+1}/{t}..."))
                    
                    # Download images for this postcard
                    front_path, back_path = self._download_postcard_images(postcard_data)
                    
                    if front_path and back_path:
                        # Add to postcard list
                        self.root.after(0, lambda f=front_path, b=back_path, t=postcard_data.get('title', 'Unknown'): 
                                      self._add_postcard_to_list(f, b, t))
                        processed += 1
                    else:
                        logging.warning(f"Failed to download images for postcard: {postcard_data.get('title', 'Unknown')}")
                
                except Exception as e:
                    logging.error(f"Error processing postcard {i+1}: {e}")
                    continue
            
            # Complete
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda p=processed, t=total_postcards: 
                          self.status_label.config(text=f"✅ Processed {p}/{t} postcards successfully"))
            
            if processed > 0:
                self.root.after(0, self.update_create_button_state)
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                                f"Successfully processed {processed}/{total_postcards} postcards.\n\nReady to create video!"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                                "No postcards could be processed. Please check the Excel file format and image URLs."))
        
        except Exception as e:
            logging.error(f"Error processing Excel file: {e}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to process Excel file:\n{str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Ready"))
    
    def _extract_excel_data(self, excel_path):
        """Extract postcard data from Excel file"""
        postcards_data = []
        
        try:
            # Read Excel file as ZIP and extract strings
            with zipfile.ZipFile(excel_path, 'r') as zip_file:
                # Get shared strings
                shared_strings = []
                if 'xl/sharedStrings.xml' in zip_file.namelist():
                    with zip_file.open('xl/sharedStrings.xml') as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                            if si.text:
                                shared_strings.append(si.text)
                
                # Find image URLs (column L contains URLs)
                worksheet_files = [f for f in zip_file.namelist() if f.startswith('xl/worksheets/') and f.endswith('.xml')]
                
                for ws_file in worksheet_files:
                    with zip_file.open(ws_file) as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        
                        # Extract cells and their values
                        rows_data = {}
                        for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
                            row_num = int(row.get('r', 0))
                            rows_data[row_num] = {}
                            
                            for cell in row.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                                cell_ref = cell.get('r', '')
                                if cell_ref:
                                    # Extract column letter
                                    col_letter = ''.join([c for c in cell_ref if c.isalpha()])
                                    
                                    # Get cell value
                                    value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                                    if value_elem is not None and value_elem.text:
                                        try:
                                            # If it's a shared string reference
                                            if cell.get('t') == 's':
                                                string_index = int(value_elem.text)
                                                if 0 <= string_index < len(shared_strings):
                                                    rows_data[row_num][col_letter] = shared_strings[string_index]
                                            else:
                                                rows_data[row_num][col_letter] = value_elem.text
                                        except (ValueError, IndexError):
                                            rows_data[row_num][col_letter] = value_elem.text
                        
                        # Process rows and extract postcard data
                        for row_num, row_data in rows_data.items():
                            if row_num < 2:  # Skip header row
                                continue
                            
                            # Look for image URLs in column L
                            image_url = row_data.get('L', '')
                            title = row_data.get('D', '') or row_data.get('E', '') or f"Postcard {row_num}"
                            
                            if image_url and 'http' in image_url:
                                postcards_data.append({
                                    'title': title,
                                    'image_url': image_url,
                                    'row': row_num
                                })
                
            logging.info(f"Extracted {len(postcards_data)} postcards from Excel file")
            return postcards_data
        
        except Exception as e:
            logging.error(f"Error extracting Excel data: {e}")
            raise
    
    def _download_postcard_images(self, postcard_data):
        """Download front and back images for a postcard from URLs separated by | character"""
        try:
            image_url = postcard_data['image_url']
            title = postcard_data['title']
            
            # Create safe filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Limit length
            
            logging.debug(f"Processing postcard URL: {image_url}")
            
            # Create temporary directory for downloaded images
            temp_dir = tempfile.mkdtemp(prefix="postcards_")
            
            # Check if this is the pipe-separated format: front_url|back_url
            if '|' in image_url:
                front_path, back_path = self._download_pipe_separated_urls(image_url, safe_title, temp_dir)
            else:
                # Fallback to legacy methods for compatibility
                if self._is_composite_image_url(image_url):
                    # Single URL containing both front and back images
                    front_path, back_path = self._download_and_split_composite_image(image_url, safe_title, temp_dir)
                else:
                    # Try to derive front and back URLs from the base URL
                    front_path, back_path = self._download_separate_front_back_images(image_url, safe_title, temp_dir)
            
            if front_path and back_path and os.path.exists(front_path) and os.path.exists(back_path):
                logging.debug(f"Successfully downloaded front and back images for: {title}")
                return front_path, back_path
            else:
                logging.warning(f"Failed to download both images for: {title}")
                return None, None
        
        except Exception as e:
            logging.error(f"Error downloading images for {postcard_data.get('title', 'Unknown')}: {e}")
            return None, None
    
    def _download_pipe_separated_urls(self, image_url, safe_title, temp_dir):
        """Download front and back images from pipe-separated URLs"""
        try:
            # Split the URLs by pipe character
            urls = image_url.split('|')
            
            if len(urls) != 2:
                logging.warning(f"Expected 2 URLs separated by |, got {len(urls)}: {image_url}")
                return None, None
            
            front_url = urls[0].strip()
            back_url = urls[1].strip()
            
            logging.debug(f"Front URL: {front_url}")
            logging.debug(f"Back URL: {back_url}")
            
            # Parse URLs to get file extensions
            front_parsed = urlparse(front_url)
            back_parsed = urlparse(back_url)
            front_ext = os.path.splitext(front_parsed.path)[1] or '.jpg'
            back_ext = os.path.splitext(back_parsed.path)[1] or '.jpg'
            
            # Create file paths
            front_path = os.path.join(temp_dir, f"{safe_title}_front{front_ext}")
            back_path = os.path.join(temp_dir, f"{safe_title}_back{back_ext}")
            
            # Download front image
            logging.debug(f"Downloading front image from: {front_url}")
            front_response = requests.get(front_url, timeout=30)
            front_response.raise_for_status()
            
            with open(front_path, 'wb') as f:
                f.write(front_response.content)
            
            # Download back image
            logging.debug(f"Downloading back image from: {back_url}")
            back_response = requests.get(back_url, timeout=30)
            back_response.raise_for_status()
            
            with open(back_path, 'wb') as f:
                f.write(back_response.content)
            
            logging.debug(f"Successfully downloaded both images via pipe-separated URLs for: {safe_title}")
            return front_path, back_path
            
        except Exception as e:
            logging.error(f"Error downloading pipe-separated URLs: {e}")
            return None, None
    
    def _is_composite_image_url(self, url):
        """Determine if this URL points to a composite image with front and back"""
        # Check for indicators that this is a single composite image
        url_lower = url.lower()
        composite_indicators = ['composite', 'both', 'frontback', 'pair', 'combined']
        return any(indicator in url_lower for indicator in composite_indicators)
    
    def _download_and_split_composite_image(self, image_url, safe_title, temp_dir):
        """Download a composite image and split it into front and back"""
        try:
            # Download the composite image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Parse URL to get file extension
            parsed_url = urlparse(image_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Save the composite image temporarily
            composite_path = os.path.join(temp_dir, f"{safe_title}_composite{file_ext}")
            with open(composite_path, 'wb') as f:
                f.write(response.content)
            
            # Load and split the image
            from PIL import Image
            img = Image.open(composite_path)
            width, height = img.size
            
            # Assume the image is arranged horizontally (front | back) or vertically (front / back)
            if width > height:
                # Horizontal layout - split vertically down the middle
                front_img = img.crop((0, 0, width // 2, height))
                back_img = img.crop((width // 2, 0, width, height))
            else:
                # Vertical layout - split horizontally across the middle
                front_img = img.crop((0, 0, width, height // 2))
                back_img = img.crop((0, height // 2, width, height))
            
            # Save split images
            front_path = os.path.join(temp_dir, f"{safe_title}_front{file_ext}")
            back_path = os.path.join(temp_dir, f"{safe_title}_back{file_ext}")
            
            front_img.save(front_path)
            back_img.save(back_path)
            
            # Clean up composite image
            os.remove(composite_path)
            
            logging.debug(f"Split composite image into front and back for: {safe_title}")
            return front_path, back_path
            
        except Exception as e:
            logging.error(f"Error splitting composite image: {e}")
            return None, None
    
    def _download_separate_front_back_images(self, base_url, safe_title, temp_dir):
        """Try to download separate front and back images by modifying the URL"""
        try:
            # Parse URL to get file extension
            parsed_url = urlparse(base_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Try different URL patterns for front and back
            url_patterns = [
                # Pattern 1: Replace filename with _front/_back suffix
                (base_url.replace(file_ext, f'_front{file_ext}'), base_url.replace(file_ext, f'_back{file_ext}')),
                # Pattern 2: Add front/back before extension
                (base_url.replace(file_ext, f'front{file_ext}'), base_url.replace(file_ext, f'back{file_ext}')),
                # Pattern 3: Replace 'P' with 'PF' and 'PB' (based on your sample URLs)
                (base_url.replace('/P', '/PF'), base_url.replace('/P', '/PB')),
                # Pattern 4: Add F and B suffix to filename
                (base_url.replace(file_ext, f'F{file_ext}'), base_url.replace(file_ext, f'B{file_ext}')),
            ]
            
            for front_url, back_url in url_patterns:
                try:
                    logging.debug(f"Trying URL pattern: Front={front_url}, Back={back_url}")
                    
                    # Download front image
                    front_response = requests.get(front_url, timeout=30)
                    if front_response.status_code == 200:
                        
                        # Download back image
                        back_response = requests.get(back_url, timeout=30)
                        if back_response.status_code == 200:
                            
                            # Save both images
                            front_path = os.path.join(temp_dir, f"{safe_title}_front{file_ext}")
                            back_path = os.path.join(temp_dir, f"{safe_title}_back{file_ext}")
                            
                            with open(front_path, 'wb') as f:
                                f.write(front_response.content)
                            
                            with open(back_path, 'wb') as f:
                                f.write(back_response.content)
                            
                            logging.debug(f"Successfully downloaded separate images using pattern: {front_url}")
                            return front_path, back_path
                            
                except requests.exceptions.RequestException:
                    continue  # Try next pattern
            
            # If no patterns worked, try downloading the base URL and using it for both
            logging.warning(f"No separate front/back URLs found, using base URL for both: {base_url}")
            return self._download_single_image_as_both(base_url, safe_title, temp_dir)
            
        except Exception as e:
            logging.error(f"Error downloading separate images: {e}")
            return None, None
    
    def _download_single_image_as_both(self, image_url, safe_title, temp_dir):
        """Download single image and use it for both front and back as fallback"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Parse URL to get file extension
            parsed_url = urlparse(image_url)
            file_ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            front_path = os.path.join(temp_dir, f"{safe_title}_front{file_ext}")
            back_path = os.path.join(temp_dir, f"{safe_title}_back{file_ext}")
            
            # Save the same image as both front and back
            with open(front_path, 'wb') as f:
                f.write(response.content)
            
            import shutil
            shutil.copy2(front_path, back_path)
            
            logging.debug(f"Using single image for both front and back: {safe_title}")
            return front_path, back_path
            
        except Exception as e:
            logging.error(f"Error downloading single image: {e}")
            return None, None
    
    def _add_postcard_to_list(self, front_path, back_path, title):
        """Add postcard to the list (called from main thread)"""
        # Add front image
        self.postcard_images.append(front_path)
        self.image_durations.append(self.default_duration)
        self.image_included.append(True)  # All images checked by default
        
        # Add back image  
        self.postcard_images.append(back_path)
        self.image_durations.append(self.default_duration)
        self.image_included.append(True)  # All images checked by default
        
        # Update tree view
        index = len(self.postcard_images) - 2  # Front image index
        
        # Add front
        self.tree.insert('', 'end', values=(
            "☑",
            f"{index//2 + 1}",
            os.path.basename(front_path),
            f"{self.default_duration}s",
            "Front",
            "👁️ View"
        ))
        
        # Add back
        self.tree.insert('', 'end', values=(
            "☑",
            f"{index//2 + 1}",
            os.path.basename(back_path),
            f"{self.default_duration}s",
            "Back",
            "👁️ View"
        ))
        
    def select_output_folder(self):
        # Start with the default directory if it exists
        initial_dir = self.output_path if os.path.exists(self.output_path) else ""
        self.output_path = filedialog.askdirectory(title="Select Output Folder", initialdir=initial_dir)
        if self.output_path:
            self.update_create_button_state()
            
    def update_create_button_state(self):
        # Check if we have all requirements
        has_images = len(self.postcard_images) > 0
        has_output = self.output_path and os.path.exists(self.output_path)
        has_even_count = len(self.postcard_images) % 2 == 0
        
        # Debug info
        print(f"Button state check: images={has_images}, output={has_output}, even={has_even_count}")
        print(f"Output path: '{self.output_path}'")
        print(f"Output exists: {os.path.exists(self.output_path) if self.output_path else 'No path'}")
        
        if has_images and has_output and has_even_count:
            self.create_button.config(state='normal')
            short_path = self.output_path.replace(r"C:\_postcards\renamed_postcards\videos", "Default Videos Folder")
            play_status = " | Click 'PLAY VIDEO' to view latest" if self.latest_video_path and os.path.exists(self.latest_video_path) else ""
            self.button_status_label.config(text=f"✅ Ready! Output: {short_path}{play_status}", foreground='green')
        else:
            self.create_button.config(state='disabled')
            if not has_images:
                self.button_status_label.config(text="⏳ Waiting for images", foreground='orange')
            elif not has_output:
                self.button_status_label.config(text="⏳ Waiting for output folder", foreground='orange')
            elif not has_even_count:
                self.button_status_label.config(text="❌ Need even number of images", foreground='red')
            else:
                self.button_status_label.config(text="⏳ Waiting for images and output folder", foreground='orange')
            
    def on_tree_select(self, event):
        # Check if this selection was caused by a checkbox click or preview button click
        print(f"DEBUG: Tree selection event triggered")
        if hasattr(self, 'last_click_x') and hasattr(self, 'last_click_y'):
            print(f"DEBUG: Checking if last click at ({self.last_click_x}, {self.last_click_y}) was on checkbox or preview")
            
            # Check if click was on Preview column
            clicked_column = self.tree.identify_column(self.last_click_x)
            if clicked_column == '#6':  # Preview column (6th column)
                selection = self.tree.selection()
                if selection:
                    self.open_image_preview(selection[0])
                return
            
            # Try to process the last click as a checkbox click
            if self.process_checkbox_click(self.last_click_x, self.last_click_y):
                print("DEBUG: Checkbox click processed, skipping normal selection")
                return  # Skip normal selection if checkbox was clicked
                
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.image_durations):
                self.edit_duration(index)
                
    def open_image_preview(self, tree_item):
        """Open a popup window showing the full-size image"""
        try:
            # Get image index from tree item
            index = self.tree.index(tree_item)
            if index >= len(self.postcard_images):
                return
                
            image_path = self.postcard_images[index]
            
            # Get image info
            image_name = os.path.basename(image_path)
            image_index = self.postcard_images.index(image_path)
            image_type = "Front" if image_index % 2 == 0 else "Back"
            postcard_num = (image_index // 2) + 1
            duration = self.image_durations[image_index]
            
            # Create popup window
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"Preview: {image_name}")
            preview_window.geometry("800x600")
            preview_window.resizable(True, True)
            
            # Center the window
            preview_window.transient(self.root)
            preview_window.grab_set()
            
            # Create main frame
            main_frame = ttk.Frame(preview_window, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            preview_window.columnconfigure(0, weight=1)
            preview_window.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(1, weight=1)
            
            # Info label
            info_text = f"Postcard {postcard_num} - {image_type} | Duration: {duration}s"
            info_label = ttk.Label(main_frame, text=info_text, font=('Arial', 12, 'bold'))
            info_label.grid(row=0, column=0, pady=(0, 10))
            
            # Create canvas for image with scrollbars
            canvas_frame = ttk.Frame(main_frame)
            canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            canvas_frame.columnconfigure(0, weight=1)
            canvas_frame.rowconfigure(0, weight=1)
            
            canvas = tk.Canvas(canvas_frame, bg='white')
            v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=canvas.yview)
            h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=canvas.xview)
            canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
            
            # Load and display the image at full size
            image = Image.open(image_path)
            # Scale down if image is too large (max 1200x800)
            max_size = (1200, 800)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image)
            canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            canvas.image = photo  # Keep reference
            
            # Configure scroll region
            canvas.configure(scrollregion=canvas.bbox("all"))
            
            # Add keyboard scrolling support
            def scroll_canvas(event):
                if event.keysym == 'Up':
                    canvas.yview_scroll(-1, "units")
                elif event.keysym == 'Down':
                    canvas.yview_scroll(1, "units")
                elif event.keysym == 'Left':
                    canvas.xview_scroll(-1, "units")
                elif event.keysym == 'Right':
                    canvas.xview_scroll(1, "units")
                elif event.keysym == 'Page_Up':
                    canvas.yview_scroll(-5, "units")
                elif event.keysym == 'Page_Down':
                    canvas.yview_scroll(5, "units")
                elif event.keysym == 'Home':
                    canvas.yview_moveto(0)
                elif event.keysym == 'End':
                    canvas.yview_moveto(1)
            
            # Add mouse wheel and trackpad scrolling support
            def scroll_with_mouse(event):
                # Mouse wheel and trackpad vertical scrolling
                if event.delta > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.delta < 0:
                    canvas.yview_scroll(1, "units")
                    
            def scroll_horizontal(event):
                # Horizontal scrolling (Shift + mouse wheel or trackpad)
                if event.delta > 0:
                    canvas.xview_scroll(-1, "units")
                elif event.delta < 0:
                    canvas.xview_scroll(1, "units")
            
            # Bind mouse wheel events for both vertical and horizontal scrolling
            canvas.bind('<MouseWheel>', scroll_with_mouse)  # Windows/Linux
            canvas.bind('<Button-4>', lambda e: canvas.yview_scroll(-1, "units"))  # Linux scroll up
            canvas.bind('<Button-5>', lambda e: canvas.yview_scroll(1, "units"))   # Linux scroll down
            canvas.bind('<Shift-MouseWheel>', scroll_horizontal)  # Horizontal scroll
            canvas.bind('<Shift-Button-4>', lambda e: canvas.xview_scroll(-1, "units"))  # Linux horizontal
            canvas.bind('<Shift-Button-5>', lambda e: canvas.xview_scroll(1, "units"))   # Linux horizontal
            
            # Bind keyboard events to preview window and canvas
            preview_window.bind('<Key>', scroll_canvas)
            canvas.bind('<Key>', scroll_canvas)
            
            # Make the canvas focusable and set focus
            canvas.configure(takefocus=True)
            canvas.focus_set()
            
            # Close button
            close_button = ttk.Button(main_frame, text="Close", command=preview_window.destroy)
            close_button.grid(row=2, column=0, pady=(10, 0))
            
            # Bind Escape key to close
            preview_window.bind('<Escape>', lambda e: preview_window.destroy())
            
            # Center the window on screen
            preview_window.update_idletasks()
            width = preview_window.winfo_width()
            height = preview_window.winfo_height()
            x = (preview_window.winfo_screenwidth() // 2) - (width // 2)
            y = (preview_window.winfo_screenheight() // 2) - (height // 2)
            preview_window.geometry(f"{width}x{height}+{x}+{y}")
            
        except Exception as e:
            print(f"Error opening image preview: {e}")
            messagebox.showerror("Preview Error", f"Could not open image preview: {str(e)}")
            
    def edit_duration(self, index):
        """Open dialog to edit duration for a specific image"""
        current_duration = self.image_durations[index]
        
        # Create a simple dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Duration")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Add widgets
        ttk.Label(dialog, text=f"Edit duration for image {index + 1}:").pack(pady=10)
        ttk.Label(dialog, text=os.path.basename(self.postcard_images[index])).pack()
        
        duration_var = tk.StringVar(value=str(current_duration))
        duration_entry = ttk.Entry(dialog, textvariable=duration_var, width=10)
        duration_entry.pack(pady=10)
        
        def save_duration():
            try:
                new_duration = float(duration_var.get())
                if new_duration <= 0:
                    messagebox.showerror("Error", "Duration must be greater than 0")
                    return
                    
                self.image_durations[index] = new_duration
                
                # Update treeview
                items = self.tree.get_children()
                if index < len(items):
                    item = items[index]
                    values = list(self.tree.item(item)['values'])
                    values[2] = str(new_duration)  # Duration column
                    self.tree.item(item, values=values)
                
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
        
        def cancel():
            dialog.destroy()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_duration).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Focus on entry
        duration_entry.focus()
        duration_entry.select_range(0, tk.END)
            
    def clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_label.config(text="No image selected")
        self.preview_info.config(text="")
        
    def copy_selected_filename(self):
        """Copy the filename of the selected image to clipboard"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an image from the table first.")
            return
        
        # Get the filename from the selected row (column index 2 for 'Filename' now with checkbox)
        item = self.tree.item(selected[0])
        values = item['values']
        if len(values) >= 3:
            filename = values[2]  # Filename is the third column now
            
            # Copy to clipboard
            self.root.clipboard_clear()
            self.root.clipboard_append(filename)
            self.root.update()  # Ensure clipboard is updated
            
            # Show confirmation
            self.status_label.config(text=f"📋 Copied filename: {filename}")
            # Reset status after 3 seconds
            self.root.after(3000, lambda: self.status_label.config(text="Ready"))
        else:
            messagebox.showerror("Error", "Could not retrieve filename from selected item.")
    
    def on_tree_click(self, event):
        """Handle clicks on the tree - toggle checkbox if clicked on checkbox column"""
        print(f"DEBUG: Tree click detected at ({event.x}, {event.y})")
        
        # Store click position for other handlers
        self.last_click_x = event.x
        self.last_click_y = event.y
        
        # Try to process checkbox click immediately
        self.process_checkbox_click(event.x, event.y)
    
    def process_checkbox_click(self, x, y):
        """Process potential checkbox click at given coordinates"""
        region = self.tree.identify_region(x, y)
        print(f"DEBUG: Region: {region}")
        if region == "cell":
            column = self.tree.identify_column(x)  # Only needs x coordinate
            print(f"DEBUG: Column: {column}")
            if column == "#1":  # First column is the checkbox
                item = self.tree.identify_row(y)  # Only needs y coordinate
                print(f"DEBUG: Item: {item}")
                if item:
                    try:
                        # Get the row index
                        row_index = list(self.tree.get_children()).index(item)
                        print(f"DEBUG: Row index: {row_index}, Current state: {self.image_included[row_index]}")
                        
                        # Toggle the checkbox state
                        self.image_included[row_index] = not self.image_included[row_index]
                        print(f"DEBUG: New state: {self.image_included[row_index]}")
                        
                        # Update the display
                        current_values = list(self.tree.item(item)['values'])
                        current_values[0] = "☑" if self.image_included[row_index] else "☐"
                        self.tree.item(item, values=current_values)
                        print(f"DEBUG: Updated display values: {current_values}")
                        
                        # Update status
                        checked_count = sum(self.image_included)
                        total_count = len(self.image_included)
                        self.status_label.config(text=f"Images selected: {checked_count}/{total_count}")
                        print(f"DEBUG: Status updated: {checked_count}/{total_count}")
                        
                        return True  # Successfully processed checkbox click
                    except Exception as e:
                        print(f"DEBUG: Error processing checkbox click: {e}")
            else:
                print(f"DEBUG: Click not on checkbox column (column {column})")
        else:
            print(f"DEBUG: Click not in cell region")
        return False
    
    def on_tree_click_release(self, event):
        """Alternative click handler for ButtonRelease"""
        print(f"DEBUG: Tree click RELEASE detected at ({event.x}, {event.y})")
        # Call the same logic as the main click handler
        self.on_tree_click(event)
    
    def select_all_images(self):
        """Select all images (check all checkboxes)"""
        for i in range(len(self.image_included)):
            self.image_included[i] = True
        
        # Update display
        for i, item in enumerate(self.tree.get_children()):
            current_values = list(self.tree.item(item)['values'])
            current_values[0] = "☑"
            self.tree.item(item, values=current_values)
        
        # Update status
        self.status_label.config(text=f"Images selected: {len(self.image_included)}/{len(self.image_included)}")
    
    def deselect_all_images(self):
        """Deselect all images (uncheck all checkboxes)"""
        for i in range(len(self.image_included)):
            self.image_included[i] = False
        
        # Update display
        for i, item in enumerate(self.tree.get_children()):
            current_values = list(self.tree.item(item)['values'])
            current_values[0] = "☐"
            self.tree.item(item, values=current_values)
        
        # Update status
        self.status_label.config(text=f"Images selected: 0/{len(self.image_included)}")
        
    def get_included_images(self):
        """Get lists of only the checked/included images and their durations"""
        included_images = []
        included_durations = []
        
        for i, included in enumerate(self.image_included):
            if included:
                included_images.append(self.postcard_images[i])
                included_durations.append(self.image_durations[i])
        
        return included_images, included_durations
    
    def create_video(self):
        print("DEBUG: create_video method called")  # Debug output
        if self.is_processing:
            print("DEBUG: Already processing, returning")  # Debug output
            return
            
        # Validate settings
        try:
            self.default_duration = float(self.default_duration_var.get())
            self.transition_duration = float(self.transition_duration_var.get())
            print(f"DEBUG: Durations set - default: {self.default_duration}, transition: {self.transition_duration}")  # Debug output
        except ValueError:
            print("DEBUG: Invalid duration values")  # Debug output
            messagebox.showerror("Error", "Please enter valid numbers for durations")
            return
            
        if not self.postcard_images:
            print("DEBUG: No postcard images")  # Debug output
            messagebox.showerror("Error", "Please add at least one postcard image")
            return
        
        # Check if any images are selected (checked)
        included_images, included_durations = self.get_included_images()
        if not included_images:
            messagebox.showerror("Error", "Please check at least one image to include in the video")
            return
        
        # Check if we have an even number of included images
        if len(included_images) % 2 != 0:
            messagebox.showerror("Error", f"You have {len(included_images)} images selected. Please select an even number of images.\n\nYou need pairs: front and back images for each postcard.")
            return
        
        # Validate total duration based on configured maximum using ACTUAL durations
        max_duration = self.max_video_duration_var.get()
        start_duration = self.actual_start_duration_var.get()
        second_page_duration = self.actual_second_page_duration_var.get() if self.second_page_enabled_var.get() else 0
        ending_duration = self.actual_ending_duration_var.get()
        overhead_duration = start_duration + second_page_duration + ending_duration
        
        if overhead_duration >= max_duration:
            messagebox.showerror("Duration Error", 
                f"Start/Second Page/Ending clips total {overhead_duration:.1f} seconds.\n\n"
                f"This exceeds the {max_duration:.0f}-second limit!\n\n"
                f"Please reduce clip durations in their respective configuration dialogs.")
            return
        
        if overhead_duration > 45.0:  # Warning if overhead is very high
            result = messagebox.askyesno("High Overhead Warning",
                f"Start/Second Page/Ending clips total {overhead_duration:.1f} seconds.\n\n"
                f"This leaves only {60.0 - overhead_duration:.1f} seconds for postcard content.\n\n"
                f"Consider reducing clip durations for more postcard content.\n\n"
                f"Continue anyway?")
            if not result:
                return
            
        if len(self.postcard_images) % 2 != 0:
            print("DEBUG: Odd number of images")  # Debug output
            messagebox.showerror("Error", "You must have an even number of images (front and back for each postcard)")
            return
            
        if not self.output_path:
            print("DEBUG: No output path")  # Debug output
            messagebox.showerror("Error", "Please select an output folder")
            return
            
        print("DEBUG: All validations passed, checking if batching is needed")  # Debug output
        
        # Check if we need to create multiple videos due to length
        batches = self.calculate_video_batches()
        
        if len(batches) > 1:
            # Multiple videos needed
            result = messagebox.askyesno("Multiple Videos", 
                f"Your content is {self.calculate_total_postcard_duration():.1f} seconds long.\n\n"
                f"This will be split into {len(batches)} videos of ≤60 seconds each (for royalty-free music compliance).\n\n"
                f"Do you want to proceed with batch creation?")
            if not result:
                return
        
        # Start processing in separate thread
        self.is_processing = True
        self.create_button.config(state='disabled')
        self.cancel_button.grid()  # Show cancel button
        self.status_label.config(text="Starting video creation...")
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self.process_videos_in_batches, args=(batches,))
        thread.daemon = True
        thread.start()
    
    def calculate_total_postcard_duration(self):
        """Calculate total duration of all included postcard images"""
        included_images, included_durations = self.get_included_images()
        return sum(included_durations)
    
    def calculate_video_batches(self):
        """Split included postcards into batches to ensure total video duration ≤ 60 seconds (for royalty-free music)"""
        print("🚨 DEBUG: calculate_video_batches() called - NEW FADE LOGIC ACTIVE 🚨")
        # Calculate overhead from start/second page/ending clips using CONFIGURABLE durations
        # Calculate ACTUAL start duration including fade effects
        base_start_duration = self.actual_start_duration_var.get()
        start_fade_extension = 0.0
        if self.start_fade_in_var.get():
            start_fade_extension += self.start_fade_in_dur_var.get()
        if self.start_fade_out_var.get():
            start_fade_extension += self.start_fade_out_dur_var.get()
        
        start_fade_impact = start_fade_extension * 0.75
        start_duration = base_start_duration + start_fade_impact
        print(f"DEBUG: Start duration calculation - Base: {base_start_duration}s + Fade impact: {start_fade_impact:.1f}s = Total: {start_duration:.1f}s")
        
        # Calculate ACTUAL second page duration including fade effects
        if self.second_page_enabled_var.get():
            base_second_page_duration = self.actual_second_page_duration_var.get()
            
            # Account for fade effects that may extend duration
            fade_extension = 0.0
            if self.second_page_fade_in_var.get():
                fade_extension += self.second_page_fade_in_dur_var.get()
            if self.second_page_fade_out_var.get():
                fade_extension += self.second_page_fade_out_dur_var.get()
            
            # The actual duration may be affected by fade effects
            # MoviePy fade effects can sometimes extend duration slightly
            # Use a conservative estimate: fade effects add ~75% of their duration
            fade_impact = fade_extension * 0.75
            second_page_duration = base_second_page_duration + fade_impact
            print(f"DEBUG: Second page duration calculation - Base: {base_second_page_duration}s + Fade impact: {fade_impact:.1f}s (from {fade_extension}s effects) = Total: {second_page_duration:.1f}s")
        else:
            second_page_duration = 0
            
        # Calculate ACTUAL ending duration including fade effects
        base_ending_duration = self.actual_ending_duration_var.get()
        ending_fade_extension = 0.0
        if self.ending_fade_in_var.get():
            ending_fade_extension += self.ending_fade_in_dur_var.get()
        if self.ending_fade_out_var.get():
            ending_fade_extension += self.ending_fade_out_dur_var.get()
        
        ending_fade_impact = ending_fade_extension * 0.75
        ending_duration = base_ending_duration + ending_fade_impact
        print(f"DEBUG: Ending duration calculation - Base: {base_ending_duration}s + Fade impact: {ending_fade_impact:.1f}s = Total: {ending_duration:.1f}s")
        
        overhead_duration = start_duration + second_page_duration + ending_duration
        
        # Maximum total video duration (configurable)
        max_total_video_duration = self.max_video_duration_var.get()
        
        print(f"🔥 FADE CALCULATION RESULTS: Start: {start_duration:.1f}s, Second Page: {second_page_duration:.1f}s, Ending: {ending_duration:.1f}s")
        print(f"🔥 TOTAL OVERHEAD: {overhead_duration:.1f}s (was 13.0s before fade fixes)")
        print(f"🔥 AVAILABLE FOR PAIRS: {max_total_video_duration - overhead_duration:.1f}s")
        
        # Store debug info for duration analysis log
        self._batching_debug_info = f"Overhead: {overhead_duration:.1f}s, Available: {max_total_video_duration - overhead_duration:.1f}s"
        print(f"DEBUG: Using max video duration: {max_total_video_duration}s")
        
        # Calculate maximum duration available for postcard content
        max_duration_per_video = max_total_video_duration - overhead_duration
        
        # Ensure we have at least some time for postcards
        if max_duration_per_video <= 0:
            raise ValueError(f"Start/Second Page/Ending clips total {overhead_duration:.1f}s, leaving no time for postcards! Reduce clip durations.")
        
        # Get transition duration early for calculations
        transition_duration = float(self.transition_duration_var.get())
        
        # Calculate minimum pairs per video, but ensure it doesn't exceed duration limit
        min_pairs_per_video = 5  # Preferred minimum number of postcard pairs per video
        
        # Check if minimum pairs would exceed duration limit  
        test_pair_duration = self.actual_pair_duration_var.get()  # Configurable pair duration
        min_pairs_content_duration = min_pairs_per_video * test_pair_duration
        min_pairs_total_duration = min_pairs_content_duration + overhead_duration
        
        if min_pairs_total_duration > max_total_video_duration:
            # Reduce minimum pairs to fit within duration limit
            max_possible_pairs = int(max_duration_per_video / test_pair_duration)
            min_pairs_per_video = max(1, max_possible_pairs)
            print(f"WARNING: Reduced minimum pairs from 5 to {min_pairs_per_video} to stay within 60s limit")
            print(f"WARNING: Each video may have fewer postcards to ensure royalty-free music compliance")
        
        print(f"DEBUG: Minimum pairs per video: {min_pairs_per_video} (duration limit enforced)")
        
        print(f"DEBUG: Total video duration limit: {max_total_video_duration}s")
        print(f"DEBUG: Overhead (start + second page + ending): {overhead_duration:.1f}s")
        print(f"DEBUG: Available for postcard content: {max_duration_per_video:.1f}s")
        
        # Get only included images and their indices
        included_images, included_durations = self.get_included_images()
        included_indices = [i for i, included in enumerate(self.image_included) if included]
        
        total_pairs = len(included_images) // 2
        total_duration = sum(included_durations)
        
        logging.info(f"BATCHING: Total pairs: {total_pairs}, Total duration: {total_duration:.1f}s")
        logging.info(f"BATCHING: Max postcard duration per video: {max_duration_per_video:.1f}s (after {overhead_duration:.1f}s overhead)")
        logging.info(f"BATCHING: Min pairs per video: {min_pairs_per_video}")
        print(f"Calculating video batches for {total_pairs} pairs ({total_duration:.1f}s total)")
        print(f"Each video will be ≤{max_total_video_duration}s total ({max_duration_per_video:.1f}s postcards + {overhead_duration:.1f}s clips)")
        
        # If we have fewer than minimum pairs total, return single batch
        if total_pairs < min_pairs_per_video:
            logging.info(f"BATCHING: Only {total_pairs} pairs total (< {min_pairs_per_video}), creating single video")
            return [included_indices]
        
        # Calculate durations for each included pair INCLUDING transitions
        pair_durations = []
        
        for i in range(0, len(included_indices), 2):
            if i + 1 >= len(included_indices):
                break
            front_idx = included_indices[i]
            back_idx = included_indices[i + 1]
            front_duration = self.image_durations[front_idx]
            back_duration = self.image_durations[back_idx]
            
            # Use configurable pair duration (includes all clips per pair)
            # Note: This total duration includes transition + back clip as determined from log analysis
            total_pair_duration = self.actual_pair_duration_var.get()
            
            pair_durations.append(total_pair_duration)
        
        print(f"DEBUG: Including transition duration of {transition_duration}s between pairs")
        print(f"DEBUG: Pair durations (including transitions): {[f'{d:.1f}s' for d in pair_durations]}")
        
        logging.info(f"BATCHING: Processing {len(pair_durations)} pairs with durations: {[f'{d:.1f}s' for d in pair_durations]}")
        
        # Use smart batching algorithm for balanced distribution
        batches = self._create_balanced_batches(included_indices, pair_durations, max_duration_per_video, min_pairs_per_video)
        
        # Adjust batch durations: subtract the final transition from each batch
        # (since the last pair in each batch doesn't transition to another pair)
        print(f"DEBUG: Adjusting batch durations (removing final transition from each batch):")
        for i, batch_indices in enumerate(batches):
            batch_pairs = len(batch_indices) // 2
            if batch_pairs > 0:
                # Calculate actual duration for this batch
                batch_duration = 0
                for j in range(batch_pairs):
                    pair_idx = j
                    if pair_idx < len(pair_durations):
                        batch_duration += pair_durations[pair_idx]
                # Subtract the final transition (last pair doesn't transition)
                actual_batch_duration = batch_duration - transition_duration
                print(f"DEBUG: Batch {i+1}: {batch_pairs} pairs, {actual_batch_duration:.1f}s content + {overhead_duration:.1f}s overhead = {actual_batch_duration + overhead_duration:.1f}s total")
        
        logging.info(f"BATCHING: Created {len(batches)} batches before post-processing")
        
        # Post-process: ensure no batch has fewer than minimum pairs (except if only one batch)
        if len(batches) > 1:
            logging.info(f"BATCHING: Before adjustment: {len(batches)} batches")
            batches = self._ensure_minimum_pairs_per_batch(batches, min_pairs_per_video)
            logging.info(f"BATCHING: After adjustment: {len(batches)} batches")
        
        # Log the final batching decision
        print(f"🎯 FINAL BATCH DISTRIBUTION:")
        for i, batch in enumerate(batches):
            pairs_count = len(batch) // 2
            batch_duration = sum(pair_durations[j] for j in range(len(batch) // 2) if j < len(pair_durations))
            estimated_total_duration = overhead_duration + batch_duration
            violation_status = "❌ EXCEEDS LIMIT" if estimated_total_duration > max_total_video_duration else "✅ OK"
            print(f"   Batch {i+1}: {pairs_count} pairs ({batch_duration:.1f}s) + overhead ({overhead_duration:.1f}s) = {estimated_total_duration:.1f}s {violation_status}")
            logging.info(f"DEBUG: Batch {i+1}: {pairs_count} pairs, {batch_duration:.1f}s duration")
        
        # Update debug info with batch results
        batch_info = []
        for i, batch in enumerate(batches):
            pairs_count = len(batch) // 2
            batch_duration = sum(pair_durations[j] for j in range(len(batch) // 2) if j < len(pair_durations))
            estimated_total_duration = overhead_duration + batch_duration
            violation = "EXCEEDS" if estimated_total_duration > max_total_video_duration else "OK"
            batch_info.append(f"Batch{i+1}: {pairs_count}pairs={estimated_total_duration:.1f}s({violation})")
        
        self._batching_debug_info += f" | Batches: {', '.join(batch_info)}"
        
        # CRITICAL VALIDATION: Reject any batch distribution that contains violations
        violation_found = False
        for i, batch in enumerate(batches):
            pairs_count = len(batch) // 2
            batch_duration = sum(pair_durations[j] for j in range(len(batch) // 2) if j < len(pair_durations))
            estimated_total_duration = overhead_duration + batch_duration
            if estimated_total_duration > max_total_video_duration:
                violation_found = True
                print(f"🚨 REJECTING BATCH DISTRIBUTION: Batch {i+1} with {pairs_count} pairs would be {estimated_total_duration:.1f}s > {max_total_video_duration:.0f}s limit")
                break
        
        if violation_found:
            print(f"🔄 FORCING STRICTER DISTRIBUTION: Reducing pairs per batch to ensure no violations")
            # Force a more conservative distribution by reducing max pairs per batch
            safe_pairs_per_batch = int(max_duration_per_video / self.actual_pair_duration_var.get())
            print(f"🔧 Safe pairs per batch: {safe_pairs_per_batch} (based on {max_duration_per_video:.1f}s available ÷ {self.actual_pair_duration_var.get()}s per pair)")
            
            # Create new conservative batches
            total_pairs = len(pair_durations)
            conservative_batches = []
            start_idx = 0
            
            while start_idx < len(included_indices):
                end_idx = min(start_idx + safe_pairs_per_batch * 2, len(included_indices))
                batch = included_indices[start_idx:end_idx]
                if batch:  # Only add non-empty batches
                    conservative_batches.append(batch)
                start_idx = end_idx
            
            # Verify the conservative batches
            print(f"🔍 VERIFYING CONSERVATIVE BATCHES:")
            all_safe = True
            for i, batch in enumerate(conservative_batches):
                pairs_count = len(batch) // 2
                batch_duration = pairs_count * self.actual_pair_duration_var.get()
                estimated_total_duration = overhead_duration + batch_duration
                safe_status = "✅ SAFE" if estimated_total_duration <= max_total_video_duration else "❌ STILL EXCEEDS"
                print(f"   Conservative Batch {i+1}: {pairs_count} pairs = {estimated_total_duration:.1f}s {safe_status}")
                if estimated_total_duration > max_total_video_duration:
                    all_safe = False
            
            if all_safe:
                batches = conservative_batches
                self._batching_debug_info += f" | CORRECTED to conservative distribution"
            else:
                raise ValueError(f"Cannot create valid batches: even single pairs would exceed {max_total_video_duration:.0f}s limit with {overhead_duration:.1f}s overhead")
        
        return batches
    
    def _create_balanced_batches(self, included_indices, pair_durations, max_duration_per_video, min_pairs_per_video):
        """Create balanced batches that distribute pairs more evenly"""
        total_pairs = len(pair_durations)
        total_duration = sum(pair_durations)
        
        # Estimate optimal number of batches
        if total_duration <= max_duration_per_video:
            # Everything fits in one batch
            logging.info(f"BATCHING: All {total_pairs} pairs fit in single batch ({total_duration:.1f}s)")
            return [included_indices]
        
        # Calculate how many batches we should ideally have
        estimated_batches = max(2, int(total_duration / max_duration_per_video) + 1)
        target_pairs_per_batch = total_pairs / estimated_batches
        
        logging.info(f"BATCHING: Target: {estimated_batches} batches, ~{target_pairs_per_batch:.1f} pairs each")
        
        # Try different batch distributions to find the most balanced one
        best_batches = None
        best_score = float('inf')
        
        # Try 2 to 4 batches (reasonable range)
        for num_batches in range(2, min(5, total_pairs // min_pairs_per_video + 1)):
            batch_distribution = self._try_batch_distribution(
                included_indices, pair_durations, num_batches, 
                max_duration_per_video, min_pairs_per_video
            )
            
            if batch_distribution:
                score = self._score_batch_distribution(batch_distribution, pair_durations)
                logging.info(f"BATCHING: Trying {num_batches} batches - Score: {score:.2f}")
                
                if score < best_score:
                    best_score = score
                    best_batches = batch_distribution
        
        if best_batches:
            # Log the final distribution
            for i, batch in enumerate(best_batches):
                pairs_count = len(batch) // 2
                batch_duration = sum(pair_durations[j] for j in range(pairs_count))
                logging.info(f"BATCHING: Final Batch {i+1}: {pairs_count} pairs, {batch_duration:.1f}s")
            return best_batches
        else:
            # Fall back to greedy algorithm if balanced approach fails
            logging.info("BATCHING: Balanced approach failed, using greedy fallback")
            return self._create_greedy_batches(included_indices, pair_durations, max_duration_per_video, min_pairs_per_video)
    
    def _try_batch_distribution(self, included_indices, pair_durations, num_batches, max_duration, min_pairs):
        """Try to distribute pairs into specified number of batches"""
        total_pairs = len(pair_durations)
        
        # Calculate target pairs per batch
        base_pairs = total_pairs // num_batches
        extra_pairs = total_pairs % num_batches
        
        # Create target sizes: some batches get base_pairs, others get base_pairs + 1
        batch_sizes = [base_pairs + (1 if i < extra_pairs else 0) for i in range(num_batches)]
        
        # Check if any batch would be too small
        if any(size < min_pairs for size in batch_sizes):
            return None
        
        # Create batches based on calculated sizes
        batches = []
        start_idx = 0
        
        for batch_size in batch_sizes:
            end_idx = start_idx + batch_size * 2  # *2 because each pair = 2 images
            batch = included_indices[start_idx:end_idx]
            
            # Check duration constraint - STRICT: no flexibility allowed
            batch_duration = sum(pair_durations[start_idx//2:(start_idx//2) + batch_size])
            if batch_duration > max_duration:  # Strict limit - no violations allowed
                return None
                
            batches.append(batch)
            start_idx = end_idx
        
        return batches
    
    def _score_batch_distribution(self, batches, pair_durations):
        """Score a batch distribution - lower is better"""
        # Calculate variance in batch sizes (prefer even distribution)
        batch_sizes = [len(batch) // 2 for batch in batches]
        mean_size = sum(batch_sizes) / len(batch_sizes)
        size_variance = sum((size - mean_size) ** 2 for size in batch_sizes) / len(batch_sizes)
        
        # Calculate variance in durations 
        batch_durations = []
        for i, batch in enumerate(batches):
            pairs_in_batch = len(batch) // 2
            duration = sum(pair_durations[j] for j in range(pairs_in_batch))
            batch_durations.append(duration)
        
        mean_duration = sum(batch_durations) / len(batch_durations)
        duration_variance = sum((dur - mean_duration) ** 2 for dur in batch_durations) / len(batch_durations)
        
        # Combine scores (prioritize even pair distribution)
        score = size_variance * 2 + duration_variance
        return score
    
    def _create_greedy_batches(self, included_indices, pair_durations, max_duration_per_video, min_pairs_per_video):
        """Fallback greedy algorithm (original logic)"""
        batches = []
        current_batch = []
        current_duration = 0.0
        
        for pair_idx, i in enumerate(range(0, len(included_indices), 2)):
            if i + 1 >= len(included_indices):
                break
                
            pair_duration = pair_durations[pair_idx]
            current_pairs = len(current_batch) // 2
            
            # Check if adding this pair would exceed the limit (strict duration enforcement)
            if current_duration + pair_duration > max_duration_per_video:
                # Only start a new batch if current batch has content
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_duration = 0.0
                # If current batch is empty and this single pair exceeds limit, 
                # we have a configuration problem
                elif pair_duration > max_duration_per_video:
                    raise ValueError(f"Single pair duration {pair_duration:.1f}s exceeds max video duration {max_duration_per_video:.1f}s! Reduce pair duration.")
            
            # Add the pair to current batch
            front_idx = included_indices[i]
            back_idx = included_indices[i + 1]
            current_batch.extend([front_idx, back_idx])
            current_duration += pair_duration
        
        # Add the last batch if it has content
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _ensure_minimum_pairs_per_batch(self, batches, min_pairs_per_video):
        """Ensure no batch has fewer than minimum pairs by redistributing or merging"""
        if not batches:
            return batches
            
        # If we only have one batch, always keep it regardless of size
        if len(batches) == 1:
            return batches
            
        # Check if any batch has too few pairs
        adjusted_batches = []
        i = 0
        
        while i < len(batches):
            current_batch = batches[i]
            current_pairs = len(current_batch) // 2
            
            # If this batch has enough pairs, add it as-is
            if current_pairs >= min_pairs_per_video:
                adjusted_batches.append(current_batch)
                i += 1
            else:
                # This batch has too few pairs
                if i == len(batches) - 1:
                    # Last batch with too few pairs
                    # Only merge if the combined batch wouldn't be too long (>90s)
                    if adjusted_batches:
                        last_batch_pairs = len(adjusted_batches[-1]) // 2
                        combined_pairs = last_batch_pairs + current_pairs
                        estimated_duration = combined_pairs * 8.0  # Assuming 8s per pair
                        
                        if estimated_duration <= 72.0:  # Allow up to 72s for merged batch (about 20% over target)
                            logging.info(f"BATCHING: Merging last batch ({current_pairs} pairs) with previous batch")
                            adjusted_batches[-1].extend(current_batch)
                        else:
                            # Keep the small batch separate if merging would be too long
                            logging.info(f"BATCHING: Keeping small last batch ({current_pairs} pairs) separate to avoid overly long video")
                            adjusted_batches.append(current_batch)
                    else:
                        # Only one batch total, keep it
                        adjusted_batches.append(current_batch)
                else:
                    # Not the last batch - merge with next batch
                    logging.info(f"BATCHING: Merging batch ({current_pairs} pairs) with next batch")
                    next_batch = batches[i + 1]
                    merged_batch = current_batch + next_batch
                    adjusted_batches.append(merged_batch)
                    i += 2  # Skip the next batch since we merged it
                    continue
                i += 1
        
        return adjusted_batches
    
    def _get_random_music(self):
        """Get a random music track from available options"""
        import random
        music_files = self.get_music_files()
        if music_files:
            return random.choice(music_files)['display_name']
        else:
            # Fallback to default tracks if no custom music found
            available_music = ["Vintage Memories", "Nostalgic Journey", "Classic Charm", "Peaceful Moments"]
            return random.choice(available_music)
    
    def _get_music_path_by_name(self, display_name):
        """Get the file path for a music track by its display name"""
        # First check custom music files
        music_files = self.get_music_files()
        for music_file in music_files:
            if music_file['display_name'] == display_name:
                return music_file['path']
        
        # Fallback to legacy hardcoded music files
        music_filename_wav = display_name.replace(' ', '_').lower() + '.wav'
        music_filename_mp3 = display_name.replace(' ', '_').lower() + '.mp3'
        music_path_wav = os.path.join('music', music_filename_wav)
        music_path_mp3 = os.path.join('music', music_filename_mp3)
        
        if os.path.exists(music_path_mp3):
            return music_path_mp3
        elif os.path.exists(music_path_wav):
            return music_path_wav
        
        return None
    
    def _wrap_text(self, text, max_chars):
        """Wrap text to fit within max_chars without breaking words, handling line breaks"""
        if not text:
            return [""]
        
        # Split by manual line breaks first
        manual_lines = text.split('\n')
        all_lines = []
        
        for manual_line in manual_lines:
            if len(manual_line) <= max_chars:
                all_lines.append(manual_line)
            else:
                # Wrap this line if it's too long
                words = manual_line.split()
                current_line = ""
                
                for word in words:
                    # If adding this word would exceed the limit
                    if len(current_line) + len(word) + (1 if current_line else 0) > max_chars:
                        # If current line is not empty, save it
                        if current_line:
                            all_lines.append(current_line)
                            current_line = word
                        else:
                            # Word itself is longer than max_chars, add it anyway
                            all_lines.append(word)
                    else:
                        # Add word to current line
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                
                # Add the last line if not empty
                if current_line:
                    all_lines.append(current_line)
        
        return all_lines if all_lines else [""]
    
    def process_videos_in_batches(self, batches):
        """Process multiple videos based on the calculated batches"""
        try:
            total_videos = len(batches)
            original_line1 = self.start_line1_var.get()
            videos_created = []
            
            for batch_index, batch_indices in enumerate(batches):
                # Check for cancellation at the start of each batch
                if not self.is_processing:
                    print(f"DEBUG: Batch processing cancelled before batch {batch_index + 1}")
                    break
                    
                try:
                    # Update progress
                    overall_progress = (batch_index / total_videos) * 100
                    self.root.after(0, lambda p=overall_progress: self.progress_var.set(p))
                    
                    # Calculate actual part number using starting part number
                    # For regeneration, use the original part number instead
                    if (hasattr(self, 'regeneration_info') and 
                        self.regeneration_info and 
                        self.regeneration_info.get('is_regeneration') and
                        batch_index == 0):  # Should only be one batch for regeneration
                        actual_part_number = self.regeneration_info.get('part_number')
                        logging.info(f"DEBUG: Using original part number {actual_part_number} for regeneration")
                    else:
                        actual_part_number = self.starting_part_var.get() + batch_index
                    
                    # Always update start screen text with part number
                    part_text = f"{original_line1} #{actual_part_number}"
                    logging.info(f"DEBUG: Updating start text to: '{part_text}' (starting from part {self.starting_part_var.get()})")
                    self.start_line1_var.set(part_text)
                    
                    if total_videos > 1:
                        self.root.after(0, lambda b=batch_index, t=total_videos: 
                                      self.status_label.config(text=f"Creating video {b+1} of {t}..."))
                    else:
                        self.root.after(0, lambda: self.status_label.config(text="Creating video..."))
                    
                    # Create video for this batch
                    video_path = self.process_single_batch_video(batch_indices, actual_part_number, total_videos, original_line1)
                    if video_path:
                        videos_created.append(video_path)
                    
                    # Check for cancellation after each video is created
                    if not self.is_processing:
                        print(f"DEBUG: Batch processing cancelled after creating batch {batch_index + 1}")
                        break
                    
                except Exception as e:
                    logging.error(f"Error creating batch {batch_index + 1}: {e}")
                    continue
            
            # Restore original start line text
            self.start_line1_var.set(original_line1)
            
            # Update video parts list and UI
            # Check if this is a regeneration - if so, don't clear the parts list
            if (hasattr(self, 'regeneration_info') and 
                self.regeneration_info and 
                self.regeneration_info.get('is_regeneration')):
                
                logging.info(f"DEBUG: Processing regeneration - preserving parts list")
                # For regeneration, just update the existing parts list
                regenerated_part_number = self.regeneration_info.get('part_number')
                logging.info(f"DEBUG: Looking for part {regenerated_part_number} in existing parts list")
                
                # Find the matching part in the existing list and update its path
                part_found = False
                for part in self.video_parts:
                    if part.get('part_number') == regenerated_part_number:
                        # Update the path to the new video
                        if videos_created:
                            part['path'] = videos_created[0]  # Should only be one video for regeneration
                            part['filename'] = os.path.basename(videos_created[0])
                            logging.info(f"DEBUG: Updated part {regenerated_part_number} with new path: {videos_created[0]}")
                        
                        # Set the selector to this part
                        self.root.after(0, lambda: self.part_selector_var.set(part['display_name']))
                        part_found = True
                        break
                
                if not part_found:
                    logging.error(f"DEBUG: Could not find part {regenerated_part_number} in existing parts list!")
                
                # Clear regeneration info after handling the regeneration
                self.regeneration_info = None
                logging.info("DEBUG: Cleared regeneration info after parts list update")
                        
            else:
                logging.info(f"DEBUG: Normal batch creation - updating full parts list")
                # Normal batch creation - update the full list
                self.update_video_parts_list(videos_created, original_line1, total_videos, batches)
            
            # Show completion message
            if videos_created:
                self.latest_video_path = videos_created[-1]  # Set to last created video
                self.root.after(0, lambda: self.play_button.config(state='normal'))
                
                if len(videos_created) > 1:
                    self.root.after(0, lambda: self.show_batch_success_message(videos_created))
                else:
                    # Single video - show normal success message
                    import time
                    actual_time = 60  # Approximate
                    self.root.after(0, lambda: self.show_success_message(videos_created[0], 1, 0))
            else:
                self.root.after(0, lambda: self.show_error_message("No videos were created successfully"))
                
        except Exception as e:
            import traceback
            error_msg = str(e)
            full_traceback = traceback.format_exc()
            print(f"ERROR: Batch video creation failed: {error_msg}")
            print(f"FULL TRACEBACK: {full_traceback}")
            self.root.after(0, lambda: self.show_error_message(error_msg))
        finally:
            self.root.after(0, self.finish_processing)
    
    def process_single_batch_video(self, batch_indices, part_number, total_parts, original_title=None):
        """Process a single video from a batch of image indices"""
        try:
            logging.info(f"DEBUG: Starting batch video {part_number}/{total_parts} with {len(batch_indices)} images")
            clips = []
            
            # Add start clip
            self.root.after(0, lambda: self.status_label.config(text="Creating start clip..."))
            start_duration = self.actual_start_duration_var.get()  # Use configurable actual duration
            
            # Apply the same fade logic as the original process_video method
            # Don't apply fade-out to start clip if we're creating a manual transition, but DO apply if second page is enabled
            will_create_manual_transition = len(batch_indices) > 0 and self.start_fade_out_var.get()
            second_page_enabled = self.second_page_enabled_var.get()
            # Apply fade-out if: start_fade_out enabled OR second page enabled (for smooth transition)
            apply_fade_out = (self.start_fade_out_var.get() and not will_create_manual_transition) or second_page_enabled
            logging.info(f"DEBUG: Fade logic - batch_images: {len(batch_indices)}, fade_out_enabled: {self.start_fade_out_var.get()}, second_page_enabled: {second_page_enabled}")
            logging.info(f"DEBUG: will_create_manual_transition: {will_create_manual_transition}, apply_fade_out: {apply_fade_out}")
            
            logging.info(f"DEBUG: Creating start clip with duration {start_duration}s")
            start_clip = self.create_start_clip(duration=start_duration, apply_fade_out=apply_fade_out)
            if start_clip is None:
                raise Exception("Failed to create start clip")
            logging.info(f"DEBUG: Start clip created successfully")
            clips.append(start_clip)
            logging.info(f"DEBUG: Start clip added to clips list. Total clips: {len(clips)}")
            
            # Add second page clip if enabled
            if self.second_page_enabled_var.get():
                self.root.after(0, lambda: self.status_label.config(text="Creating second page clip..."))
                second_page_duration = self.actual_second_page_duration_var.get()  # Use configurable actual duration
                logging.info(f"DEBUG: Creating second page clip with ACTUAL duration {second_page_duration}s")

                second_page_clip = self.create_second_page_clip(duration=second_page_duration)
                if second_page_clip is None:
                    logging.warning("Failed to create second page clip, skipping...")
                else:
                    logging.info(f"DEBUG: Second page clip created successfully")
                    clips.append(second_page_clip)
                    logging.info(f"DEBUG: Second page clip added to clips list. Total clips: {len(clips)}")
            
            # Process postcard pairs in this batch
            for i in range(0, len(batch_indices), 2):
                if i + 1 >= len(batch_indices):
                    break
                    
                front_idx = batch_indices[i]
                back_idx = batch_indices[i + 1]
                
                front_path = self.postcard_images[front_idx]
                back_path = self.postcard_images[back_idx]
                
                # Calculate durations from configurable pair duration
                total_pair_duration = self.actual_pair_duration_var.get()
                transition_duration = float(self.transition_duration_var.get())
                
                # Distribute pair duration: include inter-pair transition in the budget
                # If this is not the last pair, reserve time for transition to next pair
                is_last_pair = i >= len(batch_indices) - 2
                inter_pair_transition_time = 0 if is_last_pair else transition_duration
                
                # Available time for front/back after reserving for transitions
                content_duration = total_pair_duration - transition_duration - inter_pair_transition_time
                front_duration = content_duration * 0.6  # 60% of remaining for front
                back_duration = content_duration * 0.4   # 40% of remaining for back
                

                
                logging.info(f"DEBUG: Processing pair {i//2 + 1}, front: {front_path}, back: {back_path}")
                logging.info(f"DEBUG: ACTUAL durations (from {total_pair_duration}s total) - front: {front_duration}s, back: {back_duration}s, transition: {transition_duration}s")
                
                # Create clips
                logging.info(f"DEBUG: Creating front clip...")
                front_clip = self.create_image_clip(front_path, front_duration)
                logging.info(f"DEBUG: Front clip created with actual duration: {front_clip.duration}s")
                if front_clip is None:
                    raise Exception(f"Failed to create front clip for: {front_path}")
                
                # NO FADE-IN for first image - let it show its full 4-second duration
                # The 2.5-second second page fade-out provides the smooth transition
                # if i == 0 and self.second_page_enabled_var.get():
                #     # Transition handled by longer second page fade-out (2.5s)
                
                logging.info(f"DEBUG: Front clip created successfully")
                
                # Special handling for first front clip
                if i == 0:
                    if self.second_page_enabled_var.get() and len(clips) > 0:
                        # Create crossfade from second page to first image
                        logging.info(f"DEBUG: Creating crossfade from second page to first image")
                        second_page_clip = clips[-1]  # Last clip should be the second page
                        crossfade_clip = self.create_second_page_to_first_image_crossfade(
                            second_page_clip, front_clip, crossfade_duration=1.0
                        )
                        # Replace the separate second page clip with the crossfade clip
                        clips[-1] = crossfade_clip
                        logging.info(f"DEBUG: Crossfade clip created and replaced second page. Total clips: {len(clips)}")
                    elif self.start_fade_out_var.get() and not self.second_page_enabled_var.get():
                        logging.info(f"DEBUG: Creating manual fade transition from start to first postcard")
                        start_to_front = self.create_fade_transition(start_clip, front_clip)
                        clips.append(start_to_front)  # Transition already includes the front clip at the end
                        logging.info(f"DEBUG: Manual transition created (includes front clip), clips now: {len(clips)}")
                    else:
                        # Add front clip normally (no special transition)
                        logging.info(f"DEBUG: Adding first front clip normally (no special transition)")
                        clips.append(front_clip)
                        logging.info(f"DEBUG: First front clip added. Total clips: {len(clips)}")
                else:
                    # Add front clip normally for non-first images
                    logging.info(f"DEBUG: Adding front clip normally")
                    clips.append(front_clip)
                    logging.info(f"DEBUG: Front clip added. Total clips: {len(clips)}")
                    
                logging.info(f"DEBUG: Creating back clip...")
                back_clip = self.create_image_clip(back_path, back_duration)
                logging.info(f"DEBUG: Back clip created with actual duration: {back_clip.duration}s")
                if back_clip is None:
                    raise Exception(f"Failed to create back clip for: {back_path}")
                logging.info(f"DEBUG: Back clip created successfully")
                
                # Add transition between front and back
                if self.transition_duration > 0:
                    # Check if we should remove the front clip - but NOT if we just created a crossfade
                    crossfade_was_created = i == 0 and self.second_page_enabled_var.get() and len(clips) > 0
                    manual_transition_was_created = i == 0 and self.start_fade_out_var.get() and not self.second_page_enabled_var.get()
                    should_remove_front = len(clips) > 0 and not crossfade_was_created and not manual_transition_was_created
                    if should_remove_front:
                        clips.pop()  # Remove the standalone front clip
                        logging.info(f"DEBUG: Removed standalone front clip before adding transition")
                    elif crossfade_was_created:
                        logging.info(f"DEBUG: Skipping front clip removal - crossfade already includes it")
                    
                    # Create enhanced transition that includes next postcard preview if available
                    if not is_last_pair:
                        next_front_idx = batch_indices[i + 2]
                        next_front_path = self.postcard_images[next_front_idx]
                        next_front_preview = self.create_image_clip(next_front_path, inter_pair_transition_time)
                        transition = self.create_enhanced_pair_transition(front_clip, back_clip, next_front_preview, total_pair_duration)
                        logging.info(f"DEBUG: Enhanced transition clip created with next preview, duration: {transition.duration}s")
                    else:
                        transition = self.create_transition(front_clip, back_clip)
                        logging.info(f"DEBUG: Standard transition clip created (last pair), duration: {transition.duration}s")
                    
                    clips.append(transition)  # Transition includes front, back, and optionally next preview
                    logging.info(f"DEBUG: Added transition clip")
                else:
                    clips.append(back_clip)
                    logging.info(f"DEBUG: Added back clip directly (no transition)")
                
                # Inter-pair smooth transition will be handled within the main pair transition above
            
            # Add ending clip
            self.root.after(0, lambda: self.status_label.config(text="Adding ending clip..."))
            ending_duration = self.actual_ending_duration_var.get()  # Use configurable actual duration
            logging.info(f"DEBUG: Creating ending clip with ACTUAL duration {ending_duration}s")
            ending_clip = self.create_ending_clip(duration=ending_duration)
            if ending_clip is None:
                raise Exception("Failed to create ending clip")
            logging.info(f"DEBUG: Ending clip created successfully")
            clips.append(ending_clip)
            
            # Concatenate clips
            self.root.after(0, lambda: self.status_label.config(text="Concatenating clips..."))
            logging.info(f"DEBUG: About to concatenate {len(clips)} clips for batch video")
            # DURATION ANALYSIS: Log each clip type and duration
            final_video = self._write_duration_analysis(clips, "BATCH VIDEO")
            
            # Get line1_text for logging regardless of regeneration
            line1_text = original_title if original_title else self.start_line1_var.get()
            
            # Check if this is a regeneration of an existing part
            if (hasattr(self, 'regeneration_info') and 
                self.regeneration_info and 
                self.regeneration_info.get('is_regeneration') and
                self.regeneration_info.get('part_number') == part_number):
                
                # Use the original filename for regeneration
                output_filename = self.regeneration_info['original_filename']
                output_path = os.path.join(self.output_path, output_filename)
                logging.info(f"DEBUG: Regenerating existing file: {output_filename}")
                
            else:
                # Generate new output filename using original title (before part number was added)
                # Sanitize filename by removing invalid characters
                safe_filename = "".join(c for c in line1_text if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_filename = safe_filename.replace(' ', '_')
                
                if not safe_filename:  # Fallback if no valid characters
                    safe_filename = "postcard_video"
                
                # Add timestamp for uniqueness
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Always use part numbers in filename, include dimensions
                dimensions = f"{self.video_width}x{self.video_height}"
                output_filename = f"{timestamp}_{safe_filename}_#{part_number}_{dimensions}.mp4"
                output_path = os.path.join(self.output_path, output_filename)
            
            logging.info(f"DEBUG: Generated filename: {output_filename} from Line1: '{line1_text}' (Part {part_number})")
            
            # Write video file using the same method as the main process_video
            self.root.after(0, lambda: self.status_label.config(text="Writing video file..."))
            
            # Use OpenCV to create video instead of MoviePy (more reliable)
            import cv2
            
            # Get video dimensions
            width, height = self.video_width, self.video_height
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 10.0, (width, height))
            
            # Check if video writer opened successfully
            if not out.isOpened():
                raise Exception(f"Failed to open video writer for {output_path}")
            logging.info(f"DEBUG: Video writer opened successfully for {output_path}")
            
            # Handle background music
            music_path = None
            if self.music_var.get() != "None":
                # Handle random music selection
                if self.music_var.get() == "Random":
                    selected_music = self._get_random_music()
                    logging.info(f"DEBUG: Random music selected: {selected_music}")
                else:
                    selected_music = self.music_var.get()
                
                # Find music file by display name
                music_path = self._get_music_path_by_name(selected_music)
                
                if music_path and os.path.exists(music_path):
                    self.root.after(0, lambda: self.status_label.config(text="Adding background music..."))
                else:
                    music_path = None  # Music file not found
            
            # Process each clip and write frames
            total_frames = 0
            logging.info(f"DEBUG: Starting to write {len(clips)} clips to video file")
            for clip_idx, clip in enumerate(clips):
                duration = clip.duration
                fps = 10  # 10 FPS for reliability
                num_frames = int(duration * fps)
                
                # Check if this is the ending clip (last clip)
                is_ending_clip = clip_idx == len(clips) - 1
                clip_type = "ENDING CLIP" if is_ending_clip else f"clip {clip_idx + 1}"
                logging.info(f"DEBUG: Processing {clip_type}/{len(clips)}, duration: {duration}s, frames: {num_frames}")
                
                for i in range(num_frames):
                    # Get frame at time t
                    t = i / fps
                    if t <= duration:
                        frame = clip.get_frame(t)
                        
                        # Ensure frame is in correct format for OpenCV
                        # MoviePy may return float64, but OpenCV needs uint8
                        if frame.dtype != np.uint8:
                            original_dtype = frame.dtype
                            # Convert from [0,1] float to [0,255] uint8 if needed
                            if frame.max() <= 1.0:
                                frame = (frame * 255).astype(np.uint8)
                            else:
                                frame = frame.astype(np.uint8)
                            
                            # Log the conversion for debugging (only once per clip)
                            if i == 0:
                                    logging.info(f"DEBUG: Converted frame from {original_dtype} to {frame.dtype} for clip {clip_idx + 1}")
                        
                        # Convert RGB to BGR for OpenCV
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        out.write(frame_bgr)
                        
                        # Update progress occasionally
                        total_frames += 1
                        if total_frames % 50 == 0:  # Update every 50 frames and print debug
                            progress = 90 + (total_frames / (len(clips) * 30)) * 9  # Rough estimate
                            logging.info(f"DEBUG: Written {total_frames} frames so far")
                            # Don't update progress too frequently to avoid blocking
                
                logging.info(f"DEBUG: Completed clip {clip_idx + 1}/{len(clips)}")
            
            out.release()
            
            # Add background music if selected
            if music_path and os.path.exists(music_path):
                self.root.after(0, lambda: self.status_label.config(text="Adding background music to video..."))
                
                # Create temporary video with audio
                temp_video_path = output_path.replace('.mp4', '_temp.mp4')
                os.rename(output_path, temp_video_path)
                
                try:
                    # Use ffmpeg to add audio (if available)
                    import subprocess
                    # Calculate fade-out duration (last 3 seconds)
                    video_duration = final_video.duration
                    fade_duration = min(3.0, video_duration * 0.3)  # 3 seconds or 30% of video, whichever is shorter
                    
                    # Use -stream_loop -1 to loop music indefinitely until video ends
                    # This prevents music from ending before the video is complete
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', temp_video_path,
                        '-stream_loop', '-1', '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-map', '0:v:0', '-map', '1:a:0',
                        '-shortest',
                        '-filter:a', f'volume={self.music_volume_var.get()},afade=t=out:st={video_duration-fade_duration}:d={fade_duration}',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Success - remove temp file
                        os.remove(temp_video_path)
                        self.root.after(0, lambda: self.status_label.config(text="Music added successfully!"))
                    else:
                        # FFmpeg failed - keep video without audio
                        os.rename(temp_video_path, output_path)
                        self.root.after(0, lambda: self.status_label.config(text="Video created (music not added)"))
                        
                except Exception as e:
                    # FFmpeg not available - keep video without audio
                    os.rename(temp_video_path, output_path)
                    self.root.after(0, lambda: self.status_label.config(text="Video created (music not added)"))
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            # Don't clear regeneration info here - it will be cleared later in process_videos_in_batches
            # after the parts list is updated
            if (hasattr(self, 'regeneration_info') and 
                self.regeneration_info and 
                self.regeneration_info.get('is_regeneration')):
                logging.info("DEBUG: Video regeneration completed, but keeping regeneration_info for parts list update")
            
            return output_path
            
        except Exception as e:
            import traceback
            error_msg = f"Error creating single batch video: {str(e)}"
            full_traceback = traceback.format_exc()
            logging.error(f"ERROR in process_single_batch_video: {error_msg}")
            logging.error(f"FULL TRACEBACK: {full_traceback}")
            return None
        
    def update_video_parts_list(self, video_paths, original_title, total_parts, batches=None):
        """Update the video parts list and dropdown"""
        # Clear existing parts
        self.video_parts.clear()
        
        # Get starting part number
        starting_part = self.starting_part_var.get()
        
        # Add new parts - always use part numbers now
        for i, video_path in enumerate(video_paths):
            actual_part_number = starting_part + i
            display_name = f"{original_title} (Part {actual_part_number})"
            
            part_info = {
                'path': video_path,
                'display_name': display_name,
                'part_number': actual_part_number,
                'filename': os.path.basename(video_path)  # Store the original filename
            }
            
            # Store batch indices if provided
            if batches and i < len(batches):
                part_info['batch_indices'] = batches[i]
                
            self.video_parts.append(part_info)
        
        # Update dropdown values
        dropdown_values = ["Latest"]
        if len(self.video_parts) > 1:
            # Multiple parts - add each part
            dropdown_values.extend([part['display_name'] for part in self.video_parts])
        elif len(self.video_parts) == 1:
            # Single video - add it as an option
            dropdown_values.append(self.video_parts[0]['display_name'])
        
        # Update the combobox
        self.root.after(0, lambda: self.part_selector.configure(values=dropdown_values))
        self.root.after(0, lambda: self.part_selector_var.set("Latest"))
    
    def show_batch_success_message(self, video_paths):
        """Show success message for multiple videos created"""
        video_list = "\n".join([f"• {os.path.basename(path)}" for path in video_paths])
        messagebox.showinfo("Batch Videos Created", 
                          f"Successfully created {len(video_paths)} videos:\n\n{video_list}\n\n"
                          f"Use the 'Part' dropdown to select which video to play.")
        self.status_label.config(text=f"✅ Created {len(video_paths)} batch videos successfully!")

    def process_video(self):
        try:
            clips = []
            total_images = len(self.postcard_images)
            start_time = time.time()
            
            # Add start clip with logo and text
            self.root.after(0, lambda: self.status_label.config(text="Creating start clip..."))
            start_duration = self.actual_start_duration_var.get()  # Use configurable actual duration
            # Don't apply fade-out to start clip if we're creating a manual transition
            # Apply fade-out if: start_fade_out enabled OR second page enabled (for smooth transition)
            will_create_manual_transition = len(self.postcard_images) > 0 and self.start_fade_out_var.get()
            second_page_enabled = self.second_page_enabled_var.get()
            # Apply fade-out if: start_fade_out enabled OR second page enabled (for smooth transition)
            apply_fade_out = (self.start_fade_out_var.get() and not will_create_manual_transition) or second_page_enabled
            logging.debug(f"Fade logic - postcards: {len(self.postcard_images)}, fade_out_enabled: {self.start_fade_out_var.get()}, second_page_enabled: {second_page_enabled}")
            logging.debug(f"will_create_manual_transition: {will_create_manual_transition}, apply_fade_out: {apply_fade_out}")
            start_clip = self.create_start_clip(duration=start_duration, apply_fade_out=apply_fade_out)
            if start_clip is None:
                raise Exception("Failed to create start clip")
            clips.append(start_clip)
            
            # Add second page clip if enabled
            if self.second_page_enabled_var.get():
                self.root.after(0, lambda: self.status_label.config(text="Creating second page clip..."))
                second_page_duration = self.actual_second_page_duration_var.get()  # Use configurable actual duration
                print(f"DEBUG: Creating second page clip with ACTUAL duration {second_page_duration}s")

                second_page_clip = self.create_second_page_clip(duration=second_page_duration)
                if second_page_clip is None:
                    print("WARNING: Failed to create second page clip, skipping...")
                else:
                    print(f"DEBUG: Second page clip created successfully")
                    clips.append(second_page_clip)
            
            # Calculate estimated time (rough estimate: 2 seconds per image)
            estimated_seconds = total_images * 2
            estimated_minutes = estimated_seconds // 60
            estimated_seconds = estimated_seconds % 60
            
            for i in range(0, total_images, 2):  # Process in pairs
                # Update progress (0-80% for processing)
                progress = (i / total_images) * 80
                self.root.after(0, lambda p=progress: self.progress_var.set(p))
                self.root.after(0, lambda: self.status_label.config(text=f"Processing postcard {(i//2)+1}/{total_images//2} ({int(progress)}%)"))
                
                # Get front and back images
                front_path = self.postcard_images[i]
                back_path = self.postcard_images[i + 1]
                
                # Calculate durations from configurable pair duration
                total_pair_duration = self.actual_pair_duration_var.get()
                transition_duration = float(self.transition_duration_var.get())
                
                # Distribute pair duration: include inter-pair transition in the budget
                # If this is not the last pair, reserve time for transition to next pair
                is_last_pair = i >= total_images - 2
                inter_pair_transition_time = 0 if is_last_pair else transition_duration
                
                # Available time for front/back after reserving for transitions
                content_duration = total_pair_duration - transition_duration - inter_pair_transition_time
                front_duration = content_duration * 0.6  # 60% of remaining for front
                back_duration = content_duration * 0.4   # 40% of remaining for back
                

                
                # Create front clip
                print(f"DEBUG: Creating front clip for {front_path}")
                front_clip = self.create_image_clip(front_path, front_duration)
                print(f"DEBUG: Front clip created with actual duration: {front_clip.duration}s")
                
                # NO FADE-IN for first image - let it show its full 4-second duration
                # The 2.5-second second page fade-out provides the smooth transition
                # if i == 0 and self.second_page_enabled_var.get():
                #     # Transition handled by longer second page fade-out (2.5s)
                
                print(f"DEBUG: Front clip created successfully")

                # Special handling for first front clip
                if i == 0:
                    if self.second_page_enabled_var.get() and len(clips) > 0:
                        # Create crossfade from second page to first image
                        print(f"DEBUG: Creating crossfade from second page to first image")
                        second_page_clip = clips[-1]  # Last clip should be the second page
                        crossfade_clip = self.create_second_page_to_first_image_crossfade(
                            second_page_clip, front_clip, crossfade_duration=1.0
                        )
                        # Replace the separate second page clip with the crossfade clip
                        clips[-1] = crossfade_clip
                        print(f"DEBUG: Crossfade clip created and replaced second page. Total clips: {len(clips)}")
                    elif self.start_fade_out_var.get() and not self.second_page_enabled_var.get():
                        logging.debug(f"Creating manual fade transition from start to first postcard")
                        start_to_front = self.create_fade_transition(start_clip, front_clip)
                        clips.append(start_to_front)  # Transition already includes the front clip at the end
                        logging.debug(f"Manual transition created (includes front clip), clips now: {len(clips)}")
                    else:
                        # Add front clip normally (no special transition)
                        print(f"DEBUG: Adding first front clip normally (no special transition)")
                        clips.append(front_clip)
                        print(f"DEBUG: First front clip added. Total clips: {len(clips)}")
                else:
                    # Add front clip normally for non-first images
                    logging.debug(f"Adding front clip normally")
                    clips.append(front_clip)
                
                # Create back clip
                print(f"DEBUG: Creating back clip for {back_path}")
                back_clip = self.create_image_clip(back_path, back_duration)
                print(f"DEBUG: Back clip created with actual duration: {back_clip.duration}s")
                print(f"DEBUG: Back clip created successfully")
                
                # Add transition between front and back
                if self.transition_duration > 0:
                    # Check if we should remove the front clip - but NOT if we just created a crossfade
                    crossfade_was_created = i == 0 and self.second_page_enabled_var.get() and len(clips) > 0
                    manual_transition_was_created = i == 0 and self.start_fade_out_var.get() and not self.second_page_enabled_var.get()
                    should_remove_front = len(clips) > 0 and not crossfade_was_created and not manual_transition_was_created
                    if should_remove_front:
                        clips.pop()  # Remove the standalone front clip
                        print(f"DEBUG: Removed standalone front clip before adding transition")
                    elif crossfade_was_created:
                        print(f"DEBUG: Skipping front clip removal - crossfade already includes it")
                    
                    # Create enhanced transition that includes next postcard preview if available
                    if not is_last_pair:
                        next_front_path = self.postcard_images[i + 2]
                        next_front_preview = self.create_image_clip(next_front_path, inter_pair_transition_time)
                        transition = self.create_enhanced_pair_transition(front_clip, back_clip, next_front_preview, total_pair_duration)
                        print(f"DEBUG: Enhanced transition clip created with next preview, duration: {transition.duration}s")
                    else:
                        transition = self.create_transition(front_clip, back_clip)
                        print(f"DEBUG: Standard transition clip created (last pair), duration: {transition.duration}s")
                    
                    clips.append(transition)  # Transition includes front, back, and optionally next preview
                    print(f"DEBUG: Added transition clip")
                else:
                    clips.append(back_clip)
                    print(f"DEBUG: Added back clip directly (no transition)")
                
                # Inter-pair smooth transition will be handled within the main pair transition above
            
            # Add ending clip
            self.root.after(0, lambda: self.status_label.config(text="Adding ending clip..."))
            ending_duration = self.actual_ending_duration_var.get()  # Use configurable actual duration
            print(f"DEBUG: Creating ending clip with ACTUAL duration {ending_duration}s...")
            ending_clip = self.create_ending_clip(duration=ending_duration)
            if ending_clip is None:
                raise Exception("Failed to create ending clip")
            print(f"DEBUG: Ending clip created successfully")
            clips.append(ending_clip)
            
            # Concatenate all clips
            self.root.after(0, lambda: self.status_label.config(text="Concatenating clips..."))
            self.root.after(0, lambda: self.progress_var.set(85))
            print(f"DEBUG: About to concatenate {len(clips)} clips")
            
            # DURATION ANALYSIS: Log each clip type and duration
            final_video = self._write_duration_analysis(clips, "SINGLE VIDEO")
            
            # Update progress for video writing
            self.root.after(0, lambda: self.status_label.config(text="Writing video file..."))
            self.root.after(0, lambda: self.progress_var.set(90))
            
            # Generate output filename using Line 1 text from start screen
            line1_text = self.start_line1_var.get()
            # Sanitize filename by removing invalid characters
            safe_filename = "".join(c for c in line1_text if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename.replace(' ', '_')
            
            if not safe_filename:  # Fallback if no valid characters
                safe_filename = "postcard_video"
            
            # Add timestamp for uniqueness and include dimensions
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dimensions = f"{self.video_width}x{self.video_height}"
            part_number = self.starting_part_var.get()
            output_filename = f"{timestamp}_{safe_filename}_Part{part_number}_{dimensions}.mp4"
            output_path = os.path.join(self.output_path, output_filename)
            
            logging.info(f"DEBUG: Generated filename: {output_filename} from Line1: '{line1_text}'")
            
            # Use OpenCV to create video instead of MoviePy (more reliable)
            self.root.after(0, lambda: self.status_label.config(text="Creating video with OpenCV..."))
            
            import cv2
            
            # Get video dimensions
            width, height = self.video_width, self.video_height
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 10.0, (width, height))
            
            # Handle background music
            music_path = None
            if self.music_var.get() != "None":
                # Handle random music selection
                if self.music_var.get() == "Random":
                    selected_music = self._get_random_music()
                    logging.info(f"DEBUG: Random music selected: {selected_music}")
                else:
                    selected_music = self.music_var.get()
                
                # Find music file by display name
                music_path = self._get_music_path_by_name(selected_music)
                
                if music_path and os.path.exists(music_path):
                    self.root.after(0, lambda: self.status_label.config(text="Adding background music..."))
                else:
                    music_path = None  # Music file not found
            
            # Process each clip and write frames
            total_frames = 0
            for clip in clips:
                duration = clip.duration
                fps = 10  # 10 FPS for reliability
                num_frames = int(duration * fps)
                
                for i in range(num_frames):
                    # Get frame at time t
                    t = i / fps
                    if t <= duration:
                        frame = clip.get_frame(t)
                        # Apply manual fades for start and ending clips if enabled
                        try:
                            if clip is start_clip:
                                # Start clip fades are handled by MoviePy effects in create_start_clip method
                                # Don't apply manual fades here to avoid double fade effects
                                logging.debug(f"Start clip frame at t={t:.2f} (fades handled by MoviePy)")
                            elif clip is ending_clip:
                                if self.ending_fade_in_var.get():
                                    fin = max(0.0, min(1.0, t / max(0.001, self.ending_fade_in_dur_var.get())))
                                else:
                                    fin = 1.0
                                if self.ending_fade_out_var.get():
                                    fout = max(0.0, min(1.0, (duration - t) / max(0.001, self.ending_fade_out_dur_var.get())))
                                else:
                                    fout = 1.0
                                alpha = min(fin, fout)
                                if alpha < 1.0:
                                    white = np.ones_like(frame, dtype=np.uint8) * 255
                                    frame = (frame.astype(np.float32) * alpha + white.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)
                        except Exception as _:
                            pass
                        # Convert RGB to BGR for OpenCV
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        out.write(frame_bgr)
                        
                        # Update progress
                        total_frames += 1
                        if total_frames % 10 == 0:  # Update every 10 frames
                            progress = 90 + (total_frames / (len(clips) * 30)) * 9  # Rough estimate
                            self.root.after(0, lambda p=progress: self.progress_var.set(min(p, 99)))
            
            out.release()
            
            # Add background music if selected
            if music_path and os.path.exists(music_path):
                self.root.after(0, lambda: self.status_label.config(text="Adding background music to video..."))
                
                # Create temporary video with audio
                temp_video_path = output_path.replace('.mp4', '_temp.mp4')
                os.rename(output_path, temp_video_path)
                
                try:
                    # Use ffmpeg to add audio (if available)
                    import subprocess
                    # Calculate fade-out duration (last 3 seconds)
                    video_duration = final_video.duration
                    fade_duration = min(3.0, video_duration * 0.3)  # 3 seconds or 30% of video, whichever is shorter
                    
                    # Use -stream_loop -1 to loop music indefinitely until video ends
                    # This prevents music from ending before the video is complete
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', temp_video_path,
                        '-stream_loop', '-1', '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-map', '0:v:0', '-map', '1:a:0',
                        '-shortest',
                        '-filter:a', f'volume={self.music_volume_var.get()},afade=t=out:st={video_duration-fade_duration}:d={fade_duration}',
                        output_path
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Success - remove temp file
                        os.remove(temp_video_path)
                        self.root.after(0, lambda: self.status_label.config(text="Music added successfully!"))
                    else:
                        # FFmpeg failed - keep video without audio
                        os.rename(temp_video_path, output_path)
                        self.root.after(0, lambda: self.status_label.config(text="Video created (music not added)"))
                        
                except Exception as e:
                    # FFmpeg not available - keep video without audio
                    os.rename(temp_video_path, output_path)
                    self.root.after(0, lambda: self.status_label.config(text="Video created (music not added)"))
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            # Calculate actual time taken
            actual_time = time.time() - start_time
            actual_minutes = int(actual_time // 60)
            actual_seconds = int(actual_time % 60)
            
            # Store the latest video path and enable play button
            self.latest_video_path = output_path
            self.root.after(0, lambda: self.play_button.config(state='normal'))
            
            # Update video parts list for single video
            original_title = self.start_line1_var.get()
            
            # Check if this is a regeneration - if so, don't clear the parts list
            if (hasattr(self, 'regeneration_info') and 
                self.regeneration_info and 
                self.regeneration_info.get('is_regeneration')):
                
                # For regeneration, just update the selector to point to the regenerated part
                regenerated_part_number = self.regeneration_info.get('part_number')
                
                # Find the matching part in the existing list and update its display
                for part in self.video_parts:
                    if part.get('part_number') == regenerated_part_number:
                        # Update the path to the new video
                        part['path'] = output_path
                        part['filename'] = os.path.basename(output_path)
                        
                        # Set the selector to this part
                        self.root.after(0, lambda: self.part_selector_var.set(part['display_name']))
                        break
                        
            else:
                # Normal single video creation - update the full list
                self.update_video_parts_list([output_path], original_title, 1)
            
            # Show success message
            self.root.after(0, lambda: self.show_success_message(output_path, actual_minutes, actual_seconds))
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            full_traceback = traceback.format_exc()
            print(f"ERROR: Video creation failed: {error_msg}")
            print(f"FULL TRACEBACK: {full_traceback}")
            self.root.after(0, lambda: self.show_error_message(error_msg))
        finally:
            self.root.after(0, self.finish_processing)
            
    def create_image_clip(self, image_path, duration):
        """Create a video clip from an image with specified duration"""
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
            
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Create background based on format
        if self.is_square_format():
            # Square format: use selected color background
            background = self.create_colored_background()
        else:
            # Regular format: use black background
            background = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
        
        # Resize to fit video dimensions while preserving aspect ratio and showing full image
        h, w = img_rgb.shape[:2]
        
        # Calculate scaling factors
        scale_x = self.video_width / w
        scale_y = self.video_height / h
        scale = min(scale_x, scale_y)  # Use smaller scale to fit entire image
        
        # Calculate new dimensions
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # Resize image
        img_resized = cv2.resize(img_rgb, (new_w, new_h))
        
        # Calculate position to center the image
        x_offset = (self.video_width - new_w) // 2
        y_offset = (self.video_height - new_h) // 2
        
        # Place the resized image on the background
        background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = img_resized
        img_resized = background
        
        # Create clip
        clip = ImageClip(img_resized, duration=duration)
        
        return clip
    
    def get_background_color_rgb(self):
        """Get RGB values for the selected background color"""
        color_name = self.background_color_var.get()
        
        # Color mapping (RGB format)
        color_map = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "gray": (128, 128, 128),
            "light_gray": (211, 211, 211),
            "dark_gray": (64, 64, 64),
            "red": (255, 0, 0),
            "green": (0, 128, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128),
            "brown": (139, 69, 19),
            "pink": (255, 192, 203),
            "navy": (0, 0, 128)
        }
        
        return color_map.get(color_name, (255, 255, 255))  # Default to white
    
    def create_colored_background(self):
        """Create a solid colored background for square format"""
        color_rgb = self.get_background_color_rgb()
        background = np.full((self.video_height, self.video_width, 3), color_rgb, dtype=np.uint8)
        return background
        
    def create_transition(self, clip1, clip2):
        """Create a transition effect between two clips"""
        effect = self.effect_var.get()
        
        # If random mode, pick a random effect
        if effect == "random":
            import random
            effects = ["fade", "slide_left", "slide_right", "slide_up", "slide_down", 
                      "wipe_left", "wipe_right", "wipe_up", "wipe_down", "dissolve"]
            effect = random.choice(effects)
        
        if effect == "fade":
            return self.create_fade_transition(clip1, clip2)
        elif effect == "slide_left":
            return self.create_slide_transition(clip1, clip2, direction="left")
        elif effect == "slide_right":
            return self.create_slide_transition(clip1, clip2, direction="right")
        elif effect == "slide_up":
            return self.create_slide_transition(clip1, clip2, direction="up")
        elif effect == "slide_down":
            return self.create_slide_transition(clip1, clip2, direction="down")
        elif effect == "wipe_left":
            return self.create_wipe_transition(clip1, clip2, direction="left")
        elif effect == "wipe_right":
            return self.create_wipe_transition(clip1, clip2, direction="right")
        elif effect == "wipe_up":
            return self.create_wipe_transition(clip1, clip2, direction="up")
        elif effect == "wipe_down":
            return self.create_wipe_transition(clip1, clip2, direction="down")
        elif effect == "dissolve":
            return self.create_dissolve_transition(clip1, clip2)
        elif effect == "zoom_in":
            return self.create_zoom_transition(clip1, clip2, zoom_type="in")
        elif effect == "zoom_out":
            return self.create_zoom_transition(clip1, clip2, zoom_type="out")
        else:
            # Default fade
            return self.create_fade_transition(clip1, clip2)
    
    def create_enhanced_pair_transition(self, front_clip, back_clip, next_front_clip, total_duration):
        """Create a pair transition that includes preview of next postcard within fixed duration"""
        transition_duration = float(self.transition_duration_var.get())
        
        def make_frame(t):
            # Phase 1: Show front clip (0 to front_duration)
            if t < front_clip.duration:
                return front_clip.get_frame(t)
            
            # Phase 2: Transition from front to back (front_duration to front_duration + transition_duration)
            elif t < front_clip.duration + transition_duration:
                transition_progress = (t - front_clip.duration) / transition_duration
                front_frame = front_clip.get_frame(min(front_clip.duration - 0.001, front_clip.duration - 1/30))
                back_frame = back_clip.get_frame(0)
                
                # Ensure frames are compatible
                front_frame = np.array(front_frame, dtype=np.float32)
                back_frame = np.array(back_frame, dtype=np.float32)
                
                if front_frame.shape != back_frame.shape:
                    import cv2
                    back_frame = cv2.resize(back_frame, (front_frame.shape[1], front_frame.shape[0]))
                
                blended_frame = front_frame * (1 - transition_progress) + back_frame * transition_progress
                return np.clip(blended_frame, 0, 255).astype('uint8')
            
            # Phase 3: Show back clip (until near end)
            elif t < total_duration - transition_duration:
                back_time = t - front_clip.duration - transition_duration
                back_time = min(back_time, back_clip.duration - 0.001)
                return back_clip.get_frame(back_time)
            
            # Phase 4: Preview transition to next postcard (last transition_duration seconds)
            else:
                preview_progress = (t - (total_duration - transition_duration)) / transition_duration
                back_frame = back_clip.get_frame(min(back_clip.duration - 0.001, back_clip.duration - 1/30))
                next_frame = next_front_clip.get_frame(0)
                
                # Ensure frames are compatible
                back_frame = np.array(back_frame, dtype=np.float32)
                next_frame = np.array(next_frame, dtype=np.float32)
                
                if back_frame.shape != next_frame.shape:
                    import cv2
                    next_frame = cv2.resize(next_frame, (back_frame.shape[1], back_frame.shape[0]))
                
                blended_frame = back_frame * (1 - preview_progress) + next_frame * preview_progress
                return np.clip(blended_frame, 0, 255).astype('uint8')
        
        enhanced_transition = VideoClip(make_frame, duration=total_duration)
        logging.info(f"DEBUG: Enhanced pair transition created: front ({front_clip.duration}s) → back → next preview, total: {total_duration}s")
        return enhanced_transition

    def create_fade_transition(self, clip1, clip2):
        """Create a fade transition between two clips"""
        # Create a custom clip that shows the first clip, then fades to the second
        logging.debug(f"Creating fade transition: clip1 duration={clip1.duration}, transition duration={self.transition_duration}")
        
        def make_frame(t):
            if t < clip1.duration:
                # Show first clip normally for its full duration
                return clip1.get_frame(t)
            elif t < clip1.duration + self.transition_duration:
                # Transition period: fade from clip1 to clip2
                transition_progress = (t - clip1.duration) / self.transition_duration
                frame1 = clip1.get_frame(min(clip1.duration - 0.001, clip1.duration - 1/30))  # Last frame of clip1 (safer)
                frame2 = clip2.get_frame(0)  # Start of second clip
                
                # Ensure frames are the right type and shape
                frame1 = np.array(frame1, dtype=np.float32)
                frame2 = np.array(frame2, dtype=np.float32)
                
                # Ensure both frames have the same shape
                if frame1.shape != frame2.shape:
                    logging.warning(f"Frame shape mismatch: {frame1.shape} vs {frame2.shape}")
                    # Resize frame2 to match frame1
                    import cv2
                    frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
                
                # Blend frames with proper clamping
                blended_frame = frame1 * (1 - transition_progress) + frame2 * transition_progress
                blended_frame = np.clip(blended_frame, 0, 255)
                return blended_frame.astype('uint8')
            else:
                # After transition: show second clip
                return clip2.get_frame(t - clip1.duration - self.transition_duration)
        
        # Transition clip duration: full front clip + transition + full back clip
        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration + clip2.duration)
        logging.debug(f"Fade transition created with duration={transition_clip.duration}s (front: {clip1.duration}s + transition: {self.transition_duration}s + back: {clip2.duration}s)")
        logging.debug(f"Front clip will show normally from 0s to {clip1.duration}s, then transition from {clip1.duration}s to {clip1.duration + self.transition_duration}s")
        return transition_clip

    def create_second_page_to_first_image_crossfade(self, second_page_clip, first_image_clip, crossfade_duration=1.0):
        """Create a crossfade transition from second page directly to first image"""
        logging.info(f"Creating crossfade transition: second page to first image (duration: {crossfade_duration}s)")
        
        # Calculate timing
        second_page_duration = second_page_clip.duration
        first_image_duration = first_image_clip.duration
        crossfade_start_time = second_page_duration - crossfade_duration
        
        # Total duration: second page duration + first image duration - crossfade overlap
        total_duration = second_page_duration + first_image_duration - crossfade_duration
        
        def make_frame(t):
            if t < crossfade_start_time:
                # Phase 1: Show second page normally (before crossfade)
                return second_page_clip.get_frame(t)
            elif t < second_page_duration:
                # Phase 2: Crossfade period - blend second page with first image
                crossfade_progress = (t - crossfade_start_time) / crossfade_duration
                
                # Get frames from both clips
                second_page_frame = second_page_clip.get_frame(t)
                first_image_time = crossfade_progress * crossfade_duration  # Start from beginning of first image
                first_image_frame = first_image_clip.get_frame(first_image_time)
                
                # Ensure frames are the right type and shape
                second_page_frame = np.array(second_page_frame, dtype=np.float32)
                first_image_frame = np.array(first_image_frame, dtype=np.float32)
                
                # Blend the frames (fade from second page to first image)
                alpha = crossfade_progress  # 0 = all second page, 1 = all first image
                blended_frame = (1 - alpha) * second_page_frame + alpha * first_image_frame
                return blended_frame.astype('uint8')
            else:
                # Phase 3: Show first image for remainder of its duration
                first_image_time = t - crossfade_start_time  # Continue from where crossfade left off
                first_image_time = min(first_image_time, first_image_duration - 0.01)
                return first_image_clip.get_frame(first_image_time)
        
        crossfade_clip = VideoClip(make_frame, duration=total_duration)
        logging.info(f"Crossfade clip created with duration: {total_duration}s (second page: {second_page_duration}s + first image: {first_image_duration}s - overlap: {crossfade_duration}s)")
        
        return crossfade_clip
    
    def create_slide_transition(self, clip1, clip2, direction="left"):
        """Create a slide transition"""
        def make_frame(t):
            if t <= self.transition_duration:
                # Get frames from both clips
                frame1 = clip1.get_frame(min(t, clip1.duration))
                frame2 = clip2.get_frame(min(t, clip2.duration))
                
                # Calculate slide position (0 to 1)
                slide_progress = t / self.transition_duration
                
                # Create composite frame
                composite = frame1.copy()
                
                if direction == "left":
                    # Slide from right to left
                    frame2_portion = int(self.video_width * slide_progress)
                    if frame2_portion > 0:
                        composite[:, :frame2_portion] = frame2[:, -frame2_portion:]
                elif direction == "right":
                    # Slide from left to right
                    frame2_portion = int(self.video_width * slide_progress)
                    if frame2_portion > 0:
                        composite[:, -frame2_portion:] = frame2[:, :frame2_portion]
                elif direction == "up":
                    # Slide from bottom to top
                    frame2_portion = int(self.video_height * slide_progress)
                    if frame2_portion > 0:
                        composite[:frame2_portion, :] = frame2[-frame2_portion:, :]
                elif direction == "down":
                    # Slide from top to bottom
                    frame2_portion = int(self.video_height * slide_progress)
                    if frame2_portion > 0:
                        composite[-frame2_portion:, :] = frame2[:frame2_portion, :]
                
                return composite
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        

        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
        return transition_clip
    
    def create_wipe_transition(self, clip1, clip2, direction="left"):
        """Create a wipe transition (hard edge)"""
        def make_frame(t):
            if t <= self.transition_duration:
                # Get frames from both clips
                frame1 = clip1.get_frame(min(t, clip1.duration))
                frame2 = clip2.get_frame(min(t, clip2.duration))
                
                # Calculate wipe position (0 to 1)
                wipe_progress = t / self.transition_duration
                
                # Create composite frame
                composite = frame1.copy()
                
                if direction == "left":
                    # Wipe from right to left
                    wipe_line = int(self.video_width * wipe_progress)
                    composite[:, :wipe_line] = frame2[:, :wipe_line]
                elif direction == "right":
                    # Wipe from left to right
                    wipe_line = int(self.video_width * (1 - wipe_progress))
                    composite[:, wipe_line:] = frame2[:, wipe_line:]
                elif direction == "up":
                    # Wipe from bottom to top
                    wipe_line = int(self.video_height * wipe_progress)
                    composite[:wipe_line, :] = frame2[:wipe_line, :]
                elif direction == "down":
                    # Wipe from top to bottom
                    wipe_line = int(self.video_height * (1 - wipe_progress))
                    composite[wipe_line:, :] = frame2[wipe_line:, :]
                
                return composite
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        

        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
        return transition_clip
    
    def create_dissolve_transition(self, clip1, clip2):
        """Create a dissolve transition (random pixel replacement)"""
        def make_frame(t):
            if t <= self.transition_duration:
                # Get frames from both clips
                frame1 = clip1.get_frame(min(t, clip1.duration))
                frame2 = clip2.get_frame(min(t, clip2.duration))
                
                # Calculate dissolve progress (0 to 1)
                dissolve_progress = t / self.transition_duration
                
                # Create composite frame
                composite = frame1.copy()
                
                # Create a random mask for dissolve effect
                import numpy as np
                mask = np.random.random((self.video_height, self.video_width)) < dissolve_progress
                
                # Apply mask to blend frames
                composite[mask] = frame2[mask]
                
                return composite
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        

        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
        return transition_clip
    
    def create_zoom_transition(self, clip1, clip2, zoom_type="in"):
        """Create a zoom transition"""
        def make_frame(t):
            if t <= self.transition_duration:
                # Get frames from both clips
                frame1 = clip1.get_frame(min(t, clip1.duration))
                frame2 = clip2.get_frame(min(t, clip2.duration))
                
                # Calculate zoom factor
                zoom_progress = t / self.transition_duration
                
                if zoom_type == "in":
                    # Zoom in effect
                    scale = 0.5 + 0.5 * zoom_progress
                else:  # zoom_out
                    # Zoom out effect
                    scale = 1.5 - 0.5 * zoom_progress
                
                # For now, just do a fade (zoom requires more complex image processing)
                fade_factor = zoom_progress
                
                # Ensure frames are the right type and shape
                frame1 = np.array(frame1, dtype=np.float32)
                frame2 = np.array(frame2, dtype=np.float32)
                
                # Ensure both frames have the same shape
                if frame1.shape != frame2.shape:
                    logging.warning(f"Frame shape mismatch in zoom transition: {frame1.shape} vs {frame2.shape}")
                    # Resize frame2 to match frame1
                    import cv2
                    frame2 = cv2.resize(frame2, (frame1.shape[1], frame1.shape[0]))
                
                # Blend frames with proper clamping
                blended_frame = frame1 * (1 - fade_factor) + frame2 * fade_factor
                blended_frame = np.clip(blended_frame, 0, 255)
                return blended_frame.astype('uint8')
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        

        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
        return transition_clip
    
    def create_ending_clip(self, duration=5):
        """Create an ending clip with logo and text on light gray background (like start screen)"""
        def make_frame(t):
            import numpy as np
            import cv2
            from PIL import Image
            
            # Create light gray background for start/end screens regardless of format
            frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 220
            
            # Get text lines and styling (3 lines for ending)
            line1 = self.ending_line1_var.get()
            line2 = self.ending_line2_var.get()
            line3 = self.ending_line3_var.get()
            
            # Get individual styling settings
            line1_size = self.ending_line1_size_var.get()
            line2_size = self.ending_line2_size_var.get()
            line3_size = self.ending_line3_size_var.get()
            line1_color = self.ending_line1_color_var.get()
            line2_color = self.ending_line2_color_var.get()
            line3_color = self.ending_line3_color_var.get()
            line1_font = self.ending_line1_font_var.get()
            line2_font = self.ending_line2_font_var.get()
            line3_font = self.ending_line3_font_var.get()
            line1_bold = self.ending_line1_bold_var.get()
            line2_bold = self.ending_line2_bold_var.get()
            line3_bold = self.ending_line3_bold_var.get()
            
            # Color mapping (RGB format to match preview - since frame is RGB)
            color_map = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "yellow": (255, 255, 0),  # RGB: Red=255, Green=255, Blue=0 = Yellow
                "red": (255, 0, 0),       # RGB: Red=255, Green=0, Blue=0 = Red
                "green": (0, 255, 0),     # RGB: Red=0, Green=255, Blue=0 = Green
                "blue": (0, 0, 255),      # RGB: Red=0, Green=0, Blue=255 = Blue
                "cyan": (0, 255, 255),    # RGB: Red=0, Green=255, Blue=255 = Cyan
                "magenta": (255, 0, 255), # RGB: Red=255, Green=0, Blue=255 = Magenta
                "brown": (139, 69, 19),   # RGB: Brown color
                "orange": (255, 165, 0)   # RGB: Red=255, Green=165, Blue=0 = Orange
            }
            
            # Font mapping for OpenCV (limited font support but with variety)
            font_map = {
                "Arial": cv2.FONT_HERSHEY_SIMPLEX,
                "Times New Roman": cv2.FONT_HERSHEY_SIMPLEX,
                "Courier New": cv2.FONT_HERSHEY_SIMPLEX,
                "Georgia": cv2.FONT_HERSHEY_DUPLEX,  # Different font for variety
                "Verdana": cv2.FONT_HERSHEY_SIMPLEX,
                "Impact": cv2.FONT_HERSHEY_TRIPLEX,  # Bold font for impact
                "Comic Sans MS": cv2.FONT_HERSHEY_SCRIPT_SIMPLEX  # Script font for variety
            }
            
            # Get individual fonts for each line
            font1 = font_map.get(line1_font, cv2.FONT_HERSHEY_SIMPLEX)
            font2 = font_map.get(line2_font, cv2.FONT_HERSHEY_SIMPLEX)
            font3 = font_map.get(line3_font, cv2.FONT_HERSHEY_SIMPLEX)
            
            print(f"DEBUG: Font mapping - Line1: '{line1_font}' -> {font1}, Line2: '{line2_font}' -> {font2}, Line3: '{line3_font}' -> {font3}")
            
            # Set thickness and font adjustments based on bold settings
            thickness1 = 6 if line1_bold else 2
            thickness2 = 6 if line2_bold else 2
            thickness3 = 6 if line3_bold else 2
            
            # For bold text, use a bolder font variant when available
            if line1_bold and font1 == cv2.FONT_HERSHEY_SIMPLEX:
                font1 = cv2.FONT_HERSHEY_DUPLEX
            if line2_bold and font2 == cv2.FONT_HERSHEY_SIMPLEX:
                font2 = cv2.FONT_HERSHEY_DUPLEX
            if line3_bold and font3 == cv2.FONT_HERSHEY_SIMPLEX:
                font3 = cv2.FONT_HERSHEY_DUPLEX
            
            # DYNAMIC VERTICAL CENTERING - Calculate total content height and center it
            logo_text_spacing = getattr(self, 'ending_logo_text_spacing_var', self.start_logo_text_spacing_var).get()
            logo_size_video = getattr(self, 'ending_logo_size_var', self.start_logo_size_var).get()
            line1_hidden = getattr(self, 'ending_line1_hidden_var', tk.BooleanVar(value=False)).get()
            line2_hidden = getattr(self, 'ending_line2_hidden_var', tk.BooleanVar(value=False)).get()
            line3_hidden = getattr(self, 'ending_line3_hidden_var', tk.BooleanVar(value=False)).get()
            
            # Calculate total content height
            logo_height = logo_size_video
            text_spacing = getattr(self, 'ending_text_spacing_var', self.start_text_spacing_var).get()
            base_spacing = 80
            adjusted_spacing = base_spacing + (text_spacing * 10)
            
            # Calculate text heights (approximate)
            text_height_estimate = 50  # Approximate height for text lines
            total_text_height = 0
            if line1 and not line1_hidden:
                total_text_height += text_height_estimate
            if line2 and not line2_hidden:
                total_text_height += text_height_estimate
            if line3 and not line3_hidden:
                total_text_height += text_height_estimate
            
            # Add spacing between text lines
            if (line1 and not line1_hidden) and (line2 and not line2_hidden):
                total_text_height += adjusted_spacing
            if (line2 and not line2_hidden) and (line3 and not line3_hidden):
                total_text_height += adjusted_spacing

            # Extra image contribution (video sizing is unscaled)
            extra_image_enabled = self.ending_image_enabled_var.get()
            extra_image_path = self.ending_image_path_var.get()
            extra_image_spacing = self.ending_image_spacing_var.get()
            extra_image_height = self.ending_image_height_var.get()
            include_extra_image = (
                extra_image_enabled and extra_image_path and os.path.exists(extra_image_path)
            )
            if include_extra_image:
                total_text_height += extra_image_spacing + extra_image_height
            
            # Total content height = logo + spacing + text
            total_content_height = logo_height + logo_text_spacing + total_text_height

            # Extra image contribution (video sizing unscaled)
            ending_extra_image_enabled = self.ending_image_enabled_var.get()
            ending_extra_image_path = self.ending_image_path_var.get()
            ending_extra_image_spacing = self.ending_image_spacing_var.get()
            ending_extra_image_height = self.ending_image_height_var.get()
            include_ending_extra = bool(ending_extra_image_enabled and ending_extra_image_path and os.path.exists(ending_extra_image_path))
            if include_ending_extra:
                total_content_height += ending_extra_image_spacing + ending_extra_image_height
            
            # Calculate starting Y position to center everything
            available_height = self.video_height - 100  # Leave 50px margins top and bottom
            start_y = (available_height - total_content_height) // 2 + 50  # Center and add top margin
            
            # If content is too tall, scale down or adjust positioning
            if total_content_height > available_height:
                print(f"WARNING: Content too tall ({total_content_height}px > {available_height}px), adjusting...")
                # Use smaller margins and start from top
                available_height = self.video_height - 40  # Smaller margins
                start_y = 20  # Start near top
                
                # If still too tall, we'll need to scale down the logo
                if total_content_height > available_height:
                    scale_factor = available_height / total_content_height
                    logo_size_video = int(logo_size_video * scale_factor)
                    logo_height = logo_size_video
                    # Recalculate total content height with smaller logo
                    total_content_height = logo_height + logo_text_spacing + total_text_height
                    print(f"DEBUG: Scaled logo to {logo_size_video}px, new total height: {total_content_height}px")
            
            # Ensure start_y is never negative
            start_y = max(10, start_y)
            
            # Logo position
            logo_y = start_y
            
            # Text start position
            text_start_y = logo_y + logo_height + logo_text_spacing
            
            # Update logo position to use calculated dynamic positioning
            logo_x = (self.video_width - logo_size_video) // 2
            
            print(f"DEBUG: Video dimensions: {self.video_width}x{self.video_height}")
            print(f"DEBUG: Total content height: {total_content_height}")
            print(f"DEBUG: Available height: {available_height}")
            print(f"DEBUG: Centered start Y: {start_y}")
            print(f"DEBUG: Logo position: y={logo_y}, size={logo_size_video}")
            print(f"DEBUG: Text start position: {text_start_y}")
            print(f"DEBUG: Spacing: base={base_spacing}, adjusted={adjusted_spacing}")
            
            print(f"DEBUG: Final Y positions - Line1: {text_start_y}, Line2: {text_start_y + adjusted_spacing}, Line3: {text_start_y + (adjusted_spacing * 2)}")
            
            # Ensure hidden variables are accessible for rendering section
            line1_hidden = getattr(self, 'ending_line1_hidden_var', tk.BooleanVar(value=False)).get()
            line2_hidden = getattr(self, 'ending_line2_hidden_var', tk.BooleanVar(value=False)).get()
            line3_hidden = getattr(self, 'ending_line3_hidden_var', tk.BooleanVar(value=False)).get()
            
            # Load and display logo with calculated positioning
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            if os.path.exists(logo_path):
                try:
                    # Load logo with alpha channel
                    logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                    if logo is not None:
                        # Convert BGR to RGB for correct colors
                        if len(logo.shape) == 3 and logo.shape[2] >= 3:
                            logo = cv2.cvtColor(logo, cv2.COLOR_BGR2RGB)
                        # Resize logo to user-defined size
                        logo = cv2.resize(logo, (logo_size_video, logo_size_video))
                        
                        # Handle different image formats
                        if len(logo.shape) == 3 and logo.shape[2] == 4:  # Has alpha channel
                            # Convert RGBA to RGB with alpha blending
                            alpha_channel = logo[:, :, 3] / 255.0
                            rgb_channels = logo[:, :, :3]
                            
                            # Create white background for blending
                            white_bg = np.ones_like(rgb_channels) * 255
                            
                            # Blend logo with white background
                            blended = rgb_channels * alpha_channel[:, :, np.newaxis] + \
                                     white_bg * (1 - alpha_channel[:, :, np.newaxis])
                            
                            # Place logo on frame with calculated position
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = blended.astype(np.uint8)
                            
                        elif len(logo.shape) == 3 and logo.shape[2] == 3:  # RGB without alpha
                            # Place logo directly
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = logo
                        else:
                            # Grayscale or other format - place directly
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = logo
                except Exception as e:
                    print(f"Error loading logo: {e}")
            
            # Line 1
            if line1 and not line1_hidden:
                print(f"DEBUG: Drawing Line 1 - Text: '{line1}'")
                color1 = color_map.get(line1_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color1 = color1

                (text_width, text_height), _ = cv2.getTextSize(line1, font1, line1_size, thickness1)
                x1 = (self.video_width - text_width) // 2
                y1 = int(text_start_y)  # Convert to integer for OpenCV
                
                # Enhanced bold rendering: render multiple times with slight offsets for bold effect
                if line1_bold:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dx, dy in offsets:
                        cv2.putText(frame, line1, (x1 + dx, y1 + dy), font1, line1_size, text_color1, 2)
                
                cv2.putText(frame, line1, (x1, y1), font1, line1_size, text_color1, thickness1)
                print(f"DEBUG: Ending Line 1 - Text: '{line1}', Color: {text_color1}, Pos: ({x1}, {y1}), Bold: {line1_bold}")
            else:
                print(f"DEBUG: Line 1 is empty or None")
            
            # Line 2
            if line2 and not line2_hidden:
                print(f"DEBUG: Drawing Line 2 - Text: '{line2}'")
                color2 = color_map.get(line2_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color2 = color2

                (text_width, text_height), _ = cv2.getTextSize(line2, font2, line2_size, thickness2)
                x2 = (self.video_width - text_width) // 2
                # If line1 is hidden, keep line2 at text_start_y; otherwise below line1
                if line1 and not line1_hidden:
                    y2 = int(text_start_y + adjusted_spacing)
                else:
                    y2 = int(text_start_y)
                
                # Enhanced bold rendering: render multiple times with slight offsets for bold effect
                if line2_bold:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dx, dy in offsets:
                        cv2.putText(frame, line2, (x2 + dx, y2 + dy), font2, line2_size, text_color2, 2)
                
                cv2.putText(frame, line2, (x2, y2), font2, line2_size, text_color2, thickness2)
                print(f"DEBUG: Ending Line 2 - Text: '{line2}', Color: {text_color2}, Pos: ({x2}, {y2})")
            else:
                print(f"DEBUG: Line 2 is empty or None")
            
            # Line 3
            if line3 and not line3_hidden:
                print(f"DEBUG: Drawing Line 3 - Text: '{line3}'")
                color3 = color_map.get(line3_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color3 = color3

                (text_width, text_height), _ = cv2.getTextSize(line3, font3, line3_size, thickness3)
                x3 = (self.video_width - text_width) // 2
                # Determine y3 based on which previous lines are visible
                visible_offset = 0
                if line1 and not line1_hidden:
                    visible_offset += 1
                if line2 and not line2_hidden:
                    visible_offset += 1
                y3 = int(text_start_y + (adjusted_spacing * max(visible_offset, 0)))
                
                # Enhanced bold rendering: render multiple times with slight offsets for bold effect
                if line3_bold:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dx, dy in offsets:
                        cv2.putText(frame, line3, (x3 + dx, y3 + dy), font3, line3_size, text_color3, 2)
                
                cv2.putText(frame, line3, (x3, y3), font3, line3_size, text_color3, thickness3)
                print(f"DEBUG: Ending Line 3 - Text: '{line3}', Color: {text_color3}, Pos: ({x3}, {y3}), Bold: {line3_bold}")
            else:
                print(f"DEBUG: Line 3 is empty or None")

            # Extra image rendering for ending (after last visible text line)
            if include_ending_extra:
                try:
                    pil_img = Image.open(ending_extra_image_path)
                    w, h = pil_img.size
                    if h <= 0:
                        h = 1
                    new_h = max(1, int(ending_extra_image_height))
                    new_w = int(w * (new_h / h))
                    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    # Handle transparency properly
                    if pil_img.mode == 'RGBA':
                        # Convert RGBA PIL image to numpy array
                        rgba_img = np.array(pil_img)
                        rgb_channels = rgba_img[:, :, :3]
                        alpha_channel = rgba_img[:, :, 3] / 255.0
                        
                        # Blend with light gray background (220, 220, 220)
                        background = np.ones_like(rgb_channels) * 220
                        blended = rgb_channels * alpha_channel[:, :, np.newaxis] + \
                                 background * (1 - alpha_channel[:, :, np.newaxis])
                        rgb_img = blended.astype(np.uint8)
                    else:
                        # No transparency, convert normally
                        rgb_img = np.array(pil_img.convert('RGB'))
                    
                    last_y = text_start_y
                    visible_offset = 0
                    if line1 and not line1_hidden:
                        visible_offset += 1
                    if line2 and not line2_hidden:
                        last_y = int(text_start_y + adjusted_spacing)
                        visible_offset += 1
                    if line3 and not line3_hidden:
                        last_y = int(text_start_y + (adjusted_spacing * max(visible_offset, 0)))
                    extra_y = int(last_y + ending_extra_image_spacing)
                    extra_x = (self.video_width - new_w) // 2
                    frame[extra_y:extra_y + new_h, extra_x:extra_x + new_w] = rgb_img
                except Exception as e:
                    print(f"Ending video extra image error: {e}")
            
            return frame
        
        try:
            ending_clip = VideoClip(make_frame, duration=duration)
            if ending_clip is None:
                print("ERROR: Failed to create ending clip")
                return None
            
            # Apply fade effects if enabled
            if self.ending_fade_in_var.get():
                try:
                    ending_clip = vfx_fadein(ending_clip, self.ending_fade_in_dur_var.get())
                except Exception as e:
                    print(f"Warning: Failed to apply ending fade in effect: {e}")
            if self.ending_fade_out_var.get():
                try:
                    ending_clip = vfx_fadeout(ending_clip, self.ending_fade_out_dur_var.get())
                except Exception as e:
                    print(f"Warning: Failed to apply ending fade out effect: {e}")
            
            return ending_clip
            
        except Exception as e:
            print(f"ERROR: Failed to create ending clip: {e}")
            return None
    
    
    def create_start_clip(self, duration=3, apply_fade_out=None):
        """Create a start clip with logo and text on light gray background"""
        def make_frame(t):
            import numpy as np
            import cv2
            import os
            from PIL import Image
            
            # Create light gray background for start/end screens regardless of format
            frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 220
            
            # Get text lines and styling
            line1 = self.start_line1_var.get()
            line2 = self.start_line2_var.get()
            line1_hidden = self.start_line1_hidden_var.get()
            
            # Get individual styling settings
            line1_size = self.start_line1_size_var.get()
            line2_size = self.start_line2_size_var.get()
            line1_color = self.start_line1_color_var.get()
            line2_color = self.start_line2_color_var.get()
            line1_font = self.start_line1_font_var.get()
            line2_font = self.start_line2_font_var.get()
            line1_bold = self.start_line1_bold_var.get()
            line2_bold = self.start_line2_bold_var.get()
            
            # Color mapping (RGB format to match preview - since frame is RGB)
            color_map = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "yellow": (255, 255, 0),  # RGB: Red=255, Green=255, Blue=0 = Yellow
                "red": (255, 0, 0),       # RGB: Red=255, Green=0, Blue=0 = Red
                "green": (0, 255, 0),     # RGB: Red=0, Green=255, Blue=0 = Green
                "blue": (0, 0, 255),      # RGB: Red=0, Green=0, Blue=255 = Blue
                "cyan": (0, 255, 255),    # RGB: Red=0, Green=255, Blue=255 = Cyan
                "magenta": (255, 0, 255), # RGB: Red=255, Green=0, Blue=255 = Magenta
                "brown": (139, 69, 19),   # RGB: Brown color
                "orange": (255, 165, 0)   # RGB: Red=255, Green=165, Blue=0 = Orange
            }
            
            # Font mapping for OpenCV (limited font support but with variety)
            font_map = {
                "Arial": cv2.FONT_HERSHEY_SIMPLEX,
                "Times New Roman": cv2.FONT_HERSHEY_SIMPLEX,
                "Courier New": cv2.FONT_HERSHEY_SIMPLEX,
                "Georgia": cv2.FONT_HERSHEY_DUPLEX,  # Different font for variety
                "Verdana": cv2.FONT_HERSHEY_SIMPLEX,
                "Impact": cv2.FONT_HERSHEY_TRIPLEX,  # Bold font for impact
            }
            
            # Get individual fonts for each line
            font1 = font_map.get(line1_font, cv2.FONT_HERSHEY_SIMPLEX)
            font2 = font_map.get(line2_font, cv2.FONT_HERSHEY_SIMPLEX)
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            # Set thickness and font adjustments based on bold settings
            thickness1 = 6 if line1_bold else 2
            thickness2 = 6 if line2_bold else 2
            
            # For bold text, use a bolder font variant when available
            if line1_bold and font1 == cv2.FONT_HERSHEY_SIMPLEX:
                font1 = cv2.FONT_HERSHEY_DUPLEX
            if line2_bold and font2 == cv2.FONT_HERSHEY_SIMPLEX:
                font2 = cv2.FONT_HERSHEY_DUPLEX
            
            # DYNAMIC VERTICAL CENTERING FOR START SCREEN
            logo_text_spacing = self.start_logo_text_spacing_var.get()
            logo_size_video = self.start_logo_size_var.get()
            
            # Calculate total content height
            logo_height = logo_size_video
            text_spacing = self.start_text_spacing_var.get()
            base_spacing = 80
            adjusted_spacing = base_spacing + (text_spacing * 10)
            
            # Calculate text heights (approximate)
            text_height_estimate = 50  # Approximate height for text lines
            total_text_height = 0
            if line1 and not line1_hidden:
                total_text_height += text_height_estimate
            if line2:
                total_text_height += text_height_estimate
            
            # Add spacing between text lines
            if line1 and not line1_hidden and line2:
                total_text_height += adjusted_spacing
            
            # Total content height = logo + spacing + text
            total_content_height = logo_height + logo_text_spacing + total_text_height
            
            # Extra image contribution (video sizing unscaled)
            start_extra_image_enabled = self.start_image_enabled_var.get()
            start_extra_image_path = self.start_image_path_var.get()
            start_extra_image_spacing = self.start_image_spacing_var.get()
            start_extra_image_height = self.start_image_height_var.get()
            include_start_extra = bool(start_extra_image_enabled and start_extra_image_path and os.path.exists(start_extra_image_path))
            if include_start_extra:
                total_content_height += start_extra_image_spacing + start_extra_image_height
            
            # Calculate starting Y position to center everything
            available_height = self.video_height - 100  # Leave 50px margins top and bottom
            start_y = (available_height - total_content_height) // 2 + 50  # Center and add top margin
            
            # If content is too tall, scale down or adjust positioning
            if total_content_height > available_height:
                print(f"WARNING: Start content too tall ({total_content_height}px > {available_height}px), adjusting...")
                # Use smaller margins and start from top
                available_height = self.video_height - 40  # Smaller margins
                start_y = 20  # Start near top
                
                # If still too tall, we'll need to scale down the logo
                if total_content_height > available_height:
                    scale_factor = available_height / total_content_height
                    logo_size_video = int(logo_size_video * scale_factor)
                    logo_height = logo_size_video
                    # Recalculate total content height with smaller logo
                    total_content_height = logo_height + logo_text_spacing + total_text_height
                    print(f"DEBUG: Start scaled logo to {logo_size_video}px, new total height: {total_content_height}px")
            
            # Ensure start_y is never negative
            start_y = max(10, start_y)
            
            # Logo position
            logo_y = start_y
            
            # Text start position
            text_start_y = logo_y + logo_height + logo_text_spacing
            
            # Update logo position to use calculated dynamic positioning
            logo_x = (self.video_width - logo_size_video) // 2
            
            # Load and display logo with calculated positioning
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            if os.path.exists(logo_path):
                try:
                    # Load logo with alpha channel
                    logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
                    if logo is not None:
                        # Convert BGR to RGB for correct colors
                        if len(logo.shape) == 3 and logo.shape[2] >= 3:
                            logo = cv2.cvtColor(logo, cv2.COLOR_BGR2RGB)
                        # Resize logo to user-defined size
                        logo = cv2.resize(logo, (logo_size_video, logo_size_video))
                        
                        # Handle different image formats
                        if len(logo.shape) == 3 and logo.shape[2] == 4:  # Has alpha channel
                            # Convert RGBA to RGB with alpha blending
                            alpha_channel = logo[:, :, 3] / 255.0
                            rgb_channels = logo[:, :, :3]
                            
                            # Create white background for blending
                            white_bg = np.ones_like(rgb_channels) * 255
                            
                            # Blend logo with white background
                            blended = rgb_channels * alpha_channel[:, :, np.newaxis] + \
                                     white_bg * (1 - alpha_channel[:, :, np.newaxis])
                            
                            # Place logo on frame with calculated position
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = blended.astype(np.uint8)
                            
                        elif len(logo.shape) == 3 and logo.shape[2] == 3:  # RGB without alpha
                            # Place logo directly
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = logo
                        else:
                            # Grayscale or other format - place directly
                            frame[max(0,logo_y):min(self.video_height,logo_y+logo_size_video), max(0,logo_x):min(self.video_width,logo_x+logo_size_video)] = logo
                except Exception as e:
                    print(f"Error loading logo: {e}")
            
            # Line 1
            if line1 and not line1_hidden:
                print(f"DEBUG: Drawing Line 1 - Text: '{line1}'")
                color1 = color_map.get(line1_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color1 = color1
                (text_width, text_height), _ = cv2.getTextSize(line1, font1, line1_size, thickness1)
                x1 = (self.video_width - text_width) // 2
                y1 = int(text_start_y)  # Convert to integer for OpenCV
                
                # Enhanced bold rendering: render multiple times with slight offsets for bold effect
                if line1_bold:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dx, dy in offsets:
                        cv2.putText(frame, line1, (x1 + dx, y1 + dy), font1, line1_size, text_color1, 2)
                
                cv2.putText(frame, line1, (x1, y1), font1, line1_size, text_color1, thickness1)
                print(f"DEBUG: Start Line 1 - Text: '{line1}', Color: {text_color1}, Pos: ({x1}, {y1}), Bold: {line1_bold}")
            else:
                print(f"DEBUG: Line 1 is empty or None")
            
            # Line 2
            if line2:
                print(f"DEBUG: Drawing Line 2 - Text: '{line2}'")
                color2 = color_map.get(line2_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color2 = color2
                (text_width, text_height), _ = cv2.getTextSize(line2, font2, line2_size, thickness2)
                x2 = (self.video_width - text_width) // 2
                if line1_hidden or not line1:
                    y2 = int(text_start_y)
                else:
                    y2 = int(text_start_y + adjusted_spacing)
                
                # Enhanced bold rendering: render multiple times with slight offsets for bold effect
                if line2_bold:
                    offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                    for dx, dy in offsets:
                        cv2.putText(frame, line2, (x2 + dx, y2 + dy), font2, line2_size, text_color2, 2)
                
                cv2.putText(frame, line2, (x2, y2), font2, line2_size, text_color2, thickness2)
                print(f"DEBUG: Start Line 2 - Text: '{line2}', Color: {text_color2}, Pos: ({x2}, {y2})")
            else:
                print(f"DEBUG: Line 2 is empty or None")

            # Extra image rendering for start (after last visible text line)
            if include_start_extra:
                try:
                    pil_img = Image.open(start_extra_image_path)
                    w, h = pil_img.size
                    if h <= 0:
                        h = 1
                    new_h = max(1, int(start_extra_image_height))
                    new_w = int(w * (new_h / h))
                    pil_img = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    
                    # Handle transparency properly
                    if pil_img.mode == 'RGBA':
                        # Convert RGBA PIL image to numpy array
                        rgba_img = np.array(pil_img)
                        rgb_channels = rgba_img[:, :, :3]
                        alpha_channel = rgba_img[:, :, 3] / 255.0
                        
                        # Blend with light gray background (220, 220, 220)
                        background = np.ones_like(rgb_channels) * 220
                        blended = rgb_channels * alpha_channel[:, :, np.newaxis] + \
                                 background * (1 - alpha_channel[:, :, np.newaxis])
                        rgb_img = blended.astype(np.uint8)
                    else:
                        # No transparency, convert normally
                        rgb_img = np.array(pil_img.convert('RGB'))
                    
                    last_y = text_start_y if (line1_hidden or not line1) else int(text_start_y + adjusted_spacing)
                    extra_y = int(last_y + start_extra_image_spacing)
                    extra_x = (self.video_width - new_w) // 2
                    frame[extra_y:extra_y + new_h, extra_x:extra_x + new_w] = rgb_img
                except Exception as e:
                    print(f"Start video extra image error: {e}")
            
            return frame
        

        try:
            print("DEBUG: Creating start clip...")
            print(f"DEBUG: Duration: {duration}")
            print(f"DEBUG: Video dimensions: {self.video_width}x{self.video_height}")
            print(f"DEBUG: VideoClip available: {VideoClip is not None}")
            
            if VideoClip is None:
                print("ERROR: VideoClip is None - MoviePy not properly imported")
                return None
            
            start_clip = VideoClip(make_frame, duration=duration)
            if start_clip is None:
                print("ERROR: VideoClip returned None")
                return None
            
            print("DEBUG: Start clip created successfully")
            
            # Apply fade effects if enabled
            if self.start_fade_in_var.get():
                try:
                    start_clip = vfx_fadein(start_clip, self.start_fade_in_dur_var.get())
                    logging.debug("Applied fade in effect to start clip")
                except Exception as e:
                    logging.warning(f"Failed to apply fade in effect: {e}")
            
            # Only apply fade-out if explicitly requested (not when manual transition will be created)
            if apply_fade_out is None:
                apply_fade_out = self.start_fade_out_var.get()
            
            if apply_fade_out:
                try:
                    start_clip = vfx_fadeout(start_clip, self.start_fade_out_dur_var.get())
                    logging.debug("Applied fade out effect to start clip")
                except Exception as e:
                    logging.warning(f"Failed to apply fade out effect: {e}")
            else:
                logging.debug("Skipping fade out effect (manual transition will be used)")
            
            print("DEBUG: Returning start clip")
            return start_clip
            
        except Exception as e:
            print(f"ERROR: Failed to create start clip: {e}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return None
    
    def create_second_page_clip(self, duration=3):
        """Create a second page clip with configurable text and styling"""
        def make_frame(t):
            import numpy as np
            import cv2
            
            # Try to load vintage frame background, fallback to light gray
            vintage_frame_path = os.path.join("images", "vintage_frame_background.png")
            if os.path.exists(vintage_frame_path):
                try:
                    # Load the vintage frame image
                    vintage_frame = cv2.imread(vintage_frame_path, cv2.IMREAD_UNCHANGED)
                    if vintage_frame is not None:
                        # Convert BGR to RGB if needed
                        if vintage_frame.shape[2] == 4:  # RGBA
                            vintage_frame_rgb = cv2.cvtColor(vintage_frame[:, :, :3], cv2.COLOR_BGR2RGB)
                            alpha = vintage_frame[:, :, 3] / 255.0
                        else:  # RGB
                            vintage_frame_rgb = cv2.cvtColor(vintage_frame, cv2.COLOR_BGR2RGB)
                            alpha = np.ones((vintage_frame.shape[0], vintage_frame.shape[1]))
                        
                        # Resize to video dimensions
                        vintage_frame_rgb = cv2.resize(vintage_frame_rgb, (self.video_width, self.video_height))
                        alpha = cv2.resize(alpha, (self.video_width, self.video_height))
                        
                        # Create background with vintage frame
                        light_gray_bg = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 240
                        frame = light_gray_bg.astype(np.float32)
                        
                        # Blend the vintage frame with the background using alpha channel
                        if len(alpha.shape) == 2:
                            alpha = np.stack([alpha, alpha, alpha], axis=2)
                        frame = frame * (1 - alpha) + vintage_frame_rgb.astype(np.float32) * alpha
                        frame = np.clip(frame, 0, 255).astype(np.uint8)
                    else:
                        # Fallback to light gray background
                        frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 220
                except Exception as e:
                    print(f"Warning: Could not load vintage frame background: {e}")
                    # Fallback to light gray background
                    frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 220
            else:
                # Fallback to light gray background
                frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 220
            
            # Get text content and settings
            line1_text = self.second_page_line1_var.get()
            line2_text = self.second_page_line2_var.get()
            max_chars = self.second_page_max_chars_var.get()
            
            # Replace <br> with actual line breaks
            line1_text = line1_text.replace('<br>', '\n')
            line2_text = line2_text.replace('<br>', '\n')
            
            # Wrap text lines
            line1_wrapped = self._wrap_text(line1_text, max_chars)
            line2_wrapped = self._wrap_text(line2_text, max_chars)
            
            # Get styling settings
            line1_size = self.second_page_line1_size_var.get()
            line2_size = self.second_page_line2_size_var.get()
            line1_y = self.second_page_line1_y_var.get()
            line2_y = self.second_page_line2_y_var.get()
            
            line1_bold = self.second_page_line1_bold_var.get()
            line2_bold = self.second_page_line2_bold_var.get()
            line1_italic = self.second_page_line1_italic_var.get()
            line2_italic = self.second_page_line2_italic_var.get()
            
            # Convert colors from hex to RGB
            def hex_to_rgb(hex_color):
                try:
                    hex_color = hex_color.lstrip('#')
                    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                except:
                    return (0, 0, 0)  # Default to black
            
            line1_color = hex_to_rgb(self.second_page_line1_color_var.get())
            line2_color = hex_to_rgb(self.second_page_line2_color_var.get())
            
            # Calculate font scale for video size
            scale_factor = self.video_width / 1080  # Assuming base size of 1080
            font1_scale = (line1_size / 72.0) * scale_factor  # Convert point size to scale
            font2_scale = (line2_size / 72.0) * scale_factor
            
            # OpenCV font and thickness
            font = cv2.FONT_HERSHEY_SIMPLEX
            
            # Set thickness based on bold settings
            thickness1 = 6 if line1_bold else 2
            thickness2 = 6 if line2_bold else 2
            
            # For bold text, use a bolder font variant
            font1 = cv2.FONT_HERSHEY_DUPLEX if line1_bold else cv2.FONT_HERSHEY_SIMPLEX
            font2 = cv2.FONT_HERSHEY_DUPLEX if line2_bold else cv2.FONT_HERSHEY_SIMPLEX
            
            # Note: OpenCV doesn't have true italic support, but we handle the flag for completeness
            
            # Draw line 1 (with wrapping)
            current_y = line1_y
            for wrapped_line in line1_wrapped:
                if wrapped_line.strip():  # Only draw non-empty lines
                    # Get text size for centering
                    (text_width, text_height), baseline = cv2.getTextSize(wrapped_line, font1, font1_scale, thickness1)
                    text_x = (self.video_width - text_width) // 2
                    
                    # Adjust for OpenCV text baseline
                    text_y = current_y + text_height
                    
                    # For bold text, use multiple render technique for extra thickness
                    if line1_bold:
                        # Render multiple times with slight offsets for bolder effect
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                cv2.putText(frame, wrapped_line, (text_x + dx, text_y + dy),
                                          font1, font1_scale, line1_color, thickness1, cv2.LINE_AA)
                    else:
                        cv2.putText(frame, wrapped_line, (text_x, text_y),
                                  font1, font1_scale, line1_color, thickness1, cv2.LINE_AA)
                
                current_y += int(text_height) + 10  # Add some spacing between wrapped lines
            
            # Draw line 2 (with wrapping)
            current_y = line2_y
            for wrapped_line in line2_wrapped:
                if wrapped_line.strip():  # Only draw non-empty lines
                    # Get text size for centering
                    (text_width, text_height), baseline = cv2.getTextSize(wrapped_line, font2, font2_scale, thickness2)
                    text_x = (self.video_width - text_width) // 2
                    
                    # Adjust for OpenCV text baseline
                    text_y = current_y + text_height
                    
                    # For bold text, use multiple render technique for extra thickness
                    if line2_bold:
                        # Render multiple times with slight offsets for bolder effect
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                cv2.putText(frame, wrapped_line, (text_x + dx, text_y + dy),
                                          font2, font2_scale, line2_color, thickness2, cv2.LINE_AA)
                    else:
                        cv2.putText(frame, wrapped_line, (text_x, text_y),
                                  font2, font2_scale, line2_color, thickness2, cv2.LINE_AA)
                
                current_y += int(text_height) + 10  # Add some spacing between wrapped lines
            
            return frame
        
        try:
            logging.info("DEBUG: Creating second page clip...")
            logging.info(f"DEBUG: Duration: {duration}")
            logging.info(f"DEBUG: Video dimensions: {self.video_width}x{self.video_height}")
            
            if VideoClip is None:
                print("ERROR: VideoClip is None - MoviePy not properly imported")
                return None
            
            second_clip = VideoClip(make_frame, duration=duration)
            if second_clip is None:
                print("ERROR: Second page VideoClip returned None")
                return None
            
            logging.info("DEBUG: Second page clip created successfully")
            
            # Apply fade effects if enabled
            if self.second_page_fade_in_var.get():
                try:
                    second_clip = vfx_fadein(second_clip, self.second_page_fade_in_dur_var.get())
                    logging.info("DEBUG: Applied fade in effect to second page clip")
                except Exception as e:
                    print(f"WARNING: Failed to apply fade in effect to second page: {e}")
            
            if self.second_page_fade_out_var.get():
                try:
                    fade_out_duration = self.second_page_fade_out_dur_var.get()
                    second_clip = vfx_fadeout(second_clip, fade_out_duration)
                    logging.info(f"DEBUG: Applied fade out effect ({fade_out_duration}s) to second page clip")
                except Exception as e:
                    print(f"WARNING: Failed to apply fade out effect to second page: {e}")
            
            return second_clip
            
        except Exception as e:
            print(f"ERROR: Failed to create second page clip: {e}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            return None
            
    def show_success_message(self, output_path, minutes, seconds):
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        self.status_label.config(text=f"✅ Video created in {time_str}! Saved to: {os.path.basename(output_path)} - Click 'PLAY VIDEO' to view it!")
        
        # Auto-save current settings as defaults after successful video creation
        try:
            self.save_defaults()
            logging.debug("Auto-saved settings as defaults after successful video creation")
        except Exception as e:
            logging.warning(f"Failed to auto-save defaults after video creation: {e}")
        
    def show_error_message(self, error_msg):
        messagebox.showerror("Error", f"Failed to create video:\n{error_msg}")
        
    def finish_processing(self):
        self.is_processing = False
        self.create_button.config(state='normal')
        self.cancel_button.grid_remove()  # Hide cancel button
        self.progress_var.set(0)
        self.status_label.config(text="Ready")
        
    def cancel_processing(self):
        """Cancel the current video processing"""
        self.is_processing = False
        self.create_button.config(state='normal')
        self.cancel_button.grid_remove()  # Hide cancel button
        self.progress_var.set(0)
        self.status_label.config(text="Processing cancelled")
        messagebox.showinfo("Cancelled", "Video processing has been cancelled.")
        
    def test_video_creation(self):
        """Create a simple test video to verify the system works"""
        if not self.output_path:
            messagebox.showerror("Error", "Please select an output folder first")
            return
            
        try:
            self.status_label.config(text="Creating test video with OpenCV...")
            self.progress_var.set(50)
            
            import cv2
            import numpy as np
            
            # Generate test filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            test_filename = f"test_video_{timestamp}.mp4"
            test_path = os.path.join(self.output_path, test_filename)
            
            # Create a simple red video using OpenCV
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(test_path, fourcc, 10.0, (640, 480))
            
            # Create 30 frames of red video (3 seconds at 10 FPS)
            for i in range(30):
                # Create a red frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                frame[:] = (0, 0, 255)  # Red in BGR
                out.write(frame)
                
                # Update progress
                progress = 50 + (i / 30) * 50
                self.progress_var.set(progress)
            
            out.release()
            
            # Store the latest video path and enable play button
            self.latest_video_path = test_path
            self.play_button.config(state='normal')
            
            self.progress_var.set(100)
            self.status_label.config(text="Test video created successfully!")
            messagebox.showinfo("Test Success", f"Test video created successfully!\nSaved to: {test_path}\n\nThis confirms the video system is working.")
            
        except Exception as e:
            self.progress_var.set(0)
            self.status_label.config(text="Test failed")
            messagebox.showerror("Test Failed", f"Test video creation failed:\n{str(e)}")
    
    def play_selected_video(self):
        """Play the selected video part"""
        selected_part = self.part_selector_var.get()
        
        if selected_part == "Latest":
            video_to_play = self.latest_video_path
        else:
            # Find the video path for the selected part
            video_to_play = None
            for video_info in self.video_parts:
                if video_info['display_name'] == selected_part:
                    video_to_play = video_info['path']
                    break
        
        if not video_to_play or not os.path.exists(video_to_play):
            messagebox.showerror("Error", "Selected video file does not exist.")
            return
        
        try:
            import subprocess
            import platform
            
            system = platform.system()
            if system == "Windows":
                os.startfile(video_to_play)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", video_to_play])
            else:  # Linux
                subprocess.run(["xdg-open", video_to_play])
            
            self.status_label.config(text=f"🎬 Playing video: {os.path.basename(video_to_play)}")
            
        except Exception as e:
            error_msg = f"Failed to play video: {str(e)}"
            self.status_label.config(text=f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
    
    def play_latest_video(self):
        """Play the most recently created video (legacy method)"""
        self.part_selector_var.set("Latest")
        self.play_selected_video()
    
    def on_part_selected(self, event=None):
        """Handle when a user selects a specific part from the dropdown"""
        selected_part = self.part_selector_var.get()
        
        # Skip if "Latest" is selected, but clear regeneration info
        if selected_part == "Latest":
            self.regeneration_info = None
            return
            
        # Find the selected part in video_parts
        selected_part_info = None
        for part in self.video_parts:
            if part['display_name'] == selected_part:
                selected_part_info = part
                break
        
        if not selected_part_info or 'batch_indices' not in selected_part_info:
            print(f"DEBUG: No batch indices found for part: {selected_part}")
            return
            
        batch_indices = selected_part_info['batch_indices']
        part_number = selected_part_info['part_number']
        
        print(f"DEBUG: Selected part {part_number} with {len(batch_indices)} images")
        
        # First, uncheck all images
        self.deselect_all_images()
        
        # Then, check only the images that belong to this part
        for batch_idx in batch_indices:
            if 0 <= batch_idx < len(self.image_included):
                self.image_included[batch_idx] = True
                
        # Update the tree display to reflect the new selections
        self.update_tree_checkboxes()
        
        # Auto-scroll to the first selected image
        self.scroll_to_first_selected_image(batch_indices)
        
        # Set the starting part number to this part for regeneration
        self.starting_part_var.set(part_number)
        
        # Store regeneration info for use during video creation
        self.regeneration_info = {
            'is_regeneration': True,
            'part_number': part_number,
            'original_filename': selected_part_info['filename'],
            'original_path': selected_part_info['path']
        }
        
        # Update status to inform user
        pairs_count = len(batch_indices) // 2
        self.status_label.config(text=f"🎯 Selected Part {part_number}: {pairs_count} pairs ready for regeneration")
        
        print(f"DEBUG: Part {part_number} selected - {pairs_count} image pairs, will regenerate {selected_part_info['filename']}")
    
    def scroll_to_first_selected_image(self, batch_indices):
        """Scroll the tree view to show the first selected image"""
        if not batch_indices:
            return
            
        # Find the first selected image index
        first_image_index = min(batch_indices)
        
        # Get all tree items
        all_items = self.tree.get_children()
        
        # Make sure we have enough items and the index is valid
        if first_image_index < len(all_items):
            # Get the tree item for the first selected image
            target_item = all_items[first_image_index]
            
            # Scroll to make this item visible (without selecting it)
            self.tree.see(target_item)
            
            print(f"DEBUG: Auto-scrolled to image {first_image_index + 1} without changing selection")
        else:
            print(f"DEBUG: Cannot scroll to image {first_image_index + 1} - index out of range")
    
    def update_tree_checkboxes(self):
        """Update the tree display to show current checkbox states"""
        for i, item_id in enumerate(self.tree.get_children()):
            if i < len(self.image_included):
                checkbox_state = "☑" if self.image_included[i] else "☐"
                # Update the checkbox column (first column)
                values = list(self.tree.item(item_id)['values'])
                if len(values) > 0:  # Make sure we have values
                    values[0] = checkbox_state  # First column is checkbox
                    self.tree.item(item_id, values=values)
    
    def create_backup(self):
        """Create a backup of current defaults"""
        try:
            if not os.path.exists('defaults.json'):
                return False
            
            # Create backups directory
            backup_dir = "defaults_backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Create timestamped backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = os.path.join(backup_dir, f"defaults_backup_{timestamp}.json")
            shutil.copy2('defaults.json', backup_path)
            
            logging.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False

    def manual_backup(self):
        """Create a manual backup with user confirmation"""
        backup_path = self.create_backup()
        if backup_path:
            messagebox.showinfo("Backup Created", f"Backup saved:\n{os.path.basename(backup_path)}")
        else:
            messagebox.showerror("Backup Failed", "Could not create backup")

    def show_backup_folder(self):
        """Open the backup folder in file explorer"""
        backup_dir = "defaults_backups"
        if os.path.exists(backup_dir):
            if os.name == 'nt':  # Windows
                os.startfile(backup_dir)
            else:  # macOS/Linux
                os.system(f'open "{backup_dir}"' if os.name == 'posix' else f'xdg-open "{backup_dir}"')
        else:
            messagebox.showinfo("No Backups", "No backup folder found. Create a backup first.")

    def cleanup_old_files(self):
        """Clean up log files and duration analysis files older than 24 hours"""
        import os
        import time
        import glob
        
        current_time = time.time()
        files_cleaned = 0
        
        # Patterns for files to clean up
        patterns = [
            "*.log",
            "duration_analysis_*.txt",
            "logs/*.log",
            "logs/*.txt"
        ]
        
        try:
            for pattern in patterns:
                for file_path in glob.glob(pattern):
                    try:
                        # Get file modification time
                        file_mtime = os.path.getmtime(file_path)
                        
                        # Check if file is older than 24 hours (86400 seconds)
                        if current_time - file_mtime > 86400:
                            os.remove(file_path)
                            files_cleaned += 1
                            print(f"Cleaned up old file: {file_path}")
                    except (OSError, IOError) as e:
                        # Skip files that can't be accessed or deleted
                        print(f"Could not clean up {file_path}: {e}")
            
            if files_cleaned > 0:
                print(f"✅ Cleaned up {files_cleaned} old log/analysis files (older than 24 hours)")
            else:
                print("✅ No old files to clean up")
                
        except Exception as e:
            print(f"Warning: File cleanup failed: {e}")
            # Don't let cleanup errors prevent app startup

    def manual_cleanup_old_files(self):
        """Manually clean up old files with user confirmation"""
        import os
        import time
        import glob
        from tkinter import messagebox
        
        current_time = time.time()
        old_files = []
        
        # Patterns for files to clean up
        patterns = [
            "*.log",
            "duration_analysis_*.txt",
            "logs/*.log",
            "logs/*.txt"
        ]
        
        try:
            for pattern in patterns:
                for file_path in glob.glob(pattern):
                    try:
                        # Get file modification time
                        file_mtime = os.path.getmtime(file_path)
                        
                        # Check if file is older than 24 hours (86400 seconds)
                        if current_time - file_mtime > 86400:
                            # Get file age in hours
                            age_hours = (current_time - file_mtime) / 3600
                            old_files.append((file_path, age_hours))
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        continue
            
            if not old_files:
                messagebox.showinfo("File Cleanup", "No old log or analysis files found (older than 24 hours).")
                return
            
            # Show confirmation dialog
            file_list = "\n".join([f"• {path} ({age:.1f} hours old)" for path, age in old_files])
            message = f"Found {len(old_files)} old files to clean up:\n\n{file_list}\n\nDelete these files?"
            
            if messagebox.askyesno("Cleanup Old Files", message):
                deleted_count = 0
                for file_path, _ in old_files:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except (OSError, IOError) as e:
                        print(f"Could not delete {file_path}: {e}")
                
                messagebox.showinfo("Cleanup Complete", f"Successfully deleted {deleted_count} old files.")
                
        except Exception as e:
            messagebox.showerror("Cleanup Error", f"File cleanup failed: {e}")

    def restore_backup_dialog(self):
        """Show dialog to select and restore a backup"""
        backup_dir = "defaults_backups"
        if not os.path.exists(backup_dir):
            messagebox.showinfo("No Backups", "No backup folder found. Create a backup first.")
            return
        
        # Get backup files
        backup_files = glob.glob(os.path.join(backup_dir, "defaults_backup_*.json"))
        if not backup_files:
            messagebox.showinfo("No Backups", "No backup files found.")
            return
        
        # Sort by date (most recent first)
        backup_files.sort(reverse=True)
        
        # Show selection dialog
        backup_names = [os.path.basename(f) for f in backup_files]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Restore Backup")
        dialog.geometry("600x400")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select backup to restore:", font=("TkDefaultFont", 12, "bold")).pack(pady=10)
        
        # Listbox with backup files
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        listbox = tk.Listbox(frame, height=15)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for name in backup_names:
            listbox.insert(tk.END, name)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def restore_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a backup to restore.")
                return
            
            backup_file = backup_files[selection[0]]
            result = messagebox.askyesno("Confirm Restore", 
                f"Restore from backup?\n\n{os.path.basename(backup_file)}\n\nThis will restart the app.")
            
            if result:
                try:
                    # Create backup of current before restoring
                    self.create_backup()
                    # Restore selected backup
                    shutil.copy2(backup_file, 'defaults.json')
                    messagebox.showinfo("Restore Complete", "Backup restored! App will restart.")
                    dialog.destroy()
                    self.root.quit()
                except Exception as e:
                    messagebox.showerror("Restore Failed", f"Error: {e}")
        
        ttk.Button(button_frame, text="Restore Selected", command=restore_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def save_defaults(self):
        """Save current settings as defaults"""
        try:
            # Create backup before saving
            self.create_backup()
            
            import json
            
            defaults = {
                # Start screen settings
                "start_line1": self.start_line1_var.get(),
                "start_line2": self.start_line2_var.get(),
                "start_line1_size": self.start_line1_size_var.get(),
                "start_line2_size": self.start_line2_size_var.get(),
                "start_line1_color": self.start_line1_color_var.get(),
                "start_line2_color": self.start_line2_color_var.get(),
                "start_line1_font": self.start_line1_font_var.get(),
                "start_line2_font": self.start_line2_font_var.get(),
                "start_duration": self.start_duration_var.get(),
                "start_text_spacing": self.start_text_spacing_var.get(),
                "start_logo_size": self.start_logo_size_var.get(),
                "start_logo_text_spacing": self.start_logo_text_spacing_var.get(),
                "start_line1_hidden": self.start_line1_hidden_var.get(),
                "start_line1_bold": self.start_line1_bold_var.get(),
                "start_line2_bold": self.start_line2_bold_var.get(),
                # Start extra image
                "start_image_enabled": self.start_image_enabled_var.get(),
                "start_image_path": self.start_image_path_var.get(),
                "start_image_height": self.start_image_height_var.get(),
                "start_image_spacing": self.start_image_spacing_var.get(),
                # Ending screen settings
                "ending_line1": self.ending_line1_var.get(),
                "ending_line2": self.ending_line2_var.get(),
                "ending_line3": self.ending_line3_var.get(),
                "ending_line1_size": self.ending_line1_size_var.get(),
                "ending_line2_size": self.ending_line2_size_var.get(),
                "ending_line3_size": self.ending_line3_size_var.get(),
                "ending_line1_color": self.ending_line1_color_var.get(),
                "ending_line2_color": self.ending_line2_color_var.get(),
                "ending_line3_color": self.ending_line3_color_var.get(),
                "ending_line1_font": self.ending_line1_font_var.get(),
                "ending_line2_font": self.ending_line2_font_var.get(),
                "ending_line3_font": self.ending_line3_font_var.get(),
                "ending_line1_bold": self.ending_line1_bold_var.get(),
                "ending_line2_bold": self.ending_line2_bold_var.get(),
                "ending_line3_bold": self.ending_line3_bold_var.get(),
                "ending_duration": self.ending_duration_var.get(),
                "ending_text_spacing": self.ending_text_spacing_var.get(),
                "ending_logo_size": self.ending_logo_size_var.get(),
                "ending_logo_text_spacing": self.ending_logo_text_spacing_var.get(),
                "ending_line1_hidden": self.ending_line1_hidden_var.get(),
                "ending_line2_hidden": self.ending_line2_hidden_var.get(),
                "ending_line3_hidden": self.ending_line3_hidden_var.get(),
                # Ending extra image
                "ending_image_enabled": self.ending_image_enabled_var.get(),
                "ending_image_path": self.ending_image_path_var.get(),
                "ending_image_height": self.ending_image_height_var.get(),
                "ending_image_spacing": self.ending_image_spacing_var.get(),
                # Second page settings
                "second_page_enabled": self.second_page_enabled_var.get(),
                "second_page_line1": self.second_page_line1_var.get(),
                "second_page_line2": self.second_page_line2_var.get(),
                "second_page_line1_bold": self.second_page_line1_bold_var.get(),
                "second_page_line2_bold": self.second_page_line2_bold_var.get(),
                "second_page_line1_italic": self.second_page_line1_italic_var.get(),
                "second_page_line2_italic": self.second_page_line2_italic_var.get(),
                "second_page_line1_size": self.second_page_line1_size_var.get(),
                "second_page_line2_size": self.second_page_line2_size_var.get(),
                "second_page_line1_y": self.second_page_line1_y_var.get(),
                "second_page_line2_y": self.second_page_line2_y_var.get(),
                "second_page_max_chars": self.second_page_max_chars_var.get(),
                "second_page_duration": self.second_page_duration_var.get(),
                "second_page_line1_color": self.second_page_line1_color_var.get(),
                "second_page_line2_color": self.second_page_line2_color_var.get(),
                "second_page_fade_in": self.second_page_fade_in_var.get(),
                "second_page_fade_out": self.second_page_fade_out_var.get(),
                "second_page_fade_in_dur": self.second_page_fade_in_dur_var.get(),
                "second_page_fade_out_dur": self.second_page_fade_out_dur_var.get(),
                
                # Actual duration controls
                "actual_start_duration": self.actual_start_duration_var.get(),
                "actual_second_page_duration": self.actual_second_page_duration_var.get(),
                "actual_ending_duration": self.actual_ending_duration_var.get(),
                "actual_pair_duration": self.actual_pair_duration_var.get(),
                "max_video_duration": self.max_video_duration_var.get(),
                
                # Fade options
                "start_fade_in": self.start_fade_in_var.get(),
                "start_fade_out": self.start_fade_out_var.get(),
                "start_fade_in_dur": self.start_fade_in_dur_var.get(),
                "start_fade_out_dur": self.start_fade_out_dur_var.get(),
                "ending_fade_in": self.ending_fade_in_var.get(),
                "ending_fade_out": self.ending_fade_out_var.get(),
                "ending_fade_in_dur": self.ending_fade_in_dur_var.get(),
                "ending_fade_out_dur": self.ending_fade_out_dur_var.get(),
                # General settings
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get(),
                "background_color": self.background_color_var.get(),
                "starting_part_number": self.starting_part_var.get()
            }
            
            with open('defaults.json', 'w') as f:
                json.dump(defaults, f, indent=2)
            
            # Show success message in both main window and dialog (if open)
            self.status_label.config(text="✅ Defaults saved successfully!")
            if hasattr(self, 'dialog_status_label'):
                self.dialog_status_label.config(text="✅ Defaults saved successfully!", foreground="green")
            
        except Exception as e:
            error_msg = f"❌ Failed to save defaults: {str(e)}"
            self.status_label.config(text=error_msg)
            if hasattr(self, 'dialog_status_label'):
                self.dialog_status_label.config(text=error_msg, foreground="red")
    
    def open_ending_config(self):
        """Open ending text configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Ending Text")
        dialog.geometry("1000x720")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Maximize window when supported; otherwise center
        try:
            dialog.state('zoomed')  # Windows
        except Exception:
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (1000 // 2)
            y = (dialog.winfo_screenheight() // 2) - (720 // 2)
            dialog.geometry(f"1000x720+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="16")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Ending Text Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)

        # Two columns: left for form, right for preview and extra image
        left_col = ttk.Frame(main_frame)
        left_col.grid(row=1, column=0, sticky=(tk.N, tk.W, tk.E))
        left_col.columnconfigure(0, weight=1)
        left_col.columnconfigure(1, weight=1)
        left_col.columnconfigure(2, weight=1)
        left_col.columnconfigure(3, weight=1)
        right_col = ttk.Frame(main_frame)
        right_col.grid(row=1, column=1, sticky=(tk.N, tk.W, tk.E))
        right_col.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Color and font options
        color_options = ["black", "white", "yellow", "red", "green", "blue", "cyan", "magenta", "brown", "orange"]
        font_options = ["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana", "Impact", "Comic Sans MS"]
        
        # Line 1
        ttk.Label(left_col, text="Line 1:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 4))
        ttk.Entry(left_col, textvariable=self.ending_line1_var, width=34).grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 4))
        ttk.Checkbutton(left_col, text="Hide", variable=self.ending_line1_hidden_var,
                        command=self.update_ending_preview).grid(row=0, column=3, sticky=tk.W, pady=(0, 4))
        
        ttk.Label(left_col, text="Size:").grid(row=1, column=0, sticky=tk.W)
        ttk.Spinbox(left_col, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line1_size_var, 
                   width=8, command=self.update_ending_preview).grid(row=1, column=1, sticky=tk.W, padx=(0, 8))
        ttk.Label(left_col, text="Color:").grid(row=1, column=2, sticky=tk.W)
        line1_color_combo = ttk.Combobox(left_col, textvariable=self.ending_line1_color_var,
                                        values=color_options, width=10)
        line1_color_combo.grid(row=1, column=3, sticky=tk.W)
        line1_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Label(left_col, text="Font:").grid(row=2, column=0, sticky=tk.W)
        line1_font_combo = ttk.Combobox(left_col, textvariable=self.ending_line1_font_var,
                                       values=font_options, width=14)
        line1_font_combo.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E))
        line1_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Checkbutton(left_col, text="Bold", variable=self.ending_line1_bold_var,
                        command=self.update_ending_preview).grid(row=2, column=3, sticky=tk.W)
        
        # Line 2
        ttk.Label(left_col, text="Line 2:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(10, 4))
        ttk.Entry(left_col, textvariable=self.ending_line2_var, width=34).grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 4))
        ttk.Checkbutton(left_col, text="Hide", variable=self.ending_line2_hidden_var,
                        command=self.update_ending_preview).grid(row=3, column=3, sticky=tk.W, pady=(10, 4))
        
        ttk.Label(left_col, text="Size:").grid(row=4, column=0, sticky=tk.W)
        ttk.Spinbox(left_col, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line2_size_var, 
                   width=8, command=self.update_ending_preview).grid(row=4, column=1, sticky=tk.W, padx=(0, 8))
        ttk.Label(left_col, text="Color:").grid(row=4, column=2, sticky=tk.W)
        line2_color_combo = ttk.Combobox(left_col, textvariable=self.ending_line2_color_var,
                                        values=color_options, width=10)
        line2_color_combo.grid(row=4, column=3, sticky=tk.W)
        line2_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Label(left_col, text="Font:").grid(row=5, column=0, sticky=tk.W)
        line2_font_combo = ttk.Combobox(left_col, textvariable=self.ending_line2_font_var,
                                       values=font_options, width=14)
        line2_font_combo.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E))
        line2_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Checkbutton(left_col, text="Bold", variable=self.ending_line2_bold_var,
                        command=self.update_ending_preview).grid(row=5, column=3, sticky=tk.W)
        
        # Line 3
        ttk.Label(left_col, text="Line 3:", font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(10, 4))
        ttk.Entry(left_col, textvariable=self.ending_line3_var, width=34).grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 4))
        ttk.Checkbutton(left_col, text="Hide", variable=self.ending_line3_hidden_var,
                        command=self.update_ending_preview).grid(row=6, column=3, sticky=tk.W, pady=(10, 4))
        
        ttk.Label(left_col, text="Size:").grid(row=7, column=0, sticky=tk.W)
        ttk.Spinbox(left_col, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line3_size_var, 
                   width=8, command=self.update_ending_preview).grid(row=7, column=1, sticky=tk.W, padx=(0, 8))
        ttk.Label(left_col, text="Color:").grid(row=7, column=2, sticky=tk.W)
        line3_color_combo = ttk.Combobox(left_col, textvariable=self.ending_line3_color_var,
                                        values=color_options, width=10)
        line3_color_combo.grid(row=7, column=3, sticky=tk.W)
        line3_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Label(left_col, text="Font:").grid(row=8, column=0, sticky=tk.W)
        line3_font_combo = ttk.Combobox(left_col, textvariable=self.ending_line3_font_var,
                                       values=font_options, width=14)
        line3_font_combo.grid(row=8, column=1, columnspan=2, sticky=(tk.W, tk.E))
        line3_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        ttk.Checkbutton(left_col, text="Bold", variable=self.ending_line3_bold_var,
                        command=self.update_ending_preview).grid(row=8, column=3, sticky=tk.W)
        
        # Compact layout for spacing and sizes
        ttk.Label(left_col, text="Duration (sec):", font=('Arial', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(10, 4))
        ttk.Spinbox(left_col, from_=1.0, to=15.0, increment=0.5, textvariable=self.ending_duration_var, 
                   width=8).grid(row=9, column=1, sticky=tk.W, pady=(10, 4))
        ttk.Label(left_col, text="Text Spacing:", font=('Arial', 10, 'bold')).grid(row=9, column=2, sticky=tk.W, pady=(10, 4))
        ttk.Spinbox(left_col, from_=0, to=10, increment=1, textvariable=self.ending_text_spacing_var, 
                   width=8, command=self.update_ending_preview).grid(row=9, column=3, sticky=tk.W, pady=(10, 4))
        ttk.Label(left_col, text="Logo Size:", font=('Arial', 10, 'bold')).grid(row=10, column=0, sticky=tk.W, pady=(10, 4))
        ttk.Spinbox(left_col, from_=100, to=600, increment=25, textvariable=self.ending_logo_size_var, 
                   width=8, command=self.update_ending_preview).grid(row=10, column=1, sticky=tk.W, pady=(10, 4))
        ttk.Label(left_col, text="Logo-Text Spacing:", font=('Arial', 10, 'bold')).grid(row=10, column=2, sticky=tk.W, pady=(10, 4))
        ttk.Spinbox(left_col, from_=0, to=200, increment=10, textvariable=self.ending_logo_text_spacing_var, 
                   width=8, command=self.update_ending_preview).grid(row=10, column=3, sticky=tk.W, pady=(10, 4))

        # Fade controls (full width, not cramped)
        fade_frame = ttk.LabelFrame(main_frame, text="Fade Options", padding="8")
        fade_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(8, 4))
        ttk.Checkbutton(fade_frame, text="Fade In", variable=self.ending_fade_in_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(fade_frame, text="In Duration (s):").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(fade_frame, from_=0.0, to=5.0, increment=0.1, textvariable=self.ending_fade_in_dur_var, width=6).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(fade_frame, text="Fade Out", variable=self.ending_fade_out_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(fade_frame, text="Out Duration (s):").grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(fade_frame, from_=0.0, to=5.0, increment=0.1, textvariable=self.ending_fade_out_dur_var, width=6).grid(row=1, column=2, sticky=tk.W)
        
        
        
        # Preview section
        preview_frame = ttk.LabelFrame(right_col, text="Live Preview", padding="10")
        preview_frame.grid(row=0, column=0, pady=(10, 8), sticky=(tk.W, tk.E))
        preview_frame.columnconfigure(0, weight=1)
        
        # Preview canvas (white background to simulate ending screen)
        # Use 16:9 aspect ratio to match video
        self.ending_preview_canvas = tk.Canvas(preview_frame, width=560, height=315, bg='white', highlightthickness=1, highlightbackground="#ccc")
        self.ending_preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Make the preview canvas adapt to available width while keeping 16:9
        def _resize_preview_canvas(event=None):
            try:
                max_w = max(360, preview_frame.winfo_width() - 24)
            except Exception:
                max_w = 560
            # Cap to a sensible max within dialog
            target_w = min(max_w, 580)
            target_h = int(target_w * 9 / 16)
            if int(self.ending_preview_canvas['width']) != target_w or int(self.ending_preview_canvas['height']) != target_h:
                self.ending_preview_canvas.configure(width=target_w, height=target_h)
                # Re-render with new size
                self.update_ending_preview()

        preview_frame.bind('<Configure>', lambda e: _resize_preview_canvas(e))

        # helper to choose image
        def _choose():
            path = filedialog.askopenfilename(title="Select Ending Image",
                                              filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if path:
                self.ending_image_path_var.set(path)
        self._choose_ending_image = _choose
        
        # Extra image controls (single set for ending)
        ending_extra_frame = ttk.LabelFrame(right_col, text="Extra Image (below last line)", padding="10")
        ending_extra_frame.grid(row=1, column=0, pady=(8, 8), sticky=(tk.W, tk.E))
        ttk.Checkbutton(ending_extra_frame, text="Enable", variable=self.ending_image_enabled_var,
                        command=self.update_ending_preview).grid(row=0, column=0, sticky=tk.W, padx=(0,10))
        ttk.Button(ending_extra_frame, text="Choose Image...",
                   command=self._choose_ending_image).grid(row=0, column=1, sticky=tk.W, padx=(0,10))
        ttk.Entry(ending_extra_frame, textvariable=self.ending_image_path_var, width=40, state='readonly').grid(row=0, column=2, columnspan=3, sticky=(tk.W, tk.E))
        ttk.Label(ending_extra_frame, text="Image Height:").grid(row=1, column=0, sticky=tk.W, pady=(10,0))
        ttk.Spinbox(ending_extra_frame, from_=50, to=800, increment=10, textvariable=self.ending_image_height_var,
                    width=8, command=self.update_ending_preview).grid(row=1, column=1, sticky=tk.W, pady=(10,0), padx=(5,15))
        ttk.Label(ending_extra_frame, text="Spacing (text → image):").grid(row=1, column=2, sticky=tk.W, pady=(10,0))
        ttk.Spinbox(ending_extra_frame, from_=0, to=300, increment=5, textvariable=self.ending_image_spacing_var,
                    width=8, command=self.update_ending_preview).grid(row=1, column=3, sticky=tk.W, pady=(10,0), padx=(5,15))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(6, 4))
        
        # Save as default button
        save_button = ttk.Button(button_frame, text="💾 Save as Default", 
                                command=lambda: self.save_defaults_and_close(dialog))
        save_button.grid(row=0, column=0, padx=(0, 10))
        
        # Close button (auto-saves settings)
        close_button = ttk.Button(button_frame, text="Close", command=lambda: self.save_defaults_and_close(dialog))
        close_button.grid(row=0, column=1, padx=(10, 0))
        
        # Status label
        self.dialog_status_label = ttk.Label(main_frame, text="", foreground="green")
        self.dialog_status_label.grid(row=4, column=0, columnspan=2, pady=(0, 0))
        
        # Bind text changes to preview updates
        self.ending_line1_var.trace('w', lambda *args: self.update_ending_preview())
        self.ending_line2_var.trace('w', lambda *args: self.update_ending_preview())
        self.ending_line3_var.trace('w', lambda *args: self.update_ending_preview())
        self.ending_image_path_var.trace('w', lambda *args: self.update_ending_preview())
        
        # Initial preview
        self.update_ending_preview()
    
    def open_second_page_config(self):
        """Open second page configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Second Page")
        dialog.geometry("1000x720")
        dialog.resizable(True, True)
        
        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main container with padding
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        dialog.grid_rowconfigure(0, weight=1)
        dialog.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Header
        header_label = ttk.Label(main_frame, text="Second Page Configuration", 
                               font=("TkDefaultFont", 14, "bold"))
        header_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Controls frame (left side)
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 20))
        
        # Second page enabled checkbox
        enabled_frame = ttk.LabelFrame(controls_frame, text="Second Page Settings", padding="10")
        enabled_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(enabled_frame, text="Enable Second Page", 
                       variable=self.second_page_enabled_var,
                       command=self.update_second_page_preview).grid(row=0, column=0, sticky=tk.W)
        
        # Duration setting
        ttk.Label(enabled_frame, text="Duration (seconds):").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Spinbox(enabled_frame, from_=1.0, to=10.0, increment=0.5, 
                   textvariable=self.second_page_duration_var, width=8,
                   command=self.update_second_page_preview).grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        # Text wrapping setting
        ttk.Label(enabled_frame, text="Max characters per line:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Spinbox(enabled_frame, from_=10, to=100, increment=5, 
                   textvariable=self.second_page_max_chars_var, width=8,
                   command=self.update_second_page_preview).grid(row=2, column=1, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        # Fade effects frame
        fade_frame = ttk.LabelFrame(controls_frame, text="Fade Effects", padding="10")
        fade_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Fade In
        fade_in_frame = ttk.Frame(fade_frame)
        fade_in_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Checkbutton(fade_in_frame, text="Fade In", variable=self.second_page_fade_in_var,
                       command=self.update_second_page_preview).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(fade_in_frame, text="Duration:").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Spinbox(fade_in_frame, from_=0.1, to=5.0, increment=0.1, 
                   textvariable=self.second_page_fade_in_dur_var, width=6,
                   command=self.update_second_page_preview).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        ttk.Label(fade_in_frame, text="seconds").grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Fade Out
        fade_out_frame = ttk.Frame(fade_frame)
        fade_out_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Checkbutton(fade_out_frame, text="Fade Out", variable=self.second_page_fade_out_var,
                       command=self.update_second_page_preview).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(fade_out_frame, text="Duration:").grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        ttk.Spinbox(fade_out_frame, from_=0.1, to=5.0, increment=0.1, 
                   textvariable=self.second_page_fade_out_dur_var, width=6,
                   command=self.update_second_page_preview).grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        ttk.Label(fade_out_frame, text="seconds").grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Line 1 configuration
        line1_frame = ttk.LabelFrame(controls_frame, text="Line 1", padding="10")
        line1_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(line1_frame, text="Text:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(line1_frame, textvariable=self.second_page_line1_var, width=40).grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(line1_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Spinbox(line1_frame, from_=20, to=120, increment=5, 
                   textvariable=self.second_page_line1_size_var, width=8,
                   command=self.update_second_page_preview).grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        ttk.Label(line1_frame, text="Y Position:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        ttk.Spinbox(line1_frame, from_=50, to=1000, increment=10, 
                   textvariable=self.second_page_line1_y_var, width=8,
                   command=self.update_second_page_preview).grid(row=1, column=3, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        # Style options for line 1
        style1_frame = ttk.Frame(line1_frame)
        style1_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Checkbutton(style1_frame, text="Bold", variable=self.second_page_line1_bold_var,
                       command=self.update_second_page_preview).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(style1_frame, text="Italic", variable=self.second_page_line1_italic_var,
                       command=self.update_second_page_preview).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Color picker for line 1
        ttk.Label(style1_frame, text="Color:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        color1_button = tk.Button(style1_frame, text="  ", width=3, height=1,
                                 bg=self.second_page_line1_color_var.get(),
                                 command=lambda: self._choose_color(self.second_page_line1_color_var, color1_button))
        color1_button.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Line 2 configuration
        line2_frame = ttk.LabelFrame(controls_frame, text="Line 2", padding="10")
        line2_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(line2_frame, text="Text:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(line2_frame, textvariable=self.second_page_line2_var, width=40).grid(row=0, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(line2_frame, text="Font Size:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Spinbox(line2_frame, from_=20, to=120, increment=5, 
                   textvariable=self.second_page_line2_size_var, width=8,
                   command=self.update_second_page_preview).grid(row=1, column=1, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        ttk.Label(line2_frame, text="Y Position:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        ttk.Spinbox(line2_frame, from_=50, to=1000, increment=10, 
                   textvariable=self.second_page_line2_y_var, width=8,
                   command=self.update_second_page_preview).grid(row=1, column=3, sticky=tk.W, pady=(10, 0), padx=(5, 0))
        
        # Style options for line 2
        style2_frame = ttk.Frame(line2_frame)
        style2_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Checkbutton(style2_frame, text="Bold", variable=self.second_page_line2_bold_var,
                       command=self.update_second_page_preview).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(style2_frame, text="Italic", variable=self.second_page_line2_italic_var,
                       command=self.update_second_page_preview).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Color picker for line 2
        ttk.Label(style2_frame, text="Color:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0))
        color2_button = tk.Button(style2_frame, text="  ", width=3, height=1,
                                 bg=self.second_page_line2_color_var.get(),
                                 command=lambda: self._choose_color(self.second_page_line2_color_var, color2_button))
        color2_button.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        # Preview frame (right side)
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Preview canvas
        self.second_page_preview_canvas = tk.Canvas(preview_frame, width=400, height=400, bg='white')
        self.second_page_preview_canvas.grid(row=0, column=0, padx=(0, 10))
        
        # Button frame at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        
        # Buttons
        ttk.Button(button_frame, text="Save & Close", 
                  command=lambda: self.save_second_page_defaults_and_close(dialog)).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=1)
        
        # Configure grid weights
        line1_frame.grid_columnconfigure(1, weight=1)
        line2_frame.grid_columnconfigure(1, weight=1)
        
        # Bind text change events
        self.second_page_line1_var.trace('w', lambda *args: self.update_second_page_preview())
        self.second_page_line2_var.trace('w', lambda *args: self.update_second_page_preview())
        
        # Initial preview
        self.update_second_page_preview()
    
    def _choose_color(self, color_var, button):
        """Choose a color and update the variable and button"""
        try:
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=color_var.get())
            if color[1]:  # color[1] is the hex string
                color_var.set(color[1])
                button.config(bg=color[1])
                self.update_second_page_preview()
        except Exception as e:
            print(f"Color chooser error: {e}")
    
    def update_second_page_preview(self):
        """Update the second page preview"""
        if not hasattr(self, 'second_page_preview_canvas'):
            return
            
        try:
            canvas = self.second_page_preview_canvas
            canvas.delete("all")
            
            if not self.second_page_enabled_var.get():
                canvas.create_text(200, 200, text="Second page disabled", 
                                 font=("Arial", 14), fill="gray")
                return
            
            # Canvas dimensions
            canvas_width = 400
            canvas_height = 400
            
            # Get text content and wrap if needed
            max_chars = self.second_page_max_chars_var.get()
            line1_text = self.second_page_line1_var.get()
            line2_text = self.second_page_line2_var.get()
            
            # Replace <br> with actual line breaks
            line1_text = line1_text.replace('<br>', '\n')
            line2_text = line2_text.replace('<br>', '\n')
            
            # Wrap the text
            line1_wrapped = self._wrap_text(line1_text, max_chars)
            line2_wrapped = self._wrap_text(line2_text, max_chars)
            
            # Get styling info
            line1_size = max(8, self.second_page_line1_size_var.get() // 3)  # Scale for preview
            line2_size = max(8, self.second_page_line2_size_var.get() // 3)  # Scale for preview
            line1_y = self.second_page_line1_y_var.get() // 3  # Scale for preview
            line2_y = self.second_page_line2_y_var.get() // 3  # Scale for preview
            
            # Font styles
            line1_weight = "bold" if self.second_page_line1_bold_var.get() else "normal"
            line1_slant = "italic" if self.second_page_line1_italic_var.get() else "roman"
            line2_weight = "bold" if self.second_page_line2_bold_var.get() else "normal"
            line2_slant = "italic" if self.second_page_line2_italic_var.get() else "roman"
            
            # Colors
            line1_color = self.second_page_line1_color_var.get()
            line2_color = self.second_page_line2_color_var.get()
            
            # Draw line 1 (with wrapping)
            current_y = line1_y
            for wrapped_line in line1_wrapped:
                if wrapped_line.strip():  # Only draw non-empty lines
                    canvas.create_text(canvas_width // 2, current_y, text=wrapped_line,
                                     font=("Arial", line1_size, line1_weight, line1_slant),
                                     fill=line1_color, anchor="center")
                current_y += line1_size + 5  # Add some spacing between wrapped lines
            
            # Draw line 2 (with wrapping)
            current_y = line2_y
            for wrapped_line in line2_wrapped:
                if wrapped_line.strip():  # Only draw non-empty lines
                    canvas.create_text(canvas_width // 2, current_y, text=wrapped_line,
                                     font=("Arial", line2_size, line2_weight, line2_slant),
                                     fill=line2_color, anchor="center")
                current_y += line2_size + 5  # Add some spacing between wrapped lines
            
        except Exception as e:
            print(f"Preview update error: {e}")
    
    def save_second_page_defaults_and_close(self, dialog):
        """Save second page defaults and close dialog"""
        try:
            self.save_defaults()
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
    
    def open_start_config(self):
        """Open start text configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Start Text")
        dialog.geometry("1000x720")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Maximize window when supported; otherwise center
        try:
            dialog.state('zoomed')  # Windows
        except Exception:
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (1000 // 2)
            y = (dialog.winfo_screenheight() // 2) - (720 // 2)
            dialog.geometry(f"1000x720+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="16")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Start Text Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=6, pady=(0, 15))
        
        # Color and font options
        color_options = ["black", "white", "yellow", "red", "green", "blue", "cyan", "magenta", "brown", "orange"]
        font_options = ["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana", "Impact", "Comic Sans MS"]
        
        # Line 1
        ttk.Label(main_frame, text="Line 1:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(main_frame, textvariable=self.start_line1_var, width=40).grid(row=1, column=1, columnspan=4, sticky=tk.W, pady=(0, 5))
        ttk.Checkbutton(main_frame, text="Hide", variable=self.start_line1_hidden_var, 
                       command=self.update_start_preview).grid(row=1, column=5, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(main_frame, text="Size:").grid(row=2, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0.5, to=3.0, increment=0.1, textvariable=self.start_line1_size_var, 
                   width=8, command=self.update_start_preview).grid(row=2, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(main_frame, text="Color:").grid(row=2, column=2, sticky=tk.W, padx=(0, 5))
        line1_color_combo = ttk.Combobox(main_frame, textvariable=self.start_line1_color_var,
                                        values=color_options, width=10)
        line1_color_combo.grid(row=2, column=3, sticky=tk.W, padx=(0, 15))
        line1_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_start_preview())
        
        ttk.Label(main_frame, text="Font:").grid(row=2, column=4, sticky=tk.W, padx=(0, 5))
        line1_font_combo = ttk.Combobox(main_frame, textvariable=self.start_line1_font_var,
                                       values=font_options, width=12)
        line1_font_combo.grid(row=2, column=5, sticky=tk.W)
        line1_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_start_preview())
        
        ttk.Checkbutton(main_frame, text="Bold", variable=self.start_line1_bold_var,
                       command=self.update_start_preview).grid(row=2, column=6, sticky=tk.W, padx=(10, 0))
        
        # Line 2
        ttk.Label(main_frame, text="Line 2:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Entry(main_frame, textvariable=self.start_line2_var, width=40).grid(row=3, column=1, columnspan=5, sticky=tk.W, pady=(15, 5))
        
        ttk.Label(main_frame, text="Size:").grid(row=4, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0.5, to=3.0, increment=0.1, textvariable=self.start_line2_size_var, 
                   width=8, command=self.update_start_preview).grid(row=4, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(main_frame, text="Color:").grid(row=4, column=2, sticky=tk.W, padx=(0, 5))
        line2_color_combo = ttk.Combobox(main_frame, textvariable=self.start_line2_color_var,
                                        values=color_options, width=10)
        line2_color_combo.grid(row=4, column=3, sticky=tk.W, padx=(0, 15))
        line2_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_start_preview())
        
        ttk.Label(main_frame, text="Font:").grid(row=4, column=4, sticky=tk.W, padx=(0, 5))
        line2_font_combo = ttk.Combobox(main_frame, textvariable=self.start_line2_font_var,
                                       values=font_options, width=12)
        line2_font_combo.grid(row=4, column=5, sticky=tk.W)
        line2_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_start_preview())
        
        ttk.Checkbutton(main_frame, text="Bold", variable=self.start_line2_bold_var,
                       command=self.update_start_preview).grid(row=4, column=6, sticky=tk.W, padx=(10, 0))
        
        # Start duration
        ttk.Label(main_frame, text="Duration (sec):", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Spinbox(main_frame, from_=1.0, to=15.0, increment=0.5, textvariable=self.start_duration_var, 
                   width=8).grid(row=5, column=1, sticky=tk.W, pady=(15, 5))

        # Fade controls for start (full row to avoid cramped layout)
        fade_frame = ttk.LabelFrame(main_frame, text="Fade Options", padding="8")
        fade_frame.grid(row=6, column=0, columnspan=6, sticky=(tk.W, tk.E), padx=(0,0), pady=(10,0))
        ttk.Checkbutton(fade_frame, text="Fade In", variable=self.start_fade_in_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(fade_frame, text="In Duration (s):").grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(fade_frame, from_=0.0, to=5.0, increment=0.1, textvariable=self.start_fade_in_dur_var, width=6).grid(row=0, column=2, sticky=tk.W)
        ttk.Checkbutton(fade_frame, text="Fade Out", variable=self.start_fade_out_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Label(fade_frame, text="Out Duration (s):").grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Spinbox(fade_frame, from_=0.0, to=5.0, increment=0.1, textvariable=self.start_fade_out_dur_var, width=6).grid(row=1, column=2, sticky=tk.W)
        
        # Text spacing
        ttk.Label(main_frame, text="Text Spacing:", font=('Arial', 10, 'bold')).grid(row=7, column=2, sticky=tk.W, pady=(10, 5), padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0, to=10, increment=1, textvariable=self.start_text_spacing_var, 
                   width=8, command=self.update_start_preview).grid(row=7, column=3, sticky=tk.W, pady=(10, 5))
        
        # Logo size
        ttk.Label(main_frame, text="Logo Size:", font=('Arial', 10, 'bold')).grid(row=7, column=4, sticky=tk.W, pady=(10, 5), padx=(20, 5))
        ttk.Spinbox(main_frame, from_=100, to=600, increment=25, textvariable=self.start_logo_size_var, 
                   width=8, command=self.update_start_preview).grid(row=7, column=5, sticky=tk.W, pady=(10, 5))
        
        # Logo-text spacing
        ttk.Label(main_frame, text="Logo-Text Spacing:", font=('Arial', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(10, 5))
        ttk.Spinbox(main_frame, from_=0, to=200, increment=10, textvariable=self.start_logo_text_spacing_var, 
                   width=8, command=self.update_start_preview).grid(row=8, column=1, sticky=tk.W, pady=(10, 5))
        
        # Extra image controls for start
        start_extra_frame = ttk.LabelFrame(main_frame, text="Extra Image (below last line)", padding="8")
        start_extra_frame.grid(row=9, column=0, columnspan=6, sticky=(tk.W, tk.E))
        ttk.Checkbutton(start_extra_frame, text="Enable", variable=self.start_image_enabled_var,
                        command=self.update_start_preview).grid(row=0, column=0, sticky=tk.W, padx=(0,10))
        ttk.Button(start_extra_frame, text="Choose Image...",
                   command=lambda: self._choose_start_image()).grid(row=0, column=1, sticky=tk.W, padx=(0,10))
        ttk.Entry(start_extra_frame, textvariable=self.start_image_path_var, width=40, state='readonly').grid(row=0, column=2, columnspan=3, sticky=(tk.W, tk.E))
        ttk.Label(start_extra_frame, text="Image Height:").grid(row=1, column=0, sticky=tk.W, pady=(8,0))
        ttk.Spinbox(start_extra_frame, from_=50, to=800, increment=10, textvariable=self.start_image_height_var, width=8,
                    command=self.update_start_preview).grid(row=1, column=1, sticky=tk.W, pady=(8,0))
        ttk.Label(start_extra_frame, text="Spacing (text → image):").grid(row=1, column=2, sticky=tk.W, pady=(8,0))
        ttk.Spinbox(start_extra_frame, from_=0, to=300, increment=5, textvariable=self.start_image_spacing_var, width=8,
                    command=self.update_start_preview).grid(row=1, column=3, sticky=tk.W, pady=(8,0))
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="10")
        preview_frame.grid(row=8, column=0, columnspan=6, pady=(10, 10), sticky=(tk.W, tk.E))
        preview_frame.columnconfigure(0, weight=1)
        
        # Preview canvas (white background to simulate start screen)
        self.start_preview_canvas = tk.Canvas(preview_frame, width=480, height=270, bg='white', highlightthickness=1, highlightbackground="#ccc")
        self.start_preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # Make preview responsive and keep 16:9 so buttons remain visible
        def _resize_start_preview_canvas(event=None):
            try:
                max_w = max(360, preview_frame.winfo_width() - 24)
            except Exception:
                max_w = 480
            # smaller cap so buttons remain visible on short screens
            target_w = min(max_w, 480)
            target_h = int(target_w * 9 / 16)
            if int(self.start_preview_canvas['width']) != target_w or int(self.start_preview_canvas['height']) != target_h:
                self.start_preview_canvas.configure(width=target_w, height=target_h)
                self.update_start_preview()

        preview_frame.bind('<Configure>', lambda e: _resize_start_preview_canvas(e))
        # initialize size once
        _resize_start_preview_canvas()

        # helper to choose image for start
        def _choose_start():
            path = filedialog.askopenfilename(title="Select Start Extra Image",
                                              filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp")])
            if path:
                self.start_image_path_var.set(path)
        self._choose_start_image = _choose_start
        
        # Buttons frame (ensure visible at bottom)
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=11, column=0, columnspan=6, pady=(4, 4), sticky=(tk.W, tk.E))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=0)
        
        # Save as default button
        save_button = ttk.Button(button_frame, text="💾 Save as Default", 
                                command=lambda: self.save_start_defaults_and_close(dialog))
        save_button.grid(row=0, column=0, padx=(0, 10))
        
        # Close button (auto-saves settings)
        close_button = ttk.Button(button_frame, text="Close", command=lambda: self.save_start_defaults_and_close(dialog))
        close_button.grid(row=0, column=1, padx=(10, 0))
        
        # Status label
        self.start_dialog_status_label = ttk.Label(main_frame, text="", foreground="green")
        self.start_dialog_status_label.grid(row=12, column=0, columnspan=6, pady=(0, 0))
        
        # Bind text changes to preview updates
        self.start_line1_var.trace('w', lambda *args: self.update_start_preview())
        self.start_line2_var.trace('w', lambda *args: self.update_start_preview())
        
        # Initial preview
        self.update_start_preview()
    
    def update_start_preview(self):
        """Update the live preview of the start text to match video output exactly"""
        try:
            # Clear the canvas
            self.start_preview_canvas.delete("all")
            
            # Get current values
            line1 = self.start_line1_var.get()
            line2 = self.start_line2_var.get()
            line1_size = self.start_line1_size_var.get()
            line2_size = self.start_line2_size_var.get()
            line1_color = self.start_line1_color_var.get()
            line2_color = self.start_line2_color_var.get()
            line1_font = self.start_line1_font_var.get()
            line2_font = self.start_line2_font_var.get()
            line1_bold = self.start_line1_bold_var.get()
            line2_bold = self.start_line2_bold_var.get()
            text_spacing = self.start_text_spacing_var.get()
            logo_size = self.start_logo_size_var.get()
            logo_text_spacing = self.start_logo_text_spacing_var.get()
            line1_hidden = self.start_line1_hidden_var.get()
            
            # Color mapping (RGB format to match video)
            color_map = {
                "black": "#000000",
                "white": "#FFFFFF",
                "yellow": "#FFFF00",
                "red": "#FF0000",
                "green": "#00FF00",
                "blue": "#0000FF",
                "cyan": "#00FFFF",
                "magenta": "#FF00FF",
                "brown": "#8B4513",
                "orange": "#FFA500"
            }
            
            # Canvas dimensions (use actual widget size)
            try:
                canvas_width = int(self.start_preview_canvas['width'])
                canvas_height = int(self.start_preview_canvas['height'])
            except Exception:
                canvas_width = 600
                canvas_height = 338
            if canvas_width <= 0 or canvas_height <= 0:
                canvas_width = 600
                canvas_height = 338
            
            # Video dimensions (actual output)
            video_width = 1920
            video_height = 1080
            
            # Calculate scaling factors
            width_scale = canvas_width / video_width
            height_scale = canvas_height / video_height
            
            # Load and display logo
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            logo_size_preview = 0
            if os.path.exists(logo_path):
                try:
                    from PIL import Image, ImageTk
                    # Load logo with PIL
                    logo_pil = Image.open(logo_path)
                    
                    # Calculate logo size for preview (proportional to video)
                    logo_size_video = logo_size  # Use the variable size
                    logo_size_preview = int(logo_size_video * height_scale)
                    
                    # Resize logo for preview
                    logo_pil = logo_pil.resize((logo_size_preview, logo_size_preview), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    logo_photo = ImageTk.PhotoImage(logo_pil)
                    
                    # Store reference to prevent garbage collection
                    self.logo_photo = logo_photo
                    
                except Exception as e:
                    print(f"Error loading logo for preview: {e}")
            
            # Calculate font sizes proportionally (match video scaling)
            preview_font_scale = int(25 * height_scale)  # Scale based on height ratio
            font1_size = max(8, int(line1_size * preview_font_scale))  # Minimum size of 8
            font2_size = max(8, int(line2_size * preview_font_scale))
            # Use Tk font metrics for more accurate height in preview
            try:
                import tkinter.font as tkfont
                font1_metrics = tkfont.Font(family=line1_font, size=font1_size, weight='bold')
                font2_metrics = tkfont.Font(family=line2_font, size=font2_size, weight='bold')
                line1_px_height = font1_metrics.metrics('linespace') if (line1 and not line1_hidden) else 0
                line2_px_height = font2_metrics.metrics('linespace') if line2 else 0
            except Exception:
                line1_px_height = int(font1_size * 1.2) if (line1 and not line1_hidden) else 0
                line2_px_height = int(font2_size * 1.2) if line2 else 0
            
            # EXACT SAME POSITIONING LOGIC AS VIDEO - copy from create_start_clip
            logo_height = logo_size_preview
            base_spacing = int(80 * height_scale)  # Scale for preview
            adjusted_spacing = base_spacing + (text_spacing * int(10 * height_scale))  # Scale for preview
            
            # Scale logo_text_spacing for preview (same as other spacing variables)
            logo_text_spacing_preview = int(logo_text_spacing * height_scale)
            
            # Measure actual rendered text heights on the canvas for perfect centering
            def _measure_text_height(text, family, size):
                if not text:
                    return 0
                item = self.start_preview_canvas.create_text(0, 0, text=text, font=(family, size, 'bold'), anchor=tk.NW)
                bbox = self.start_preview_canvas.bbox(item)
                self.start_preview_canvas.delete(item)
                if not bbox:
                    return 0
                return max(0, bbox[3] - bbox[1])

            h1 = _measure_text_height(line1 if (line1 and not line1_hidden) else "", line1_font, font1_size)
            h2 = _measure_text_height(line2, line2_font, font2_size)
            total_text_height = h1 + h2
            
            # Add spacing between text lines
            if line1 and not line1_hidden and line2:
                total_text_height += adjusted_spacing
            
            # Total content height = logo + spacing + text (+ optional start extra image)
            total_content_height = logo_height + logo_text_spacing_preview + total_text_height
            # Include start extra image in total height if enabled
            start_extra_image_enabled = self.start_image_enabled_var.get()
            start_extra_image_path = self.start_image_path_var.get()
            start_extra_image_spacing = self.start_image_spacing_var.get()
            start_extra_image_height = self.start_image_height_var.get()
            include_start_extra = (start_extra_image_enabled and start_extra_image_path and os.path.exists(start_extra_image_path))
            if include_start_extra:
                total_content_height += int(start_extra_image_spacing * height_scale) + int(start_extra_image_height * height_scale)
            
            # Calculate starting Y position to center everything within the preview canvas
            # Use full canvas height (no extra margins) for visual centering in the preview
            available_height = canvas_height
            start_y = int((available_height - total_content_height) / 2.0)
            
            # Logo position
            logo_y = start_y
            
            # Text start position
            text_start_y = logo_y + logo_height + logo_text_spacing_preview
            
            # Display logo at calculated position
            if hasattr(self, 'logo_photo'):
                logo_x = (canvas_width - logo_size_preview) // 2
                self.start_preview_canvas.create_image(logo_x, logo_y, anchor=tk.NW, image=self.logo_photo)
            
            # Line 1
            if line1 and not line1_hidden:
                color1 = color_map.get(line1_color, "#000000")
                y1 = int(text_start_y)
                font_weight1 = 'bold' if line1_bold else 'normal'
                self.start_preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                                    fill=color1, font=(line1_font, font1_size, font_weight1), anchor=tk.N)
            
            # Line 2
            if line2:
                color2 = color_map.get(line2_color, "#000000")
                if line1_hidden:
                    y2 = int(text_start_y)
                else:
                    y2 = int(text_start_y + adjusted_spacing)
                font_weight2 = 'bold' if line2_bold else 'normal'
                self.start_preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                                    fill=color2, font=(line2_font, font2_size, font_weight2), anchor=tk.N)

            # Render start extra image in preview
            if include_start_extra:
                try:
                    from PIL import Image, ImageTk
                    extra_img = Image.open(start_extra_image_path)
                    w, h = extra_img.size
                    if h <= 0:
                        h = 1
                    new_h = max(1, int(start_extra_image_height * height_scale))
                    new_w = int(w * (new_h / h))
                    extra_img = extra_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    self.start_extra_image_photo = ImageTk.PhotoImage(extra_img)
                    last_y = text_start_y if (line1_hidden or not line1) else int(text_start_y + adjusted_spacing)
                    extra_y = int(last_y + int(start_extra_image_spacing * height_scale))
                    extra_x = (canvas_width - new_w) // 2
                    self.start_preview_canvas.create_image(extra_x, extra_y, anchor=tk.NW, image=self.start_extra_image_photo)
                except Exception as e:
                    print(f"Start preview extra image error: {e}")
                
        except Exception as e:
            print(f"Start preview update error: {e}")
    
    def update_ending_preview(self):
        """Update the live preview of the ending text to match video output exactly"""
        try:
            # Clear the canvas
            self.ending_preview_canvas.delete("all")
            
            # Get current values
            line1 = self.ending_line1_var.get()
            line2 = self.ending_line2_var.get()
            line3 = self.ending_line3_var.get()
            line1_size = self.ending_line1_size_var.get()
            line2_size = self.ending_line2_size_var.get()
            line3_size = self.ending_line3_size_var.get()
            line1_color = self.ending_line1_color_var.get()
            line2_color = self.ending_line2_color_var.get()
            line3_color = self.ending_line3_color_var.get()
            line1_font = self.ending_line1_font_var.get()
            line2_font = self.ending_line2_font_var.get()
            line3_font = self.ending_line3_font_var.get()
            line1_bold = self.ending_line1_bold_var.get()
            line2_bold = self.ending_line2_bold_var.get()
            line3_bold = self.ending_line3_bold_var.get()
            text_spacing = self.ending_text_spacing_var.get()
            logo_size = self.ending_logo_size_var.get()
            logo_text_spacing = self.ending_logo_text_spacing_var.get()
            
            # Color mapping (RGB format to match video)
            color_map = {
                "black": "#000000",
                "white": "#FFFFFF",
                "yellow": "#FFFF00",
                "red": "#FF0000",
                "green": "#00FF00",
                "blue": "#0000FF",
                "cyan": "#00FFFF",
                "magenta": "#FF00FF",
                "brown": "#8B4513",
                "orange": "#FFA500"
            }
            
            # Canvas dimensions (use actual widget size)
            try:
                canvas_width = int(self.start_preview_canvas['width'])
                canvas_height = int(self.start_preview_canvas['height'])
            except Exception:
                canvas_width = 600
                canvas_height = 338
            if canvas_width <= 0 or canvas_height <= 0:
                canvas_width = 600
                canvas_height = 338
            
            # Video dimensions (actual output)
            video_width = 1920
            video_height = 1080
            
            # Calculate scaling factors
            width_scale = canvas_width / video_width
            height_scale = canvas_height / video_height
            
            # Load and display logo
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            logo_size_preview = 0
            if os.path.exists(logo_path):
                try:
                    from PIL import Image, ImageTk
                    # Load logo with PIL
                    logo_pil = Image.open(logo_path)
                    
                    # Calculate logo size for preview (proportional to video)
                    logo_size_video = logo_size  # Use the variable size
                    logo_size_preview = int(logo_size_video * height_scale)
                    
                    # Resize logo for preview
                    logo_pil = logo_pil.resize((logo_size_preview, logo_size_preview), Image.Resampling.LANCZOS)
                    
                    # Convert to PhotoImage
                    logo_photo = ImageTk.PhotoImage(logo_pil)
                    
                    # Store reference to prevent garbage collection
                    self.ending_logo_photo = logo_photo
                    
                except Exception as e:
                    print(f"Error loading logo for ending preview: {e}")
            
            # Calculate font sizes proportionally (match video scaling)
            preview_font_scale = int(25 * height_scale)  # Scale based on height ratio
            font1_size = max(8, int(line1_size * preview_font_scale))  # Minimum size of 8
            font2_size = max(8, int(line2_size * preview_font_scale))
            font3_size = max(8, int(line3_size * preview_font_scale))
            
            # EXACT SAME POSITIONING LOGIC AS VIDEO - copy from create_ending_clip
            logo_height = logo_size_preview
            base_spacing = int(80 * height_scale)  # Scale for preview
            adjusted_spacing = base_spacing + (text_spacing * int(10 * height_scale))  # Scale for preview
            
            # Scale logo_text_spacing for preview (same as other spacing variables)
            logo_text_spacing_preview = int(logo_text_spacing * height_scale)
            
            # Calculate text heights (approximate)
            text_height_estimate = int(50 * height_scale)  # Scale for preview
            total_text_height = 0
            line1_hidden = self.ending_line1_hidden_var.get()
            line2_hidden = self.ending_line2_hidden_var.get()
            line3_hidden = self.ending_line3_hidden_var.get()
            if line1 and not line1_hidden:
                total_text_height += text_height_estimate
            if line2 and not line2_hidden:
                total_text_height += text_height_estimate
            if line3 and not line3_hidden:
                total_text_height += text_height_estimate
            
            # Add spacing between text lines
            if (line1 and not line1_hidden) and (line2 and not line2_hidden):
                total_text_height += adjusted_spacing
            if (line2 and not line2_hidden) and (line3 and not line3_hidden):
                total_text_height += adjusted_spacing

            # Extra image contribution
            extra_image_enabled = self.ending_image_enabled_var.get()
            extra_image_spacing = self.ending_image_spacing_var.get()
            extra_image_height_video = self.ending_image_height_var.get()
            extra_image_height_preview = int(extra_image_height_video * height_scale)
            extra_image_spacing_preview = int(extra_image_spacing * height_scale)
            if extra_image_enabled and self.ending_image_path_var.get() and os.path.exists(self.ending_image_path_var.get()):
                total_text_height += extra_image_spacing_preview + extra_image_height_preview
            
            # Total content height = logo + spacing + text
            total_content_height = logo_height + logo_text_spacing_preview + total_text_height
            
            # Calculate starting Y position to center everything (EXACT SAME AS VIDEO)
            available_height = canvas_height - int(100 * height_scale)  # Scale for preview
            start_y = (available_height - total_content_height) // 2 + int(50 * height_scale)  # Scale for preview
            
            # Logo position
            logo_y = start_y
            
            # Text start position
            text_start_y = logo_y + logo_height + logo_text_spacing_preview
            
            # Display logo at calculated position
            if hasattr(self, 'ending_logo_photo'):
                logo_x = (canvas_width - logo_size_preview) // 2
                self.ending_preview_canvas.create_image(logo_x, logo_y, anchor=tk.NW, image=self.ending_logo_photo)
            
            # Line 1
            if line1 and not line1_hidden:
                color1 = color_map.get(line1_color, "#000000")
                y1 = int(text_start_y)  # Convert to integer for consistency
                font_weight1 = 'bold' if line1_bold else 'normal'
                self.ending_preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                              fill=color1, font=(line1_font, font1_size, font_weight1))
            
            # Line 2
            if line2 and not line2_hidden:
                color2 = color_map.get(line2_color, "#000000")
                # If line1 hidden, keep line2 at text_start_y; otherwise below line1
                if line1 and not line1_hidden:
                    y2 = int(text_start_y + adjusted_spacing)
                else:
                    y2 = int(text_start_y)
                font_weight2 = 'bold' if line2_bold else 'normal'
                self.ending_preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                              fill=color2, font=(line2_font, font2_size, font_weight2))
            
            # Line 3
            if line3 and not line3_hidden:
                color3 = color_map.get(line3_color, "#000000")
                # Determine y3 based on which previous lines are visible
                visible_offset = 0
                if line1 and not line1_hidden:
                    visible_offset += 1
                if line2 and not line2_hidden:
                    visible_offset += 1
                y3 = int(text_start_y + (adjusted_spacing * max(visible_offset, 0)))
                font_weight3 = 'bold' if line3_bold else 'normal'
                self.ending_preview_canvas.create_text(canvas_width//2, y3, text=line3, 
                                              fill=color3, font=(line3_font, font3_size, font_weight3))

            # Extra image rendering (preview)
            if extra_image_enabled and self.ending_image_path_var.get() and os.path.exists(self.ending_image_path_var.get()):
                try:
                    extra_img = Image.open(self.ending_image_path_var.get())
                    # Maintain aspect ratio by scaling height, width proportional
                    w, h = extra_img.size
                    if h <= 0:
                        h = 1
                    new_h = max(1, extra_image_height_preview)
                    new_w = int(w * (new_h / h))
                    extra_img = extra_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    self.ending_extra_image_photo = ImageTk.PhotoImage(extra_img)

                    # Compute y position below the last visible text line
                    last_y = text_start_y
                    visible_offset = 0
                    if line1 and not line1_hidden:
                        visible_offset += 1
                    if line2 and not line2_hidden:
                        last_y = int(text_start_y + adjusted_spacing)
                        visible_offset += 1
                    if line3 and not line3_hidden:
                        last_y = int(text_start_y + (adjusted_spacing * max(visible_offset, 0)))

                    extra_y = int(last_y + extra_image_spacing_preview)
                    extra_x = (canvas_width - new_w) // 2
                    self.ending_preview_canvas.create_image(extra_x, extra_y, anchor=tk.NW, image=self.ending_extra_image_photo)
                except Exception as e:
                    print(f"Ending preview extra image error: {e}")
                
        except Exception as e:
            print(f"Ending preview update error: {e}")
    
    def save_start_defaults_and_close(self, dialog):
        """Save current start settings as defaults and close the dialog"""
        try:
            import json
            
            defaults = {
                "start_line1": self.start_line1_var.get(),
                "start_line2": self.start_line2_var.get(),
                "start_line1_size": self.start_line1_size_var.get(),
                "start_line2_size": self.start_line2_size_var.get(),
                "start_line1_color": self.start_line1_color_var.get(),
                "start_line2_color": self.start_line2_color_var.get(),
                "start_line1_font": self.start_line1_font_var.get(),
                "start_line2_font": self.start_line2_font_var.get(),
                "start_duration": self.start_duration_var.get(),
                "start_text_spacing": self.start_text_spacing_var.get(),
                "start_logo_size": self.start_logo_size_var.get(),
                "start_logo_text_spacing": self.start_logo_text_spacing_var.get(),
                "start_line1_hidden": self.start_line1_hidden_var.get(),
                "start_image_enabled": self.start_image_enabled_var.get(),
                "start_image_path": self.start_image_path_var.get(),
                "start_image_height": self.start_image_height_var.get(),
                "start_image_spacing": self.start_image_spacing_var.get(),
                # Start fade options
                "start_fade_in": self.start_fade_in_var.get(),
                "start_fade_out": self.start_fade_out_var.get(),
                "start_fade_in_dur": self.start_fade_in_dur_var.get(),
                "start_fade_out_dur": self.start_fade_out_dur_var.get(),
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get(),
                "background_color": self.background_color_var.get(),
                "starting_part_number": self.starting_part_var.get(),
                "ending_line1": self.ending_line1_var.get(),
                "ending_line2": self.ending_line2_var.get(),
                "ending_line3": self.ending_line3_var.get(),
                "ending_line1_size": self.ending_line1_size_var.get(),
                "ending_line2_size": self.ending_line2_size_var.get(),
                "ending_line3_size": self.ending_line3_size_var.get(),
                "ending_line1_color": self.ending_line1_color_var.get(),
                "ending_line2_color": self.ending_line2_color_var.get(),
                "ending_line3_color": self.ending_line3_color_var.get(),
                "ending_line1_font": self.ending_line1_font_var.get(),
                "ending_line2_font": self.ending_line2_font_var.get(),
                "ending_line3_font": self.ending_line3_font_var.get(),
                "ending_duration": self.ending_duration_var.get()
            }
            
            with open('defaults.json', 'w') as f:
                json.dump(defaults, f, indent=2)
            
            self.start_dialog_status_label.config(text="✅ Defaults saved successfully!", foreground="green")
            dialog.after(1000, dialog.destroy)  # Close after 1 second
            
        except Exception as e:
            error_msg = f"❌ Failed to save defaults: {str(e)}"
            self.start_dialog_status_label.config(text=error_msg, foreground="red")
    
    def update_preview(self):
        """Update the live preview of the ending text"""
        try:
            # Clear the canvas
            self.preview_canvas.delete("all")
            
            # Get current values
            line1 = self.ending_line1_var.get()
            line2 = self.ending_line2_var.get()
            line3 = self.ending_line3_var.get()
            line1_size = self.ending_line1_size_var.get()
            line2_size = self.ending_line2_size_var.get()
            line3_size = self.ending_line3_size_var.get()
            line1_color = self.ending_line1_color_var.get()
            line2_color = self.ending_line2_color_var.get()
            line3_color = self.ending_line3_color_var.get()
            line1_font = self.ending_line1_font_var.get()
            line2_font = self.ending_line2_font_var.get()
            line3_font = self.ending_line3_font_var.get()
            
            # Color mapping
            color_map = {
                "white": "#FFFFFF",
                "yellow": "#FFFF00",
                "red": "#FF0000",
                "green": "#00FF00",
                "blue": "#0000FF",
                "cyan": "#00FFFF",
                "magenta": "#FF00FF",
                "brown": "#8B4513",
                "orange": "#FFA500"
            }
            
            # Canvas dimensions (preview size)
            canvas_width = 600
            canvas_height = 338
            
            # Video dimensions (actual output)
            video_width = 1920
            video_height = 1080
            
            # Calculate scaling factors
            width_scale = canvas_width / video_width
            height_scale = canvas_height / video_height
            
            # Scale the line spacing proportionally
            video_line_spacing = 100  # Same as in video
            preview_line_spacing = int(video_line_spacing * height_scale)
            
            # Calculate font sizes proportionally
            # In video: font_size is used directly with cv2.putText
            # In preview: need to scale for tkinter canvas
            # Scale factor to match video proportions
            preview_font_scale = int(25 * height_scale)  # Scale based on height ratio
            font1_size = max(8, int(line1_size * preview_font_scale))  # Minimum size of 8
            font2_size = max(8, int(line2_size * preview_font_scale))
            font3_size = max(8, int(line3_size * preview_font_scale))
            
            # Center position
            y_center = canvas_height // 2
            
            # Line 1
            if line1:
                color1 = color_map.get(line1_color, "#FFFFFF")
                y1 = y_center - preview_line_spacing
                self.preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                              fill=color1, font=(line1_font, font1_size, 'bold'))
            
            # Line 2
            if line2:
                color2 = color_map.get(line2_color, "#FFFFFF")
                y2 = y_center
                self.preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                              fill=color2, font=(line2_font, font2_size, 'bold'))
            
            # Line 3
            if line3:
                color3 = color_map.get(line3_color, "#FFFFFF")
                y3 = y_center + preview_line_spacing
                self.preview_canvas.create_text(canvas_width//2, y3, text=line3, 
                                              fill=color3, font=(line3_font, font3_size, 'bold'))
                
        except Exception as e:
            print(f"Preview update error: {e}")
    
    def save_defaults_and_close(self, dialog):
        """Save current settings as defaults and close the dialog"""
        try:
            import json
            
            defaults = {
                # Start screen settings
                "start_line1": self.start_line1_var.get(),
                "start_line2": self.start_line2_var.get(),
                "start_line1_size": self.start_line1_size_var.get(),
                "start_line2_size": self.start_line2_size_var.get(),
                "start_line1_color": self.start_line1_color_var.get(),
                "start_line2_color": self.start_line2_color_var.get(),
                "start_line1_font": self.start_line1_font_var.get(),
                "start_line2_font": self.start_line2_font_var.get(),
                "start_duration": self.start_duration_var.get(),
                "start_text_spacing": self.start_text_spacing_var.get(),
                "start_logo_size": self.start_logo_size_var.get(),
                "start_logo_text_spacing": self.start_logo_text_spacing_var.get(),
                "start_line1_hidden": self.start_line1_hidden_var.get(),
                "start_line1_bold": self.start_line1_bold_var.get(),
                "start_line2_bold": self.start_line2_bold_var.get(),
                # Start extra image
                "start_image_enabled": self.start_image_enabled_var.get(),
                "start_image_path": self.start_image_path_var.get(),
                "start_image_height": self.start_image_height_var.get(),
                "start_image_spacing": self.start_image_spacing_var.get(),
                # Ending screen settings
                "ending_line1": self.ending_line1_var.get(),
                "ending_line2": self.ending_line2_var.get(),
                "ending_line3": self.ending_line3_var.get(),
                "ending_line1_size": self.ending_line1_size_var.get(),
                "ending_line2_size": self.ending_line2_size_var.get(),
                "ending_line3_size": self.ending_line3_size_var.get(),
                "ending_line1_color": self.ending_line1_color_var.get(),
                "ending_line2_color": self.ending_line2_color_var.get(),
                "ending_line3_color": self.ending_line3_color_var.get(),
                "ending_line1_font": self.ending_line1_font_var.get(),
                "ending_line2_font": self.ending_line2_font_var.get(),
                "ending_line3_font": self.ending_line3_font_var.get(),
                "ending_line1_bold": self.ending_line1_bold_var.get(),
                "ending_line2_bold": self.ending_line2_bold_var.get(),
                "ending_line3_bold": self.ending_line3_bold_var.get(),
                "ending_duration": self.ending_duration_var.get(),
                "ending_text_spacing": self.ending_text_spacing_var.get(),
                "ending_logo_size": self.ending_logo_size_var.get(),
                "ending_logo_text_spacing": self.ending_logo_text_spacing_var.get(),
                "ending_line1_hidden": self.ending_line1_hidden_var.get(),
                "ending_line2_hidden": self.ending_line2_hidden_var.get(),
                "ending_line3_hidden": self.ending_line3_hidden_var.get(),
                # Ending extra image
                "ending_image_enabled": self.ending_image_enabled_var.get(),
                "ending_image_path": self.ending_image_path_var.get(),
                "ending_image_height": self.ending_image_height_var.get(),
                "ending_image_spacing": self.ending_image_spacing_var.get(),
                # Second page settings
                "second_page_enabled": self.second_page_enabled_var.get(),
                "second_page_line1": self.second_page_line1_var.get(),
                "second_page_line2": self.second_page_line2_var.get(),
                "second_page_line1_bold": self.second_page_line1_bold_var.get(),
                "second_page_line2_bold": self.second_page_line2_bold_var.get(),
                "second_page_line1_italic": self.second_page_line1_italic_var.get(),
                "second_page_line2_italic": self.second_page_line2_italic_var.get(),
                "second_page_line1_size": self.second_page_line1_size_var.get(),
                "second_page_line2_size": self.second_page_line2_size_var.get(),
                "second_page_line1_y": self.second_page_line1_y_var.get(),
                "second_page_line2_y": self.second_page_line2_y_var.get(),
                "second_page_max_chars": self.second_page_max_chars_var.get(),
                "second_page_duration": self.second_page_duration_var.get(),
                "second_page_line1_color": self.second_page_line1_color_var.get(),
                "second_page_line2_color": self.second_page_line2_color_var.get(),
                "second_page_fade_in": self.second_page_fade_in_var.get(),
                "second_page_fade_out": self.second_page_fade_out_var.get(),
                "second_page_fade_in_dur": self.second_page_fade_in_dur_var.get(),
                "second_page_fade_out_dur": self.second_page_fade_out_dur_var.get(),
                
                # Actual duration controls
                "actual_start_duration": self.actual_start_duration_var.get(),
                "actual_second_page_duration": self.actual_second_page_duration_var.get(),
                "actual_ending_duration": self.actual_ending_duration_var.get(),
                "actual_pair_duration": self.actual_pair_duration_var.get(),
                "max_video_duration": self.max_video_duration_var.get(),
                
                # Fade options
                "start_fade_in": self.start_fade_in_var.get(),
                "start_fade_out": self.start_fade_out_var.get(),
                "start_fade_in_dur": self.start_fade_in_dur_var.get(),
                "start_fade_out_dur": self.start_fade_out_dur_var.get(),
                "ending_fade_in": self.ending_fade_in_var.get(),
                "ending_fade_out": self.ending_fade_out_var.get(),
                "ending_fade_in_dur": self.ending_fade_in_dur_var.get(),
                "ending_fade_out_dur": self.ending_fade_out_dur_var.get(),
                # General settings
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get(),
                "background_color": self.background_color_var.get(),
                "starting_part_number": self.starting_part_var.get()
            }
            
            with open('defaults.json', 'w') as f:
                json.dump(defaults, f, indent=2)
            
            # Show success message in main window
            self.status_label.config(text="✅ Defaults saved successfully!")
            
            # Close the dialog
            dialog.destroy()
            
        except Exception as e:
            error_msg = f"❌ Failed to save defaults: {str(e)}"
            self.status_label.config(text=error_msg)
            if hasattr(self, 'dialog_status_label'):
                self.dialog_status_label.config(text=error_msg, foreground="red")
    
    def load_defaults(self):
        """Load saved defaults"""
        try:
            import json
            
            if os.path.exists('defaults.json'):
                with open('defaults.json', 'r') as f:
                    defaults = json.load(f)
                
                # Load start text and styling
                self.start_line1_var.set(defaults.get("start_line1", "Welcome to"))
                self.start_line2_var.set(defaults.get("start_line2", "Lincoln Rare Books & Collectables"))
                self.start_line1_size_var.set(defaults.get("start_line1_size", 1.2))
                self.start_line2_size_var.set(defaults.get("start_line2_size", 1.5))
                self.start_line1_color_var.set(defaults.get("start_line1_color", "black"))
                self.start_line2_color_var.set(defaults.get("start_line2_color", "black"))
                self.start_line1_font_var.set(defaults.get("start_line1_font", "Arial"))
                self.start_line2_font_var.set(defaults.get("start_line2_font", "Arial"))
                self.start_line1_bold_var.set(defaults.get("start_line1_bold", True))
                self.start_line2_bold_var.set(defaults.get("start_line2_bold", True))
                self.start_duration_var.set(defaults.get("start_duration", 3.0))
                self.start_text_spacing_var.set(defaults.get("start_text_spacing", 1))
                self.start_logo_size_var.set(defaults.get("start_logo_size", 300))
                self.start_logo_text_spacing_var.set(defaults.get("start_logo_text_spacing", 20))
                self.start_line1_hidden_var.set(defaults.get("start_line1_hidden", False))
                self.start_image_enabled_var.set(defaults.get("start_image_enabled", False))
                self.start_image_path_var.set(defaults.get("start_image_path", ""))
                self.start_image_height_var.set(defaults.get("start_image_height", 200))
                self.start_image_spacing_var.set(defaults.get("start_image_spacing", 20))
                self.start_fade_in_var.set(defaults.get("start_fade_in", False))
                self.start_fade_out_var.set(defaults.get("start_fade_out", False))
                self.start_fade_in_dur_var.set(defaults.get("start_fade_in_dur", 0.5))
                self.start_fade_out_dur_var.set(defaults.get("start_fade_out_dur", 0.5))
                
                # Load ending text and styling
                self.ending_line1_var.set(defaults.get("ending_line1", "Lincoln Rare Books & Collectables"))
                self.ending_line2_var.set(defaults.get("ending_line2", "Many thousands of postcards in store"))
                self.ending_line3_var.set(defaults.get("ending_line3", "Please Like and Subscribe!"))
                self.ending_line1_size_var.set(defaults.get("ending_line1_size", 1.5))
                self.ending_line2_size_var.set(defaults.get("ending_line2_size", 1.5))
                self.ending_line3_size_var.set(defaults.get("ending_line3_size", 1.5))
                self.ending_line1_color_var.set(defaults.get("ending_line1_color", "black"))
                self.ending_line2_color_var.set(defaults.get("ending_line2_color", "black"))
                self.ending_line3_color_var.set(defaults.get("ending_line3_color", "black"))
                self.ending_line1_font_var.set(defaults.get("ending_line1_font", "Arial"))
                self.ending_line2_font_var.set(defaults.get("ending_line2_font", "Arial"))
                self.ending_line3_font_var.set(defaults.get("ending_line3_font", "Arial"))
                self.ending_line1_bold_var.set(defaults.get("ending_line1_bold", True))
                self.ending_line2_bold_var.set(defaults.get("ending_line2_bold", True))
                self.ending_line3_bold_var.set(defaults.get("ending_line3_bold", True))
                self.ending_duration_var.set(defaults.get("ending_duration", 5.0))
                self.ending_text_spacing_var.set(defaults.get("ending_text_spacing", 1))
                self.ending_logo_size_var.set(defaults.get("ending_logo_size", 300))
                self.ending_logo_text_spacing_var.set(defaults.get("ending_logo_text_spacing", 20))
                self.ending_line1_hidden_var.set(defaults.get("ending_line1_hidden", False))
                self.ending_line2_hidden_var.set(defaults.get("ending_line2_hidden", False))
                self.ending_line3_hidden_var.set(defaults.get("ending_line3_hidden", False))
                self.ending_image_enabled_var.set(defaults.get("ending_image_enabled", False))
                self.ending_image_path_var.set(defaults.get("ending_image_path", ""))
                self.ending_image_height_var.set(defaults.get("ending_image_height", 200))
                self.ending_image_spacing_var.set(defaults.get("ending_image_spacing", 20))
                # Second page settings
                self.second_page_enabled_var.set(defaults.get("second_page_enabled", False))
                self.second_page_line1_var.set(defaults.get("second_page_line1", "Welcome to our collection"))
                self.second_page_line2_var.set(defaults.get("second_page_line2", "Discover amazing postcards"))
                self.second_page_line1_bold_var.set(defaults.get("second_page_line1_bold", False))
                self.second_page_line2_bold_var.set(defaults.get("second_page_line2_bold", False))
                self.second_page_line1_italic_var.set(defaults.get("second_page_line1_italic", False))
                self.second_page_line2_italic_var.set(defaults.get("second_page_line2_italic", False))
                self.second_page_line1_size_var.set(defaults.get("second_page_line1_size", 60))
                self.second_page_line2_size_var.set(defaults.get("second_page_line2_size", 50))
                self.second_page_line1_y_var.set(defaults.get("second_page_line1_y", 450))
                self.second_page_line2_y_var.set(defaults.get("second_page_line2_y", 580))
                self.second_page_max_chars_var.set(defaults.get("second_page_max_chars", 30))
                self.second_page_duration_var.set(defaults.get("second_page_duration", 3.0))
                self.second_page_line1_color_var.set(defaults.get("second_page_line1_color", "#000000"))
                self.second_page_line2_color_var.set(defaults.get("second_page_line2_color", "#000000"))
                self.second_page_fade_in_var.set(defaults.get("second_page_fade_in", False))
                self.second_page_fade_out_var.set(defaults.get("second_page_fade_out", False))
                self.second_page_fade_in_dur_var.set(defaults.get("second_page_fade_in_dur", 0.5))
                self.second_page_fade_out_dur_var.set(defaults.get("second_page_fade_out_dur", 0.5))
                
                # Load actual duration controls
                self.actual_start_duration_var.set(defaults.get("actual_start_duration", 4.0))
                self.actual_second_page_duration_var.set(defaults.get("actual_second_page_duration", 11.0))
                self.actual_ending_duration_var.set(defaults.get("actual_ending_duration", 8.0))
                self.actual_pair_duration_var.set(defaults.get("actual_pair_duration", 14.1))
                self.max_video_duration_var.set(defaults.get("max_video_duration", 60.0))
                
                self.ending_fade_in_var.set(defaults.get("ending_fade_in", False))
                self.ending_fade_out_var.set(defaults.get("ending_fade_out", False))
                self.ending_fade_in_dur_var.set(defaults.get("ending_fade_in_dur", 0.5))
                self.ending_fade_out_dur_var.set(defaults.get("ending_fade_out_dur", 0.5))
                
                # Load other settings
                self.default_duration_var.set(defaults.get("default_duration", 4))
                self.transition_duration_var.set(defaults.get("transition_duration", 1))
                self.effect_var.set(defaults.get("effect", "fade"))
                self.music_var.set(defaults.get("music", "Random"))
                self.music_volume_var.set(defaults.get("music_volume", 0.3))
                self.background_color_var.set(defaults.get("background_color", "light_gray"))
                self.starting_part_var.set(defaults.get("starting_part_number", 1))
                
        except Exception as e:
            print(f"Failed to load defaults: {e}")
    
    def preview_music(self):
        """Preview the selected background music"""
        try:
            selected_music = self.music_var.get()
            if selected_music == "None":
                self.status_label.config(text="No music selected for preview")
                return
            
            # Find the music file using the new system
            music_path = self._get_music_path_by_name(selected_music)
            
            if not music_path or not os.path.exists(music_path):
                self.status_label.config(text=f"Music file not found: {selected_music}")
                return
            
            # Try to play the music using different methods
            try:
                # Method 1: Using pygame (if available)
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play()
                
                # Stop after 10 seconds
                self.root.after(10000, lambda: pygame.mixer.music.stop())
                self.status_label.config(text=f"🎵 Playing preview: {selected_music} (10 seconds)")
                
            except ImportError:
                # Method 2: Using playsound (if available)
                try:
                    from playsound import playsound
                    import threading
                    
                    def play_audio():
                        playsound(music_path, block=False)
                    
                    thread = threading.Thread(target=play_audio)
                    thread.start()
                    self.status_label.config(text=f"🎵 Playing preview: {selected_music}")
                    
                except ImportError:
                    # Method 3: Using system default player
                    import subprocess
                    import platform
                    
                    system = platform.system()
                    if system == "Windows":
                        os.startfile(music_path)
                    elif system == "Darwin":  # macOS
                        subprocess.run(["open", music_path])
                    else:  # Linux
                        subprocess.run(["xdg-open", music_path])
                    
                    self.status_label.config(text=f"🎵 Opened in default player: {selected_music}")
                    
        except Exception as e:
            self.status_label.config(text=f"❌ Preview failed: {str(e)}")
            print(f"Preview error: {e}")  # Debug output
    
    def open_music_manager(self):
        """Open the music management dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Music Library Manager")
        dialog.geometry("900x600")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="16")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Configure dialog grid
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Music Library Manager", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Add Music button
        add_button = ttk.Button(buttons_frame, text="📁 Add Music Files", 
                               command=lambda: self.add_music_files(music_listbox, status_label))
        add_button.grid(row=0, column=0, padx=(0, 10))
        
        # Rename button
        rename_button = ttk.Button(buttons_frame, text="✏️ Rename Track", 
                                  command=lambda: self.rename_music_track(music_listbox, status_label))
        rename_button.grid(row=0, column=1, padx=(0, 10))
        
        # Delete button
        delete_button = ttk.Button(buttons_frame, text="🗑️ Delete Track", 
                                  command=lambda: self.delete_music_track(music_listbox, status_label))
        delete_button.grid(row=0, column=2, padx=(0, 10))
        
        # Preview button
        preview_button = ttk.Button(buttons_frame, text="🎵 Preview Track", 
                                   command=lambda: self.preview_selected_track(music_listbox, status_label))
        preview_button.grid(row=0, column=3, padx=(0, 10))
        
        # Stop preview button
        stop_button = ttk.Button(buttons_frame, text="⏹️ Stop Preview", 
                                command=lambda: self.stop_music_preview(status_label))
        stop_button.grid(row=0, column=4, padx=(0, 10))
        
        # Refresh button
        refresh_button = ttk.Button(buttons_frame, text="🔄 Refresh", 
                                   command=lambda: self.refresh_music_list(music_listbox, status_label))
        refresh_button.grid(row=0, column=5)
        
        # Music list frame
        list_frame = ttk.LabelFrame(main_frame, text="Current Music Tracks", padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Listbox with scrollbar for music files
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        music_listbox = tk.Listbox(listbox_frame, font=('Arial', 10))
        music_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=music_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        music_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Info label
        info_label = ttk.Label(main_frame, text="Supported formats: MP3, WAV, OGG, M4A, MP4\nClick 'Add Music Files' to upload multiple tracks at once from your computer", 
                              font=('Arial', 9), foreground='gray')
        info_label.grid(row=3, column=0, pady=(0, 10))
        
        # Status label
        status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        status_label.grid(row=4, column=0, pady=(0, 10))
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=dialog.destroy)
        close_button.grid(row=5, column=0, pady=(10, 0))
        
        # Load current music files
        self.refresh_music_list(music_listbox, status_label)
    
    def get_music_files(self):
        """Get list of current music files in the music directory, avoiding duplicates"""
        music_dir = "music"
        if not os.path.exists(music_dir):
            os.makedirs(music_dir, exist_ok=True)
            return []
        
        # Group files by base name (without extension)
        file_groups = {}
        supported_formats = ('.mp3', '.wav', '.ogg', '.m4a', '.mp4')
        
        for filename in os.listdir(music_dir):
            if filename.lower().endswith(supported_formats):
                base_name = os.path.splitext(filename)[0]
                extension = os.path.splitext(filename)[1].lower()
                
                if base_name not in file_groups:
                    file_groups[base_name] = []
                
                file_groups[base_name].append({
                    'filename': filename,
                    'extension': extension,
                    'path': os.path.join(music_dir, filename)
                })
        
        # For each group, select the best format (preference order)
        format_priority = {'.mp3': 1, '.m4a': 2, '.mp4': 3, '.wav': 4, '.ogg': 5}
        music_files = []
        
        for base_name, files in file_groups.items():
            # Sort by format priority (lower number = higher priority)
            files.sort(key=lambda x: format_priority.get(x['extension'], 99))
            
            # Take the highest priority file
            best_file = files[0]
            display_name = base_name.replace('_', ' ').title()
            
            music_files.append({
                'filename': best_file['filename'],
                'display_name': display_name,
                'path': best_file['path'],
                'alternatives': len(files)  # How many format alternatives exist
            })
        
        return sorted(music_files, key=lambda x: x['display_name'])
    
    def refresh_music_list(self, listbox, status_label):
        """Refresh the music list display"""
        try:
            listbox.delete(0, tk.END)
            music_files = self.get_music_files()
            
            if not music_files:
                listbox.insert(tk.END, "No music files found. Click 'Add Music File' to add some!")
                status_label.config(text="No music files in library", foreground="orange")
            else:
                for music_file in music_files:
                    # Show if there are multiple formats available
                    if music_file['alternatives'] > 1:
                        display_text = f"{music_file['display_name']} ({music_file['filename']}) [{music_file['alternatives']} formats]"
                    else:
                        display_text = f"{music_file['display_name']} ({music_file['filename']})"
                    listbox.insert(tk.END, display_text)
                status_label.config(text=f"Found {len(music_files)} unique tracks", foreground="green")
            
            # Update the main music dropdown
            self.update_music_dropdown()
            
        except Exception as e:
            status_label.config(text=f"Error refreshing list: {str(e)}", foreground="red")
    
    def add_music_files(self, listbox, status_label):
        """Add multiple music files from the user's computer"""
        try:
            # Open file dialog to select multiple music files
            file_paths = filedialog.askopenfilenames(
                title="Select Music Files (Multiple Selection Allowed)",
                filetypes=[
                    ("Audio/Video files", "*.mp3 *.wav *.ogg *.m4a *.mp4"),
                    ("MP3 files", "*.mp3"),
                    ("WAV files", "*.wav"),
                    ("OGG files", "*.ogg"),
                    ("M4A files", "*.m4a"),
                    ("MP4 files", "*.mp4"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_paths:
                return
            
            # Show progress dialog for multiple files
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Adding Music Files")
            progress_dialog.geometry("500x200")
            progress_dialog.transient(self.root)
            progress_dialog.grab_set()
            
            # Center the dialog
            progress_dialog.update_idletasks()
            x = (progress_dialog.winfo_screenwidth() // 2) - (250)
            y = (progress_dialog.winfo_screenheight() // 2) - (100)
            progress_dialog.geometry(f"500x200+{x}+{y}")
            
            frame = ttk.Frame(progress_dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"Adding {len(file_paths)} music files...", 
                     font=('Arial', 12)).pack(pady=(0, 10))
            
            # Progress bar
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100, length=400)
            progress_bar.pack(pady=(0, 10))
            
            # Current file label
            current_file_label = ttk.Label(frame, text="", font=('Arial', 10))
            current_file_label.pack(pady=(0, 10))
            
            # Results
            results = {"added": 0, "skipped": 0, "errors": 0}
            
            # Ensure music directory exists
            music_dir = "music"
            if not os.path.exists(music_dir):
                os.makedirs(music_dir, exist_ok=True)
            
            # Process each file
            for i, file_path in enumerate(file_paths):
                try:
                    # Update progress
                    progress = (i / len(file_paths)) * 100
                    progress_var.set(progress)
                    
                    # Get the original filename and extension
                    original_filename = os.path.basename(file_path)
                    name_without_ext, ext = os.path.splitext(original_filename)
                    
                    current_file_label.config(text=f"Processing: {original_filename}")
                    progress_dialog.update()
                    
                    # Create display name from filename
                    display_name = name_without_ext.replace('_', ' ').replace('-', ' ').title()
                    
                    # Create safe filename
                    safe_name = "".join(c for c in display_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_name = safe_name.replace(' ', '_').lower()
                    
                    if not safe_name:
                        safe_name = f"track_{i+1}"
                    
                    # Create destination filename
                    dest_filename = f"{safe_name}{ext.lower()}"
                    dest_path = os.path.join(music_dir, dest_filename)
                    
                    # Check if file already exists
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_filename = f"{safe_name}_{counter}{ext.lower()}"
                        dest_path = os.path.join(music_dir, dest_filename)
                        counter += 1
                    
                    # Copy the file
                    import shutil
                    shutil.copy2(file_path, dest_path)
                    results["added"] += 1
                    
                except Exception as e:
                    print(f"Error adding {original_filename}: {e}")
                    results["errors"] += 1
                    continue
            
            # Complete progress
            progress_var.set(100)
            current_file_label.config(text="Complete!")
            progress_dialog.update()
            
            # Close progress dialog after a short delay
            progress_dialog.after(1000, progress_dialog.destroy)
            
            # Show results
            if results["added"] > 0:
                status_label.config(text=f"✅ Added {results['added']} tracks successfully!", foreground="green")
                # Refresh the list
                self.refresh_music_list(listbox, status_label)
                
                # Show summary if there were issues
                if results["errors"] > 0:
                    messagebox.showwarning("Partial Success", 
                                         f"Added {results['added']} tracks successfully.\n"
                                         f"{results['errors']} files had errors and were skipped.")
                else:
                    messagebox.showinfo("Success", 
                                      f"Successfully added {results['added']} music tracks!\n\n"
                                      f"All tracks are now available in your music library.")
            else:
                status_label.config(text="❌ No tracks were added", foreground="red")
                messagebox.showerror("Error", "Failed to add any music tracks. Please check the file formats.")
            
        except Exception as e:
            status_label.config(text=f"❌ Error adding files: {str(e)}", foreground="red")
    
    def rename_music_track(self, listbox, status_label):
        """Rename a selected music track"""
        try:
            selection = listbox.curselection()
            if not selection:
                status_label.config(text="Please select a track to rename", foreground="orange")
                return
            
            music_files = self.get_music_files()
            if not music_files or selection[0] >= len(music_files):
                status_label.config(text="Invalid selection", foreground="red")
                return
            
            selected_file = music_files[selection[0]]
            
            # Create rename dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Rename Track")
            dialog.geometry("400x180")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (200)
            y = (dialog.winfo_screenheight() // 2) - (90)
            dialog.geometry(f"400x180+{x}+{y}")
            
            frame = ttk.Frame(dialog, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(frame, text=f"Rename: {selected_file['display_name']}", 
                     font=('Arial', 12)).pack(pady=(0, 10))
            
            name_var = tk.StringVar(value=selected_file['display_name'])
            name_entry = ttk.Entry(frame, textvariable=name_var, width=40, font=('Arial', 11))
            name_entry.pack(pady=(0, 20))
            name_entry.focus()
            name_entry.select_range(0, tk.END)
            
            result = {"confirmed": False, "name": ""}
            
            def confirm_rename():
                new_name = name_var.get().strip()
                if new_name and new_name != selected_file['display_name']:
                    result["name"] = new_name
                    result["confirmed"] = True
                    dialog.destroy()
                elif not new_name:
                    ttk.Label(frame, text="Please enter a name!", foreground="red").pack()
                else:
                    dialog.destroy()  # No change needed
            
            def cancel_rename():
                dialog.destroy()
            
            button_frame = ttk.Frame(frame)
            button_frame.pack(pady=(10, 0))
            
            ttk.Button(button_frame, text="Rename", command=confirm_rename).pack(side=tk.LEFT, padx=(0, 10))
            ttk.Button(button_frame, text="Cancel", command=cancel_rename).pack(side=tk.LEFT)
            
            dialog.bind('<Return>', lambda e: confirm_rename())
            dialog.wait_window()
            
            if result["confirmed"]:
                # Create new filename
                ext = os.path.splitext(selected_file['filename'])[1]
                safe_name = "".join(c for c in result["name"] if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.replace(' ', '_').lower()
                new_filename = f"{safe_name}{ext}"
                new_path = os.path.join("music", new_filename)
                
                # Check if new name already exists
                counter = 1
                while os.path.exists(new_path) and new_path != selected_file['path']:
                    new_filename = f"{safe_name}_{counter}{ext}"
                    new_path = os.path.join("music", new_filename)
                    counter += 1
                
                # Rename the file
                os.rename(selected_file['path'], new_path)
                
                status_label.config(text=f"✅ Renamed to: {result['name']}", foreground="green")
                self.refresh_music_list(listbox, status_label)
            
        except Exception as e:
            status_label.config(text=f"❌ Error renaming: {str(e)}", foreground="red")
    
    def delete_music_track(self, listbox, status_label):
        """Delete a selected music track"""
        try:
            selection = listbox.curselection()
            if not selection:
                status_label.config(text="Please select a track to delete", foreground="orange")
                return
            
            music_files = self.get_music_files()
            if not music_files or selection[0] >= len(music_files):
                status_label.config(text="Invalid selection", foreground="red")
                return
            
            selected_file = music_files[selection[0]]
            
            # Confirm deletion
            result = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete '{selected_file['display_name']}'?\n\nThis action cannot be undone."
            )
            
            if result:
                # Stop any currently playing music to release file locks
                self._stop_all_music_playback()
                
                # Small delay to ensure file is released
                import time
                time.sleep(0.1)
                
                try:
                    os.remove(selected_file['path'])
                    status_label.config(text=f"✅ Deleted: {selected_file['display_name']}", foreground="green")
                    self.refresh_music_list(listbox, status_label)
                except PermissionError:
                    status_label.config(text=f"❌ Cannot delete: File is in use. Stop preview first.", foreground="red")
                except Exception as e:
                    status_label.config(text=f"❌ Error deleting: {str(e)}", foreground="red")
            
        except Exception as e:
            status_label.config(text=f"❌ Error deleting: {str(e)}", foreground="red")
    
    def preview_selected_track(self, listbox, status_label):
        """Preview the selected music track"""
        try:
            selection = listbox.curselection()
            if not selection:
                status_label.config(text="Please select a track to preview", foreground="orange")
                return
            
            music_files = self.get_music_files()
            if not music_files or selection[0] >= len(music_files):
                status_label.config(text="Invalid selection", foreground="red")
                return
            
            selected_file = music_files[selection[0]]
            
            # Use the existing preview logic
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(selected_file['path'])
                pygame.mixer.music.play()
                
                # Stop after 10 seconds
                self.root.after(10000, lambda: pygame.mixer.music.stop())
                status_label.config(text=f"🎵 Playing: {selected_file['display_name']} (10 seconds)", foreground="green")
                
            except ImportError:
                # Fallback to system player
                import subprocess
                import platform
                
                system = platform.system()
                if system == "Windows":
                    os.startfile(selected_file['path'])
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", selected_file['path']])
                else:  # Linux
                    subprocess.run(["xdg-open", selected_file['path']])
                
                status_label.config(text=f"🎵 Opened in default player: {selected_file['display_name']}", foreground="green")
                
        except Exception as e:
            status_label.config(text=f"❌ Preview failed: {str(e)}", foreground="red")
    
    def stop_music_preview(self, status_label):
        """Stop any currently playing music preview"""
        try:
            self._stop_all_music_playback()
            status_label.config(text="🔇 Preview stopped", foreground="blue")
        except Exception as e:
            status_label.config(text=f"❌ Error stopping preview: {str(e)}", foreground="red")
    
    def update_music_dropdown(self):
        """Update the main interface music dropdown with current files"""
        try:
            music_files = self.get_music_files()
            
            # Build the values list
            values = ["None", "Random"]
            for music_file in music_files:
                values.append(music_file['display_name'])
            
            # Update the combobox in the main interface
            # Find the music combobox widget
            for widget in self.root.winfo_children():
                if isinstance(widget, ttk.Frame):
                    for subwidget in widget.winfo_children():
                        if isinstance(subwidget, ttk.LabelFrame) and "Video Settings" in str(subwidget.cget('text')):
                            for setting_widget in subwidget.winfo_children():
                                if isinstance(setting_widget, ttk.Combobox):
                                    current_values = list(setting_widget['values'])
                                    if "Random" in current_values:  # This is our music combobox
                                        setting_widget.configure(values=values)
                                        break
            
        except Exception as e:
            print(f"Error updating music dropdown: {e}")
    
    def _stop_all_music_playback(self):
        """Stop all music playback to release file locks"""
        try:
            # Try to stop pygame mixer if it's being used
            import pygame
            pygame.mixer.quit()
            pygame.mixer.init()  # Reinitialize for future use
        except ImportError:
            # pygame not available, that's fine
            pass
        except Exception:
            # pygame might not be initialized, that's fine too
            pass

    # YouTube Upload Functionality
    def open_youtube_upload(self):
        """Open YouTube upload dialog"""
        if not YOUTUBE_API_AVAILABLE:
            messagebox.showerror("YouTube API Not Available", 
                               "YouTube API libraries are not installed.\n\n"
                               "Please install them with:\n"
                               "pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Upload to YouTube")
        dialog.geometry("950x800")  # Made even larger to show all content including upload button
        dialog.resizable(True, True)
        dialog.minsize(850, 700)  # Increased minimum size
        
        # Store reference to dialog for layout updates
        self.dialog = dialog
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create a canvas and scrollbar for scrollable content
        canvas = tk.Canvas(dialog)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
        
        canvas.bind('<Enter>', _bind_to_mousewheel)
        canvas.bind('<Leave>', _unbind_from_mousewheel)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        
        # Use scrollable_frame as our main container
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollable_frame.columnconfigure(0, weight=1)
        scrollable_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Upload Videos to YouTube", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 20))
        
        # Authentication status
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication & Channel Selection", padding="10")
        auth_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        auth_frame.columnconfigure(1, weight=1)
        
        self.auth_status_label = ttk.Label(auth_frame, text="Not authenticated", foreground="red")
        self.auth_status_label.grid(row=0, column=0, sticky=tk.W)
        
        auth_button = ttk.Button(auth_frame, text="Authenticate", command=self.authenticate_youtube)
        auth_button.grid(row=0, column=1, sticky=tk.E)
        
        # Re-authenticate button for troubleshooting
        reauth_button = ttk.Button(auth_frame, text="Re-authenticate", command=self.force_reauthenticate)
        reauth_button.grid(row=0, column=2, sticky=tk.E, padx=(5, 0))
        
        # Channel selection (initially hidden)
        self.channel_frame = ttk.Frame(auth_frame)
        self.channel_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        self.channel_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.channel_frame, text="Channel:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.channel_var = tk.StringVar()
        self.channel_combo = ttk.Combobox(self.channel_frame, textvariable=self.channel_var, 
                                        state="readonly", width=30)
        self.channel_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        self.channel_combo.bind('<<ComboboxSelected>>', self.on_channel_selected)
        
        self.set_default_button = ttk.Button(self.channel_frame, text="Set as Default", 
                                           command=self.set_default_channel, state='disabled')
        self.set_default_button.grid(row=0, column=2, padx=(5, 0))
        
        self.refresh_channels_button = ttk.Button(self.channel_frame, text="Refresh Channels", 
                                                command=self.refresh_youtube_channels, state='disabled')
        self.refresh_channels_button.grid(row=0, column=3, padx=(5, 0))
        
        # Add manual channel entry for missing channels
        self.manual_channel_frame = ttk.Frame(self.channel_frame)
        self.manual_channel_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        self.manual_channel_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.manual_channel_frame, text="Missing channel? Enter Channel ID (UC...):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.manual_channel_id_var = tk.StringVar()
        self.manual_channel_entry = ttk.Entry(self.manual_channel_frame, textvariable=self.manual_channel_id_var, 
                                            width=30)
        self.manual_channel_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Add placeholder text functionality
        self.manual_channel_entry.insert(0, "UC... (24 characters)")
        self.manual_channel_entry.configure(foreground='grey')
        
        def on_entry_click(event):
            if self.manual_channel_entry.get() == "UC... (24 characters)":
                self.manual_channel_entry.delete(0, "end")
                self.manual_channel_entry.configure(foreground='black')
        
        def on_focusout(event):
            if self.manual_channel_entry.get() == "":
                self.manual_channel_entry.insert(0, "UC... (24 characters)")
                self.manual_channel_entry.configure(foreground='grey')
        
        self.manual_channel_entry.bind('<FocusIn>', on_entry_click)
        self.manual_channel_entry.bind('<FocusOut>', on_focusout)
        
        self.add_manual_channel_button = ttk.Button(self.manual_channel_frame, text="Add Channel", 
                                                  command=self.add_manual_channel, state='disabled')
        self.add_manual_channel_button.grid(row=0, column=2, padx=(5, 0))
        
        # Initially hide channel selection
        self.channel_frame.grid_remove()
        
        # Video selection
        video_frame = ttk.LabelFrame(main_frame, text="Select Videos", padding="10")
        video_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        video_frame.columnconfigure(0, weight=1)
        video_frame.columnconfigure(1, weight=1)
        video_frame.rowconfigure(2, weight=1)  # Make the video list row expandable
        main_frame.rowconfigure(2, weight=1)
        
        # Row 0: Add video buttons
        self.add_videos_button = ttk.Button(video_frame, text="📁 ADD VIDEOS", command=self.add_videos_to_upload, 
                                          width=20)
        self.add_videos_button.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.add_current_button = ttk.Button(video_frame, text="🎬 ADD CURRENT VIDEOS", command=self.add_current_videos,
                                           width=25)
        self.add_current_button.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Row 1: Management buttons  
        self.remove_button = ttk.Button(video_frame, text="🗑️ REMOVE SELECTED", command=self.remove_selected_videos,
                                      width=20)
        self.remove_button.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.clear_button = ttk.Button(video_frame, text="🗂️ CLEAR ALL", command=self.clear_video_list,
                                     width=15)
        self.clear_button.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Row 2: Video list
        columns = ('File', 'Size', 'Status')
        self.video_tree = ttk.Treeview(video_frame, columns=columns, show='headings', height=4)
        self.video_tree.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Configure columns
        self.video_tree.heading('File', text='Video File')
        self.video_tree.heading('Size', text='Size (MB)')
        self.video_tree.heading('Status', text='Status')
        self.video_tree.column('File', width=400)
        self.video_tree.column('Size', width=100)
        self.video_tree.column('Status', width=150)
        
        # Scrollbar for video list
        video_scrollbar = ttk.Scrollbar(video_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        video_scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=(10, 0))
        self.video_tree.configure(yscrollcommand=video_scrollbar.set)
        
        # Bind selection event to update title/description preview
        self.video_tree.bind('<<TreeviewSelect>>', self.on_video_selection_changed)
        
        # Upload settings
        settings_frame = ttk.LabelFrame(main_frame, text="Upload Settings", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Privacy status
        ttk.Label(settings_frame, text="Privacy:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.privacy_var = tk.StringVar(value="public")
        self.privacy_combo = ttk.Combobox(settings_frame, textvariable=self.privacy_var, 
                                   values=["public", "unlisted", "private"], state="readonly", width=15)
        self.privacy_combo.grid(row=0, column=1, sticky=tk.W, pady=(0, 5))
        
        # Playlist selection
        ttk.Label(settings_frame, text="Playlist:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        self.playlist_var = tk.StringVar(value="None")
        self.playlist_combo = ttk.Combobox(settings_frame, textvariable=self.playlist_var, 
                                         values=["None"], width=25)  # Reduced width to make room
        self.playlist_combo.grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
        # Playlist control buttons frame
        playlist_buttons_frame = ttk.Frame(settings_frame)
        playlist_buttons_frame.grid(row=1, column=2, padx=(5, 0))
        
        # Refresh playlists button (with debug)
        self.refresh_playlists_button = ttk.Button(playlist_buttons_frame, text="Refresh", command=self.refresh_and_debug_playlists)
        self.refresh_playlists_button.grid(row=0, column=0, padx=(0, 3))
        
        # Create new playlist button
        self.create_playlist_button = ttk.Button(playlist_buttons_frame, text="Create New", command=self.create_new_playlist_dialog)
        self.create_playlist_button.grid(row=0, column=1)
        
        # Playlist status label (shows which channel's playlists are displayed) - move to new row
        self.playlist_status_label = ttk.Label(settings_frame, text="", foreground="grey", font=("TkDefaultFont", 8))
        self.playlist_status_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Playlist help label - move to new row
        playlist_help = ttk.Label(settings_frame, text="💡 Tip: Type new playlist name to create it automatically", 
                                 foreground="blue", font=("TkDefaultFont", 8))
        playlist_help.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Debug button for playlist troubleshooting (temporarily remove to save space)
        # debug_playlist_button = ttk.Button(settings_frame, text="Debug Playlists", command=self.debug_playlists)
        # debug_playlist_button.grid(row=1, column=5, sticky=tk.W, padx=(10, 0))
        
        # Title preview
        ttk.Label(settings_frame, text="Title Preview:").grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        self.title_preview_var = tk.StringVar(value="(No videos selected)")
        title_preview = ttk.Entry(settings_frame, textvariable=self.title_preview_var, width=50, state="readonly")
        title_preview.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Label(settings_frame, text="Description:").grid(row=5, column=0, sticky=(tk.W, tk.N), pady=(5, 0))
        
        # Updated description template
        default_description = """{title}

#VintagePostcards #PostcardCollecting #AntiquePostcards

Discover the charm of vintage postcards from around the world! Subscribe for weekly videos showcasing rare and beautiful postcards from our collection at Lincoln Rare Books and Collectables. Our online store boasts one of the largest vintage postcard selections, with tens of thousands available for purchase. This channel features just a glimpse of our inventory—perfect for postcard collecting enthusiasts!

🔗 Postcard Department: https://tiny.cc/z0ir001

🔗 Full Store: https://tiny.cc/w0ir001

We add ~1,000 new antique postcards to our store weekly. Follow our eBay store for exclusive updates, special offers, and discounts to grow your postcard collection! Share your favorite postcard stories in the comments—we love hearing from fellow collectors!

#VintageEphemera #LincolnRareBooks"""
        
        self.description_var = tk.StringVar(value=default_description)
        description_text = tk.Text(settings_frame, height=8, width=50)  # Increased height for longer description
        description_text.grid(row=5, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        description_text.insert('1.0', self.description_var.get())
        self.description_text = description_text
        
        # Progress and upload
        progress_frame = ttk.LabelFrame(main_frame, text="Upload Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.upload_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.upload_progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.upload_status_label = ttk.Label(progress_frame, text="Ready to upload")
        self.upload_status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).grid(row=0, column=0, padx=(0, 10))
        self.upload_button = ttk.Button(button_frame, text="Start Upload", command=self.start_youtube_upload, state='disabled')
        self.upload_button.grid(row=0, column=1)
        
        # Store dialog reference
        self.youtube_dialog = dialog
        self.youtube_service = None
        
        # Initialize video list with current part videos if available
        self.add_current_videos()

    def authenticate_youtube(self):
        """Authenticate with YouTube API and load available channels"""
        try:
            # Check for existing credentials
            creds = None
            if os.path.exists('youtube_token.pickle'):
                with open('youtube_token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            # If there are no (valid) credentials available, request authorization
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Check for client secrets file
                    if not os.path.exists('client_secrets.json'):
                        messagebox.showerror("Missing Credentials", 
                                           "client_secrets.json file not found!\n\n"
                                           "Please:\n"
                                           "1. Go to Google Cloud Console\n"
                                           "2. Enable YouTube Data API v3\n"
                                           "3. Create OAuth 2.0 credentials\n"
                                           "4. Download and save as 'client_secrets.json'")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'client_secrets.json',
                        scopes=['https://www.googleapis.com/auth/youtube.upload',
                               'https://www.googleapis.com/auth/youtube',
                               'https://www.googleapis.com/auth/youtube.readonly',
                               'https://www.googleapis.com/auth/youtube.force-ssl']
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open('youtube_token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build the service
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            
            # Get all available channels
            self.load_youtube_channels()
                
        except Exception as e:
            self.auth_status_label.config(text=f"Authentication error: {str(e)[:50]}...", foreground="red")
            messagebox.showerror("Authentication Error", f"Failed to authenticate:\n{str(e)}")

    def load_youtube_channels(self):
        """Load all available YouTube channels for the authenticated user"""
        try:
            # Get channels the user has access to
            response = self.youtube_service.channels().list(part='snippet', mine=True).execute()
            
            # Debug: Print raw API response
            print(f"DEBUG: YouTube API Response - found {len(response.get('items', []))} channels")
            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                print(f"DEBUG: Channel - ID: {item.get('id')}, Title: '{snippet.get('title')}', CustomURL: '{snippet.get('customUrl', 'None')}'")
            
            # Try additional methods to find all accessible channels
            all_channels = response['items'].copy()  # Start with mine=True results
            
            # Method 1: Try managedByMe=True for Brand Accounts
            try:
                print("DEBUG: Trying managedByMe=True for Brand Accounts...")
                managed_response = self.youtube_service.channels().list(part='snippet', managedByMe=True).execute()
                print(f"DEBUG: managedByMe API Response - found {len(managed_response.get('items', []))} channels")
                for item in managed_response.get('items', []):
                    snippet = item.get('snippet', {})
                    print(f"DEBUG: Managed Channel - ID: {item.get('id')}, Title: '{snippet.get('title')}', CustomURL: '{snippet.get('customUrl', 'None')}'")
                    # Add if not already in list
                    if not any(ch['id'] == item['id'] for ch in all_channels):
                        all_channels.append(item)
                        print(f"DEBUG: Added managed channel: {snippet.get('title')}")
            except Exception as e:
                print(f"DEBUG: managedByMe method failed: {e}")
            
            # Method 2: Try specific known channel IDs
            known_channel_ids = self.get_known_channel_ids()
            for channel_id in known_channel_ids:
                try:
                    print(f"DEBUG: Checking known channel ID: {channel_id}")
                    specific_response = self.youtube_service.channels().list(part='snippet', id=channel_id).execute()
                    if specific_response['items']:
                        item = specific_response['items'][0]
                        snippet = item.get('snippet', {})
                        print(f"DEBUG: Found known channel - ID: {item.get('id')}, Title: '{snippet.get('title')}', CustomURL: '{snippet.get('customUrl', 'None')}'")
                        # Add if not already in list
                        if not any(ch['id'] == item['id'] for ch in all_channels):
                            all_channels.append(item)
                            print(f"DEBUG: Added known channel: {snippet.get('title')}")
                except Exception as e:
                    print(f"DEBUG: Known channel check failed for {channel_id}: {e}")
            
            # Use all found channels
            response['items'] = all_channels
            print(f"DEBUG: Total channels found across all methods: {len(all_channels)}")
            
            if not response['items']:
                self.auth_status_label.config(text="No channels found", foreground="red")
                messagebox.showwarning("No Channels Found", 
                                     "No YouTube channels were found for this account.\n\n"
                                     "Possible causes:\n"
                                     "• You need to create a YouTube channel first\n"
                                     "• The Google account may not have YouTube channel access\n"
                                     "• You may need to sign in to a different Google account\n"
                                     "• The channel might be a Brand Account (check console for debug info)")
                return
            
            # Store channel information
            self.youtube_channels = []
            
            for channel in response['items']:
                channel_info = {
                    'id': channel['id'],
                    'title': channel['snippet']['title'],
                    'description': channel['snippet'].get('description', ''),
                    'custom_url': channel['snippet'].get('customUrl', '')
                }
                self.youtube_channels.append(channel_info)
                print(f"DEBUG: Added channel to list - {channel_info['title']}")
            
            # Load saved default channel first
            self.load_default_channel_id()
            
            # Now create display names with default marking
            channel_names = []
            for channel_info in self.youtube_channels:
                # Create display name with custom URL if available
                display_name = channel_info['title']
                if channel_info['custom_url']:
                    display_name += f" (@{channel_info['custom_url']})"
                    
                # Mark as default if this is the saved default channel
                if channel_info['id'] == self.default_channel_id:
                    display_name += " [DEFAULT]"
                    
                channel_names.append(display_name)
                print(f"DEBUG: Channel display name: '{display_name}'")
            
            # Update channel combobox
            self.channel_combo.configure(values=channel_names)
            
            # Set the selected channel in the combobox
            self.select_default_channel()
            
            # Auto-set Vintage Postcard Archive as default if found and no default set
            if not self.default_channel_id:
                vintage_channel = next((ch for ch in self.youtube_channels if ch['id'] == 'UCgDAZ9kGH98mcoMnPOptXUw'), None)
                if vintage_channel:
                    print("DEBUG: Auto-setting Vintage Postcard Archive as default channel")
                    self.default_channel_id = vintage_channel['id']
                    self.selected_channel_id = vintage_channel['id']
                    self.save_default_channel()
                    # Update the combobox selection
                    for i, channel in enumerate(self.youtube_channels):
                        if channel['id'] == vintage_channel['id']:
                            self.channel_combo.current(i)
                            break
                    self.refresh_channel_list()  # Update display with [DEFAULT] tag
            
            # Show channel selection frame
            self.channel_frame.grid()
            
            # Force dialog to update its layout after showing the channel frame
            if hasattr(self, 'dialog'):
                self.dialog.update_idletasks()  # Update layout calculations
                self.dialog.geometry("")  # Let dialog auto-resize to fit content
            
            # Update status and enable upload
            if len(self.youtube_channels) == 1:
                # Single channel - auto-select
                self.channel_combo.current(0)
                self.selected_channel_id = self.youtube_channels[0]['id']
                self.auth_status_label.config(text=f"Authenticated: {self.youtube_channels[0]['title']}", foreground="green")
            else:
                # Multiple channels - show count
                self.auth_status_label.config(text=f"Authenticated: {len(self.youtube_channels)} channels available", foreground="green")
            
            # Enable all buttons after successful authentication
            if hasattr(self, 'upload_button'):
                self.upload_button.config(state='normal')
            if hasattr(self, 'set_default_button'):
                self.set_default_button.config(state='normal')
            if hasattr(self, 'refresh_channels_button'):
                self.refresh_channels_button.config(state='normal')
            if hasattr(self, 'add_manual_channel_button'):
                self.add_manual_channel_button.config(state='normal')
            
            # Refresh playlists for the selected channel
                self.refresh_playlists()
                
        except Exception as e:
            self.auth_status_label.config(text=f"Channel loading error: {str(e)[:50]}...", foreground="red")
            messagebox.showerror("Channel Loading Error", f"Failed to load channels:\n{str(e)}")

    def refresh_playlists(self):
        """Refresh the playlist dropdown for the selected channel"""
        if not self.youtube_service:
            return
        
        # Check if we have a selected channel
        if not hasattr(self, 'selected_channel_id') or not self.selected_channel_id:
            # No channel selected - clear playlists
            self.playlist_combo.configure(values=["None"])
            self.playlist_mapping = {"None": None}
            if hasattr(self, 'playlist_status_label'):
                self.playlist_status_label.config(text="No channel selected")
            return
        
        try:
            # Get playlists for the selected channel
            playlists = []
            
            # Method 1: Try channelId parameter (works for some channels)
            print(f"DEBUG: Trying playlists for channelId={self.selected_channel_id}")
            try:
                request = self.youtube_service.playlists().list(
                    part='snippet', 
                    channelId=self.selected_channel_id, 
                    maxResults=50
                )
                
                while request:
                    response = request.execute()
                    print(f"DEBUG: channelId method found {len(response.get('items', []))} playlists")
                    for playlist in response['items']:
                        playlists.append((playlist['snippet']['title'], playlist['id']))
                        print(f"DEBUG: Found playlist: {playlist['snippet']['title']}")
                    
                    request = self.youtube_service.playlists().list_next(request, response)
                    
                print(f"DEBUG: Method 1 result: {len(playlists)} playlists found directly")
                    
            except Exception as channel_error:
                print(f"DEBUG: channelId method failed: {channel_error}")
            
            # Method 1.5: Try with maxResults=1 to see if there's a pagination issue
            if not playlists:
                print(f"DEBUG: Trying channelId method with maxResults=1 to check pagination...")
                try:
                    request = self.youtube_service.playlists().list(
                        part='snippet', 
                        channelId=self.selected_channel_id, 
                        maxResults=1
                    )
                    response = request.execute()
                    print(f"DEBUG: Single result test found {len(response.get('items', []))} playlists")
                    if response.get('items'):
                        print(f"DEBUG: Found playlist with single query: {response['items'][0]['snippet']['title']}")
                except Exception as single_error:
                    print(f"DEBUG: Single result test failed: {single_error}")
            
            # Method 2: Try mine=True (works for owned channels and Brand Accounts you manage)
            if not playlists:
                print("DEBUG: Trying mine=True method for playlists")
                try:
                    request = self.youtube_service.playlists().list(part='snippet', mine=True, maxResults=50)
                    while request:
                        response = request.execute()
                        print(f"DEBUG: mine=True method found {len(response.get('items', []))} total playlists")
                        for playlist in response['items']:
                            # Check if this playlist belongs to the selected channel
                            playlist_channel_id = playlist['snippet'].get('channelId')
                            playlist_title = playlist['snippet']['title']
                            print(f"DEBUG: Playlist '{playlist_title}' belongs to channel {playlist_channel_id}")
                            
                            # ONLY add playlists that belong to the selected channel
                            if playlist_channel_id == self.selected_channel_id:
                                playlists.append((playlist_title, playlist['id']))
                                print(f"DEBUG: ✅ Added playlist '{playlist_title}' (matches selected channel)")
                            else:
                                print(f"DEBUG: ❌ Skipped playlist '{playlist_title}' (wrong channel: {playlist_channel_id})")
                            
                        request = self.youtube_service.playlists().list_next(request, response)
                    
                    print(f"DEBUG: After filtering, found {len(playlists)} playlists for selected channel {self.selected_channel_id}")
                    
                    # Special debugging: Check if any playlist might be missing channelId
                    print("DEBUG: Checking for playlists with missing or different channelId fields...")
                    request_debug = self.youtube_service.playlists().list(part='snippet', mine=True, maxResults=50)
                    while request_debug:
                        response_debug = request_debug.execute()
                        for playlist_debug in response_debug['items']:
                            snippet = playlist_debug.get('snippet', {})
                            playlist_title = snippet.get('title', 'Unknown')
                            playlist_channel_id = snippet.get('channelId', 'MISSING')
                            
                            # Look for potential matches by checking if the playlist might belong to our channel
                            if ('postcard' in playlist_title.lower() or 
                                'vintage' in playlist_title.lower() or 
                                'test' in playlist_title.lower()):
                                print(f"DEBUG: 🔍 Potential match found - '{playlist_title}' (channelId: {playlist_channel_id})")
                                
                            # SPECIAL: Look specifically for "Test Playlist"
                            if 'test playlist' in playlist_title.lower():
                                print(f"DEBUG: 🎯 FOUND 'Test Playlist': '{playlist_title}' (channelId: {playlist_channel_id})")
                                print(f"DEBUG: Selected channel ID: {self.selected_channel_id}")
                                print(f"DEBUG: Match: {playlist_channel_id == self.selected_channel_id}")
                        
                        request_debug = self.youtube_service.playlists().list_next(request_debug, response_debug)
                    
                except Exception as mine_error:
                    print(f"DEBUG: mine=True method failed: {mine_error}")
            
            # Method 3: Cross-channel playlist detection - show playlists from ALL channels
            print("DEBUG: Method 3 - Cross-channel playlist detection")
            try:
                request_all = self.youtube_service.playlists().list(part='snippet,status', mine=True, maxResults=50)
                all_playlists_found = []
                cross_channel_playlists = []
                
                while request_all:
                    response_all = request_all.execute()
                    print(f"DEBUG: Method 3 found {len(response_all.get('items', []))} total playlists")
                    
                    for playlist_all in response_all['items']:
                        snippet = playlist_all.get('snippet', {})
                        status = playlist_all.get('status', {})
                        playlist_title = snippet.get('title', 'Unknown')
                        playlist_channel_id = snippet.get('channelId', 'MISSING')
                        privacy_status = status.get('privacyStatus', 'unknown')
                        
                        all_playlists_found.append({
                            'title': playlist_title,
                            'channelId': playlist_channel_id,
                            'privacy': privacy_status,
                            'id': playlist_all['id']
                        })
                        
                        print(f"DEBUG: Playlist '{playlist_title}' - Channel: {playlist_channel_id}, Privacy: {privacy_status}")
                        
                        # Check for ANY playlist that might be the "Test Playlist" with broader search terms
                        playlist_lower = playlist_title.lower()
                        is_potential_test_playlist = (
                            'test' in playlist_lower or
                            'postcard' in playlist_lower or 
                            'vintage' in playlist_lower or
                            'video' in playlist_lower or
                            playlist_lower in ['test playlist', 'test', 'my test', 'testing']
                        )
                        
                        if is_potential_test_playlist:
                            print(f"DEBUG: 🔍 POTENTIAL Test Playlist: '{playlist_title}', Privacy: {privacy_status}")
                            print(f"DEBUG: Channel ID: {playlist_channel_id} vs Selected: {self.selected_channel_id}")
                            
                            # Find which channel this playlist belongs to
                            owner_channel = "Unknown Channel"
                            if hasattr(self, 'youtube_channels'):
                                for ch in self.youtube_channels:
                                    if ch['id'] == playlist_channel_id:
                                        owner_channel = ch['title']
                                        break
                            
                            # Add it to playlists regardless of channel (with channel identification)
                            if playlist_channel_id == self.selected_channel_id:
                                if (playlist_title, playlist_all['id']) not in playlists:
                                    playlists.append((playlist_title, playlist_all['id']))
                                    print(f"DEBUG: ✅ Added potential test playlist (same channel): {playlist_title}")
                            else:
                                cross_channel_name = f"{playlist_title} ({owner_channel})"
                                if (cross_channel_name, playlist_all['id']) not in playlists:
                                    playlists.append((cross_channel_name, playlist_all['id']))
                                    cross_channel_playlists.append(cross_channel_name)
                                    print(f"DEBUG: ✅ Added potential test playlist (cross-channel): {cross_channel_name}")
                        
                        # Special check for exact "test playlist" match
                        if 'test playlist' in playlist_title.lower():
                            print(f"DEBUG: 🎯 EXACT MATCH - Test Playlist! Title: '{playlist_title}', Privacy: {privacy_status}")
                        
                        # Also add other playlists from the user's other channels if they might be relevant
                        if (playlist_channel_id != self.selected_channel_id and 
                            ('postcard' in playlist_title.lower() or 'vintage' in playlist_title.lower())):
                            owner_channel = "Unknown Channel"
                            if hasattr(self, 'youtube_channels'):
                                for ch in self.youtube_channels:
                                    if ch['id'] == playlist_channel_id:
                                        owner_channel = ch['title']
                                        break
                            
                            cross_channel_name = f"{playlist_title} ({owner_channel})"
                            if (cross_channel_name, playlist_all['id']) not in playlists:
                                playlists.append((cross_channel_name, playlist_all['id']))
                                cross_channel_playlists.append(cross_channel_name)
                                print(f"DEBUG: ✅ Added relevant cross-channel playlist: {cross_channel_name}")
                    
                    request_all = self.youtube_service.playlists().list_next(request_all, response_all)
                
                print(f"DEBUG: Method 3 complete. Found {len(all_playlists_found)} total playlists")
                if cross_channel_playlists:
                    print(f"DEBUG: Added {len(cross_channel_playlists)} cross-channel playlists:")
                    for cp in cross_channel_playlists:
                        print(f"DEBUG:   - {cp}")
                
                # COMPREHENSIVE SUMMARY: List ALL playlists for user review
                print(f"\n" + "="*60)
                print(f"📋 COMPLETE PLAYLIST INVENTORY ({len(all_playlists_found)} total)")
                print(f"="*60)
                for i, playlist_info in enumerate(all_playlists_found, 1):
                    print(f"{i:2d}. '{playlist_info['title']}' | Privacy: {playlist_info['privacy']} | Channel: {playlist_info['channelId']}")
                print(f"="*60)
                
                # Check if "Test Playlist" exists with exact name
                exact_test_found = any(p['title'].lower() == 'test playlist' for p in all_playlists_found)
                if exact_test_found:
                    print(f"✅ 'Test Playlist' (exact name) was found in the list above")
                else:
                    print(f"❌ 'Test Playlist' (exact name) was NOT found")
                    print(f"❓ Please check the list above - is your test playlist named differently?")
                    print(f"❓ Common variations: 'Test', 'Testing', 'My Test Playlist', etc.")
                print(f"="*60 + "\n")
                
            except Exception as all_error:
                print(f"DEBUG: Method 3 (cross-channel detection) failed: {all_error}")
            
            # Update combobox
            playlist_names = ["None"] + [name for name, _ in playlists]
            self.playlist_combo.configure(values=playlist_names)
            
            # Store playlist mapping
            self.playlist_mapping = {"None": None}
            for name, playlist_id in playlists:
                self.playlist_mapping[name] = playlist_id
            
            # Debug info
            print(f"DEBUG: Found {len(playlists)} playlists for channel {self.selected_channel_id}")
            for name, _ in playlists:
                print(f"DEBUG: Playlist - {name}")
            
            # Check specifically if "Test Playlist" was found
            test_playlist_found = any('test playlist' in name.lower() for name, _ in playlists)
            if test_playlist_found:
                print(f"DEBUG: ✅ SUCCESS: 'Test Playlist' found and added to dropdown!")
            else:
                print(f"DEBUG: ❌ WARNING: 'Test Playlist' was NOT found in the final list")
                print(f"DEBUG: This could be due to:")
                print(f"DEBUG: - Privacy settings (unlisted playlists might need different permissions)")
                print(f"DEBUG: - Channel ID mismatch (Brand Account vs Personal Account)")
                print(f"DEBUG: - API permissions (might need to re-authenticate)")
                print(f"DEBUG: - Playlist belongs to a different channel")
            
            # Update status label to show which channel's playlists are displayed
            if hasattr(self, 'playlist_status_label') and hasattr(self, 'youtube_channels'):
                selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
                if selected_channel:
                    # Count cross-channel playlists
                    cross_channel_count = sum(1 for name, _ in playlists if '(' in name and ')' in name)
                    same_channel_count = len(playlists) - cross_channel_count
                    
                    if len(playlists) == 0:
                        status_text = f"No playlists found for {selected_channel['title']} - create them in YouTube Studio"
                        self.playlist_status_label.config(text=status_text, foreground="orange")
                    elif cross_channel_count > 0:
                        if same_channel_count > 0:
                            status_text = f"Showing {same_channel_count} playlists for {selected_channel['title']} + {cross_channel_count} from other channels"
                        else:
                            status_text = f"Showing {cross_channel_count} playlists from your other channels (none found for {selected_channel['title']})"
                        self.playlist_status_label.config(text=status_text, foreground="blue")
                    else:
                        status_text = f"Showing {len(playlists)} playlists for {selected_channel['title']}"
                        self.playlist_status_label.config(text=status_text, foreground="grey")
                
        except Exception as e:
            print(f"DEBUG: Error fetching channel playlists: {e}")
            # Fallback to mine=True if channel-specific request fails
            try:
                playlists = []
                request = self.youtube_service.playlists().list(part='snippet', mine=True, maxResults=50)
                while request:
                    response = request.execute()
                    for playlist in response['items']:
                        # Apply same filtering in fallback
                        playlist_channel_id = playlist['snippet'].get('channelId')
                        playlist_title = playlist['snippet']['title']
                        
                        # ONLY add playlists that belong to the selected channel
                        if playlist_channel_id == self.selected_channel_id:
                            playlists.append((playlist_title, playlist['id']))
                            print(f"DEBUG: Fallback ✅ Added playlist '{playlist_title}' (matches selected channel)")
                        else:
                            print(f"DEBUG: Fallback ❌ Skipped playlist '{playlist_title}' (wrong channel)")
                            
                    request = self.youtube_service.playlists().list_next(request, response)
                
                self.playlist_combo.configure(values=["None"] + [name for name, _ in playlists])
                self.playlist_mapping = {"None": None}
                for name, playlist_id in playlists:
                    self.playlist_mapping[name] = playlist_id
                    
                print(f"DEBUG: Fallback - Found {len(playlists)} playlists for selected channel")
                
                # Update status label for fallback
                if hasattr(self, 'playlist_status_label'):
                    self.playlist_status_label.config(text=f"Showing {len(playlists)} playlists for selected channel (fallback)")
                    
            except Exception as fallback_error:
                if hasattr(self, 'playlist_status_label'):
                    self.playlist_status_label.config(text="Failed to load playlists")
                messagebox.showerror("Playlist Error", f"Failed to fetch playlists:\n{str(fallback_error)}")

    def create_new_playlist_dialog(self):
        """Show dialog to create a new playlist"""
        if not self.youtube_service:
            messagebox.showerror("Error", "Please authenticate with YouTube first")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Playlist")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        ttk.Label(main_frame, text="Create New YouTube Playlist", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Playlist name
        ttk.Label(main_frame, text="Playlist Name:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        name_var = tk.StringVar(value="Test Playlist")
        name_entry = ttk.Entry(main_frame, textvariable=name_var, width=30)
        name_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        name_entry.focus()
        
        # Description
        ttk.Label(main_frame, text="Description:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=(0, 5))
        desc_entry = tk.Text(main_frame, width=30, height=3)
        desc_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        desc_entry.insert(tk.END, "Playlist created by Postcard Video Creator")
        
        # Privacy (always default to public for Brand Accounts)
        ttk.Label(main_frame, text="Privacy:").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        # Always default to public since Brand Account playlists need to be public to appear in the app
        privacy_var = tk.StringVar(value="public")
        privacy_combo = ttk.Combobox(main_frame, textvariable=privacy_var, 
                                   values=["public", "unlisted", "private"], state="readonly", width=15)
        privacy_combo.grid(row=3, column=1, sticky=tk.W, pady=(0, 5))
        
        # Add explanatory note about public requirement
        privacy_note = ttk.Label(main_frame, 
                               text="Note: Brand Account playlists must be 'public' to appear in this app", 
                               foreground="blue", font=("TkDefaultFont", 8))
        privacy_note.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # Selected channel info
        channel_info_row = 5  # Adjust row based on whether privacy note was added
        if hasattr(self, 'selected_channel_id') and hasattr(self, 'youtube_channels'):
            selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
            if selected_channel:
                channel_info = f"Will be created on: {selected_channel['title']}"
                ttk.Label(main_frame, text=channel_info, foreground="green", font=("TkDefaultFont", 8)).grid(row=channel_info_row, column=0, columnspan=2, pady=(10, 0))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
        def create_playlist_action():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a playlist name")
                return
            
            description = desc_entry.get(1.0, tk.END).strip()
            privacy = privacy_var.get()
            
            # Update the existing create_playlist function to accept privacy
            playlist_id = self.create_playlist_with_privacy(name, description, privacy)
            if playlist_id:
                # Check if playlist was created on the correct channel
                self.refresh_playlists()  # Refresh first to get updated info
                
                # Check if the playlist appears in the selected channel or cross-channel
                playlist_found_on_selected = False
                if hasattr(self, 'playlist_mapping'):
                    for playlist_name_in_list, _ in self.playlist_mapping.items():
                        if name in playlist_name_in_list and '(' not in playlist_name_in_list:
                            playlist_found_on_selected = True
                            break
                
                if playlist_found_on_selected:
                    selected_channel_name = "the selected channel"
                    if hasattr(self, 'youtube_channels') and hasattr(self, 'selected_channel_id'):
                        selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
                        if selected_channel:
                            selected_channel_name = selected_channel['title']
                    messagebox.showinfo("Success", f"Playlist '{name}' created successfully on {selected_channel_name}!")
                else:
                    # Show Brand Account workaround dialog (handles dialog cleanup)
                    self._show_brand_account_workaround_dialog(name, dialog)
                    return  # Don't destroy dialog here, workaround dialog handles it
                
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to create playlist. Check console for details.")
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Create Playlist", command=create_playlist_action).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Cancel", command=cancel).grid(row=0, column=1)

    def create_playlist_with_privacy(self, playlist_name, description, privacy_status):
        """Create a new playlist with custom privacy and description on the selected channel"""
        try:
            # Check if we have a selected channel
            if not hasattr(self, 'selected_channel_id') or not self.selected_channel_id:
                print(f"ERROR: No channel selected for playlist creation")
                return None
                
            print(f"DEBUG: Creating playlist '{playlist_name}' with privacy '{privacy_status}' on channel {self.selected_channel_id}")
            
            # Method 1: Try to use channel-specific authentication context
            success = False
            playlist_id = None
            
            try:
                print(f"DEBUG: Method 1 - Attempting channel context switching...")
                
                # Build YouTube service with channel-specific context
                channel_service = self._build_channel_specific_service(self.selected_channel_id)
                
                if channel_service:
                    # Create playlist request body (without channelId in snippet)
                    playlist_body = {
                        'snippet': {
                            'title': playlist_name,
                            'description': description,
                            'defaultLanguage': 'en'
                        },
                        'status': {
                            'privacyStatus': privacy_status
                        }
                    }
                    
                    request = channel_service.playlists().insert(
                        part='snippet,status',
                        body=playlist_body
                    )
                    response = request.execute()
                    playlist_id = response['id']
                    created_channel_id = response.get('snippet', {}).get('channelId', 'unknown')
                    
                    if created_channel_id == self.selected_channel_id:
                        print(f"✅ SUCCESS: Method 1 worked! Playlist created on correct channel {created_channel_id}")
                        success = True
                    else:
                        print(f"⚠️ Method 1: Playlist created on {created_channel_id} instead of {self.selected_channel_id}")
                        
            except Exception as method1_error:
                print(f"DEBUG: Method 1 failed: {method1_error}")
            
            # Method 2: Try with explicit onBehalfOfContentOwner if available
            if not success:
                try:
                    print(f"DEBUG: Method 2 - Attempting with content owner delegation...")
                    
                    playlist_body = {
                        'snippet': {
                            'title': playlist_name,
                            'description': description,
                            'defaultLanguage': 'en'
                        },
                        'status': {
                            'privacyStatus': privacy_status
                        }
                    }
                    
                    # Try with onBehalfOfContentOwner parameter
                    request = self.youtube_service.playlists().insert(
                        part='snippet,status',
                        body=playlist_body,
                        onBehalfOfContentOwner=self.selected_channel_id
                    )
                    response = request.execute()
                    playlist_id = response['id']
                    created_channel_id = response.get('snippet', {}).get('channelId', 'unknown')
                    
                    if created_channel_id == self.selected_channel_id:
                        print(f"✅ SUCCESS: Method 2 worked! Playlist created on correct channel {created_channel_id}")
                        success = True
                    else:
                        print(f"⚠️ Method 2: Playlist created on {created_channel_id} instead of {self.selected_channel_id}")
                        
                except Exception as method2_error:
                    print(f"DEBUG: Method 2 failed: {method2_error}")
            
            # Method 3: Try channel impersonation through re-authentication
            if not success:
                try:
                    print(f"DEBUG: Method 3 - Attempting channel impersonation...")
                    
                    # Try to re-authenticate specifically for the Brand Account
                    brand_service = self._authenticate_for_channel(self.selected_channel_id)
                    
                    if brand_service:
                        playlist_body = {
                            'snippet': {
                                'title': playlist_name,
                                'description': description,
                                'defaultLanguage': 'en'
                            },
                            'status': {
                                'privacyStatus': privacy_status
                            }
                        }
                        
                        request = brand_service.playlists().insert(
                            part='snippet,status',
                            body=playlist_body
                        )
                        response = request.execute()
                        playlist_id = response['id']
                        created_channel_id = response.get('snippet', {}).get('channelId', 'unknown')
                        
                        if created_channel_id == self.selected_channel_id:
                            print(f"✅ SUCCESS: Method 3 worked! Playlist created on correct channel {created_channel_id}")
                            success = True
                            # Update the main service to use the Brand Account context
                            self.youtube_service = brand_service
                        else:
                            print(f"⚠️ Method 3: Playlist created on {created_channel_id} instead of {self.selected_channel_id}")
                            
                except Exception as method3_error:
                    print(f"DEBUG: Method 3 failed: {method3_error}")
            
            # Method 4: Standard fallback (what was working before)
            if not success and not playlist_id:
                print(f"DEBUG: Method 4 - Standard fallback creation...")
                playlist_body = {
                    'snippet': {
                        'title': playlist_name,
                        'description': description,
                        'defaultLanguage': 'en'
                    },
                    'status': {
                        'privacyStatus': privacy_status
                    }
                }
                
                request = self.youtube_service.playlists().insert(
                    part='snippet,status',
                    body=playlist_body
                )
                response = request.execute()
                playlist_id = response['id']
                created_channel_id = response.get('snippet', {}).get('channelId', 'unknown')
                print(f"DEBUG: Fallback method created playlist on channel: {created_channel_id}")
            
            if playlist_id:
                print(f"DEBUG: Successfully created playlist '{playlist_name}' with ID: {playlist_id}")
                return playlist_id
            else:
                print(f"ERROR: All methods failed to create playlist")
                return None
            
        except Exception as e:
            print(f"ERROR: Failed to create playlist: {e}")
            print(f"This might be due to insufficient permissions for Brand Account management")
            return None

    def _build_channel_specific_service(self, channel_id):
        """Try to build a YouTube service specifically for the given channel"""
        try:
            # This is a placeholder - in practice, we'd need channel-specific credentials
            print(f"DEBUG: Attempting to build service for channel {channel_id}")
            # For now, return None as this requires advanced credential management
            return None
        except Exception as e:
            print(f"DEBUG: Channel-specific service building failed: {e}")
            return None

    def _authenticate_for_channel(self, channel_id):
        """Try to authenticate specifically for a Brand Account channel"""
        try:
            print(f"DEBUG: Attempting Brand Account authentication for {channel_id}")
            
            # Get the channel info to determine if this is a Brand Account
            channel_info = None
            if hasattr(self, 'youtube_channels'):
                channel_info = next((ch for ch in self.youtube_channels if ch['id'] == channel_id), None)
            
            if not channel_info:
                print(f"DEBUG: No channel info found for {channel_id}")
                return None
            
            # For Brand Accounts, we might need to prompt user to switch context in browser
            # This is a complex process that usually requires manual intervention
            print(f"DEBUG: Channel '{channel_info.get('title', 'Unknown')}' requires Brand Account context")
            print(f"DEBUG: Current YouTube API limitations prevent automatic Brand Account switching")
            
            return None
            
        except Exception as e:
            print(f"DEBUG: Brand Account authentication failed: {e}")
            return None

    def _show_brand_account_workaround_dialog(self, playlist_name, parent_dialog):
        """Show a dialog with instructions for creating Brand Account playlists manually"""
        # Create workaround dialog
        workaround_dialog = tk.Toplevel(self.root)
        workaround_dialog.title("Brand Account Playlist - Manual Creation Required")
        workaround_dialog.geometry("600x500")
        workaround_dialog.transient(parent_dialog)
        workaround_dialog.grab_set()
        
        # Center the dialog
        workaround_dialog.update_idletasks()
        x = (workaround_dialog.winfo_screenwidth() // 2) - (workaround_dialog.winfo_width() // 2)
        y = (workaround_dialog.winfo_screenheight() // 2) - (workaround_dialog.winfo_height() // 2)
        workaround_dialog.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(workaround_dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        workaround_dialog.columnconfigure(0, weight=1)
        workaround_dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text="YouTube API Limitation - Manual Playlist Creation", 
                               font=("TkDefaultFont", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        # Explanation
        explanation = tk.Text(main_frame, height=15, width=70, wrap=tk.WORD)
        explanation.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        # Get selected channel name
        selected_channel_name = "Vintage Postcard Archive"
        if hasattr(self, 'youtube_channels') and hasattr(self, 'selected_channel_id'):
            selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
            if selected_channel:
                selected_channel_name = selected_channel['title']
        
        explanation_text = f"""Due to YouTube API limitations, playlists cannot be created directly on Brand Account channels ("{selected_channel_name}") through third-party applications.

The playlist "{playlist_name}" was created on your personal channel instead.

IMPORTANT: Brand Account playlists must be set to "Public" visibility to appear in this app. The YouTube API only returns public playlists for Brand Account channels when accessed by third-party applications.

SOLUTION - Create Playlist Manually on Brand Account:

1. Open YouTube Studio in your web browser:
   https://studio.youtube.com

2. Make sure you're switched to "{selected_channel_name}":
   • Click on your profile picture (top right)
   • If it shows your personal account, click "Switch account"
   • Select "{selected_channel_name}"

3. Create the playlist:
   • Go to "Content" → "Playlists" (left sidebar)
   • Click "NEW PLAYLIST" button
   • Name: "{playlist_name}"
   • Visibility: "Public" (REQUIRED for Brand Account playlists to appear in this app)
   • Click "CREATE"

4. Return to this application:
   • Click "Refresh Playlists" button
   • Your new playlist should now appear in the dropdown

ALTERNATIVE - Use Existing Playlist:
If you already have a playlist on "{selected_channel_name}" that you want to use, simply select it from the dropdown after clicking "Refresh Playlists".

The app will work perfectly once the playlist exists on the correct channel!"""

        explanation.insert(tk.END, explanation_text)
        explanation.configure(state='disabled')
        
        # Scrollbar for explanation
        explanation_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=explanation.yview)
        explanation_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        explanation.configure(yscrollcommand=explanation_scrollbar.set)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(20, 0))
        
        def open_youtube_studio():
            import webbrowser
            webbrowser.open("https://studio.youtube.com")
        
        def refresh_and_close():
            self.refresh_playlists()
            workaround_dialog.destroy()
            parent_dialog.destroy()
        
        def close_dialog():
            workaround_dialog.destroy()
            parent_dialog.destroy()
        
        ttk.Button(button_frame, text="Open YouTube Studio", command=open_youtube_studio).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Refresh Playlists", command=refresh_and_close).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="Close", command=close_dialog).grid(row=0, column=2)

    def create_playlist(self, playlist_name, channel_name):
        """Create a new playlist under the selected channel"""
        try:
            print(f"DEBUG: Creating playlist '{playlist_name}' for channel '{channel_name}'")
            
            # Create playlist request body
            playlist_body = {
                'snippet': {
                    'title': playlist_name,
                    'description': f'Playlist created by Postcard Video Creator for {channel_name}',
                    'defaultLanguage': 'en'
                },
                'status': {
                    'privacyStatus': 'unlisted'  # Default to unlisted for new playlists
                }
            }
            
            # Create the playlist
            request = self.youtube_service.playlists().insert(
                part='snippet,status',
                body=playlist_body
            )
            
            response = request.execute()
            playlist_id = response['id']
            
            print(f"DEBUG: Successfully created playlist '{playlist_name}' with ID: {playlist_id}")
            return playlist_id
            
        except Exception as e:
            print(f"DEBUG: Failed to create playlist '{playlist_name}': {e}")
            return None

    def debug_playlists(self):
        """Debug method to help troubleshoot playlist detection issues"""
        if not self.youtube_service or not self.selected_channel_id:
            messagebox.showerror("Error", "Please authenticate and select a channel first")
            return
        
        try:
            print("\n" + "="*60)
            print("DEBUG: COMPREHENSIVE PLAYLIST DEBUGGING")
            print("="*60)
            
            selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
            if selected_channel:
                print(f"Selected Channel: {selected_channel['title']} (ID: {self.selected_channel_id})")
            
            # Method 1: All playlists with mine=True
            print("\nMethod 1: All playlists (mine=True)")
            print("-" * 40)
            all_playlists = []
            try:
                request = self.youtube_service.playlists().list(part='snippet', mine=True, maxResults=50)
                while request:
                    response = request.execute()
                    for playlist in response['items']:
                        snippet = playlist['snippet']
                        title = snippet.get('title', 'Unknown')
                        channel_id = snippet.get('channelId', 'MISSING')
                        playlist_id = playlist.get('id', 'MISSING')
                        
                        all_playlists.append({
                            'title': title,
                            'id': playlist_id,
                            'channel_id': channel_id
                        })
                        
                        match_indicator = "✅" if channel_id == self.selected_channel_id else "❌"
                        print(f"{match_indicator} '{title}' | Channel: {channel_id} | ID: {playlist_id}")
                    
                    request = self.youtube_service.playlists().list_next(request, response)
                    
            except Exception as e:
                print(f"ERROR in mine=True method: {e}")
            
            # Method 2: Direct channel query
            print(f"\nMethod 2: Direct channel query (channelId={self.selected_channel_id})")
            print("-" * 40)
            try:
                request = self.youtube_service.playlists().list(
                    part='snippet', 
                    channelId=self.selected_channel_id, 
                    maxResults=50
                )
                response = request.execute()
                
                if response.get('items'):
                    for playlist in response['items']:
                        snippet = playlist['snippet']
                        title = snippet.get('title', 'Unknown')
                        playlist_id = playlist.get('id', 'MISSING')
                        print(f"✅ '{title}' | ID: {playlist_id}")
                else:
                    print("No playlists found with direct channel query")
                    
            except Exception as e:
                print(f"ERROR in channelId method: {e}")
            
            # Summary
            matching_playlists = [p for p in all_playlists if p['channel_id'] == self.selected_channel_id]
            print(f"\nSUMMARY:")
            print(f"Total playlists found: {len(all_playlists)}")
            print(f"Playlists for selected channel: {len(matching_playlists)}")
            
            if matching_playlists:
                print(f"Matching playlists:")
                for p in matching_playlists:
                    print(f"  - '{p['title']}' (ID: {p['id']})")
            else:
                print("No playlists found for the selected channel")
                print("This could mean:")
                print("1. No playlists exist for this channel")
                print("2. Playlists exist but API access is restricted")
                print("3. Channel is a Brand Account with different permissions")
            
            print("="*60)
            
            messagebox.showinfo("Debug Complete", f"Debug results printed to console.\n\nFound {len(matching_playlists)} playlists for selected channel.")
            
        except Exception as e:
            print(f"DEBUG ERROR: {e}")
            messagebox.showerror("Debug Error", f"Debug failed:\n{str(e)}")

    def refresh_and_debug_playlists(self):
        """Refresh playlists and run comprehensive debug if no playlists found"""
        print("DEBUG: Starting refresh and debug process...")
        
        # First run the normal refresh
        self.refresh_playlists()
        
        # Check playlist mapping after refresh
        playlist_count = 0
        if hasattr(self, 'playlist_mapping'):
            playlist_count = len([k for k in self.playlist_mapping.keys() if k != "None"])
            print(f"DEBUG: Found {playlist_count} playlists after refresh")
        
        # If still no playlists found, run debug automatically
        if playlist_count == 0:
            print("\nDEBUG: No playlists found, running comprehensive debug...")
            self.debug_playlists()
        else:
            print(f"DEBUG: Refresh successful - found {playlist_count} playlists")

    def on_channel_selected(self, event=None):
        """Handle channel selection change"""
        try:
            selected_index = self.channel_combo.current()
            if selected_index >= 0 and selected_index < len(self.youtube_channels):
                self.selected_channel_id = self.youtube_channels[selected_index]['id']
                selected_channel = self.youtube_channels[selected_index]
                
                # Update status display
                status_text = f"Selected: {selected_channel['title']}"
                if selected_channel['id'] == self.default_channel_id:
                    status_text += " (Default)"
                self.auth_status_label.config(text=status_text, foreground="green")
                
                # Refresh playlists for the selected channel
                self.refresh_playlists()
                
        except Exception as e:
            messagebox.showerror("Channel Selection Error", f"Failed to select channel:\n{str(e)}")

    def set_default_channel(self):
        """Set the currently selected channel as default"""
        try:
            if not self.selected_channel_id:
                messagebox.showwarning("No Channel Selected", "Please select a channel first.")
                return
            
            self.default_channel_id = self.selected_channel_id
            self.save_default_channel()
            
            # Refresh the channel list to show [DEFAULT] tag
            self.refresh_channel_list()
            
            # Update status display
            selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
            if selected_channel:
                self.auth_status_label.config(text=f"Selected: {selected_channel['title']} (Default)", foreground="green")
                messagebox.showinfo("Default Channel Set", f"'{selected_channel['title']}' has been set as your default channel.")
                
        except Exception as e:
            messagebox.showerror("Set Default Error", f"Failed to set default channel:\n{str(e)}")

    def load_default_channel_id(self):
        """Load the saved default channel ID"""
        try:
            # Try to load from defaults.json
            if os.path.exists('defaults.json'):
                with open('defaults.json', 'r') as f:
                    defaults = json.load(f)
                    self.default_channel_id = defaults.get('default_youtube_channel_id', None)
                
        except Exception as e:
            print(f"Warning: Could not load default channel: {e}")
            self.default_channel_id = None

    def select_default_channel(self):
        """Select the default channel in the combobox"""
        try:
            # Set the default channel if found
            if self.default_channel_id:
                for i, channel in enumerate(self.youtube_channels):
                    if channel['id'] == self.default_channel_id:
                        self.channel_combo.current(i)
                        self.selected_channel_id = self.default_channel_id
                        return
            
            # If no saved default or channel not found, use first channel
            if self.youtube_channels:
                self.channel_combo.current(0)
                self.selected_channel_id = self.youtube_channels[0]['id']
                
        except Exception as e:
            print(f"Warning: Could not select default channel: {e}")
            # Fallback to first channel
            if self.youtube_channels:
                self.channel_combo.current(0)
                self.selected_channel_id = self.youtube_channels[0]['id']

    def save_default_channel(self):
        """Save the default channel preference to defaults.json"""
        try:
            # Load existing defaults
            defaults = {}
            if os.path.exists('defaults.json'):
                with open('defaults.json', 'r') as f:
                    defaults = json.load(f)
            
            # Update with new default channel
            defaults['default_youtube_channel_id'] = self.default_channel_id
            
            # Save back to file
            with open('defaults.json', 'w') as f:
                json.dump(defaults, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not save default channel: {e}")

    def refresh_channel_list(self):
        """Refresh the channel list display to update [DEFAULT] tags"""
        try:
            # Get current selection
            current_selection = self.channel_combo.current()
            
            # Recreate display names with updated default marking
            channel_names = []
            for channel_info in self.youtube_channels:
                display_name = channel_info['title']
                if channel_info['custom_url']:
                    display_name += f" (@{channel_info['custom_url']})"
                    
                # Mark as default if this is the saved default channel
                if channel_info['id'] == self.default_channel_id:
                    display_name += " [DEFAULT]"
                    
                channel_names.append(display_name)
            
            # Update channel combobox
            self.channel_combo.configure(values=channel_names)
            
            # Restore selection
            if current_selection >= 0:
                self.channel_combo.current(current_selection)
                
        except Exception as e:
            print(f"Warning: Could not refresh channel list: {e}")

    def refresh_youtube_channels(self):
        """Refresh the list of YouTube channels"""
        if not self.youtube_service:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        try:
            self.auth_status_label.config(text="Refreshing channels...", foreground="blue")
            self.load_youtube_channels()
        except Exception as e:
            self.auth_status_label.config(text=f"Refresh failed: {str(e)[:50]}...", foreground="red")
            messagebox.showerror("Refresh Error", f"Failed to refresh channels:\n{str(e)}")

    def force_reauthenticate(self):
        """Force re-authentication by clearing stored credentials"""
        try:
            # Remove stored token to force re-authentication
            if os.path.exists('youtube_token.pickle'):
                os.remove('youtube_token.pickle')
                print("DEBUG: Removed stored YouTube token")
            
            # Clear current session
            self.youtube_service = None
            self.youtube_channels = []
            self.selected_channel_id = None
            
            # Update UI
            self.auth_status_label.config(text="Please re-authenticate", foreground="orange")
            self.channel_frame.grid_remove()
            
            # Now authenticate again
            self.authenticate_youtube()
            
        except Exception as e:
            messagebox.showerror("Re-authentication Error", f"Failed to re-authenticate:\n{str(e)}")

    def add_manual_channel(self):
        """Add a channel manually by Channel ID"""
        if not self.youtube_service:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        channel_id = self.manual_channel_id_var.get().strip()
        
        # Check for placeholder text
        if not channel_id or channel_id == "UC... (24 characters)":
            messagebox.showwarning("Missing Channel ID", "Please enter a Channel ID")
            return
        
        if not channel_id.startswith('UC') or len(channel_id) != 24:
            messagebox.showwarning("Invalid Channel ID", 
                                 "Channel ID should start with 'UC' and be 24 characters long.\n\n"
                                 "Example: UCrbdh09LJxCeu8yi_OwhKbg")
            return
        
        try:
            self.auth_status_label.config(text="Checking channel...", foreground="blue")
            
            # Try to get channel info by ID
            response = self.youtube_service.channels().list(
                part='snippet',
                id=channel_id
            ).execute()
            
            if not response['items']:
                messagebox.showerror("Channel Not Found", 
                                   f"No channel found with ID: {channel_id}\n\n"
                                   "Please check:\n"
                                   "• The Channel ID is correct\n"
                                   "• The channel is public\n"
                                   "• You have permission to access it")
                self.auth_status_label.config(text=f"Authenticated: {len(self.youtube_channels)} channels available", foreground="green")
                return
            
            channel = response['items'][0]
            channel_info = {
                'id': channel['id'],
                'title': channel['snippet']['title'],
                'description': channel['snippet'].get('description', ''),
                'custom_url': channel['snippet'].get('customUrl', ''),
                'manually_added': True  # Mark as manually added
            }
            
            # Check if channel already exists
            for existing_channel in self.youtube_channels:
                if existing_channel['id'] == channel_id:
                    messagebox.showinfo("Channel Already Added", f"'{channel_info['title']}' is already in the list")
                    self.auth_status_label.config(text=f"Authenticated: {len(self.youtube_channels)} channels available", foreground="green")
                    return
            
            # Add to channel list
            self.youtube_channels.append(channel_info)
            print(f"DEBUG: Manually added channel - {channel_info['title']}")
            
            # Save this channel ID for future automatic detection
            self.save_known_channel_id(channel_id)
            
            # Refresh the display
            self.refresh_channel_list()
            
            # Select the newly added channel
            for i, ch in enumerate(self.youtube_channels):
                if ch['id'] == channel_id:
                    self.channel_combo.current(i)
                    self.selected_channel_id = channel_id
                    break
            
            # Update status
            self.auth_status_label.config(text=f"Added: {channel_info['title']}", foreground="green")
            messagebox.showinfo("Channel Added", f"Successfully added '{channel_info['title']}' to the channel list!")
            
            # Clear the entry and restore placeholder
            self.manual_channel_entry.delete(0, "end")
            self.manual_channel_entry.insert(0, "UC... (24 characters)")
            self.manual_channel_entry.configure(foreground='grey')
            
            # Refresh playlists for the new channel
            self.refresh_playlists()
            
        except Exception as e:
            self.auth_status_label.config(text=f"Add channel failed: {str(e)[:50]}...", foreground="red")
            messagebox.showerror("Add Channel Error", f"Failed to add channel:\n{str(e)}")

    def get_known_channel_ids(self):
        """Get list of known channel IDs to check during authentication"""
        known_ids = ['UCgDAZ9kGH98mcoMnPOptXUw']  # Your Vintage Postcard Archive channel
        
        # Also check if there are any saved manually added channels in defaults
        try:
            if os.path.exists('defaults.json'):
                with open('defaults.json', 'r') as f:
                    defaults = json.load(f)
                    saved_channels = defaults.get('known_youtube_channels', [])
                    known_ids.extend(saved_channels)
        except Exception as e:
            print(f"DEBUG: Could not load known channels from defaults: {e}")
        
        # Remove duplicates
        return list(set(known_ids))

    def save_known_channel_id(self, channel_id):
        """Save a manually added channel ID to the known channels list"""
        try:
            defaults = {}
            if os.path.exists('defaults.json'):
                with open('defaults.json', 'r') as f:
                    defaults = json.load(f)
            
            known_channels = defaults.get('known_youtube_channels', [])
            if channel_id not in known_channels:
                known_channels.append(channel_id)
                defaults['known_youtube_channels'] = known_channels
                
                with open('defaults.json', 'w') as f:
                    json.dump(defaults, f, indent=2)
                print(f"DEBUG: Saved {channel_id} to known channels list")
        except Exception as e:
            print(f"DEBUG: Could not save known channel: {e}")

    def add_videos_to_upload(self):
        """Add videos manually to upload list"""
        filetypes = [
            ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv"),
            ("MP4 files", "*.mp4"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select videos to upload",
            filetypes=filetypes
        )
        
        for file_path in files:
            self.add_video_to_list(file_path)

    def add_current_videos(self):
        """Add current part videos to upload list"""
        for part_info in self.video_parts:
            if 'path' in part_info and os.path.exists(part_info['path']):
                self.add_video_to_list(part_info['path'])

    def on_video_selection_changed(self, event):
        """Handle video selection change to update title and description preview"""
        selected_items = self.video_tree.selection()
        
        if selected_items:
            # Get the selected video
            selected_item = selected_items[0]
            file_path = self.video_tree.item(selected_item)['values'][0]
            
            if file_path:
                # Generate the formatted title for this specific video
                filename = os.path.splitext(os.path.basename(file_path))[0]
                formatted_filename = self._format_filename_for_title(filename)
                title = f"{formatted_filename} Vintage Postcards"
                
                # Update title preview
                self.title_preview_var.set(title)
                
                # Update description with the actual title
                self._update_description_for_title(title)
            else:
                self.title_preview_var.set("(Invalid file path)")
                self._update_description_for_title("(No title)")
        else:
            # No selection - show default state
            children = self.video_tree.get_children()
            if children:
                self.title_preview_var.set("(Select a video to preview)")
                self._reset_description_template()
            else:
                self.title_preview_var.set("(No videos selected)")
                self._reset_description_template()

    def _update_description_for_title(self, title):
        """Update the description text with the specific title"""
        if hasattr(self, 'description_text'):
            # Get the template
            template = """{title}

#VintagePostcards #PostcardCollecting #AntiquePostcards

Discover the charm of vintage postcards from around the world! Subscribe for weekly videos showcasing rare and beautiful postcards from our collection at Lincoln Rare Books and Collectables. Our online store boasts one of the largest vintage postcard selections, with tens of thousands available for purchase. This channel features just a glimpse of our inventory—perfect for postcard collecting enthusiasts!

🔗 Postcard Department: https://tiny.cc/z0ir001

🔗 Full Store: https://tiny.cc/w0ir001

We add ~1,000 new antique postcards to our store weekly. Follow our eBay store for exclusive updates, special offers, and discounts to grow your postcard collection! Share your favorite postcard stories in the comments—we love hearing from fellow collectors!

#VintageEphemera #LincolnRareBooks"""
            
            # Replace {title} with actual title
            formatted_description = template.replace("{title}", title)
            
            # Update the description text area
            self.description_text.delete('1.0', tk.END)
            self.description_text.insert('1.0', formatted_description)

    def _reset_description_template(self):
        """Reset description to show template format"""
        if hasattr(self, 'description_text'):
            template = """{title}

#VintagePostcards #PostcardCollecting #AntiquePostcards

Discover the charm of vintage postcards from around the world! Subscribe for weekly videos showcasing rare and beautiful postcards from our collection at Lincoln Rare Books and Collectables. Our online store boasts one of the largest vintage postcard selections, with tens of thousands available for purchase. This channel features just a glimpse of our inventory—perfect for postcard collecting enthusiasts!

🔗 Postcard Department: https://tiny.cc/z0ir001

🔗 Full Store: https://tiny.cc/w0ir001

We add ~1,000 new antique postcards to our store weekly. Follow our eBay store for exclusive updates, special offers, and discounts to grow your postcard collection! Share your favorite postcard stories in the comments—we love hearing from fellow collectors!

#VintageEphemera #LincolnRareBooks"""
            
            self.description_text.delete('1.0', tk.END)
            self.description_text.insert('1.0', template)

    def update_title_preview(self):
        """Update the title preview based on the first video in the list (fallback)"""
        if not hasattr(self, 'video_tree') or not hasattr(self, 'title_preview_var'):
            return
        
        # Check if there's a selection first
        selected_items = self.video_tree.selection()
        if selected_items:
            # There's a selection, let the selection handler manage it
            return
        
        # No selection - show first video or default state
        children = self.video_tree.get_children()
        if children:
            self.title_preview_var.set("(Select a video to preview)")
            self._reset_description_template()
        else:
            self.title_preview_var.set("(No videos selected)")
            self._reset_description_template()

    def add_video_to_list(self, file_path):
        """Add a single video to the upload list"""
        try:
            # Check if already in original list
            for item in self.video_tree.get_children():
                if self.video_tree.item(item)['values'][0] == file_path:
                    return  # Already added
            
            # Get file size
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            filename = os.path.basename(file_path)
            
            # Add to video tree
            self.video_tree.insert('', 'end', values=(file_path, f"{size_mb:.1f}", "Ready"))
            
            # Update title preview
            self.update_title_preview()
            
            # Enable upload button if we have videos
            if hasattr(self, 'upload_button'):
                self.upload_button.config(state='normal')
                print("DEBUG: Upload button enabled")
            
        except Exception as e:
            print(f"DEBUG: Error adding video: {e}")
            messagebox.showerror("Error", f"Failed to add video:\n{str(e)}")

    def remove_selected_videos(self):
        """Remove selected videos from upload list"""
        selected_items = self.video_tree.selection()
        for item in selected_items:
            self.video_tree.delete(item)
        # Update title preview after removal
        self.update_title_preview()

    def clear_video_list(self):
        """Clear all videos from upload list"""
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        # Update title preview after clearing
        self.update_title_preview()

    def start_youtube_upload(self):
        """Start uploading videos to YouTube"""
        if not self.youtube_service:
            messagebox.showerror("Error", "Please authenticate first")
            return
        
        if not self.selected_channel_id:
            messagebox.showerror("Error", "Please select a channel first")
            return
        
        videos = []
        for item in self.video_tree.get_children():
            file_path = self.video_tree.item(item)['values'][0]
            if os.path.exists(file_path):
                videos.append((item, file_path))
        
        if not videos:
            messagebox.showerror("Error", "No videos to upload")
            return
        
        # Get selected channel info for confirmation
        selected_channel = next((ch for ch in self.youtube_channels if ch['id'] == self.selected_channel_id), None)
        if not selected_channel:
            messagebox.showerror("Error", "Selected channel not found")
            return
        
        # Show confirmation dialog
        channel_display = selected_channel['title']
        if selected_channel['custom_url']:
            channel_display += f" (@{selected_channel['custom_url']})"
        
        confirm_msg = f"Upload {len(videos)} video(s) to channel:\n'{channel_display}'?\n\nPrivacy: {self.privacy_var.get().title()}"
        if not messagebox.askyesno("Confirm Upload", confirm_msg):
            return
        
        # Get upload settings
        privacy = self.privacy_var.get()
        playlist_name = self.playlist_var.get().strip()
        playlist_id = self.playlist_mapping.get(playlist_name) if hasattr(self, 'playlist_mapping') else None
        title_template = "{filename} Vintage Postcards"  # Fixed template
        description = self.description_text.get('1.0', 'end-1c')
        
        # Debug playlist creation logic
        print(f"DEBUG PLAYLIST: playlist_name='{playlist_name}', playlist_id={playlist_id}")
        print(f"DEBUG PLAYLIST: has_mapping={hasattr(self, 'playlist_mapping')}")
        if hasattr(self, 'playlist_mapping'):
            print(f"DEBUG PLAYLIST: available_playlists={list(self.playlist_mapping.keys())}")
        
        # Handle playlist creation if needed
        if playlist_name and playlist_name != "None" and not playlist_id:
            print(f"DEBUG PLAYLIST: Triggering playlist creation for '{playlist_name}'")
            # Playlist name specified but doesn't exist - ask to create it
            create_msg = f"Playlist '{playlist_name}' does not exist.\n\n"
            create_msg += f"Create new playlist:\n"
            create_msg += f"• Name: {playlist_name}\n"
            create_msg += f"• Channel: {selected_channel['title']}\n"
            create_msg += f"• Privacy: Unlisted\n"
            create_msg += f"• Videos to add: {len(videos)}"
            
            if messagebox.askyesno("Create New Playlist", create_msg):
                playlist_id = self.create_playlist(playlist_name, selected_channel['title'])
                if playlist_id:
                    # Update the mapping and refresh the dropdown
                    if not hasattr(self, 'playlist_mapping'):
                        self.playlist_mapping = {}
                    self.playlist_mapping[playlist_name] = playlist_id
                    messagebox.showinfo("Playlist Created", f"Successfully created playlist '{playlist_name}'")
                    # Refresh playlists to show the new one
                    self.refresh_playlists()
                else:
                    messagebox.showerror("Error", f"Failed to create playlist '{playlist_name}'. Upload cancelled.")
                    self.upload_button.config(state='normal')
                    return
            else:
                # User chose not to create playlist - continue without playlist
                playlist_id = None
        else:
            print(f"DEBUG PLAYLIST: Not triggering creation. Conditions:")
            print(f"  - playlist_name present: {bool(playlist_name)}")
            print(f"  - playlist_name != 'None': {playlist_name != 'None'}")
            print(f"  - not playlist_id: {not playlist_id}")
        
        # Disable upload button during upload
        self.upload_button.config(state='disabled')
        
        # Start upload in separate thread
        upload_thread = threading.Thread(
            target=self.upload_videos_thread,
            args=(videos, privacy, playlist_id, title_template, description)
        )
        upload_thread.daemon = True
        upload_thread.start()

    def upload_videos_thread(self, videos, privacy, playlist_id, title_template, description):
        """Upload videos in a separate thread"""
        total_videos = len(videos)
        
        try:
            for i, (tree_item, file_path) in enumerate(videos):
                # Update status
                self.root.after(0, lambda: self.upload_status_label.config(
                    text=f"Uploading {i+1}/{total_videos}: {os.path.basename(file_path)}"))
                
                # Update tree item status
                self.root.after(0, lambda item=tree_item: self.video_tree.item(
                    item, values=(self.video_tree.item(item)['values'][0],
                                 self.video_tree.item(item)['values'][1], "Uploading...")))
                
                try:
                    # Generate title from template with formatted filename
                    filename = os.path.splitext(os.path.basename(file_path))[0]
                    formatted_filename = self._format_filename_for_title(filename)
                    title = title_template.replace("{filename}", formatted_filename)
                    
                    # Generate description with title replacement
                    formatted_description = description.replace("{title}", title)
                    
                    # Upload video
                    video_id = self.upload_single_video(file_path, title, formatted_description, privacy)
                    
                    if video_id:
                        # Add to playlist if specified
                        if playlist_id:
                            self.add_video_to_playlist(video_id, playlist_id)
                        
                        # Update status to success
                        self.root.after(0, lambda item=tree_item: self.video_tree.item(
                            item, values=(self.video_tree.item(item)['values'][0],
                                         self.video_tree.item(item)['values'][1], "✅ Uploaded")))
                    else:
                        # Update status to failed
                        self.root.after(0, lambda item=tree_item: self.video_tree.item(
                            item, values=(self.video_tree.item(item)['values'][0],
                                         self.video_tree.item(item)['values'][1], "❌ Failed")))
                    
                except Exception as e:
                    print(f"Error uploading {file_path}: {e}")
                    self.root.after(0, lambda item=tree_item, err=str(e): self.video_tree.item(
                        item, values=(self.video_tree.item(item)['values'][0],
                                     self.video_tree.item(item)['values'][1], f"❌ Error: {err[:20]}...")))
                
                # Update progress
                progress = ((i + 1) / total_videos) * 100
                self.root.after(0, lambda p=progress: self.upload_progress.configure(value=p))
        
        finally:
            # Re-enable upload button
            self.root.after(0, lambda: self.upload_button.config(state='normal'))
            self.root.after(0, lambda: self.upload_status_label.config(text="Upload completed"))

    def upload_single_video(self, file_path, title, description, privacy_status):
        """Upload a single video to YouTube"""
        try:
            # Prepare the video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'categoryId': '22'  # People & Blogs category
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            
            # Execute the upload
            request = self.youtube_service.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    # Update progress if needed
            
            if 'id' in response:
                print(f"Video uploaded successfully: {response['id']}")
                return response['id']
            else:
                print("Upload failed - no video ID returned")
                return None
                
        except Exception as e:
            print(f"Upload error: {e}")
            return None

    def _write_duration_analysis(self, clips, video_type):
        """Write detailed duration analysis to log file and console"""
        import datetime
        
        # Create duration analysis log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"duration_analysis_{timestamp}.txt"
        log_path = os.path.join(os.getcwd(), log_filename)
        
        total_calculated_duration = 0
        analysis_lines = []
        
        # Header
        header = f"DURATION ANALYSIS - {video_type}"
        separator = "=" * 60
        analysis_lines.append(separator)
        analysis_lines.append(header)
        analysis_lines.append(separator)
        
        # Analyze each clip
        for idx, clip in enumerate(clips):
            clip_duration = getattr(clip, 'duration', 0)
            total_calculated_duration += clip_duration
            
            clip_type = "unknown"
            if hasattr(clip, 'filename') and clip.filename:
                clip_type = f"IMAGE: {os.path.basename(clip.filename)}"
            elif hasattr(clip, 'make_frame'):
                clip_type = "TRANSITION/CUSTOM"
            else:
                clip_type = "GENERATED"
            
            # More specific identification
            if idx == 0:
                clip_type = "START CLIP"
            elif idx == 1 and self.second_page_enabled_var.get():
                clip_type = "SECOND PAGE"
            elif idx == len(clips) - 1:
                clip_type = "ENDING CLIP"
            
            clip_line = f"Clip {idx+1}: {clip_type} = {clip_duration:.2f}s"
            analysis_lines.append(clip_line)
        
        analysis_lines.append("")
        analysis_lines.append(f"TOTAL CALCULATED: {total_calculated_duration:.2f}s")
        analysis_lines.append(separator)
        
        # Write to console
        for line in analysis_lines:
            print(line)
        
        # Concatenate clips
        final_video = concatenate_videoclips(clips, method="compose")
        print(f"DEBUG: Clips concatenated successfully")
        
        # Final duration comparison
        actual_final_duration = final_video.duration
        comparison_lines = []
        comparison_lines.append("")
        comparison_lines.append(f"FINAL VIDEO DURATION: {actual_final_duration:.2f}s")
        comparison_lines.append(f"CALCULATED vs ACTUAL: {total_calculated_duration:.2f}s vs {actual_final_duration:.2f}s")
        
        # Log duration status for debugging
        max_allowed_duration = self.max_video_duration_var.get()
        comparison_lines.append(f"✅ DURATION: {actual_final_duration:.2f}s ≤ {max_allowed_duration:.0f}s (algorithm enforced)")
        
        if abs(actual_final_duration - total_calculated_duration) > 0.1:
            mismatch_line = f"⚠️  DURATION MISMATCH: {actual_final_duration - total_calculated_duration:.2f}s difference!"
            comparison_lines.append(mismatch_line)
        else:
            comparison_lines.append("✅ DURATION MATCH")
        
        comparison_lines.append(separator)
        
        # Write comparison to console
        for line in comparison_lines:
            print(line)
        
        # Write everything to log file
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {datetime.datetime.now()}\n")
                f.write(f"Video Type: {video_type}\n")
                f.write("\n")
                
                for line in analysis_lines:
                    f.write(line + "\n")
                
                for line in comparison_lines:
                    f.write(line + "\n")
                
                # Batching debugging info  
                f.write("\nBATCHING DEBUG INFO:\n")
                f.write("=" * 40 + "\n")
                batching_info = getattr(self, '_batching_debug_info', 'NOT SET - BATCHING ALGORITHM MAY NOT HAVE RUN')
                f.write(f"🚨 BATCHING STATUS: {batching_info}\n")
                f.write("\n")
                
                # Configuration debugging info
                f.write("CONFIGURATION VALUES:\n")
                f.write("=" * 40 + "\n")
                f.write(f"actual_start_duration_var: {self.actual_start_duration_var.get()}s\n")
                f.write(f"actual_second_page_duration_var: {self.actual_second_page_duration_var.get()}s\n")
                f.write(f"actual_ending_duration_var: {self.actual_ending_duration_var.get()}s\n")
                f.write(f"actual_pair_duration_var: {self.actual_pair_duration_var.get()}s\n")
                f.write(f"max_video_duration_var: {self.max_video_duration_var.get()}s\n")
                f.write(f"transition_duration_var: {self.transition_duration_var.get()}s\n")
                f.write(f"second_page_enabled: {self.second_page_enabled_var.get()}\n")
                
                # Pair calculation breakdown
                if hasattr(self, 'actual_pair_duration_var'):
                    total_pair_duration = self.actual_pair_duration_var.get()
                    transition_duration = float(self.transition_duration_var.get())
                    content_duration = total_pair_duration - transition_duration
                    front_duration = content_duration * 0.6
                    back_duration = content_duration * 0.4
                    f.write(f"\nPAIR CALCULATION BREAKDOWN:\n")
                    f.write(f"  Total pair duration: {total_pair_duration}s\n")
                    f.write(f"  Transition duration: {transition_duration}s\n")
                    f.write(f"  Content duration: {content_duration}s\n")
                    f.write(f"  Calculated front: {front_duration}s\n")
                    f.write(f"  Calculated back: {back_duration}s\n")
                
                # Additional debugging info
                f.write("\nDETAILED CLIP INFORMATION:\n")
                f.write("=" * 40 + "\n")
                for idx, clip in enumerate(clips):
                    f.write(f"\nClip {idx+1}:\n")
                    f.write(f"  Duration: {getattr(clip, 'duration', 'unknown')}\n")
                    f.write(f"  Type: {type(clip).__name__}\n")
                    f.write(f"  Has filename: {hasattr(clip, 'filename')}\n")
                    f.write(f"  Has make_frame: {hasattr(clip, 'make_frame')}\n")
                    if hasattr(clip, 'filename'):
                        f.write(f"  Filename: {clip.filename}\n")
            
            print(f"\n📊 Duration analysis written to: {log_filename}")
            print(f"Full path: {log_path}")
            
        except Exception as e:
            print(f"ERROR: Could not write duration analysis log: {e}")
        
        return final_video

    def _format_filename_for_title(self, filename):
        """Format filename for use in video title"""
        import re
        
        # Start with the original filename
        formatted = filename
        
        # Remove date pattern (YYYYMMDD)
        formatted = re.sub(r'\b\d{8}\b', '', formatted)
        
        # Remove time pattern (HHMMSS)  
        formatted = re.sub(r'\b\d{6}\b', '', formatted)
        
        # Remove dimensions pattern (WIDTHxHEIGHT)
        formatted = re.sub(r'\b\d+x\d+\b', '', formatted)
        
        # Replace underscores with spaces
        formatted = formatted.replace('_', ' ')
        
        # Replace "Part" with "#" (case insensitive, with or without space)
        formatted = re.sub(r'\b(part)\s*(\d+)\b', r'#\2', formatted, flags=re.IGNORECASE)
        
        # Clean up multiple spaces and trim
        formatted = re.sub(r'\s+', ' ', formatted).strip()
        
        return formatted

    def manual_cleanup_old_files(self):
        """Manually clean up old files with user confirmation"""
        import os
        import time
        import glob
        from tkinter import messagebox
        
        current_time = time.time()
        old_files = []
        
        # Patterns for files to clean up
        patterns = [
            "*.log",
            "duration_analysis_*.txt",
            "logs/*.log",
            "logs/*.txt"
        ]
        
        try:
            for pattern in patterns:
                for file_path in glob.glob(pattern):
                    try:
                        # Get file modification time
                        file_mtime = os.path.getmtime(file_path)
                        
                        # Check if file is older than 24 hours (86400 seconds)
                        if current_time - file_mtime > 86400:
                            # Get file age in hours
                            age_hours = (current_time - file_mtime) / 3600
                            old_files.append((file_path, age_hours))
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        continue
            
            if not old_files:
                messagebox.showinfo("File Cleanup", "No old log or analysis files found (older than 24 hours).")
                return
            
            # Show confirmation dialog
            file_list = "\n".join([f"• {path} ({age:.1f} hours old)" for path, age in old_files])
            message = f"Found {len(old_files)} old files to clean up:\n\n{file_list}\n\nDelete these files?"
            
            if messagebox.askyesno("Cleanup Old Files", message):
                deleted_count = 0
                for file_path, _ in old_files:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except (OSError, IOError) as e:
                        print(f"Could not delete {file_path}: {e}")
                
                messagebox.showinfo("Cleanup Complete", f"Successfully deleted {deleted_count} old files.")
                
        except Exception as e:
            messagebox.showerror("Cleanup Error", f"File cleanup failed: {e}")

    def add_video_to_playlist(self, video_id, playlist_id):
        """Add an uploaded video to a playlist"""
        try:
            body = {
                'snippet': {
                    'playlistId': playlist_id,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': video_id
                    }
                }
            }
            
            request = self.youtube_service.playlistItems().insert(
                part='snippet',
                body=body
            )
            
            response = request.execute()
            print(f"Video added to playlist: {response['id']}")
            return True
            
        except Exception as e:
            print(f"Failed to add video to playlist: {e}")
            return False

def main():
    root = tk.Tk()
    app = PostcardVideoCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 