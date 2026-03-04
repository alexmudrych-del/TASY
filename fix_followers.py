"""
Script to fix follower counts based on actual current count
This adjusts the cumulative totals to match the real follower count
"""

from app import app, db
from models import FollowerSnapshot
from datetime import datetime

def fix_follower_counts(actual_count=837, platform='instagram'):
    """
    Adjust follower counts to match actual current count
    This works backwards from the actual count to normalize the data
    """
    with app.app_context():
        # Get all snapshots for the platform, ordered by date
        snapshots = FollowerSnapshot.query.filter_by(platform=platform).order_by(FollowerSnapshot.date).all()
        
        if not snapshots:
            print(f"No snapshots found for platform {platform}")
            return
        
        # Get the last snapshot
        last_snapshot = snapshots[-1]
        last_date = last_snapshot.date
        last_count_in_db = last_snapshot.follower_count
        
        print(f"Last snapshot: {last_date}, count in DB: {last_count_in_db}, actual count: {actual_count}")
        
        # Calculate adjustment factor
        if last_count_in_db > 0:
            adjustment_factor = actual_count / last_count_in_db
            print(f"Adjustment factor: {adjustment_factor}")
        else:
            adjustment_factor = 1.0
        
        # Adjust all counts proportionally
        for snapshot in snapshots:
            # Calculate what the count should be based on proportion
            # We'll use the ratio of actual to DB count
            original_count = snapshot.follower_count
            adjusted_count = int(original_count * adjustment_factor)
            
            snapshot.follower_count = adjusted_count
            print(f"  {snapshot.date}: {original_count} -> {adjusted_count}")
        
        db.session.commit()
        print(f"\nFixed {len(snapshots)} snapshots for {platform}")
        print(f"Last count is now: {snapshots[-1].follower_count} (should be {actual_count})")

if __name__ == '__main__':
    print("Fixing follower counts...")
    print("Using actual Instagram count: 837")
    fix_follower_counts(actual_count=837, platform='instagram')
