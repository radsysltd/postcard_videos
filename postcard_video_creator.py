import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
import time
from PIL import Image, ImageTk
import cv2
from moviepy import *
from moviepy.video.fx import Resize, FadeIn, FadeOut
import numpy as np
from datetime import datetime
import json

class PostcardVideoCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Postcard Video Creator")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Variables
        self.postcard_images = []  # List of image paths in order
        self.image_durations = []  # List of durations for each image
        self.output_path = r"C:\_postcards\renamed_postcards\videos"
        self.is_processing = False
        
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
        self.video_width = 1920
        self.video_height = 1080
        
        # Ending text variables
        self.ending_line1_var = tk.StringVar(value="Lincoln Rare Books & Collectables")
        self.ending_line2_var = tk.StringVar(value="Many thousands of postcards in store")
        self.ending_line3_var = tk.StringVar(value="Please Like and Subscribe!")
        self.ending_line1_size_var = tk.DoubleVar(value=1.5)
        self.ending_line2_size_var = tk.DoubleVar(value=1.5)
        self.ending_line3_size_var = tk.DoubleVar(value=1.5)
        self.ending_line1_color_var = tk.StringVar(value="white")
        self.ending_line2_color_var = tk.StringVar(value="white")
        self.ending_line3_color_var = tk.StringVar(value="white")
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
        self.resolution_var = tk.StringVar(value="1920x1080")
        resolution_combo = ttk.Combobox(settings_frame, textvariable=self.resolution_var, 
                                       values=["1920x1080", "1280x720", "3840x2160"], width=15)
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
        self.music_var = tk.StringVar(value="Vintage Memories")
        music_combo = ttk.Combobox(settings_frame, textvariable=self.music_var,
                                  values=["None", "Vintage Memories", "Nostalgic Journey", 
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
        
        # Ending text configuration button
        ending_config_button = ttk.Button(settings_frame, text="🎬 Configure Ending Text", command=self.open_ending_config)
        ending_config_button.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Start text configuration button
        start_config_button = ttk.Button(settings_frame, text="🎬 Configure Start Text", command=self.open_start_config)
        start_config_button.grid(row=3, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="Postcard Images", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons for adding images
        ttk.Button(file_frame, text="Select Multiple Images", 
                  command=self.select_multiple_images).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(file_frame, text="Clear All", 
                  command=self.clear_all_images).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(file_frame, text="Select Output Folder", 
                  command=self.select_output_folder).grid(row=0, column=2)
        
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
        
        # Cancel button (initially hidden)
        self.cancel_button = ttk.Button(control_frame, text="❌ CANCEL", 
                                       command=self.cancel_processing, state='normal')
        self.cancel_button.grid(row=0, column=3, padx=(10, 0), ipadx=20, ipady=5)
        self.cancel_button.grid_remove()  # Hide initially
        
        # Add a label to show button status
        self.button_status_label = ttk.Label(control_frame, text="Button: Waiting for images and output folder", 
                                            font=('Arial', 8))
        self.button_status_label.grid(row=1, column=0, columnspan=3, pady=(5, 0))
        
        # Add a test button for quick verification
        self.test_button = ttk.Button(control_frame, text="🧪 TEST VIDEO", 
                                     command=self.test_video_creation, state='normal')
        self.test_button.grid(row=1, column=2, padx=(10, 0), pady=(5, 0))
        
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
            self.button_status_label.config(text=f"✅ Ready! Output: {short_path}", foreground='green')
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
            
        print("DEBUG: All validations passed, starting video creation")  # Debug output
        # Start processing in separate thread
        self.is_processing = True
        self.create_button.config(state='disabled')
        self.cancel_button.grid()  # Show cancel button
        self.status_label.config(text="Starting video creation...")
        self.progress_var.set(0)
        
        thread = threading.Thread(target=self.process_video)
        thread.daemon = True
        thread.start()
        
    def process_video(self):
        try:
            clips = []
            total_images = len(self.postcard_images)
            start_time = time.time()
            
            # Add start clip with logo and text
            self.root.after(0, lambda: self.status_label.config(text="Creating start clip..."))
            start_duration = self.start_duration_var.get()
            start_clip = self.create_start_clip(duration=start_duration)
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
                front_clip = self.create_image_clip(front_path, front_duration)
                
                # Create back clip
                back_clip = self.create_image_clip(back_path, back_duration)
                
                # Add transition between front and back
                if self.transition_duration > 0:
                    transition = self.create_transition(front_clip, back_clip)
                    clips.extend([front_clip, transition, back_clip])
                else:
                    clips.extend([front_clip, back_clip])
                
                # Add transition to next postcard (except for last one)
                if i < total_images - 2:
                    next_front_path = self.postcard_images[i + 2]
                    next_front_clip = self.create_image_clip(next_front_path, 0.1)  # Short clip for transition
                    transition = self.create_transition(back_clip, next_front_clip)
                    clips.append(transition)
            
            # Add ending clip
            self.root.after(0, lambda: self.status_label.config(text="Adding ending clip..."))
            ending_duration = self.ending_duration_var.get()
            ending_clip = self.create_ending_clip(duration=ending_duration)
            clips.append(ending_clip)
            
            # Concatenate all clips
            self.root.after(0, lambda: self.status_label.config(text="Concatenating clips..."))
            self.root.after(0, lambda: self.progress_var.set(85))
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Update progress for video writing
            self.root.after(0, lambda: self.status_label.config(text="Writing video file..."))
            self.root.after(0, lambda: self.progress_var.set(90))
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"postcard_video_{timestamp}.mp4"
            output_path = os.path.join(self.output_path, output_filename)
            
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
                music_filename_wav = self.music_var.get().replace(' ', '_').lower() + '.wav'
                music_filename_mp3 = self.music_var.get().replace(' ', '_').lower() + '.mp3'
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
            
            # Show success message
            self.root.after(0, lambda: self.show_success_message(output_path, actual_minutes, actual_seconds))
            
        except Exception as e:
            error_msg = str(e)
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
        
        # Create black background
        background = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
        
        # Calculate position to center the image
        x_offset = (self.video_width - new_w) // 2
        y_offset = (self.video_height - new_h) // 2
        
        # Place the resized image on the background
        background[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = img_resized
        img_resized = background
        
        # Create clip
        clip = ImageClip(img_resized, duration=duration)
        
        # No zoom effect for now - just return the clip as is
        
        return clip
        
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
        # Create a custom clip that blends between the two
        def make_frame(t):
            if t <= self.transition_duration:
                # Get frames from both clips
                frame1 = clip1.get_frame(min(t, clip1.duration))
                frame2 = clip2.get_frame(min(t, clip2.duration))
                
                # Calculate fade factor
                fade_factor = t / self.transition_duration
                
                # Blend frames
                blended_frame = frame1 * (1 - fade_factor) + frame2 * fade_factor
                return blended_frame.astype('uint8')
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        
        # Create a custom clip with the transition
        from moviepy import VideoClip
        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
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
        
        from moviepy import VideoClip
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
        
        from moviepy import VideoClip
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
        
        from moviepy import VideoClip
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
                blended_frame = frame1 * (1 - fade_factor) + frame2 * fade_factor
                return blended_frame.astype('uint8')
            else:
                return clip2.get_frame(min(t - self.transition_duration, clip2.duration))
        
        from moviepy import VideoClip
        transition_clip = VideoClip(make_frame, duration=clip1.duration + self.transition_duration)
        return transition_clip
    
    def create_ending_clip(self, duration=5):
        """Create an ending clip with fade to black and text"""
        def make_frame(t):
            import numpy as np
            import cv2
            
            # Create black frame
            frame = np.zeros((self.video_height, self.video_width, 3), dtype=np.uint8)
            
            # Calculate fade progress (0 to 1 over duration)
            fade_progress = min(t / duration, 1.0)
            
            # Add text with fade-in effect
            if fade_progress > 0.2:  # Start showing text after 20% of duration
                text_fade = min((fade_progress - 0.2) / 0.8, 1.0)  # Text fades in over remaining 80%
                
                # Get text lines and styling
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
                
                # Color mapping
                color_map = {
                    "white": (255, 255, 255),
                    "yellow": (0, 255, 255),
                    "red": (0, 0, 255),
                    "green": (0, 255, 0),
                    "blue": (255, 0, 0),
                    "cyan": (255, 255, 0),
                    "magenta": (255, 0, 255),
                    "brown": (19, 69, 139),
                    "orange": (0, 165, 255)
                }
                
                # Font settings
                font = cv2.FONT_HERSHEY_SIMPLEX
                thickness = 3
                
                # Calculate text positions (centered)
                y_center = self.video_height // 2
                line_spacing = 100
                
                # Line 1
                alpha = int(255 * text_fade)
                color1 = color_map.get(line1_color, (255, 255, 255))
                text_color1 = (int(color1[0] * alpha / 255), int(color1[1] * alpha / 255), int(color1[2] * alpha / 255))
                (text_width, text_height), _ = cv2.getTextSize(line1, font, line1_size, thickness)
                x1 = (self.video_width - text_width) // 2
                y1 = y_center - line_spacing
                cv2.putText(frame, line1, (x1, y1), font, line1_size, text_color1, thickness)
                
                # Line 2
                color2 = color_map.get(line2_color, (255, 255, 255))
                text_color2 = (int(color2[0] * alpha / 255), int(color2[1] * alpha / 255), int(color2[2] * alpha / 255))
                (text_width, text_height), _ = cv2.getTextSize(line2, font, line2_size, thickness)
                x2 = (self.video_width - text_width) // 2
                y2 = y_center
                cv2.putText(frame, line2, (x2, y2), font, line2_size, text_color2, thickness)
                
                # Line 3
                color3 = color_map.get(line3_color, (255, 255, 255))
                text_color3 = (int(color3[0] * alpha / 255), int(color3[1] * alpha / 255), int(color3[2] * alpha / 255))
                (text_width, text_height), _ = cv2.getTextSize(line3, font, line3_size, thickness)
                x3 = (self.video_width - text_width) // 2
                y3 = y_center + line_spacing
                cv2.putText(frame, line3, (x3, y3), font, line3_size, text_color3, thickness)
            
            return frame
        
        from moviepy import VideoClip
        ending_clip = VideoClip(make_frame, duration=duration)
        return ending_clip
    
    def create_start_clip(self, duration=3):
        """Create a start clip with logo and text on white background"""
        def make_frame(t):
            import numpy as np
            import cv2
            
            # Create white frame
            frame = np.ones((self.video_height, self.video_width, 3), dtype=np.uint8) * 255
            
            # No fade-in effect - show content immediately
            # Add logo and text immediately (no fade effect)
            
            # Load and display logo
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
                        logo_size_video = self.start_logo_size_var.get()
                        logo = cv2.resize(logo, (logo_size_video, logo_size_video))
                        
                        # Calculate logo position (centered, above text)
                        logo_x = (self.video_width - logo_size_video) // 2
                        # Use the same logo_y calculation as defined above
                        logo_y = 50  # Top margin (same as preview)
                        
                        # No fade effect - display logo immediately
                        
                        # Handle different image formats
                        if len(logo.shape) == 3 and logo.shape[2] == 4:  # Has alpha channel
                            # Convert RGBA to RGB with alpha blending
                            alpha_channel = logo[:, :, 3] / 255.0
                            rgb_channels = logo[:, :, :3]
                            
                            # Create white background for blending
                            white_bg = np.ones_like(rgb_channels) * 255
                            
                            # Blend logo with white background (no fade)
                            blended = rgb_channels * alpha_channel[:, :, np.newaxis] + \
                                     white_bg * (1 - alpha_channel[:, :, np.newaxis])
                            
                            # Place logo on frame (no fade effect)
                            frame[logo_y:logo_y+logo_size_video, logo_x:logo_x+logo_size_video] = blended.astype(np.uint8)
                            
                        elif len(logo.shape) == 3 and logo.shape[2] == 3:  # RGB without alpha
                            # Place logo directly (no fade)
                            frame[logo_y:logo_y+logo_size_video, logo_x:logo_x+logo_size_video] = logo
                        else:
                            # Grayscale or other format - place directly (no fade)
                            frame[logo_y:logo_y+logo_size_video, logo_x:logo_x+logo_size_video] = logo
                except Exception as e:
                    print(f"Error loading logo: {e}")
            
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
            
            # Color mapping (BGR format for OpenCV)
            color_map = {
                "black": (0, 0, 0),
                "white": (255, 255, 255),
                "yellow": (0, 255, 255),
                "red": (0, 0, 255),
                "green": (0, 255, 0),
                "blue": (255, 0, 0),
                "cyan": (255, 255, 0),
                "magenta": (255, 0, 255),
                "brown": (19, 69, 139),
                "orange": (0, 165, 255)
            }
            
            # Font settings
            font = cv2.FONT_HERSHEY_SIMPLEX
            thickness = 3
            
            # Calculate text positions (centered, below logo)
            logo_text_spacing = self.start_logo_text_spacing_var.get()
            logo_size_video = self.start_logo_size_var.get()
            
                        # Calculate logo position to match preview exactly
            logo_y = 50  # Top margin (same as preview)
            
            # Calculate text start position below logo (matching preview calculation)
            text_start_y = logo_y + logo_size_video + logo_text_spacing + (50 * 3.2)  # Scale 50 pixels from preview
            base_line_spacing = 30 * 3.2  # Scale from preview (30) by height ratio
            text_spacing = self.start_text_spacing_var.get()
            adjusted_spacing = base_line_spacing + (text_spacing * 10 * 3.2)  # Scale spacing to match preview
            
            # Line 1
            if line1 and not line1_hidden:
                color1 = color_map.get(line1_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color1 = color1
                (text_width, text_height), _ = cv2.getTextSize(line1, font, line1_size, thickness)
                x1 = (self.video_width - text_width) // 2
                y1 = int(text_start_y)  # Convert to integer for OpenCV
                cv2.putText(frame, line1, (x1, y1), font, line1_size, text_color1, thickness)
            
            # Line 2
            if line2:
                color2 = color_map.get(line2_color, (0, 0, 0))
                # No fade effect - use full color immediately
                text_color2 = color2
                (text_width, text_height), _ = cv2.getTextSize(line2, font, line2_size, thickness)
                x2 = (self.video_width - text_width) // 2
                if line1_hidden:
                    # If line 1 is hidden, line 2 uses the text start position
                    y2 = int(text_start_y)  # Convert to integer for OpenCV
                else:
                    # If line 1 is visible, line 2 is positioned below it
                    y2 = int(text_start_y + adjusted_spacing)  # Convert to integer for OpenCV
                cv2.putText(frame, line2, (x2, y2), font, line2_size, text_color2, thickness)
            
            return frame
        
        from moviepy import VideoClip
        start_clip = VideoClip(make_frame, duration=duration)
        return start_clip
            
    def show_success_message(self, output_path, minutes, seconds):
        time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
        self.status_label.config(text=f"✅ Video created in {time_str}! Saved to: {os.path.basename(output_path)}")
        
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
            
            self.progress_var.set(100)
            self.status_label.config(text="Test video created successfully!")
            messagebox.showinfo("Test Success", f"Test video created successfully!\nSaved to: {test_path}\n\nThis confirms the video system is working.")
            
        except Exception as e:
            self.progress_var.set(0)
            self.status_label.config(text="Test failed")
            messagebox.showerror("Test Failed", f"Test video creation failed:\n{str(e)}")
    
    def save_defaults(self):
        """Save current settings as defaults"""
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
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get()
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
        dialog.geometry("900x750")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"900x750+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Ending Text Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=6, pady=(0, 15))
        
        # Color and font options
        color_options = ["white", "yellow", "red", "green", "blue", "cyan", "magenta", "brown", "orange"]
        font_options = ["Arial", "Times New Roman", "Courier New", "Georgia", "Verdana", "Impact", "Comic Sans MS"]
        
        # Line 1
        ttk.Label(main_frame, text="Line 1:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(main_frame, textvariable=self.ending_line1_var, width=40).grid(row=1, column=1, columnspan=5, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(main_frame, text="Size:").grid(row=2, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line1_size_var, 
                   width=8, command=self.update_preview).grid(row=2, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(main_frame, text="Color:").grid(row=2, column=2, sticky=tk.W, padx=(0, 5))
        line1_color_combo = ttk.Combobox(main_frame, textvariable=self.ending_line1_color_var,
                                        values=color_options, width=10)
        line1_color_combo.grid(row=2, column=3, sticky=tk.W, padx=(0, 15))
        line1_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(main_frame, text="Font:").grid(row=2, column=4, sticky=tk.W, padx=(0, 5))
        line1_font_combo = ttk.Combobox(main_frame, textvariable=self.ending_line1_font_var,
                                       values=font_options, width=12)
        line1_font_combo.grid(row=2, column=5, sticky=tk.W)
        line1_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Line 2
        ttk.Label(main_frame, text="Line 2:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Entry(main_frame, textvariable=self.ending_line2_var, width=40).grid(row=3, column=1, columnspan=5, sticky=tk.W, pady=(15, 5))
        
        ttk.Label(main_frame, text="Size:").grid(row=4, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line2_size_var, 
                   width=8, command=self.update_preview).grid(row=4, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(main_frame, text="Color:").grid(row=4, column=2, sticky=tk.W, padx=(0, 5))
        line2_color_combo = ttk.Combobox(main_frame, textvariable=self.ending_line2_color_var,
                                        values=color_options, width=10)
        line2_color_combo.grid(row=4, column=3, sticky=tk.W, padx=(0, 15))
        line2_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(main_frame, text="Font:").grid(row=4, column=4, sticky=tk.W, padx=(0, 5))
        line2_font_combo = ttk.Combobox(main_frame, textvariable=self.ending_line2_font_var,
                                       values=font_options, width=12)
        line2_font_combo.grid(row=4, column=5, sticky=tk.W)
        line2_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Line 3
        ttk.Label(main_frame, text="Line 3:", font=('Arial', 10, 'bold')).grid(row=5, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Entry(main_frame, textvariable=self.ending_line3_var, width=40).grid(row=5, column=1, columnspan=5, sticky=tk.W, pady=(15, 5))
        
        ttk.Label(main_frame, text="Size:").grid(row=6, column=0, sticky=tk.W, padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0.5, to=3.0, increment=0.1, textvariable=self.ending_line3_size_var, 
                   width=8, command=self.update_preview).grid(row=6, column=1, sticky=tk.W, padx=(0, 15))
        
        ttk.Label(main_frame, text="Color:").grid(row=6, column=2, sticky=tk.W, padx=(0, 5))
        line3_color_combo = ttk.Combobox(main_frame, textvariable=self.ending_line3_color_var,
                                        values=color_options, width=10)
        line3_color_combo.grid(row=6, column=3, sticky=tk.W, padx=(0, 15))
        line3_color_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        ttk.Label(main_frame, text="Font:").grid(row=6, column=4, sticky=tk.W, padx=(0, 5))
        line3_font_combo = ttk.Combobox(main_frame, textvariable=self.ending_line3_font_var,
                                       values=font_options, width=12)
        line3_font_combo.grid(row=6, column=5, sticky=tk.W)
        line3_font_combo.bind('<<ComboboxSelected>>', lambda e: self.update_preview())
        
        # Ending duration
        ttk.Label(main_frame, text="Duration (sec):", font=('Arial', 10, 'bold')).grid(row=7, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Spinbox(main_frame, from_=1.0, to=15.0, increment=0.5, textvariable=self.ending_duration_var, 
                   width=8).grid(row=7, column=1, sticky=tk.W, pady=(15, 5))
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="10")
        preview_frame.grid(row=8, column=0, columnspan=6, pady=(15, 10), sticky=(tk.W, tk.E))
        
        # Preview canvas (black background to simulate video)
        # Use 16:9 aspect ratio to match video
        self.preview_canvas = tk.Canvas(preview_frame, width=600, height=338, bg='black')
        self.preview_canvas.grid(row=0, column=0, pady=(0, 10))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=6, pady=(10, 5))
        
        # Save as default button
        save_button = ttk.Button(button_frame, text="💾 Save as Default", 
                                command=lambda: self.save_defaults_and_close(dialog))
        save_button.grid(row=0, column=0, padx=(0, 10))
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.grid(row=0, column=1, padx=(10, 0))
        
        # Status label
        self.dialog_status_label = ttk.Label(main_frame, text="", foreground="green")
        self.dialog_status_label.grid(row=10, column=0, columnspan=6, pady=(5, 0))
        
        # Bind text changes to preview updates
        self.ending_line1_var.trace('w', lambda *args: self.update_preview())
        self.ending_line2_var.trace('w', lambda *args: self.update_preview())
        self.ending_line3_var.trace('w', lambda *args: self.update_preview())
        
        # Initial preview
        self.update_preview()
    
    def open_start_config(self):
        """Open start text configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Start Text")
        dialog.geometry("900x750")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"900x750+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="20")
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
        
        # Text spacing
        ttk.Label(main_frame, text="Text Spacing:", font=('Arial', 10, 'bold')).grid(row=5, column=2, sticky=tk.W, pady=(15, 5), padx=(20, 5))
        ttk.Spinbox(main_frame, from_=0, to=10, increment=1, textvariable=self.start_text_spacing_var, 
                   width=8, command=self.update_start_preview).grid(row=5, column=3, sticky=tk.W, pady=(15, 5))
        
        # Logo size
        ttk.Label(main_frame, text="Logo Size:", font=('Arial', 10, 'bold')).grid(row=5, column=4, sticky=tk.W, pady=(15, 5), padx=(20, 5))
        ttk.Spinbox(main_frame, from_=100, to=600, increment=25, textvariable=self.start_logo_size_var, 
                   width=8, command=self.update_start_preview).grid(row=5, column=5, sticky=tk.W, pady=(15, 5))
        
        # Logo-text spacing
        ttk.Label(main_frame, text="Logo-Text Spacing:", font=('Arial', 10, 'bold')).grid(row=6, column=0, sticky=tk.W, pady=(15, 5))
        ttk.Spinbox(main_frame, from_=0, to=200, increment=10, textvariable=self.start_logo_text_spacing_var, 
                   width=8, command=self.update_start_preview).grid(row=6, column=1, sticky=tk.W, pady=(15, 5))
        
        # Preview section
        preview_frame = ttk.LabelFrame(main_frame, text="Live Preview", padding="10")
        preview_frame.grid(row=7, column=0, columnspan=6, pady=(15, 10), sticky=(tk.W, tk.E))
        
        # Preview canvas (white background to simulate start screen)
        self.start_preview_canvas = tk.Canvas(preview_frame, width=600, height=338, bg='white')
        self.start_preview_canvas.grid(row=0, column=0, pady=(0, 10))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=8, column=0, columnspan=6, pady=(10, 5))
        
        # Save as default button
        save_button = ttk.Button(button_frame, text="💾 Save as Default", 
                                command=lambda: self.save_start_defaults_and_close(dialog))
        save_button.grid(row=0, column=0, padx=(0, 10))
        
        # Close button
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.grid(row=0, column=1, padx=(10, 0))
        
        # Status label
        self.start_dialog_status_label = ttk.Label(main_frame, text="", foreground="green")
        self.start_dialog_status_label.grid(row=9, column=0, columnspan=6, pady=(5, 0))
        
        # Bind text changes to preview updates
        self.start_line1_var.trace('w', lambda *args: self.update_start_preview())
        self.start_line2_var.trace('w', lambda *args: self.update_start_preview())
        
        # Initial preview
        self.update_start_preview()
    
    def update_start_preview(self):
        """Update the live preview of the start text"""
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
            
            # Color mapping
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
            
            # Load and display logo
            logo_path = os.path.join(os.path.dirname(__file__), "images", "logo.png")
            logo_y_offset = 0
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
                    
                    # Calculate logo position (centered, above text)
                    logo_x = (canvas_width - logo_size_preview) // 2
                    logo_y = 50  # Top margin
                    
                    # Display logo
                    self.start_preview_canvas.create_image(logo_x, logo_y, anchor=tk.NW, image=logo_photo)
                    
                    # Update text position to be below logo
                    logo_y_offset = logo_y + logo_size_preview + logo_text_spacing
                    
                except Exception as e:
                    print(f"Error loading logo for preview: {e}")
            
            # Calculate font sizes proportionally
            preview_font_scale = int(25 * height_scale)  # Scale based on height ratio
            font1_size = max(8, int(line1_size * preview_font_scale))  # Minimum size of 8
            font2_size = max(8, int(line2_size * preview_font_scale))
            
            # Calculate text positions (below logo)
            text_start_y = logo_y_offset + 50  # Start text below logo
            base_line_spacing = 30  # Base spacing between lines
            adjusted_spacing = base_line_spacing + (text_spacing * 10)  # Add spacing based on control
            
            # Line 1
            if line1 and not line1_hidden:
                color1 = color_map.get(line1_color, "#000000")
                y1 = text_start_y
                self.start_preview_canvas.create_text(canvas_width//2, y1, text=line1, 
                                                    fill=color1, font=(line1_font, font1_size, 'bold'))
            
            # Line 2
            if line2:
                color2 = color_map.get(line2_color, "#000000")
                if line1_hidden:
                    # If line 1 is hidden, line 2 uses the logo-text spacing directly
                    y2 = text_start_y
                else:
                    # If line 1 is visible, line 2 is positioned below it
                    y2 = text_start_y + adjusted_spacing
                self.start_preview_canvas.create_text(canvas_width//2, y2, text=line2, 
                                                    fill=color2, font=(line2_font, font2_size, 'bold'))
                
        except Exception as e:
            print(f"Start preview update error: {e}")
    
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
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get(),
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
                "default_duration": self.default_duration_var.get(),
                "transition_duration": self.transition_duration_var.get(),
                "effect": self.effect_var.get(),
                "music": self.music_var.get(),
                "music_volume": self.music_volume_var.get()
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
                
                # Load ending text and styling
                self.ending_line1_var.set(defaults.get("ending_line1", "Lincoln Rare Books & Collectables"))
                self.ending_line2_var.set(defaults.get("ending_line2", "Many thousands of postcards in store"))
                self.ending_line3_var.set(defaults.get("ending_line3", "Please Like and Subscribe!"))
                self.ending_line1_size_var.set(defaults.get("ending_line1_size", 1.5))
                self.ending_line2_size_var.set(defaults.get("ending_line2_size", 1.5))
                self.ending_line3_size_var.set(defaults.get("ending_line3_size", 1.5))
                self.ending_line1_color_var.set(defaults.get("ending_line1_color", "white"))
                self.ending_line2_color_var.set(defaults.get("ending_line2_color", "white"))
                self.ending_line3_color_var.set(defaults.get("ending_line3_color", "white"))
                self.ending_line1_font_var.set(defaults.get("ending_line1_font", "Arial"))
                self.ending_line2_font_var.set(defaults.get("ending_line2_font", "Arial"))
                self.ending_line3_font_var.set(defaults.get("ending_line3_font", "Arial"))
                self.ending_duration_var.set(defaults.get("ending_duration", 5.0))
                
                # Load other settings
                self.default_duration_var.set(defaults.get("default_duration", 4))
                self.transition_duration_var.set(defaults.get("transition_duration", 1))
                self.effect_var.set(defaults.get("effect", "fade"))
                self.music_var.set(defaults.get("music", "Vintage Memories"))
                self.music_volume_var.set(defaults.get("music_volume", 0.3))
                
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