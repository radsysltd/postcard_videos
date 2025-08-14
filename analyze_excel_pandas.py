#!/usr/bin/env python3
"""
Analyze the UPLOAD_postcards.xlsx file using pandas and multiple methods
"""

import pandas as pd
import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def analyze_excel_structure(file_path):
    """Analyze Excel file structure by examining the ZIP contents"""
    print(f"🔍 Analyzing Excel file structure: {file_path}")
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_file:
            print(f"📦 ZIP Contents:")
            file_list = zip_file.namelist()
            for file in sorted(file_list):
                size = zip_file.getinfo(file).file_size
                print(f"   • {file} ({size:,} bytes)")
            
            # Try to read shared strings
            if 'xl/sharedStrings.xml' in file_list:
                print(f"\n📝 Extracting shared strings...")
                try:
                    with zip_file.open('xl/sharedStrings.xml') as f:
                        content = f.read().decode('utf-8')
                        # Parse XML to extract text
                        root = ET.fromstring(content)
                        strings = []
                        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                            if si.text:
                                strings.append(si.text)
                        
                        print(f"   • Found {len(strings)} shared strings")
                        print(f"   • Sample strings (first 20):")
                        for i, s in enumerate(strings[:20]):
                            # Truncate long strings
                            display_string = s[:50] + "..." if len(s) > 50 else s
                            print(f"     {i+1:2d}: {repr(display_string)}")
                        
                        return strings
                        
                except Exception as e:
                    print(f"   ❌ Error reading shared strings: {e}")
            
            # Try to read worksheet data
            worksheet_files = [f for f in file_list if f.startswith('xl/worksheets/')]
            for ws_file in worksheet_files:
                print(f"\n📄 Analyzing {ws_file}...")
                try:
                    with zip_file.open(ws_file) as f:
                        content = f.read().decode('utf-8')
                        print(f"   • File size: {len(content):,} characters")
                        
                        # Count rows and cells
                        root = ET.fromstring(content)
                        rows = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row')
                        cells = root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c')
                        print(f"   • Rows: {len(rows)}")
                        print(f"   • Cells: {len(cells)}")
                        
                        # Sample cell values
                        print(f"   • Sample cell references:")
                        for i, cell in enumerate(cells[:10]):
                            ref = cell.get('r', f'Cell{i+1}')
                            value_elem = cell.find('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                            if value_elem is not None:
                                print(f"     {ref}: {value_elem.text}")
                        
                except Exception as e:
                    print(f"   ❌ Error reading worksheet: {e}")
                    
    except Exception as e:
        print(f"❌ Error analyzing ZIP structure: {e}")
        return []

def analyze_with_pandas(file_path):
    """Try to analyze using pandas with different engines and options"""
    print(f"\n📊 Attempting to read with pandas...")
    
    engines = ['openpyxl', 'xlrd']
    
    for engine in engines:
        try:
            print(f"\n🔧 Trying engine: {engine}")
            
            # Try reading with different options
            df = pd.read_excel(file_path, engine=engine, header=None)
            
            print(f"✅ Success with {engine}!")
            print(f"   • Shape: {df.shape[0]} rows × {df.shape[1]} columns")
            
            # Show data types
            print(f"   • Data types: {df.dtypes.value_counts().to_dict()}")
            
            # Show first few rows
            print(f"   • First 5 rows:")
            pd.set_option('display.max_columns', 10)
            pd.set_option('display.width', 120)
            print(df.head())
            
            # Look for non-null data
            print(f"   • Non-null counts per column:")
            non_null_counts = df.count()
            for col, count in non_null_counts.items():
                if count > 0:
                    print(f"     Column {col}: {count} non-null values")
            
            # Look for specific patterns
            print(f"   • Searching for postcard-related content...")
            postcard_terms = ['postcard', 'vintage', 'lincolnshire', 'image', 'photo', 'upload', 'description']
            
            for term in postcard_terms:
                matches = 0
                for col in df.columns:
                    col_matches = df[col].astype(str).str.contains(term, case=False, na=False).sum()
                    matches += col_matches
                
                if matches > 0:
                    print(f"     Found '{term}': {matches} occurrences")
            
            # Try to identify potential headers
            print(f"   • Potential headers (first row):")
            first_row = df.iloc[0]
            for i, value in enumerate(first_row):
                if pd.notna(value) and str(value).strip():
                    print(f"     Column {i}: {repr(str(value)[:50])}")
            
            return df
            
        except Exception as e:
            print(f"   ❌ Failed with {engine}: {e}")
    
    return None

def main():
    """Main function"""
    excel_file = "data/UPLOAD_postcards.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ File not found: {excel_file}")
        return
    
    print(f"📁 File size: {os.path.getsize(excel_file):,} bytes")
    
    # Analyze structure first
    strings = analyze_excel_structure(excel_file)
    
    # Try pandas approach
    df = analyze_with_pandas(excel_file)
    
    # Summary based on findings
    print(f"\n📋 Summary:")
    if strings:
        print(f"   • The file contains {len(strings)} text strings")
        print(f"   • This appears to be a valid Excel file with data")
    
    if df is not None:
        print(f"   • Successfully read with pandas")
        print(f"   • Contains {df.shape[0]} rows and {df.shape[1]} columns")
    else:
        print(f"   • Could not read with pandas (may have formatting issues)")
    
    print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
