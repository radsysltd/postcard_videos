#!/usr/bin/env python3
"""
Create sample postcard images for testing the Postcard Video Creator
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_postcard(front=True, postcard_num=1, size=(800, 600)):
    """Create a sample postcard image"""
    # Create image
    img = Image.new('RGB', size, color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Add border
    draw.rectangle([(10, 10), (size[0]-10, size[1]-10)], outline='black', width=3)
    
    if front:
        # Front of postcard
        title = f"POSTCARD {postcard_num} - FRONT"
        draw.text((size[0]//2, 100), title, fill='black', font=font, anchor='mm')
        
        # Add some decorative elements
        draw.rectangle([(50, 200), (size[0]-50, size[1]-150)], fill='lightblue', outline='blue', width=2)
        draw.text((size[0]//2, size[1]//2), f"Beautiful Scene {postcard_num}", fill='darkblue', font=font, anchor='mm')
        
        # Add stamp area
        draw.rectangle([(size[0]-120, 50), (size[0]-20, 150)], fill='red', outline='darkred', width=2)
        draw.text((size[0]-70, 100), "STAMP", fill='white', font=small_font, anchor='mm')
        
    else:
        # Back of postcard
        title = f"POSTCARD {postcard_num} - BACK"
        draw.text((size[0]//2, 50), title, fill='black', font=font, anchor='mm')
        
        # Add address lines
        draw.line([(50, 150), (size[0]-50, 150)], fill='black', width=2)
        draw.text((60, 120), "To:", fill='black', font=small_font)
        draw.text((60, 180), "From:", fill='black', font=small_font)
        
        # Add message area
        draw.rectangle([(50, 250), (size[0]-50, size[1]-100)], fill='lightyellow', outline='orange', width=2)
        draw.text((60, 270), f"Dear Friend,", fill='black', font=small_font)
        draw.text((60, 300), f"This is postcard {postcard_num}.", fill='black', font=small_font)
        draw.text((60, 330), f"Wish you were here!", fill='black', font=small_font)
        
        # Add date
        draw.text((size[0]-100, size[1]-50), "2024", fill='black', font=small_font)
    
    return img

def main():
    """Create sample postcard images"""
    print("Creating sample postcard images...")
    
    # Create test_images directory
    if not os.path.exists('test_images'):
        os.makedirs('test_images')
    
    # Create 5 sample postcards (10 images total)
    for i in range(1, 6):
        # Front
        front_img = create_sample_postcard(front=True, postcard_num=i)
        front_img.save(f'test_images/postcard_{i}_front.jpg', 'JPEG', quality=95)
        
        # Back
        back_img = create_sample_postcard(front=False, postcard_num=i)
        back_img.save(f'test_images/postcard_{i}_back.jpg', 'JPEG', quality=95)
        
        print(f"Created postcard {i} (front and back)")
    
    print("\n✅ Sample images created successfully!")
    print("Files created in 'test_images' directory:")
    print("- postcard_1_front.jpg, postcard_1_back.jpg")
    print("- postcard_2_front.jpg, postcard_2_back.jpg")
    print("- postcard_3_front.jpg, postcard_3_back.jpg")
    print("- postcard_4_front.jpg, postcard_4_back.jpg")
    print("- postcard_5_front.jpg, postcard_5_back.jpg")
    print("\nYou can now test the application with these images.")
    print("Select them in order: front1, back1, front2, back2, etc.")

if __name__ == "__main__":
    main() 