"""
Script to import all CSV files from Imput CSV directory into the database
Run this once to load all data without using the web upload interface
"""

import os
import glob
from app import app, db
from csv_parser import parse_csv_file

def import_all_csv_files():
    """Import all CSV files from the Imput CSV directory"""
    
    # Path to CSV directory
    csv_dir = os.path.join(os.path.dirname(__file__), 'Imput CSV')
    
    if not os.path.exists(csv_dir):
        print(f"Error: Directory '{csv_dir}' not found!")
        return
    
    # Get all CSV files
    csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in '{csv_dir}'")
        return
    
    print(f"Found {len(csv_files)} CSV files to import")
    print("=" * 60)
    
    results = {
        'success': [],
        'failed': []
    }
    
    with app.app_context():
        for csv_file in sorted(csv_files):
            filename = os.path.basename(csv_file)
            print(f"\nProcessing: {filename}")
            
            try:
                result = parse_csv_file(csv_file, db)
                imported = result.get('imported', 0)
                csv_type = result.get('type', 'unknown')
                
                print(f"  ✓ Successfully imported {imported} records (type: {csv_type})")
                results['success'].append({
                    'file': filename,
                    'imported': imported,
                    'type': csv_type
                })
                
            except Exception as e:
                error_msg = str(e)
                print(f"  ✗ Error: {error_msg}")
                results['failed'].append({
                    'file': filename,
                    'error': error_msg
                })
    
    # Summary
    print("\n" + "=" * 60)
    print("IMPORT SUMMARY")
    print("=" * 60)
    print(f"Total files: {len(csv_files)}")
    print(f"Successfully imported: {len(results['success'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results['success']:
        print("\nSuccessfully imported files:")
        for item in results['success']:
            print(f"  - {item['file']}: {item['imported']} records ({item['type']})")
    
    if results['failed']:
        print("\nFailed files:")
        for item in results['failed']:
            print(f"  - {item['file']}: {item['error']}")
    
    print("\n" + "=" * 60)
    print("Import completed!")
    print("You can now view the data in the dashboard at http://127.0.0.1:5000")


if __name__ == '__main__':
    print("Starting CSV import process...")
    print("This will import all CSV files from 'Imput CSV' directory")
    print()
    
    import_all_csv_files()
