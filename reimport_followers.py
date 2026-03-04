"""
Script to reimport follower data from specific CSV files
This ensures data is correctly linked to the platform based on the file location
"""

import os
from app import app, db
from models import FollowerSnapshot
from csv_parser import parse_followers_csv

def reimport_followers():
    """Reimport follower data from specific CSV files"""
    
    # Clear existing follower data
    with app.app_context():
        print("Clearing existing follower data...")
        FollowerSnapshot.query.delete()
        db.session.commit()
        print("✓ Cleared existing data")
        
        # Import Facebook data
        fb_file = '/Users/alex08/Desktop/Cursor Git/META Přehledy/Imput FB Pneuboss/Follows.csv'
        if os.path.exists(fb_file):
            print(f"\nImporting Facebook data from: {os.path.basename(fb_file)}")
            try:
                imported = parse_followers_csv(fb_file, db)
                print(f"✓ Successfully imported {imported} Facebook records")
            except Exception as e:
                print(f"✗ Error importing Facebook data: {e}")
        else:
            print(f"✗ Facebook file not found: {fb_file}")
        
        # Import Instagram data
        ig_file = '/Users/alex08/Desktop/Cursor Git/META Přehledy/Imput IG Pneuboss/Follows (1).csv'
        if os.path.exists(ig_file):
            print(f"\nImporting Instagram data from: {os.path.basename(ig_file)}")
            try:
                imported = parse_followers_csv(ig_file, db)
                print(f"✓ Successfully imported {imported} Instagram records")
            except Exception as e:
                print(f"✗ Error importing Instagram data: {e}")
        else:
            print(f"✗ Instagram file not found: {ig_file}")
        
        # Verify import
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)
        fb_count = FollowerSnapshot.query.filter_by(platform='facebook').count()
        ig_count = FollowerSnapshot.query.filter_by(platform='instagram').count()
        
        print(f"Facebook records: {fb_count}")
        print(f"Instagram records: {ig_count}")
        
        # Check latest records
        latest_fb = FollowerSnapshot.query.filter_by(platform='facebook').order_by(FollowerSnapshot.date.desc()).first()
        latest_ig = FollowerSnapshot.query.filter_by(platform='instagram').order_by(FollowerSnapshot.date.desc()).first()
        
        if latest_fb:
            print(f"\nLatest Facebook: {latest_fb.date} - {latest_fb.follower_count} followers")
        if latest_ig:
            print(f"Latest Instagram: {latest_ig.date} - {latest_ig.follower_count} followers")
        
        print("\n✓ Reimport completed!")

if __name__ == '__main__':
    print("Starting follower data reimport...")
    print("This will clear existing follower data and reimport from:")
    print("  - Facebook: Imput FB Pneuboss/Follows.csv")
    print("  - Instagram: Imput IG Pneuboss/Follows (1).csv")
    print()
    
    reimport_followers()
