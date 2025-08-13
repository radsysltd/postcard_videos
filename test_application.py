#!/usr/bin/env python3
"""
Test script for Postcard Video Creator application
"""

import os
import sys
import time
from PIL import Image

def test_sample_images_exist():
    """Test that sample images were created"""
    print("Testing sample images...")
    
    test_dir = "test_images"
    if not os.path.exists(test_dir):
        print("❌ test_images directory not found")
        return False
    
    expected_files = [
        "postcard_1_front.jpg", "postcard_1_back.jpg",
        "postcard_2_front.jpg", "postcard_2_back.jpg", 
        "postcard_3_front.jpg", "postcard_3_back.jpg",
        "postcard_4_front.jpg", "postcard_4_back.jpg",
        "postcard_5_front.jpg", "postcard_5_back.jpg"
    ]
    
    missing_files = []
    for file in expected_files:
        file_path = os.path.join(test_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All sample images found")
    return True

def test_image_loading():
    """Test that images can be loaded properly"""
    print("\nTesting image loading...")
    
    test_dir = "test_images"
    image_files = [f for f in os.listdir(test_dir) if f.endswith('.jpg')]
    
    for file in image_files:
        try:
            file_path = os.path.join(test_dir, file)
            img = Image.open(file_path)
            img.verify()  # Verify image integrity
            print(f"✅ {file} - OK")
        except Exception as e:
            print(f"❌ {file} - FAILED: {e}")
            return False
    
    return True

def test_application_import():
    """Test that the main application can be imported"""
    print("\nTesting application import...")
    
    try:
        # Import the main application
        import postcard_video_creator
        print("✅ Application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Application import failed: {e}")
        return False

def test_gui_creation():
    """Test that the GUI can be created (without showing it)"""
    print("\nTesting GUI creation...")
    
    try:
        import tkinter as tk
        from postcard_video_creator import PostcardVideoCreator
        
        # Create root window but don't show it
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create application instance
        app = PostcardVideoCreator(root)
        
        # Test basic properties
        assert hasattr(app, 'postcard_images')
        assert hasattr(app, 'image_durations')
        assert hasattr(app, 'default_duration')
        assert hasattr(app, 'transition_duration')
        
        print("✅ GUI creation successful")
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI creation failed: {e}")
        return False

def test_video_processing_logic():
    """Test the video processing logic with sample data"""
    print("\nTesting video processing logic...")
    
    try:
        import tkinter as tk
        from postcard_video_creator import PostcardVideoCreator
        
        # Create root window but don't show it
        root = tk.Tk()
        root.withdraw()
        
        # Create application instance
        app = PostcardVideoCreator(root)
        
        # Test with sample data
        test_images = [
            "test_images/postcard_1_front.jpg",
            "test_images/postcard_1_back.jpg",
            "test_images/postcard_2_front.jpg",
            "test_images/postcard_2_back.jpg"
        ]
        
        # Verify files exist
        for img_path in test_images:
            if not os.path.exists(img_path):
                print(f"❌ Test image not found: {img_path}")
                root.destroy()
                return False
        
        # Test image clip creation
        try:
            clip = app.create_image_clip(test_images[0], 5.0)
            print("✅ Image clip creation successful")
        except Exception as e:
            print(f"❌ Image clip creation failed: {e}")
            root.destroy()
            return False
        
        # Test transition creation
        try:
            clip1 = app.create_image_clip(test_images[0], 1.0)
            clip2 = app.create_image_clip(test_images[1], 1.0)
            transition = app.create_transition(clip1, clip2)
            print("✅ Transition creation successful")
        except Exception as e:
            print(f"❌ Transition creation failed: {e}")
            root.destroy()
            return False
        
        # Clean up
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ Video processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Postcard Video Creator - Application Test")
    print("=" * 50)
    
    tests = [
        test_sample_images_exist,
        test_image_loading,
        test_application_import,
        test_gui_creation,
        test_video_processing_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error: {test.__name__} - {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to use.")
        print("\nTo run the application:")
        print("python postcard_video_creator.py")
        print("\nTo test with sample images:")
        print("1. Launch the application")
        print("2. Click 'Select Multiple Images'")
        print("3. Select all images from test_images folder in order:")
        print("   postcard_1_front.jpg, postcard_1_back.jpg, postcard_2_front.jpg, etc.")
        print("4. Set output folder and create video")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 