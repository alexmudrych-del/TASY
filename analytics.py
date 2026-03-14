"""
Analytics engine for calculating metrics and generating insights
"""

from datetime import datetime, timedelta
from collections import defaultdict


def calculate_follower_growth(snapshots):
    """Calculate follower growth metrics"""
    if not snapshots or len(snapshots) < 2:
        return {
            'total_growth': 0,
            'growth_rate': 0,
            'monthly_growth': [],
            'average_daily_growth': 0
        }
    
    sorted_snapshots = sorted(snapshots, key=lambda x: x.date)
    first = sorted_snapshots[0]
    last = sorted_snapshots[-1]
    
    # Total growth from first to last
    total_growth = last.follower_count - first.follower_count
    days_diff = (last.date - first.date).days
    
    # Calculate growth rate - use snapshot from 30 days ago as baseline
    # This gives month-over-month growth rate
    from datetime import timedelta
    month_ago = last.date - timedelta(days=30)
    baseline = next((s for s in reversed(sorted_snapshots) if s.date <= month_ago), None)
    
    # If no baseline from 30 days ago, use first snapshot from 3 months ago
    if not baseline:
        three_months_ago = last.date - timedelta(days=90)
        baseline = next((s for s in reversed(sorted_snapshots) if s.date <= three_months_ago), first)
    
    if baseline and baseline.follower_count > 0 and baseline != last:
        # Calculate growth from baseline to last
        growth_from_baseline = last.follower_count - baseline.follower_count
        growth_rate = (growth_from_baseline / baseline.follower_count * 100)
    elif first.follower_count > 0 and first != last:
        # Use first value if no baseline found
        growth_rate = (total_growth / first.follower_count * 100) if first.follower_count > 0 else 0
    else:
        # Started from 0 or same value - show 0%
        growth_rate = 0
    
    average_daily_growth = total_growth / days_diff if days_diff > 0 else 0
    
    monthly_growth = []
    current_month = None
    month_start = None
    
    for snapshot in sorted_snapshots:
        month_key = snapshot.date.strftime('%Y-%m')
        
        if month_key != current_month:
            if current_month and month_start:
                month_end_snapshot = snapshot
                month_growth = month_end_snapshot.follower_count - month_start.follower_count
                monthly_growth.append({
                    'month': current_month,
                    'growth': month_growth,
                    'start_count': month_start.follower_count,
                    'end_count': month_end_snapshot.follower_count
                })
            
            current_month = month_key
            month_start = snapshot
    
    if current_month and month_start:
        last_snapshot = sorted_snapshots[-1]
        if last_snapshot.date.strftime('%Y-%m') == current_month:
            monthly_growth.append({
                'month': current_month,
                'growth': last_snapshot.follower_count - month_start.follower_count,
                'start_count': month_start.follower_count,
                'end_count': last_snapshot.follower_count
            })
    
    return {
        'total_growth': total_growth,
        'growth_rate': round(growth_rate, 2),
        'average_daily_growth': round(average_daily_growth, 2),
        'monthly_growth': monthly_growth,
        'first_date': first.date.isoformat(),
        'last_date': last.date.isoformat(),
        'first_count': first.follower_count,
        'last_count': last.follower_count,
        'current_followers': last.follower_count  # Alias for frontend
    }


def aggregate_demographics(demographics_list):
    """Aggregate demographic data"""
    if not demographics_list:
        return {
            'by_age': {},
            'by_gender': {},
            'by_location': {},
            'by_city': {},
            'total': 0
        }
    
    by_age = defaultdict(int)
    by_gender = defaultdict(int)
    by_location = defaultdict(int)
    by_city = defaultdict(int)
    total = 0
    
    for demo in demographics_list:
        total += demo.count
        if demo.age_range:
            by_age[demo.age_range] += demo.count
        if demo.gender:
            by_gender[demo.gender] += demo.count
        if demo.location:
            by_location[demo.location] += demo.count
        if demo.city:
            by_city[demo.city] += demo.count
    
    age_list = [{'age_range': age, 'count': count} for age, count in sorted(by_age.items())]
    gender_list = [{'gender': gender, 'count': count} for gender, count in sorted(by_gender.items())]
    
    # Combine locations and cities - prefer cities if they exist, otherwise use location
    # This prevents duplicates like "Czech Republic" and "Prague, Czech Republic"
    combined_locations = defaultdict(int)
    for demo in demographics_list:
        if demo.city:
            # Use city name as location identifier
            combined_locations[demo.city] += demo.count
        elif demo.location:
            # Only use country if no city is specified
            # Skip if location contains a city name (e.g., "Prague, Czech Republic")
            if ',' not in demo.location:
                combined_locations[demo.location] += demo.count
    
    location_list = [{'location': loc, 'count': count} for loc, count in sorted(combined_locations.items(), key=lambda x: x[1], reverse=True)[:20]]
    city_list = [{'city': city, 'count': count} for city, count in sorted(by_city.items(), key=lambda x: x[1], reverse=True)[:20]]
    
    return {
        'by_age': age_list,
        'by_gender': gender_list,
        'by_location': location_list,
        'by_city': city_list,
        'total': total
    }


def calculate_engagement_metrics(metrics_list):
    """Calculate engagement rates"""
    if not metrics_list:
        return {
            'average_engagement_rate': 0,
            'average_reach': 0,
            'total_interactions': 0,
            'total_views': 0,
            'total_visits': 0
        }
    
    total_interactions = sum(m.interactions for m in metrics_list)
    total_views = sum(m.views for m in metrics_list)
    total_reach = sum(m.reach for m in metrics_list)
    total_visits = sum(getattr(m, 'visits', 0) for m in metrics_list)  # Handle visits if column exists
    
    engagement_rate = (total_interactions / total_reach * 100) if total_reach > 0 else 0
    average_reach = total_reach / len(metrics_list) if metrics_list else 0
    
    monthly_engagement = defaultdict(lambda: {'interactions': 0, 'views': 0, 'reach': 0, 'count': 0})
    
    for metric in metrics_list:
        month_key = metric.date.strftime('%Y-%m')
        monthly_engagement[month_key]['interactions'] += metric.interactions
        monthly_engagement[month_key]['views'] += metric.views
        monthly_engagement[month_key]['reach'] += metric.reach
        monthly_engagement[month_key]['count'] += 1
    
    monthly_list = []
    for month, data in sorted(monthly_engagement.items()):
        avg_reach = data['reach'] / data['count'] if data['count'] > 0 else 0
        engagement_rate_month = (data['interactions'] / data['reach'] * 100) if data['reach'] > 0 else 0
        monthly_list.append({
            'month': month,
            'interactions': data['interactions'],
            'views': data['views'],
            'reach': data['reach'],
            'average_reach': round(avg_reach, 2),
            'engagement_rate': round(engagement_rate_month, 2)
        })
    
    total_visits = sum(getattr(m, 'visits', 0) for m in metrics_list)  # Handle visits if column exists
    
    return {
        'average_engagement_rate': round(engagement_rate, 2),
        'average_reach': round(average_reach, 2),
        'total_interactions': total_interactions,
        'total_views': total_views,
        'total_reach': total_reach,
        'total_visits': total_visits,
        'monthly_engagement': monthly_list
    }
