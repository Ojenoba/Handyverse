from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Artisan, Message, Favorite, JobPost, JobApplication
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from flask import current_app
from app import db
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField, PasswordField, FloatField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional
from app.models import Review
from email_validator import validate_email, EmailNotValidError
from app.forms import ContactForm, UploadForm, MessageForm, JobPostForm
from collections import defaultdict
import logging
import re
import os
import math
import sqlalchemy as sa

main = Blueprint('main', __name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper function to validate email format (basic check)
def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

# Helper function to handle database session commits with rollback
def safe_commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

# Helper function for file upload validation
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/search', methods=['GET'])
def search():
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    location = request.args.get('location', '').strip()
    try:
        if lat is not None and lng is not None:
            # Location-based search using Haversine formula (within 30km radius)
            def haversine(lat1, lon1, lat2, lon2):
                R = 6371  # Earth radius in km
                phi1, phi2 = math.radians(lat1), math.radians(lat2)
                dphi = math.radians(lat2 - lat1)
                dlambda = math.radians(lon2 - lon1)
                a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
                return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            artisans = Artisan.query.join(User).all()
            result = []
            for a in artisans:
                if hasattr(a, 'latitude') and hasattr(a, 'longitude') and a.latitude and a.longitude:
                    dist = haversine(lat, lng, a.latitude, a.longitude)
                    if dist <= 30:  # 30km radius
                        result.append({
                            'id': a.id,
                            'name': a.user.name,
                            'skills': a.skills,
                            'location': a.location,
                            'profile_pic': a.user.profile_pic or 'https://via.placeholder.com/150',
                            'distance_km': round(dist, 2)
                        })
            # Sort by distance
            result.sort(key=lambda x: x['distance_km'])
            return jsonify(result)
        elif location:
            artisans = Artisan.query.join(User).filter(Artisan.location.ilike(f'%{location}%')).all()
            result = [
                {
                    'id': a.id,
                    'name': a.user.name,
                    'skills': a.skills,
                    'location': a.location,
                    'profile_pic': a.user.profile_pic or 'https://via.placeholder.com/150'
                } for a in artisans
            ]
            return jsonify(result)
        else:
            return jsonify([]), 400
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/check_login', methods=['GET'])
def check_login():
    try:
        # Safely handle current_user
        user_state = {
            'is_authenticated': False,
            'id': None
        }
        if hasattr(current_user, 'is_authenticated'):
            user_state['is_authenticated'] = bool(current_user.is_authenticated)  # Explicitly convert to bool
        if hasattr(current_user, 'id'):
            user_state['id'] = current_user.id

        # Safely handle session
        session_info = {}
        for key, value in session.items():
            session_info[key] = str(value) if not isinstance(value, (int, str, float, bool, type(None))) else value

        logger.debug(f"Checking login, user_state: {user_state}, session_info: {dict(session_info)}")  # Convert to dict for safety
        response = {'is_authenticated': user_state['is_authenticated']}
        logger.debug(f"Check login response: {response}")
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in check_login: {str(e)}", exc_info=True)
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

@main.route('/contact/<int:artisan_id>', methods=['GET', 'POST'])
@login_required
def contact_artisan(artisan_id):
    artisan = Artisan.query.get_or_404(artisan_id)
    form = ContactForm()
    if form.validate_on_submit():
        try:
            content = form.message.data
            message = Message(sender_id=current_user.id, recipient_id=artisan.user_id, content=content)
            db.session.add(message)
            safe_commit()
            # Notify artisan of new message
            create_notification(
                user_id=artisan.user_id,
                notif_type='message',
                message=f'New message from {current_user.name}',
                url=url_for('main.messages', _external=True)
            )
            flash('Message sent successfully!', 'success')
            return redirect(url_for('main.user_dashboard'))
        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'error')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    logger.debug(f"Contact artisan for ID {artisan_id}, user: {current_user}")
    return render_template('contact_artisan.html', artisan=artisan, form=form)

@main.route('/signup')
def signup():
    return render_template('register.html')

@main.route('/signup_user')
def signup_user():
    return render_template('signup_user.html')

@main.route('/signup_artisan')
def signup_artisan():
    return render_template('signup_artisan.html')

@main.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        logger.debug(f"Received registration data: {data}")
        if not data:
            return jsonify({'success': False, 'message': 'No JSON data provided'}), 400

        account_type = data.get('accountType')
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        phone_number = data.get('phone_number')
        location = data.get('location')
        trade = data.get('trade') if account_type == 'artisan' else None
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Check required fields
        if not all([account_type, name, email, password, phone_number, location]):
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400
        if account_type == 'artisan' and not trade:
            return jsonify({'success': False, 'message': 'Trade is required for artisans.'}), 400
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Invalid email format.'}), 400
        if not is_strong_password(password):
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters long and include uppercase, lowercase, and numbers.'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email already registered.'}), 400

        user = User(
            email=email,
            name=name,
            location=location,
            phone_number=phone_number,
            is_artisan=(account_type == 'artisan')
        )
        user.set_password(password)
        db.session.add(user)
        safe_commit()

        if account_type == 'artisan':
            artisan = Artisan(user_id=user.id, skills=trade, location=location)
            if latitude and longitude:
                artisan.latitude = float(latitude)
                artisan.longitude = float(longitude)
            db.session.add(artisan)
            safe_commit()

        login_user(user)
        message = 'Registered as artisan successfully' if account_type == 'artisan' else 'Registered as user successfully'
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@main.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        if request.is_json:
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'message': 'No JSON data provided'}), 400
                email = data.get('email')
                password = data.get('password')
                logger.debug(f"Login attempt for email: {email}, password provided: {password is not None}")
                if not all([email, password]) or not is_valid_email(email):
                    return jsonify({'message': 'Invalid email or password'}), 401
                user = User.query.filter_by(email=email).first()
                if user and user.check_password(password):
                    login_user(user)
                    logger.debug(f"Login successful, user: {user}, session: {session}")
                    redirect_url = '/user_dashboard' if not user.is_artisan else '/artisan_dashboard'
                    return jsonify({'message': 'Login successful', 'redirect_url': redirect_url})
                return jsonify({'message': 'Invalid email or password'}), 401
            except Exception as e:
                logger.error(f"Login error: {str(e)}", exc_info=True)
                return jsonify({'message': f'Login error: {str(e)}'}), 500
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            if not all([email, password]) or not is_valid_email(email):
                flash('Invalid email or password', 'error')
                return render_template('login.html')
            user = User.query.filter_by(email=email).first()
            if user:
                if user.check_password(password):
                    login_user(user)
                    logger.debug(f"Login successful, user: {user}, session: {session}")
                    return redirect(url_for('main.user_dashboard' if not user.is_artisan else 'main.artisan_dashboard'))
                else:
                    flash(
                        'Incorrect password. <a href="/forgot_password">Forgot password?</a>',
                        'error'
                    )
                    return render_template('login.html')
            else:
                flash(
                    'No account found with that email. <a href="/signup">Sign up for a new account</a>',
                    'error'
                )
                return render_template('login.html')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login_page'))

@main.route('/logout_all')
def logout_all():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/user_dashboard')
@login_required
def user_dashboard():
    if current_user.is_artisan:
        return redirect(url_for('main.artisan_dashboard'))
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    chat_histories = defaultdict(list)
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        chat_histories[other_id].append(msg)
    participants = {user.id: user for user in User.query.filter(User.id.in_(chat_histories.keys())).all()}
    form = MessageForm()  # <-- Add this line
    return render_template(
        'user_dashboard.html',
        messages=messages,
        chat_histories=chat_histories,
        participants=participants,
        form=form  # <-- And this
    )

@main.route('/artisan_dashboard')
@login_required
def artisan_dashboard():
    if not current_user.is_artisan:
        return redirect(url_for('main.user_dashboard'))
    artisan = Artisan.query.filter_by(user_id=current_user.id).first()
    if not artisan:
        flash('No artisan profile found. Please contact support.', 'error')
        return redirect(url_for('main.user_dashboard'))
    # Get all messages where the artisan is sender or recipient
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()

    # Group messages by the other participant
    chat_histories = defaultdict(list)
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        chat_histories[other_id].append(msg)

    participants = {user.id: user for user in User.query.filter(User.id.in_(chat_histories.keys())).all()}
    form = MessageForm()  # <-- FIXED HERE
    return render_template(
        'artisan_dashboard.html',
        artisan=artisan,
        messages=messages,
        chat_histories=chat_histories,
        participants=participants,
        form=form
    )

@main.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
def reply_message(message_id):
    original_message = Message.query.get_or_404(message_id)
    content = request.form.get('content')
    if not content:
        flash('Reply content is required.', 'error')
        # Redirect to the appropriate dashboard/messages page
        if current_user.is_artisan:
            return redirect(url_for('main.artisan_dashboard'))
        else:
            return redirect(url_for('main.messages'))
    try:
        reply = Message(
            sender_id=current_user.id,
            recipient_id=original_message.sender_id,
            content=content,
            parent_id=original_message.id  # For threaded replies
        )
        db.session.add(reply)
        safe_commit()
        flash('Reply sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending reply: {str(e)}', 'error')
    # Redirect to the appropriate dashboard/messages page
    if current_user.is_artisan:
        return redirect(url_for('main.artisan_dashboard'))
    else:
        return redirect(url_for('main.messages'))

@main.route('/upload_profile_pic', methods=['GET', 'POST'])
@login_required
def upload_profile_pic():
    form = UploadForm()
    if request.method == 'POST' and form.validate_on_submit():
        try:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file', 'error')
                return redirect(url_for('main.upload_profile_pic'))
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                base, ext = os.path.splitext(filename)
                counter = 1
                new_filename = filename
                while os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)):
                    new_filename = f"{base}_{counter}{ext}"
                    counter += 1
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename))
                current_user.profile_pic = f"/{current_app.config['UPLOAD_FOLDER']}/{new_filename}"
                safe_commit()
                flash('Profile picture uploaded successfully!', 'success')
                return redirect(url_for('main.user_dashboard' if not current_user.is_artisan else 'main.artisan_dashboard'))
        except Exception as e:
            flash(f'Error uploading profile picture: {str(e)}', 'error')
            return redirect(url_for('main.upload_profile_pic'))
    return render_template('upload_profile_pic.html', form=form)

@main.route('/api/reviews', methods=['GET'])
def get_reviews():
    try:
        reviews = Review.query.all()
        return jsonify([{
            'customer': r.customer.name if r.customer else 'Unknown',
            'comment': r.comment,
            'rating': r.rating
        } for r in reviews])
    except sa.exc.OperationalError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Database not initialized. Please run migrations.'}), 500
    except Exception as e:
        logger.error(f"Error fetching reviews: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main.route('/favicon.ico')
def favicon():
    return '', 204

@main.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    form = MessageForm()
    all_users = User.query.filter(User.id != current_user.id).all()
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    chat_partner_ids = set()
    for msg in messages:
        chat_partner_ids.add(msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id)
    chat_partners = User.query.filter(User.id.in_(chat_partner_ids)).all()
    partner_id = request.args.get('partner_id', type=int)
    chat_history = []
    partner = None
    if partner_id:
        partner = User.query.get(partner_id)
        chat_history = [
            msg for msg in messages
            if (msg.sender_id == partner_id and msg.recipient_id == current_user.id) or
               (msg.sender_id == current_user.id and msg.recipient_id == partner_id)
        ]
    # AJAX partial for polling
    if request.args.get('ajax'):
        return render_template('partials/_message_list.html', chat_history=chat_history, partner=partner)
    return render_template(
        'messages.html',
        chat_partners=chat_partners,
        partner=partner,
        chat_history=chat_history,
        form=form,
        all_users=all_users
    )

@main.route('/artisan_messages')
@login_required
def artisan_messages():
    if not current_user.is_artisan:
        return redirect(url_for('main.user_dashboard'))
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()
    chat_histories = defaultdict(list)
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        chat_histories[other_id].append(msg)
    participants = {user.id: user for user in User.query.filter(User.id.in_(chat_histories.keys())).all()}
    form = MessageForm()  # <-- Use MessageForm, not ReplyForm
    return render_template(
        'artisan_messages.html',
        chat_histories=chat_histories,
        participants=participants,
        form=form
    )

@main.route('/send_message/<int:recipient_id>', methods=['POST'])
@login_required
def send_message(recipient_id):
    form = MessageForm()
    if form.validate_on_submit():
        try:
            content = form.content.data
            message = Message(sender_id=current_user.id, recipient_id=recipient_id, content=content)
            db.session.add(message)
            safe_commit()
            # Notify recipient of new message
            create_notification(
                user_id=recipient_id,
                notif_type='message',
                message=f'New message from {current_user.name}',
                url=url_for('main.messages', _external=True)
            )
            flash('Message sent!', 'success')
        except Exception as e:
            flash(f'Error sending message: {str(e)}', 'error')
    return redirect(url_for('main.messages', partner_id=recipient_id))

@main.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    password = PasswordField('New Password', validators=[Optional(), Length(min=8)])
    submit = StringField('Update')

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    upload_form = UploadForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        current_user.location = form.location.data
        if form.password.data:
            if is_strong_password(form.password.data):
                current_user.set_password(form.password.data)
            else:
                flash('Password must be at least 8 characters and include uppercase, lowercase, and numbers.', 'error')
                return render_template('profile.html', form=form, upload_form=upload_form)
        try:
            safe_commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            flash(f'Error updating profile: {str(e)}', 'error')
    return render_template('profile.html', form=form, upload_form=upload_form)

@main.route('/artisan_profile', methods=['GET', 'POST'])
@login_required
def artisan_profile():
    if not current_user.is_artisan:
        flash('Only artisans can access this page.', 'error')
        return redirect(url_for('main.user_dashboard'))
    from app.models import Artisan
    artisan = Artisan.query.filter_by(user_id=current_user.id).first()
    form = ProfileForm(obj=current_user)
    upload_form = UploadForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            current_user.name = form.name.data
            current_user.email = form.email.data
            current_user.phone_number = form.phone_number.data
            current_user.location = form.location.data
            if form.password.data:
                if is_strong_password(form.password.data):
                    current_user.set_password(form.password.data)
                else:
                    flash('Password must be at least 8 characters and include uppercase, lowercase, and numbers.', 'error')
                    return render_template('artisan_profile.html', form=form, upload_form=upload_form, artisan=artisan)
            # Update artisan skills/trade
            if artisan:
                artisan.skills = request.form.get('skills', artisan.skills)
                artisan.location = form.location.data
                # Save latitude/longitude if provided
                lat = request.form.get('latitude')
                lng = request.form.get('longitude')
                if lat and lng:
                    artisan.latitude = float(lat)
                    artisan.longitude = float(lng)
            try:
                safe_commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('main.artisan_profile'))
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'error')
    return render_template('artisan_profile.html', form=form, upload_form=upload_form, artisan=artisan)

@main.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    notifications = current_user.notifications.order_by(db.desc('timestamp')).limit(20).all()
    return jsonify([
        {
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'timestamp': n.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        for n in notifications
    ])

@main.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    from app.models import Notification
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first_or_404()
    notif.is_read = True
    safe_commit()
    return jsonify({'success': True})

def create_notification(user_id, notif_type, message, url=None):
    from app.models import Notification
    notif = Notification(user_id=user_id, type=notif_type, message=message, url=url)
    db.session.add(notif)
    safe_commit()

@main.route('/favorite/<int:artisan_id>', methods=['POST'])
@login_required
def add_favorite(artisan_id):
    if current_user.is_artisan:
        return jsonify({'success': False, 'message': 'Artisans cannot favorite.'})
    existing = Favorite.query.filter_by(user_id=current_user.id, artisan_id=artisan_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already favorited.'})
    fav = Favorite(user_id=current_user.id, artisan_id=artisan_id)
    db.session.add(fav)
    safe_commit()
    return jsonify({'success': True, 'message': 'Artisan favorited.'})

@main.route('/unfavorite/<int:artisan_id>', methods=['POST'])
@login_required
def remove_favorite(artisan_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, artisan_id=artisan_id).first()
    if not fav:
        return jsonify({'success': False, 'message': 'Not in favorites.'})
    db.session.delete(fav)
    safe_commit()
    return jsonify({'success': True, 'message': 'Artisan unfavorited.'})

@main.route('/favorites', methods=['GET'])
@login_required
def list_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    result = [
        {
            'artisan_id': fav.artisan_id,
            'name': fav.artisan.user.name,
            'skills': fav.artisan.skills,
            'location': fav.artisan.location,
            'profile_pic': fav.artisan.user.profile_pic or 'https://via.placeholder.com/150'
        }
        for fav in favorites
    ]
    return jsonify(result)

# --- JOB BOARD ROUTES ---

@main.route('/jobs')
def list_jobs():
    jobs = JobPost.query.order_by(JobPost.timestamp.desc()).all()
    return render_template('jobs.html', jobs=jobs)

@main.route('/jobs/new', methods=['GET', 'POST'])
@login_required
def create_job():
    form = JobPostForm()
    if form.validate_on_submit():
        # Sanitize budget input
        budget_raw = form.budget.data or ""
        try:
            budget_clean = float(budget_raw.replace(',', '').replace('₦', '').strip()) if budget_raw else None
        except ValueError:
            flash('Please enter a valid number for budget (e.g. 20000 or 20000.00)', 'danger')
            return render_template('create_job.html', form=form)
        job = JobPost(
            title=form.title.data,
            description=form.description.data,
            location=form.location.data,
            budget=budget_clean,
            user_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('main.list_jobs'))
    return render_template('create_job.html', form=form)

@main.route('/jobs/<int:job_id>', methods=['GET'])
@login_required
def job_detail(job_id):
    job = JobPost.query.get_or_404(job_id)
    applicants = None
    if current_user.id == job.user_id:
        applicants = JobApplication.query.filter_by(job_post_id=job.id).all()
    return render_template('job_detail.html', job=job, applicants=applicants)

@main.route('/jobs/<int:job_id>/apply', methods=['POST'])
@login_required
def apply_to_job(job_id):
    job = JobPost.query.get_or_404(job_id)
    # Prevent job owner from applying
    if job.user_id == current_user.id:
        flash('You cannot apply to your own job.', 'warning')
        return redirect(url_for('main.job_detail', job_id=job_id))
    # Prevent duplicate applications
    existing = JobApplication.query.filter_by(job_post_id=job_id, artisan_id=current_user.id).first()
    if existing:
        flash('You have already applied to this job.', 'info')
        return redirect(url_for('main.job_detail', job_id=job_id))
    application = JobApplication(
        job_post_id=job_id,
        artisan_id=current_user.id,
        message=request.form.get('message', '')
    )
    db.session.add(application)
    db.session.commit()
    # --- Notification for job owner ---
    create_notification(
        user_id=job.user_id,
        notif_type='job_application',
        message=f'New application from {current_user.name} for your job: {job.title}',
        url=url_for('main.job_detail', job_id=job.id)
    )
    flash('Application submitted!', 'success')
    return redirect(url_for('main.job_detail', job_id=job_id))