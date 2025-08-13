# Postcard Video Creator

A desktop application that creates YouTube-style videos from postcard image pairs with professional effects and transitions.

## Features

- **Easy-to-use GUI**: Simple interface for adding postcard pairs and configuring video settings
- **Customizable Timing**: Set individual duration for each image (default 10s)
- **Multiple Transition Effects**: Choose from fade, slide, and zoom transitions
- **High-Quality Output**: Support for 1080p, 720p, and 4K resolutions
- **Real-time Preview**: Preview selected postcard images before processing
- **Progress Tracking**: Visual progress bar and status updates during video creation
- **Batch Processing**: Add multiple postcard pairs for longer videos

## Installation

### Prerequisites

- Python 3.7 or higher
- Windows 10/11 (tested on Windows 10)

### Setup

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd postcard_videos
   ```

2. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python postcard_video_creator.py
   ```

## Usage

### Getting Started

1. **Launch the application** by running `python postcard_video_creator.py`

2. **Configure video settings**:
   - Set default duration (default: 10 seconds)
   - Set transition duration (default: 1 second)
   - Choose video resolution (1920x1080, 1280x720, or 3840x2160)
   - Select transition effect (fade, slide_left, slide_right, zoom_in, zoom_out)

3. **Add postcard images**:
   - Click "Select Multiple Images"
   - Select all your postcard images in order: front1, back1, front2, back2, front3, back3, etc.
   - The application will validate that you have an even number of images
   - You can double-click any row to edit individual image durations

4. **Select output folder**:
   - Click "Select Output Folder"
   - Choose where to save the generated video

5. **Create the video**:
   - Click "Create Video" to start processing
   - Monitor progress in the progress bar
   - Wait for completion notification

### Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- BMP (.bmp)
- TIFF (.tiff)

### Video Output

- **Format**: MP4 (H.264 codec)
- **Frame Rate**: 30 FPS
- **Audio**: AAC codec (silent video)
- **Naming**: `postcard_video_YYYYMMDD_HHMMSS.mp4`

## Transition Effects

1. **Fade**: Smooth crossfade between images
2. **Slide Left**: New image slides in from the right
3. **Slide Right**: New image slides in from the left
4. **Zoom In**: New image starts small and zooms to full size
5. **Zoom Out**: New image starts large and zooms to normal size

## Tips for Best Results

1. **Image Quality**: Use high-resolution images (at least 1920x1080) for best results
2. **Aspect Ratio**: Images will be automatically resized to fit the selected video resolution
3. **File Organization**: Keep all postcard images in the same folder for easier selection
4. **Image Order**: Select images in the correct order: front1, back1, front2, back2, etc.
5. **Individual Durations**: Double-click any row to customize duration for specific images
6. **Processing Time**: Video creation time depends on the number of postcards and selected resolution
7. **Storage**: Ensure sufficient disk space for video output

## Troubleshooting

### Common Issues

1. **"Could not load image" error**:
   - Ensure image files are not corrupted
   - Check that file paths don't contain special characters
   - Verify image format is supported

2. **Video creation fails**:
   - Check available disk space
   - Ensure output folder is writable
   - Verify all dependencies are installed correctly

3. **Slow performance**:
   - Use lower resolution for faster processing
   - Close other applications to free up system resources
   - Consider reducing the number of postcards in a single video

### Dependencies

If you encounter import errors, ensure all required packages are installed:

```bash
pip install opencv-python moviepy Pillow numpy
```

## Technical Details

- **GUI Framework**: Tkinter (built-in Python GUI library)
- **Video Processing**: MoviePy library
- **Image Processing**: OpenCV and Pillow
- **Threading**: Background video processing to keep UI responsive

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the application.

## Support

For questions or support, please open an issue in the repository or contact the maintainer. 