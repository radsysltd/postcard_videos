#!/usr/bin/env python3
"""
Extract and analyze all content from the UPLOAD_postcards.xlsx file
"""

import zipfile
import xml.etree.ElementTree as ET
import re
from collections import Counter

def extract_all_strings(file_path):
    """Extract all text strings from the Excel file"""
    print(f"🔍 Extracting all content from: {file_path}")
    
    all_strings = []
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            
            # Extract shared strings
            if 'xl/sharedStrings.xml' in zip_file.namelist():
                print(f"📝 Reading shared strings...")
                with zip_file.open('xl/sharedStrings.xml') as f:
                    content = f.read().decode('utf-8')
                    root = ET.fromstring(content)
                    
                    for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                        if si.text:
                            all_strings.append(si.text)
            
            # Extract comments if any
            comment_files = [f for f in zip_file.namelist() if 'comments' in f]
            for comment_file in comment_files:
                print(f"💬 Reading comments from {comment_file}...")
                try:
                    with zip_file.open(comment_file) as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        
                        # Extract comment text
                        for text_elem in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                            if text_elem.text:
                                all_strings.append(f"[COMMENT] {text_elem.text}")
                                
                except Exception as e:
                    print(f"   ❌ Error reading comments: {e}")
            
            # Extract worksheet data
            worksheet_files = [f for f in zip_file.namelist() if f.startswith('xl/worksheets/') and f.endswith('.xml')]
            for ws_file in worksheet_files:
                print(f"📄 Reading worksheet {ws_file}...")
                try:
                    with zip_file.open(ws_file) as f:
                        content = f.read().decode('utf-8')
                        root = ET.fromstring(content)
                        
                        # Extract cell values that are inline strings
                        for cell in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                            # Check for inline strings
                            is_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}is')
                            if is_elem is not None:
                                for t in is_elem.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                                    if t.text:
                                        all_strings.append(f"[INLINE] {t.text}")
                        
                except Exception as e:
                    print(f"   ❌ Error reading worksheet: {e}")
    
    except Exception as e:
        print(f"❌ Error extracting strings: {e}")
    
    return all_strings

def analyze_strings(strings):
    """Analyze the extracted strings for patterns and content"""
    print(f"\n📊 Analyzing {len(strings)} extracted strings...")
    
    # Categorize strings
    categories = {
        'ebay_template': [],
        'postcard_related': [],
        'field_names': [],
        'descriptions': [],
        'urls': [],
        'file_paths': [],
        'numbers': [],
        'other': []
    }
    
    # Keywords for categorization
    ebay_keywords = ['action', 'siteid', 'currency', 'version', 'template', 'ebay']
    postcard_keywords = ['postcard', 'vintage', 'lincolnshire', 'card', 'old', 'antique']
    field_keywords = ['title', 'description', 'category', 'price', 'condition', 'shipping']
    
    for string in strings:
        string_lower = string.lower()
        
        # Check categories
        if any(keyword in string_lower for keyword in ebay_keywords):
            categories['ebay_template'].append(string)
        elif any(keyword in string_lower for keyword in postcard_keywords):
            categories['postcard_related'].append(string)
        elif any(keyword in string_lower for keyword in field_keywords):
            categories['field_names'].append(string)
        elif string.startswith('http') or 'www.' in string:
            categories['urls'].append(string)
        elif ('\\' in string or '/' in string) and len(string) > 10:
            categories['file_paths'].append(string)
        elif re.match(r'^\d+(\.\d+)?$', string.strip()):
            categories['numbers'].append(string)
        elif len(string) > 50:
            categories['descriptions'].append(string)
        else:
            categories['other'].append(string)
    
    # Print categorized results
    for category, items in categories.items():
        if items:
            print(f"\n📂 {category.upper().replace('_', ' ')} ({len(items)} items):")
            for i, item in enumerate(items[:10]):  # Show first 10
                # Clean up display
                display_item = item.replace('[COMMENT] ', '').replace('[INLINE] ', '')
                if len(display_item) > 80:
                    display_item = display_item[:77] + "..."
                print(f"   {i+1:2d}: {repr(display_item)}")
            
            if len(items) > 10:
                print(f"   ... and {len(items) - 10} more items")
    
    # Look for specific patterns
    print(f"\n🔍 Pattern Analysis:")
    
    # Count unique first words
    first_words = [s.split()[0].lower() for s in strings if s.strip() and ' ' in s]
    common_first_words = Counter(first_words).most_common(10)
    if common_first_words:
        print(f"   • Most common first words: {dict(common_first_words)}")
    
    # Look for structured data
    structured_patterns = []
    for string in strings:
        if '=' in string and len(string) < 100:
            structured_patterns.append(string)
    
    if structured_patterns:
        print(f"   • Found {len(structured_patterns)} key=value patterns:")
        for pattern in structured_patterns[:5]:
            print(f"     {repr(pattern)}")
    
    # Look for field indicators
    field_indicators = [s for s in strings if s.strip().startswith('*') or 'required' in s.lower()]
    if field_indicators:
        print(f"   • Found {len(field_indicators)} field indicators:")
        for indicator in field_indicators[:5]:
            print(f"     {repr(indicator)}")

def main():
    """Main function"""
    excel_file = "data/UPLOAD_postcards.xlsx"
    
    strings = extract_all_strings(excel_file)
    
    if strings:
        analyze_strings(strings)
        
        print(f"\n📋 SUMMARY:")
        print(f"   • This appears to be an eBay listing template file")
        print(f"   • Contains {len(strings)} text elements")
        print(f"   • Likely used for bulk uploading postcard listings to eBay")
        print(f"   • May contain template fields for:")
        print(f"     - Product titles and descriptions")
        print(f"     - Category information")
        print(f"     - Pricing and shipping details")
        print(f"     - Image references")
        print(f"     - Postcard-specific metadata")
    else:
        print(f"❌ No strings extracted")
    
    print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
