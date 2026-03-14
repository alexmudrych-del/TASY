"""
Database models for Meta Business Analytics Dashboard
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()


class FollowerSnapshot(db.Model):
    """Follower count snapshots over time"""
    __tablename__ = 'follower_snapshots'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    follower_count = db.Column(db.Integer, nullable=False)
    new_followers = db.Column(db.Integer, default=0)
    lost_followers = db.Column(db.Integer, default=0)
    platform = db.Column(db.String(20), nullable=False, default='instagram')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('date', 'platform', name='unique_date_platform'),)
    
    def __repr__(self):
        return f'<FollowerSnapshot {self.date} {self.platform}: {self.follower_count}>'


class Demographics(db.Model):
    """Demographic data for followers"""
    __tablename__ = 'demographics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    age_range = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    location = db.Column(db.String(100))
    city = db.Column(db.String(100))
    count = db.Column(db.Integer, nullable=False)
    platform = db.Column(db.String(20), nullable=False, default='instagram')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('date', 'platform', 'age_range', 'gender', 'location', 'city', name='unique_demographics'),)
    
    def __repr__(self):
        return f'<Demographics {self.date} {self.platform} {self.age_range} {self.gender} {self.location}: {self.count}>'


class EngagementMetric(db.Model):
    """Engagement metrics"""
    __tablename__ = 'engagement_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, index=True)
    views = db.Column(db.Integer, default=0)
    interactions = db.Column(db.Integer, default=0)
    reach = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    visits = db.Column(db.Integer, default=0)  # Profile visits
    platform = db.Column(db.String(20), nullable=False, default='instagram')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    __table_args__ = (db.UniqueConstraint('date', 'platform', name='unique_engagement_date_platform'),)
    
    def __repr__(self):
        return f'<EngagementMetric {self.date} {self.platform}: {self.interactions} interactions>'
