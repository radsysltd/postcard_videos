import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from PIL import Image, ImageTk
import cv2
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
        self.output_path = r"C:\_postcards\renamed_postcards\videos"
        self.is_processing = False
        self.latest_video_path = None  # Track the most recently created video
        self.video_parts = []  # Track all created video parts for selection
        
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
        
        self.setup_ui()
        
        # Load saved defaults after UI is set up
        self.load_defaults()
        
        # Update button state to show default output directory
        self.update_create_button_state()
        
    def setup_ui(self):
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
        
        # Duration settings
        ttk.Label(settings_frame, text="Default Duration (seconds):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.default_duration_var = tk.StringVar(value=str(self.default_duration))
        default_duration_entry = ttk.Entry(settings_frame, textvariable=self.default_duration_var, width=10)
        default_duration_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(settings_frame, text="Transition Duration (seconds):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.transition_duration_var = tk.StringVar(value=str(self.transition_duration))
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
        
        # Background color for square format
        ttk.Label(settings_frame, text="Square Background:").grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        background_color_combo = ttk.Combobox(settings_frame, textvariable=self.background_color_var,
                                            values=["white", "black", "gray", "light_gray", "dark_gray", 
                                                   "red", "green", "blue", "yellow", "cyan", "magenta", 
                                                   "orange", "purple", "brown", "pink", "navy"], width=15)
        background_color_combo.grid(row=3, column=1, sticky=tk.W, pady=(10, 0), padx=(0, 20))
        
        # Starting part number setting
        ttk.Label(settings_frame, text="Starting Part Number:").grid(row=3, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 0))
        starting_part_spinbox = ttk.Spinbox(settings_frame, from_=1, to=999, textvariable=self.starting_part_var, width=8)
        starting_part_spinbox.grid(row=3, column=3, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        
        # Ending text configuration button
        ending_config_button = ttk.Button(settings_frame, text="🎬 Configure Ending Text", command=self.open_ending_config)
        ending_config_button.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Start text configuration button
        start_config_button = ttk.Button(settings_frame, text="🎬 Configure Start Text", command=self.open_start_config)
        start_config_button.grid(row=4, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
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
        columns = ('Image #', 'Image Name', 'Duration (s)', 'Type', 'Status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.tree.heading(col, text=col)
            if col == 'Image #':
                self.tree.column(col, width=80)
            elif col == 'Duration (s)':
                self.tree.column(col, width=100)
            elif col == 'Type':
                self.tree.column(col, width=80)
            else:
                self.tree.column(col, width=200)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Preview frame
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(preview_frame, width=400, height=300, bg='white')
        self.preview_canvas.grid(row=0, column=0, padx=(0, 10))
        
        # Preview info
        info_frame = ttk.Frame(preview_frame)
        info_frame.grid(row=0, column=1, sticky=(tk.N, tk.W))
        
        self.preview_label = ttk.Label(info_frame, text="No image selected")
        self.preview_label.grid(row=0, column=0, sticky=tk.W)
        
        self.preview_info = ttk.Label(info_frame, text="")
        self.preview_info.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Bind tree selection and double-click for editing duration
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # Progress and control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        main_frame.rowconfigure(3, weight=1)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(1, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
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
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Add images and set default durations
        for i, path in enumerate(image_paths):
            self.postcard_images.append(path)
            self.image_durations.append(self.default_duration)
            
            # Determine if it's front or back
            image_type = "Front" if i % 2 == 0 else "Back"
            postcard_num = (i // 2) + 1
            
            # Add to treeview
            image_name = os.path.basename(path)
            self.tree.insert('', 'end', values=(f"{i+1}", image_name, str(self.default_duration), image_type, "Ready"))
            
        # No dialog box - just update status
        self.status_label.config(text=f"Added {len(image_paths)} images ({len(image_paths)//2} postcards)")
        
        # Enable create button if we have images and output folder
        self.update_create_button_state()
        
    def clear_all_images(self):
        self.postcard_images.clear()
        self.image_durations.clear()
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
        
        # Add back image  
        self.postcard_images.append(back_path)
        self.image_durations.append(self.default_duration)
        
        # Update tree view
        index = len(self.postcard_images) - 2  # Front image index
        
        # Add front
        self.tree.insert('', 'end', values=(
            f"{index//2 + 1}",
            "Front",
            os.path.basename(front_path),
            f"{self.default_duration}s",
            title
        ))
        
        # Add back
        self.tree.insert('', 'end', values=(
            f"{index//2 + 1}",
            "Back", 
            os.path.basename(back_path),
            f"{self.default_duration}s",
            title
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
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.postcard_images):
                image_path = self.postcard_images[index]
                self.show_preview(image_path)
                
    def on_tree_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            index = self.tree.index(item)
            if index < len(self.image_durations):
                self.edit_duration(index)
                
    def show_preview(self, image_path):
        try:
            # Load and resize image for preview
            img = Image.open(image_path)
            img.thumbnail((400, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            # Update canvas
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(200, 150, image=photo)
            self.preview_canvas.image = photo  # Keep reference
            
            # Update info
            image_name = os.path.basename(image_path)
            image_index = self.postcard_images.index(image_path)
            image_type = "Front" if image_index % 2 == 0 else "Back"
            postcard_num = (image_index // 2) + 1
            duration = self.image_durations[image_index]
            
            self.preview_label.config(text=f"Image {image_index + 1}: {image_name}")
            self.preview_info.config(text=f"Type: {image_type} | Postcard: {postcard_num} | Duration: {duration}s")
            
        except Exception as e:
            self.preview_label.config(text=f"Error loading preview: {str(e)}")
            
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
                f"This will be split into {len(batches)} videos of approximately 60 seconds each.\n\n"
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
        """Calculate total duration of all postcard images"""
        return sum(self.image_durations)
    
    def calculate_video_batches(self):
        """Split postcards into batches of approximately 60 seconds each, with minimum 5 pairs per batch"""
        max_duration_per_video = 60.0  # Maximum seconds of postcard content per video
        min_pairs_per_video = 5  # Minimum number of postcard pairs per video
        
        total_pairs = len(self.postcard_images) // 2
        
        # If we have fewer than minimum pairs total, return single batch
        if total_pairs < min_pairs_per_video:
            logging.info(f"DEBUG: Only {total_pairs} pairs total, creating single video")
            return [list(range(len(self.postcard_images)))]
        
        batches = []
        current_batch = []
        current_duration = 0.0
        
        # Calculate durations for each pair
        pair_durations = []
        for i in range(0, len(self.postcard_images), 2):
            if i + 1 >= len(self.postcard_images):
                break
            front_duration = self.image_durations[i]
            back_duration = self.image_durations[i + 1]
            pair_durations.append(front_duration + back_duration)
        
        # Process images in pairs (front and back)
        for pair_idx, i in enumerate(range(0, len(self.postcard_images), 2)):
            if i + 1 >= len(self.postcard_images):
                break  # Ensure we have a complete pair
                
            pair_duration = pair_durations[pair_idx]
            
            # Check if adding this pair would exceed the limit AND we have minimum pairs
            current_pairs = len(current_batch) // 2
            if (current_duration + pair_duration > max_duration_per_video and 
                current_pairs >= min_pairs_per_video):
                # Start a new batch
                batches.append(current_batch)
                current_batch = []
                current_duration = 0.0
            
            # Add the pair to current batch
            current_batch.extend([i, i + 1])  # Add indices for front and back
            current_duration += pair_duration
        
        # Add the last batch if it has content
        if current_batch:
            batches.append(current_batch)
        
        # Post-process: ensure no batch has fewer than minimum pairs (except if only one batch)
        if len(batches) > 1:
            logging.info(f"DEBUG: Before adjustment: {len(batches)} batches")
            batches = self._ensure_minimum_pairs_per_batch(batches, min_pairs_per_video)
            logging.info(f"DEBUG: After adjustment: {len(batches)} batches")
        
        # Log the final batching decision
        for i, batch in enumerate(batches):
            pairs_count = len(batch) // 2
            batch_duration = sum(pair_durations[j] for j in range(len(batch) // 2) if j < len(pair_durations))
            logging.info(f"DEBUG: Batch {i+1}: {pairs_count} pairs, {batch_duration:.1f}s duration")
        
        return batches
    
    def _ensure_minimum_pairs_per_batch(self, batches, min_pairs_per_video):
        """Ensure no batch has fewer than minimum pairs by redistributing or merging"""
        if not batches:
            return batches
            
        # Check if any batch (except possibly the last) has too few pairs
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
                    # Last batch with too few pairs - merge with previous batch
                    if adjusted_batches:
                        logging.info(f"DEBUG: Merging last batch ({current_pairs} pairs) with previous batch")
                        adjusted_batches[-1].extend(current_batch)
                    else:
                        # Only one batch total, keep it
                        adjusted_batches.append(current_batch)
                else:
                    # Not the last batch - merge with next batch
                    logging.info(f"DEBUG: Merging batch ({current_pairs} pairs) with next batch")
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
        available_music = ["Vintage Memories", "Nostalgic Journey", "Classic Charm", "Peaceful Moments"]
        return random.choice(available_music)
    
    def process_videos_in_batches(self, batches):
        """Process multiple videos based on the calculated batches"""
        try:
            total_videos = len(batches)
            original_line1 = self.start_line1_var.get()
            videos_created = []
            
            for batch_index, batch_indices in enumerate(batches):
                try:
                    # Update progress
                    overall_progress = (batch_index / total_videos) * 100
                    self.root.after(0, lambda p=overall_progress: self.progress_var.set(p))
                    
                    # Calculate actual part number using starting part number
                    actual_part_number = self.starting_part_var.get() + batch_index
                    
                    # Always update start screen text with part number
                    part_text = f"{original_line1} (Part {actual_part_number})"
                    logging.info(f"DEBUG: Updating start text to: '{part_text}' (starting from part {self.starting_part_var.get()})")
                    self.start_line1_var.set(part_text)
                    
                    if total_videos > 1:
                        self.root.after(0, lambda b=batch_index, t=total_videos: 
                                      self.status_label.config(text=f"Creating video {b+1} of {t}..."))
                    else:
                        self.root.after(0, lambda: self.status_label.config(text="Creating video..."))
                    
                    # Create video for this batch
                    video_path = self.process_single_batch_video(batch_indices, actual_part_number, total_videos)
                    if video_path:
                        videos_created.append(video_path)
                    
                except Exception as e:
                    logging.error(f"Error creating batch {batch_index + 1}: {e}")
                    continue
            
            # Restore original start line text
            self.start_line1_var.set(original_line1)
            
            # Update video parts list and UI
            self.update_video_parts_list(videos_created, original_line1, total_videos)
            
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
    
    def process_single_batch_video(self, batch_indices, part_number, total_parts):
        """Process a single video from a batch of image indices"""
        try:
            logging.info(f"DEBUG: Starting batch video {part_number}/{total_parts} with {len(batch_indices)} images")
            clips = []
            
            # Add start clip
            self.root.after(0, lambda: self.status_label.config(text="Creating start clip..."))
            start_duration = self.start_duration_var.get()
            
            # Apply the same fade logic as the original process_video method
            # Don't apply fade-out to start clip if we're creating a manual transition
            will_create_manual_transition = len(batch_indices) > 0 and self.start_fade_out_var.get()
            apply_fade_out = self.start_fade_out_var.get() and not will_create_manual_transition
            logging.info(f"DEBUG: Fade logic - batch_images: {len(batch_indices)}, fade_out_enabled: {self.start_fade_out_var.get()}")
            logging.info(f"DEBUG: will_create_manual_transition: {will_create_manual_transition}, apply_fade_out: {apply_fade_out}")
            
            logging.info(f"DEBUG: Creating start clip with duration {start_duration}s")
            start_clip = self.create_start_clip(duration=start_duration, apply_fade_out=apply_fade_out)
            if start_clip is None:
                raise Exception("Failed to create start clip")
            logging.info(f"DEBUG: Start clip created successfully")
            clips.append(start_clip)
            
            # Process postcard pairs in this batch
            for i in range(0, len(batch_indices), 2):
                if i + 1 >= len(batch_indices):
                    break
                    
                front_idx = batch_indices[i]
                back_idx = batch_indices[i + 1]
                
                front_path = self.postcard_images[front_idx]
                back_path = self.postcard_images[back_idx]
                front_duration = self.image_durations[front_idx]
                back_duration = self.image_durations[back_idx]
                
                logging.info(f"DEBUG: Processing pair {i//2 + 1}, front: {front_path}, back: {back_path}")
                logging.info(f"DEBUG: Durations - front: {front_duration}s, back: {back_duration}s")
                
                # Create clips
                logging.info(f"DEBUG: Creating front clip...")
                front_clip = self.create_image_clip(front_path, front_duration)
                if front_clip is None:
                    raise Exception(f"Failed to create front clip for: {front_path}")
                logging.info(f"DEBUG: Front clip created successfully")
                
                # If this is the first front clip and start fade-out is enabled, create manual transition
                if i == 0 and self.start_fade_out_var.get():
                    logging.info(f"DEBUG: Creating manual fade transition from start to first postcard")
                    start_to_front = self.create_fade_transition(start_clip, front_clip)
                    clips.extend([start_to_front, front_clip])
                    logging.info(f"DEBUG: Manual transition created, clips now: {len(clips)}")
                else:
                    logging.info(f"DEBUG: No manual transition, adding front clip directly")
                    clips.append(front_clip)
                    
                logging.info(f"DEBUG: Creating back clip...")
                back_clip = self.create_image_clip(back_path, back_duration)
                if back_clip is None:
                    raise Exception(f"Failed to create back clip for: {back_path}")
                logging.info(f"DEBUG: Back clip created successfully")
                
                # Add transition between front and back
                if self.transition_duration > 0:
                    transition = self.create_transition(front_clip, back_clip)
                    clips.extend([transition, back_clip])
                else:
                    clips.append(back_clip)
                
                # Add transition to next postcard (except for last one)
                if i < len(batch_indices) - 2:
                    next_front_idx = batch_indices[i + 2]
                    next_front_path = self.postcard_images[next_front_idx]
                    next_front_clip = self.create_image_clip(next_front_path, 0.1)
                    transition = self.create_transition(back_clip, next_front_clip)
                    clips.append(transition)
            
            # Add ending clip
            self.root.after(0, lambda: self.status_label.config(text="Adding ending clip..."))
            ending_duration = self.ending_duration_var.get()
            logging.info(f"DEBUG: Creating ending clip with duration {ending_duration}s")
            ending_clip = self.create_ending_clip(duration=ending_duration)
            if ending_clip is None:
                raise Exception("Failed to create ending clip")
            logging.info(f"DEBUG: Ending clip created successfully")
            clips.append(ending_clip)
            
            # Concatenate clips
            self.root.after(0, lambda: self.status_label.config(text="Concatenating clips..."))
            logging.info(f"DEBUG: About to concatenate {len(clips)} clips for batch video")
            final_video = concatenate_videoclips(clips, method="compose")
            logging.info(f"DEBUG: Clips concatenated successfully for batch video")
            
            # Generate output filename using Line 1 text from start screen
            line1_text = self.start_line1_var.get()
            # Sanitize filename by removing invalid characters
            safe_filename = "".join(c for c in line1_text if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename.replace(' ', '_')
            
            if not safe_filename:  # Fallback if no valid characters
                safe_filename = "postcard_video"
            
            # Add timestamp for uniqueness
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Always use part numbers in filename, include dimensions
            dimensions = f"{self.video_width}x{self.video_height}"
            output_filename = f"{timestamp}_{safe_filename}_Part{part_number}_{dimensions}.mp4"
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
                
                music_filename_wav = selected_music.replace(' ', '_').lower() + '.wav'
                music_filename_mp3 = selected_music.replace(' ', '_').lower() + '.mp3'
                music_path_wav = os.path.join('music', music_filename_wav)
                music_path_mp3 = os.path.join('music', music_filename_mp3)
                
                # Check which file exists
                if os.path.exists(music_path_mp3):
                    music_path = music_path_mp3
                    self.root.after(0, lambda: self.status_label.config(text="Adding background music..."))
                elif os.path.exists(music_path_wav):
                    music_path = music_path_wav
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
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', temp_video_path,
                        '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
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
            
            return output_path
            
        except Exception as e:
            import traceback
            error_msg = f"Error creating single batch video: {str(e)}"
            full_traceback = traceback.format_exc()
            logging.error(f"ERROR in process_single_batch_video: {error_msg}")
            logging.error(f"FULL TRACEBACK: {full_traceback}")
            return None
        
    def update_video_parts_list(self, video_paths, original_title, total_parts):
        """Update the video parts list and dropdown"""
        # Clear existing parts
        self.video_parts.clear()
        
        # Get starting part number
        starting_part = self.starting_part_var.get()
        
        # Add new parts - always use part numbers now
        for i, video_path in enumerate(video_paths):
            actual_part_number = starting_part + i
            display_name = f"{original_title} (Part {actual_part_number})"
            
            self.video_parts.append({
                'path': video_path,
                'display_name': display_name,
                'part_number': actual_part_number
            })
        
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
            start_duration = self.start_duration_var.get()
            # Don't apply fade-out to start clip if we're creating a manual transition
            # Apply fade-out only if: fade-out enabled AND (no postcards OR manual transition disabled)
            will_create_manual_transition = len(self.postcard_images) > 0 and self.start_fade_out_var.get()
            apply_fade_out = self.start_fade_out_var.get() and not will_create_manual_transition
            logging.debug(f"Fade logic - postcards: {len(self.postcard_images)}, fade_out_enabled: {self.start_fade_out_var.get()}")
            logging.debug(f"will_create_manual_transition: {will_create_manual_transition}, apply_fade_out: {apply_fade_out}")
            start_clip = self.create_start_clip(duration=start_duration, apply_fade_out=apply_fade_out)
            if start_clip is None:
                raise Exception("Failed to create start clip")
            clips.append(start_clip)
            
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
                front_duration = self.image_durations[i]
                back_duration = self.image_durations[i + 1]
                
                # Create front clip
                print(f"DEBUG: Creating front clip for {front_path}")
                front_clip = self.create_image_clip(front_path, front_duration)
                print(f"DEBUG: Front clip created successfully")

                # If requested, fade the start screen into the first front clip
                if i == 0 and self.start_fade_out_var.get():
                    logging.debug(f"Creating manual fade transition from start to first postcard")
                    start_to_front = self.create_fade_transition(start_clip, front_clip)
                    clips.extend([start_to_front, front_clip])
                    logging.debug(f"Manual transition created, clips now: {len(clips)}")
                else:
                    logging.debug(f"No manual transition, adding front clip directly")
                    clips.append(front_clip)
                
                # Create back clip
                print(f"DEBUG: Creating back clip for {back_path}")
                back_clip = self.create_image_clip(back_path, back_duration)
                print(f"DEBUG: Back clip created successfully")
                
                # Add transition between front and back
                if self.transition_duration > 0:
                    transition = self.create_transition(front_clip, back_clip)
                    clips.extend([transition, back_clip])
                else:
                    clips.append(back_clip)
                
                # Add transition to next postcard (except for last one)
                if i < total_images - 2:
                    next_front_path = self.postcard_images[i + 2]
                    next_front_clip = self.create_image_clip(next_front_path, 0.1)  # Short clip for transition
                    transition = self.create_transition(back_clip, next_front_clip)
                    clips.append(transition)
            
            # Add ending clip
            self.root.after(0, lambda: self.status_label.config(text="Adding ending clip..."))
            ending_duration = self.ending_duration_var.get()
            print(f"DEBUG: Creating ending clip...")
            ending_clip = self.create_ending_clip(duration=ending_duration)
            if ending_clip is None:
                raise Exception("Failed to create ending clip")
            print(f"DEBUG: Ending clip created successfully")
            clips.append(ending_clip)
            
            # Concatenate all clips
            self.root.after(0, lambda: self.status_label.config(text="Concatenating clips..."))
            self.root.after(0, lambda: self.progress_var.set(85))
            print(f"DEBUG: About to concatenate {len(clips)} clips")
            final_video = concatenate_videoclips(clips, method="compose")
            print(f"DEBUG: Clips concatenated successfully")
            
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
                
                music_filename_wav = selected_music.replace(' ', '_').lower() + '.wav'
                music_filename_mp3 = selected_music.replace(' ', '_').lower() + '.mp3'
                music_path_wav = os.path.join('music', music_filename_wav)
                music_path_mp3 = os.path.join('music', music_filename_mp3)
                
                # Check which file exists
                if os.path.exists(music_path_mp3):
                    music_path = music_path_mp3
                    self.root.after(0, lambda: self.status_label.config(text="Adding background music..."))
                elif os.path.exists(music_path_wav):
                    music_path = music_path_wav
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
                    
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', temp_video_path,
                        '-i', music_path,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
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
    
    def create_fade_transition(self, clip1, clip2):
        """Create a fade transition between two clips"""
        # Create a custom clip that shows the first clip, then fades to the second
        logging.debug(f"Creating fade transition: clip1 duration={clip1.duration}, transition duration={self.transition_duration}")
        
        def make_frame(t):
            if t < clip1.duration - self.transition_duration:
                # Show first clip normally (before transition starts)
                return clip1.get_frame(t)
            elif t < clip1.duration:
                # Transition period: fade from clip1 to clip2
                transition_progress = (t - (clip1.duration - self.transition_duration)) / self.transition_duration
                frame1 = clip1.get_frame(t)
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
                return clip2.get_frame(t - clip1.duration)
        
        # Transition clip duration is just the first clip duration (transition happens within it)
        transition_clip = VideoClip(make_frame, duration=clip1.duration)
        logging.debug(f"Fade transition created with duration={transition_clip.duration}")
        return transition_clip
    
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
        """Create an ending clip with logo and text on white background (like start screen)"""
        def make_frame(t):
            import numpy as np
            import cv2
            from PIL import Image
            
            # Create white background for start/end screens regardless of format
            frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 255
            
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
            
            thickness = 3
            
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

                (text_width, text_height), _ = cv2.getTextSize(line1, font1, line1_size, thickness)
                x1 = (self.video_width - text_width) // 2
                y1 = int(text_start_y)  # Convert to integer for OpenCV
                cv2.putText(frame, line1, (x1, y1), font1, line1_size, text_color1, thickness)
                print(f"DEBUG: Ending Line 1 - Text: '{line1}', Color: {text_color1}, Pos: ({x1}, {y1})")
            else:
                print(f"DEBUG: Line 1 is empty or None")
            
            # Line 2
            if line2 and not line2_hidden:
                print(f"DEBUG: Drawing Line 2 - Text: '{line2}'")
                color2 = color_map.get(line2_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color2 = color2

                (text_width, text_height), _ = cv2.getTextSize(line2, font2, line2_size, thickness)
                x2 = (self.video_width - text_width) // 2
                # If line1 is hidden, keep line2 at text_start_y; otherwise below line1
                if line1 and not line1_hidden:
                    y2 = int(text_start_y + adjusted_spacing)
                else:
                    y2 = int(text_start_y)
                cv2.putText(frame, line2, (x2, y2), font2, line2_size, text_color2, thickness)
                print(f"DEBUG: Ending Line 2 - Text: '{line2}', Color: {text_color2}, Pos: ({x2}, {y2})")
            else:
                print(f"DEBUG: Line 2 is empty or None")
            
            # Line 3
            if line3 and not line3_hidden:
                print(f"DEBUG: Drawing Line 3 - Text: '{line3}'")
                color3 = color_map.get(line3_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color3 = color3

                (text_width, text_height), _ = cv2.getTextSize(line3, font3, line3_size, thickness)
                x3 = (self.video_width - text_width) // 2
                # Determine y3 based on which previous lines are visible
                visible_offset = 0
                if line1 and not line1_hidden:
                    visible_offset += 1
                if line2 and not line2_hidden:
                    visible_offset += 1
                y3 = int(text_start_y + (adjusted_spacing * max(visible_offset, 0)))
                cv2.putText(frame, line3, (x3, y3), font3, line3_size, text_color3, thickness)
                print(f"DEBUG: Ending Line 3 - Text: '{line3}', Color: {text_color3}, Pos: ({x3}, {y3})")
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
        """Create a start clip with logo and text on white background"""
        def make_frame(t):
            import numpy as np
            import cv2
            import os
            from PIL import Image
            
            # Create white background for start/end screens regardless of format
            frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 255
            
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
            thickness = 3
            
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
                (text_width, text_height), _ = cv2.getTextSize(line1, font1, line1_size, thickness)
                x1 = (self.video_width - text_width) // 2
                y1 = int(text_start_y)  # Convert to integer for OpenCV
                cv2.putText(frame, line1, (x1, y1), font1, line1_size, text_color1, thickness)
                print(f"DEBUG: Ending Line 1 - Text: '{line1}', Color: {text_color1}, Pos: ({x1}, {y1})")
            else:
                print(f"DEBUG: Line 1 is empty or None")
            
            # Line 2
            if line2:
                print(f"DEBUG: Drawing Line 2 - Text: '{line2}'")
                color2 = color_map.get(line2_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color2 = color2
                (text_width, text_height), _ = cv2.getTextSize(line2, font2, line2_size, thickness)
                x2 = (self.video_width - text_width) // 2
                if line1_hidden or not line1:
                    y2 = int(text_start_y)
                else:
                    y2 = int(text_start_y + adjusted_spacing)
                cv2.putText(frame, line2, (x2, y2), font2, line2_size, text_color2, thickness)
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
    
    def save_defaults(self):
        """Save current settings as defaults"""
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
        line1_font_combo.grid(row=2, column=1, columnspan=3, sticky=(tk.W, tk.E))
        line1_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        
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
        line2_font_combo.grid(row=5, column=1, columnspan=3, sticky=(tk.W, tk.E))
        line2_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        
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
        line3_font_combo.grid(row=8, column=1, columnspan=3, sticky=(tk.W, tk.E))
        line3_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_ending_preview())
        
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
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
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
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
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
                self.start_preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                                    fill=color1, font=(line1_font, font1_size, 'bold'), anchor=tk.N)
            
            # Line 2
            if line2:
                color2 = color_map.get(line2_color, "#000000")
                if line1_hidden:
                    y2 = int(text_start_y)
                else:
                    y2 = int(text_start_y + adjusted_spacing)
                self.start_preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                                    fill=color2, font=(line2_font, font2_size, 'bold'), anchor=tk.N)

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
                self.ending_preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                              fill=color1, font=(line1_font, font1_size, 'bold'))
            
            # Line 2
            if line2 and not line2_hidden:
                color2 = color_map.get(line2_color, "#000000")
                # If line1 hidden, keep line2 at text_start_y; otherwise below line1
                if line1 and not line1_hidden:
                    y2 = int(text_start_y + adjusted_spacing)
                else:
                    y2 = int(text_start_y)
                self.ending_preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                              fill=color2, font=(line2_font, font2_size, 'bold'))
            
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
                self.ending_preview_canvas.create_text(canvas_width//2, y3, text=line3, 
                                              fill=color3, font=(line3_font, font3_size, 'bold'))

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
            
            # Find the music file (try both .mp3 and .wav)
            music_filename_wav = selected_music.replace(' ', '_').lower() + '.wav'
            music_filename_mp3 = selected_music.replace(' ', '_').lower() + '.mp3'
            music_path_wav = os.path.join('music', music_filename_wav)
            music_path_mp3 = os.path.join('music', music_filename_mp3)
            
            # Check which file exists
            if os.path.exists(music_path_mp3):
                music_path = music_path_mp3
            elif os.path.exists(music_path_wav):
                music_path = music_path_wav
            else:
                self.status_label.config(text=f"Music file not found: {music_filename_mp3} or {music_filename_wav}")
                return
            
            if not os.path.exists(music_path):
                self.status_label.config(text=f"Music file not found: {music_path}")
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

def main():
    root = tk.Tk()
    app = PostcardVideoCreator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 