from app import app, db
from models import FollowerSnapshot, EngagementMetric

with app.app_context():
    print('📊 Follower data by platform:')
    for platform in ['instagram', 'facebook']:
        count = FollowerSnapshot.query.filter_by(platform=platform).count()
        last = FollowerSnapshot.query.filter_by(platform=platform).order_by(FollowerSnapshot.date.desc()).first()
        if last:
            print(f'  {platform.upper()}: {count} records, last: {last.date} ({last.follower_count} followers)')
        else:
            print(f'  {platform.upper()}: {count} records')
    
    print('\n📈 Engagement data by platform:')
    for platform in ['instagram', 'facebook']:
        count = EngagementMetric.query.filter_by(platform=platform).count()
        if count > 0:
            sample = EngagementMetric.query.filter_by(platform=platform).first()
            print(f'  {platform.upper()}: {count} records (sample: {sample.date}, views={sample.views})')
        else:
            print(f'  {platform.upper()}: {count} records')
