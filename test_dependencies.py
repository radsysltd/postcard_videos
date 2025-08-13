#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed
"""

def test_imports():
    """Test all required imports"""
    print("Testing imports...")
    
    try:
        import tkinter as tk
        print("✓ tkinter - OK")
    except ImportError as e:
        print(f"✗ tkinter - FAILED: {e}")
        return False
    
    try:
        from PIL import Image, ImageTk
        print("✓ Pillow (PIL) - OK")
    except ImportError as e:
        print(f"✗ Pillow (PIL) - FAILED: {e}")
        return False
    
    try:
        import cv2
        print("✓ OpenCV - OK")
    except ImportError as e:
        print(f"✗ OpenCV - FAILED: {e}")
        return False
    
    try:
        import moviepy
        print("✓ MoviePy - OK")
    except ImportError as e:
        print(f"✗ MoviePy - FAILED: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy - OK")
    except ImportError as e:
        print(f"✗ NumPy - FAILED: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of key components"""
    print("\nTesting basic functionality...")
    
    try:
        # Test PIL
        from PIL import Image
        test_img = Image.new('RGB', (100, 100), color='red')
        print("✓ PIL image creation - OK")
    except Exception as e:
        print(f"✗ PIL image creation - FAILED: {e}")
        return False
    
    try:
        # Test OpenCV
        import cv2
        import numpy as np
        test_array = np.zeros((100, 100, 3), dtype=np.uint8)
        test_array[:] = (255, 0, 0)  # Red
        print("✓ OpenCV array creation - OK")
    except Exception as e:
        print(f"✗ OpenCV array creation - FAILED: {e}")
        return False
    
    try:
        # Test MoviePy (basic)
        from moviepy import ColorClip
        test_clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
        print("✓ MoviePy clip creation - OK")
    except Exception as e:
        print(f"✗ MoviePy clip creation - FAILED: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("Postcard Video Creator - Dependency Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n❌ Some imports failed. Please install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    
    # Test functionality
    if not test_basic_functionality():
        print("\n❌ Some functionality tests failed.")
        return False
    
    print("\n✅ All tests passed! The application should work correctly.")
    print("\nTo run the application:")
    print("python postcard_video_creator.py")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1) 