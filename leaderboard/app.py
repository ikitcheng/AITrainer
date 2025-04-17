import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from wtforms import PasswordField
import sys
from dotenv import load_dotenv
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
# Add parent directory to path to import workout_monitoring
sys.path.append(str(Path(__file__).parent.parent))
from src.workout_monitoring import process_video
from models import db, User, Workout

# Environment Variables
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
app.config['MONGODB_SETTINGS'] = {
    'db': os.getenv('MONGODB_DB', default=None),
    'host': os.getenv('MONGODB_URI', default=None)
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database
db.init_app(app)

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('You need to be an admin to access this page.')
        return redirect(url_for('login'))

# Initialize Flask-Admin
admin = Admin(app, name='AI Trainer Admin', template_mode='bootstrap4', index_view=MyAdminIndexView())

class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('You need to be an admin to access this page.')
        return redirect(url_for('login'))

    def create_form(self, obj=None):
        form = super(SecureModelView, self).create_form(obj)
        if hasattr(form, 'password'):
            form.password = PasswordField('Password')
        return form

    def update_form(self, obj=None):
        form = super(SecureModelView, self).update_form(obj)
        if hasattr(form, 'password'):
            form.password = PasswordField('Password')
        return form

    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)

class UserModelView(SecureModelView):
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_admin', 'created_at']
    can_create = True
    can_edit = True
    can_delete = True
    form_excluded_columns = ['password_hash', 'created_at']
    
    def init_search(self):
        return False  # Disable search functionality
    
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.password_hash = generate_password_hash(form.password.data)

# Add model views
admin.add_view(UserModelView(User))
admin.add_view(SecureModelView(Workout))  # Assuming Workout is also a MongoEngine model

@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=user_id).first()  # MongoEngine query

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}

@app.route('/')
def index():
    # Get public workouts for leaderboard
    public_workouts = Workout.objects(is_public=True).order_by('-max_power_per_kg').limit(10)
    return render_template('index.html', workouts=public_workouts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.objects(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        user.save()
        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.objects(username=username).first() 

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's workouts ordered by creation date
    user_workouts = Workout.objects(user=current_user.id).order_by('-created_at')

    # Calculate statistics
    total_reps = sum(workout.rep_count for workout in user_workouts)
    best_power = max((workout.max_power_per_kg for workout in user_workouts), default=0)

    # Get best power per exercise type
    exercise_powers = {}
    for workout in user_workouts:
        current_max = exercise_powers.get(workout.exercise_type, 0)
        exercise_powers[workout.exercise_type] = max(current_max, workout.max_power_per_kg)

    return render_template('dashboard.html',
                           workouts=user_workouts,
                           total_reps=total_reps,
                           best_power=best_power,
                           exercise_powers=exercise_powers)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file')
            return redirect(request.url)

        file = request.files['video']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Save video file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process video and get workout metrics
            body_mass = float(request.form['body_mass'])
            exercise_mass = float(request.form['exercise_mass'])
            exercise_type = request.form['exercise_type']
            is_public = 'is_public' in request.form

            try:
                # Process video using workout_monitoring.py
                metrics = process_video(
                    filepath,
                    body_mass=body_mass,
                    exercise_mass=exercise_mass,
                    exercise_type=exercise_type,
                )

                # Create workout entry
                workout = Workout(
                    user=current_user,  # Use current_user object
                    body_mass=body_mass,
                    exercise_mass=exercise_mass,
                    exercise_type=exercise_type,
                    rep_count=metrics['rep_count'],
                    avg_power=metrics['avg_power'],
                    max_power=metrics['max_power'],
                    avg_power_per_kg=metrics['avg_power_per_kg'],
                    max_power_per_kg=metrics['max_power_per_kg'],
                    video_path=metrics['processed_video_path'],
                    is_public=is_public,
                )
                workout.save()

                flash('Workout uploaded successfully')

                if os.path.exists(filepath):
                    os.remove(filepath)

                return redirect(url_for('dashboard'))

            except Exception as e:
                flash(f'Error processing video: {str(e)}')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

    return render_template('upload.html')

@app.route('/leaderboard')
def leaderboard():
    exercise_type = request.args.get('exercise_type', 'pullups')
    sort_by = request.args.get('sort_by', 'max_power_per_kg')

    # Get public workouts for specified exercise type
    workouts = Workout.objects(is_public=True, exercise_type=exercise_type).order_by(f'-{sort_by}')

    return render_template('leaderboard.html',
                           workouts=workouts,
                           exercise_type=exercise_type,
                           sort_by=sort_by)

@app.route('/toggle_visibility/<workout_id>', methods=['POST'])  # Include workout_id in the route
@login_required
def toggle_visibility(workout_id):
    workout = Workout.objects(id=workout_id).first()

    if not workout or workout.user != current_user:
        flash('You do not have permission to modify this workout')
        return redirect(url_for('dashboard'))

    workout.is_public = not workout.is_public
    workout.save()

    visibility_status = "public" if workout.is_public else "private"
    flash(f'Workout is now {visibility_status}')
    return redirect(url_for('dashboard'))

@app.route('/delete_workout/<workout_id>', methods=['POST'])  # Include workout_id in the route
@login_required
def delete_workout(workout_id):
    workout = Workout.objects(id=workout_id).first()

    if not workout or workout.user != current_user:
        flash('You do not have permission to delete this workout')
        return redirect(url_for('dashboard'))

    workout.delete()
    flash('Workout deleted successfully')
    return redirect(url_for('dashboard'))

@app.route('/download_video/<workout_id>', methods=['GET'])  # Include workout_id in the route
@login_required
def download_video(workout_id):
    workout = Workout.objects(id=workout_id).first()

    if not workout or (workout.user != current_user and not workout.is_public):
        flash('You do not have permission to download this video')
        return redirect(url_for('dashboard'))

    video_path = workout.video_path
    if not video_path or not os.path.exists(video_path):
        flash('Processed video not found')
        return redirect(url_for('dashboard'))

    return send_file(video_path, as_attachment=True)

# Create initial admin user
def create_admin_user():
    admin = User.objects(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),  # Change this in production
            is_admin=True
        )
        admin.save()

def cleanup_old_videos():
    """Delete processed videos older than 1 day and update database records."""
    cutoff_date = datetime.now() - timedelta(days=1)
    old_workouts = Workout.objects(created_at__lt=cutoff_date, video_path__ne=None)

    for workout in old_workouts:
        if os.path.exists(workout.video_path):
            try:
                os.remove(workout.video_path)
                workout.video_path = None
                workout.save()
                app.logger.info(f"Deleted old video for workout ID {workout.id}")
            except Exception as e:
                app.logger.error(f"Error deleting video for workout ID {workout.id}: {str(e)}")

# Initialize the scheduler (run once a day)
scheduler = BackgroundScheduler()
scheduler.add_job(func=cleanup_old_videos, trigger="interval", days=1)
scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        create_admin_user()

    # Use PORT environment variable if available
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

    # Ensure scheduler is shut down when the app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())
