"""
Script to import all CSV files from Imput IG Pneuboss and Imput FB Pneuboss directories
This will import data for both Instagram and Facebook platforms
"""

import os
import glob
from app import app, db
from csv_parser import parse_csv_file

def import_all_csv_files():
    """Import all CSV files from both Instagram and Facebook directories"""
    
    # Paths to CSV directories
    base_dir = os.path.dirname(__file__)
    ig_dir = os.path.join(base_dir, 'Imput IG Pneuboss')
    fb_dir = os.path.join(base_dir, 'Imput FB Pneuboss')
    
    directories = [
        ('Instagram', ig_dir),
        ('Facebook', fb_dir)
    ]
    
    results = {
        'success': [],
        'failed': []
    }
    
    print("=" * 60)
    print("IMPORTING PNEUBOSS DATA")
    print("=" * 60)
    
    with app.app_context():
        for platform_name, csv_dir in directories:
            if not os.path.exists(csv_dir):
                print(f"\n⚠️  Directory '{csv_dir}' not found! Skipping {platform_name}...")
                continue
            
            # Get all CSV files
            csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
            
            if not csv_files:
                print(f"\n⚠️  No CSV files found in '{csv_dir}'")
                continue
            
            print(f"\n📁 Processing {platform_name} files ({len(csv_files)} files)...")
            print("-" * 60)
            
            for csv_file in sorted(csv_files):
                filename = os.path.basename(csv_file)
                print(f"\n  Processing: {filename}")
                
                try:
                    result = parse_csv_file(csv_file, db)
                    imported = result.get('imported', 0)
                    csv_type = result.get('type', 'unknown')
                    
                    print(f"    ✓ Successfully imported {imported} records (type: {csv_type})")
                    results['success'].append({
                        'file': filename,
                        'platform': platform_name,
                        'imported': imported,
                        'type': csv_type
                    })
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"    ✗ Error: {error_msg}")
                    results['failed'].append({
                        'file': filename,
                        'platform': platform_name,
                        'error': error_msg
                    })
    
    # Summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(results['success']) + len(results['failed'])}")
    print(f"Successfully imported: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results['success']:
        print("\n✅ Successfully imported files:")
        for item in results['success']:
            print(f"  [{item['platform']}] {item['file']}: {item['imported']} records ({item['type']})")
    
    if results['failed']:
        print("\n❌ Failed files:")
        for item in results['failed']:
            print(f"  [{item['platform']}] {item['file']}: {item['error']}")
    
    print("\n" + "=" * 60)
    print("Import completed!")
    print("You can now view the data in the dashboard at http://127.0.0.1:5000")
    print("\n💡 Tip: Use the platform filter in the dashboard to view Instagram or Facebook data separately")


if __name__ == '__main__':
    print("Starting Pneuboss CSV import process...")
    print("This will import all CSV files from 'Imput IG Pneuboss' and 'Imput FB Pneuboss' directories")
    print()
    
    import_all_csv_files()
