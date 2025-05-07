import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.mongoengine import ModelView
from flask_mongoengine import MongoEngine
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from wtforms import PasswordField
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
import requests
import tempfile
from apscheduler.schedulers.background import BackgroundScheduler
from leaderboard.database.mongodb import db, User, Workout
from leaderboard.database.gcs_storage import GCSStorage
from leaderboard.auth.google_auth import GoogleAuth
from leaderboard.config.settings import settings

# Environment Variables
app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY
app.config['MONGODB_SETTINGS'] = {
    'db': settings.MONGODB_DB,
    'host': settings.MONGODB_URI
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

# Initialize Google Auth
oauth = GoogleAuth(app)

# Initialize GCS Storage
gcs = GCSStorage()

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

@app.route('/auth/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_authorize():
    token = oauth.google.authorize_access_token()
    user_info = token['userinfo']
    
    if not user_info:
        flash('Failed to verify token')
        return redirect(url_for('login'))

    # Get or create user
    user = User.get_or_create_from_google(user_info)
    login_user(user)
    
    flash(f"Successfully logged in with {user['email']}")
    return redirect(url_for('dashboard'))

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
            # Save video file temporarily
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{current_user.id}_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Upload to GCS
            try:
                video_url = gcs.upload_video(filepath, str(current_user.id))

                # Create initial workout entry with pending status
                body_mass = float(request.form['body_mass'])
                exercise_mass = float(request.form['exercise_mass'])
                exercise_type = request.form['exercise_type']
                is_public = 'is_public' in request.form
                
                workout = Workout(
                    user=current_user,
                    body_mass=body_mass,
                    exercise_mass=exercise_mass,
                    exercise_type=exercise_type,
                    # Will be updated after processing
                    rep_count=0,  
                    avg_power=0,  
                    max_power=0,  
                    avg_power_per_kg=0,  
                    max_power_per_kg=0,  
                    video_path=video_url,  # Original video URL
                    is_public=is_public,
                    status="pending"  # Add status field to Workout model
                )
                workout.save()
                
                print('Workout created in mongodb...')

                # Send request to inference service
                inference_request_data = {
                    "workout_id": str(workout.id),
                    "video_url": video_url,
                    "body_mass": body_mass,
                    "exercise_mass": exercise_mass,
                    "exercise_type": exercise_type
                }
                
                # Make async request to inference service
                response = requests.post(
                    f"{settings.INFERENCE_URL}/process_workout", 
                    json=inference_request_data
                )

                results = response.json()
                
                if response.status_code == 200:
                    flash('Workout uploaded and processing started')
                    # Update workout with processed metrics
                    workout.update(
                        status="complete",
                        error_message="",
                        rep_count=results['metrics']['rep_count'],
                        avg_power=results['metrics']['avg_power'],
                        max_power=results['metrics']['max_power'],
                        avg_power_per_kg=results['metrics']['avg_power_per_kg'],
                        max_power_per_kg=results['metrics']['max_power_per_kg'],
                        video_path=results['processed_video_url']
                    )
                else:
                    # If inference service fails, set status to error
                    error_msg = results.get('error', 'Unknown error')
                    workout.update(status="error", error_message=error_msg)
                    flash(f'Error starting workout processing: {error_msg}')
                
                # Clean up temporary file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                print(f'Error uploading workout: {str(e)}')
                flash(f'Error uploading workout: {str(e)}')
                # Clean up temporary file
                if os.path.exists(filepath):
                    os.remove(filepath)

                return redirect(url_for('upload'))

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

@app.route('/toggle_visibility/<workout_id>', methods=['POST'])  
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

@app.route('/delete_workout/<workout_id>', methods=['POST'])  
@login_required
def delete_workout(workout_id):
    workout = Workout.objects(id=workout_id).first()

    if not workout or workout.user != current_user:
        flash('You do not have permission to delete this workout')
        return redirect(url_for('dashboard'))

    # Delete video from GCS if exists
    if workout.video_path:
        try:
            gcs.delete_video(workout.video_path)
        except Exception as e:
            app.logger.error(f"Error deleting video from GCS: {e}")
    
    workout.delete()
    flash('Workout deleted successfully')
    return redirect(url_for('dashboard'))

@app.route('/download_video/<workout_id>', methods=['GET'])  
@login_required
def download_video(workout_id):
    workout = Workout.objects(id=workout_id).first()

    if not workout or (workout.user != current_user and not workout.is_public):
        flash('You do not have permission to download this video')
        return redirect(url_for('dashboard'))

    video_path = workout.video_path
    if not video_path:
        flash('Processed video not found')
        return redirect(url_for('dashboard'))

    try:
        # Create temporary file to download from GCS
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Download from GCS to temporary file
        gcs.download_video(video_path, temp_path)
        
        def generate_and_remove(file_path):
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    yield chunk
            try:
                os.remove(file_path)
            except Exception as e:
                app.logger.error(f"Error deleting temp file: {e}")
        
        return Response(generate_and_remove(temp_path),
                mimetype='video/mp4',
                headers={
                    'Content-Disposition': f'attachment; filename=workout_{workout_id}.mp4'
                })

    except Exception as e:
        flash(f'Error downloading video: {str(e)}')
        return redirect(url_for('dashboard'))

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

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

if __name__ == '__main__':
    with app.app_context():
        create_admin_user()

    # Use PORT environment variable if available
    app.run(host=settings.HOST, port=settings.PORT, debug=False, use_reloader=False)

    # Ensure scheduler is shut down when the app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())
