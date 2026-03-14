"""
Meta Business CSV Analytics Dashboard
Main Flask application for analyzing Meta Business Suite data
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory, session, redirect, url_for, flash
import os
from datetime import datetime
import io
import csv
from functools import wraps
try:
    from werkzeug.security import generate_password_hash, check_password_hash
except ImportError:
    # Fallback for older Python versions
    def generate_password_hash(password):
        return password  # Simple fallback
    def check_password_hash(pwhash, password):
        return pwhash == password

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
base_dir = os.path.dirname(os.path.abspath(__file__))
# Na Vercelu uploady do /tmp; lokálně do uploads
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads' if os.environ.get('VERCEL') else 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['PASSWORD'] = os.environ.get('APP_PASSWORD', 'pneuboss2025')  # Default password

if os.environ.get('VERCEL'):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
else:
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('data', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

from models import db, FollowerSnapshot, Demographics, EngagementMetric
from csv_parser import parse_csv_file
from analytics import calculate_follower_growth, aggregate_demographics, calculate_engagement_metrics

# Database: Vercel = POSTGRES_URL/DATABASE_URL; lokálně SQLite
database_url = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    db_path = os.path.join(base_dir, 'data', 'database.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

try:
    with app.app_context():
        db.create_all()
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"Database: {'Postgres' if 'postgresql' in uri else 'SQLite'}")
except Exception as e:
    print(f"Error initializing database: {e}")
    raise


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == app.config['PASSWORD']:
            session['logged_in'] = True
            flash('Přihlášení úspěšné!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nesprávné heslo!', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('logged_in', None)
    flash('Odhlášení úspěšné!', 'success')
    return redirect(url_for('login'))


if not os.environ.get('VERCEL'):
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(base_dir, 'static', 'css'), filename)
    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(os.path.join(base_dir, 'static', 'js'), filename)


@app.route('/test')
def test():
    """Test route to check if Flask is working"""
    return "Flask is working! Server is running correctly."


@app.route('/simple')
def simple():
    """Simple test page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <style>
            body { font-family: Arial; padding: 50px; background: #f0f0f0; }
            .box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #667eea; }
            a { color: #667eea; text-decoration: none; font-weight: bold; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="box">
            <h1>✅ Flask Server Funguje!</h1>
            <p>Server běží správně na <strong>http://127.0.0.1:5000</strong></p>
            <p><a href="/">Přejít na Dashboard</a></p>
            <p><a href="/upload">Přejít na Upload</a></p>
            <hr>
            <h2>Test API:</h2>
            <p><a href="/api/followers">/api/followers</a> - Test followers API</p>
            <p><a href="/api/demographics">/api/demographics</a> - Test demographics API</p>
            <p><a href="/api/engagement">/api/engagement</a> - Test engagement API</p>
        </div>
    </body>
    </html>
    """


@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    try:
        template_path = os.path.join(app.template_folder, 'index.html')
        if not os.path.exists(template_path):
            return f"Template not found at: {template_path}<br>Current dir: {os.getcwd()}<br>Templates: {os.listdir('templates') if os.path.exists('templates') else 'NOT FOUND'}", 500
        return render_template('index.html')
    except Exception as e:
        import traceback
        return f"Error loading template: {str(e)}<br><pre>{traceback.format_exc()}</pre>", 500


@app.route('/upload')
@login_required
def upload_page():
    """CSV upload page"""
    try:
        return render_template('upload.html')
    except Exception as e:
        return f"Error loading upload template: {str(e)}", 500


@app.errorhandler(403)
def forbidden(e):
    return "Access forbidden. Please check server logs.", 403


@app.errorhandler(404)
def not_found(e):
    return "Page not found.", 404


@app.errorhandler(500)
def internal_error(e):
    return f"Internal server error: {str(e)}", 500


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_csv():
    """Handle CSV file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400
    
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            result = parse_csv_file(filepath, db)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Successfully imported {result["imported"]} records',
            'type': result['type'],
            'details': result.get('details', {})
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/followers')
@login_required
def get_followers():
    """Get follower development data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform', 'all')
    
    query = FollowerSnapshot.query
    
    if start_date:
        query = query.filter(FollowerSnapshot.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(FollowerSnapshot.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if platform != 'all':
        query = query.filter(FollowerSnapshot.platform == platform)
    
    snapshots = query.order_by(FollowerSnapshot.date).all()
    
    # If platform is 'all', we need to aggregate by date (sum follower counts from both platforms)
    if platform == 'all':
        from collections import defaultdict
        by_date = defaultdict(lambda: {'instagram': 0, 'facebook': 0, 'total': 0, 'new': 0, 'lost': 0})
        
        for s in snapshots:
            by_date[s.date][s.platform] = s.follower_count
            by_date[s.date]['new'] += s.new_followers
            by_date[s.date]['lost'] += s.lost_followers
        
        # Create combined snapshots
        combined_snapshots = []
        for date in sorted(by_date.keys()):
            data = by_date[date]
            total = data['instagram'] + data['facebook']
            # Create a mock snapshot object for growth calculation
            class MockSnapshot:
                def __init__(self, date, count):
                    self.date = date
                    self.follower_count = count
            combined_snapshots.append(MockSnapshot(date, total))
        
        snapshots_for_growth = combined_snapshots
    else:
        snapshots_for_growth = snapshots
    
    data = [{
        'date': s.date.isoformat(),
        'follower_count': s.follower_count,
        'new_followers': s.new_followers,
        'lost_followers': s.lost_followers,
        'platform': s.platform
    } for s in snapshots]
    
    growth_data = calculate_follower_growth(snapshots_for_growth)
    
    return jsonify({
        'snapshots': data,
        'growth': growth_data
    })


@app.route('/api/demographics')
@login_required
def get_demographics():
    """Get demographics data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform', 'all')
    
    query = Demographics.query
    
    if start_date:
        query = query.filter(Demographics.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Demographics.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if platform != 'all':
        query = query.filter(Demographics.platform == platform)
    
    demographics = query.all()
    aggregated = aggregate_demographics(demographics)
    
    return jsonify(aggregated)


@app.route('/api/engagement')
@login_required
def get_engagement():
    """Get engagement metrics"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    platform = request.args.get('platform', 'all')
    
    query = EngagementMetric.query
    
    if start_date:
        query = query.filter(EngagementMetric.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(EngagementMetric.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if platform != 'all':
        query = query.filter(EngagementMetric.platform == platform)
    
    metrics = query.order_by(EngagementMetric.date).all()
    
    data = [{
        'date': m.date.isoformat(),
        'views': m.views,
        'interactions': m.interactions,
        'reach': m.reach,
        'clicks': m.clicks,
        'visits': m.visits if hasattr(m, 'visits') else 0,
        'platform': m.platform
    } for m in metrics]
    
    engagement_rates = calculate_engagement_metrics(metrics)
    
    return jsonify({
        'metrics': data,
        'rates': engagement_rates
    })


@app.route('/api/export/csv')
@login_required
def export_csv():
    """Export data to CSV"""
    export_type = request.args.get('type', 'followers')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if export_type == 'followers':
        query = FollowerSnapshot.query
        if start_date:
            query = query.filter(FollowerSnapshot.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(FollowerSnapshot.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        snapshots = query.order_by(FollowerSnapshot.date).all()
        writer.writerow(['Date', 'Platform', 'Follower Count', 'New Followers', 'Lost Followers'])
        for s in snapshots:
            writer.writerow([s.date, s.platform, s.follower_count, s.new_followers, s.lost_followers])
    
    elif export_type == 'demographics':
        query = Demographics.query
        if start_date:
            query = query.filter(Demographics.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Demographics.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        demographics = query.all()
        writer.writerow(['Date', 'Age Range', 'Gender', 'Location', 'City', 'Count'])
        for d in demographics:
            writer.writerow([d.date, d.age_range, d.gender, d.location, d.city, d.count])
    
    elif export_type == 'engagement':
        query = EngagementMetric.query
        if start_date:
            query = query.filter(EngagementMetric.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(EngagementMetric.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        metrics = query.order_by(EngagementMetric.date).all()
        writer.writerow(['Date', 'Platform', 'Views', 'Interactions', 'Reach', 'Clicks'])
        for m in metrics:
            writer.writerow([m.date, m.platform, m.views, m.interactions, m.reach, m.clicks])
    
    output.seek(0)
    filename = f"{export_type}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


if __name__ == '__main__':
    print("Starting Meta Business Analytics Dashboard...")
    print("Server will be available at http://127.0.0.1:5000")
    print("Press CTRL+C to stop the server")
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule}")
    print()
    try:
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Trying with different host...")
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
