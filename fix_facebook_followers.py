"""
Script to fix Facebook follower count to actual current count (19,357)
This adjusts the cumulative totals to match the real follower count
"""

from app import app, db
from models import FollowerSnapshot
from datetime import datetime

def fix_facebook_followers(actual_count=19357):
    """
    Adjust Facebook follower counts to match actual current count
    The CSV contains daily new followers, so we need to:
    1. Calculate the sum of all daily new followers
    2. Calculate the starting value before the first date
    3. Adjust all counts proportionally
    """
    with app.app_context():
        # Get all Facebook snapshots, ordered by date
        snapshots = FollowerSnapshot.query.filter_by(platform='facebook').order_by(FollowerSnapshot.date).all()
        
        if not snapshots:
            print("No Facebook snapshots found")
            return
        
        # Calculate sum of all new followers
        total_new = sum(s.new_followers for s in snapshots)
        first_count = snapshots[0].follower_count
        last_count = snapshots[-1].follower_count
        
        print(f"Current state:")
        print(f"  First date: {snapshots[0].date}, count: {first_count}")
        print(f"  Last date: {snapshots[-1].date}, count: {last_count}")
        print(f"  Total new followers (sum): {total_new}")
        print(f"  Actual current count: {actual_count}")
        
        # Calculate what the starting value should be
        # If last_count = starting_value + total_new, then:
        # starting_value = actual_count - total_new
        starting_value = actual_count - total_new
        
        print(f"\nCalculated starting value: {starting_value:,}")
        
        # Now adjust all snapshots
        # The first snapshot should have: starting_value + new_followers[0]
        # Each subsequent snapshot: previous_count + new_followers - lost_followers
        
        current_count = starting_value
        for snapshot in snapshots:
            current_count = current_count + snapshot.new_followers - snapshot.lost_followers
            snapshot.follower_count = current_count
        
        db.session.commit()
        
        print(f"\n✓ Fixed {len(snapshots)} Facebook snapshots")
        print(f"  First count: {snapshots[0].follower_count:,}")
        print(f"  Last count: {snapshots[-1].follower_count:,} (should be {actual_count:,})")
        
        # Verify
        if snapshots[-1].follower_count == actual_count:
            print("✓ Verification passed!")
        else:
            print(f"⚠ Warning: Last count ({snapshots[-1].follower_count}) doesn't match expected ({actual_count})")

if __name__ == '__main__':
    print("Fixing Facebook follower counts...")
    print("Using actual Facebook count: 19,357")
    fix_facebook_followers(actual_count=19357)
