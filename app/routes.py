from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Artisan, Message
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
from flask import current_app
from app import db
from flask_wtf import FlaskForm
from wtforms import TextAreaField, StringField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import Review
import logging
import re
import sqlalchemy as sa
from email_validator import validate_email, EmailNotValidError
from app.forms import ContactForm, UploadForm, MessageForm
from collections import defaultdict

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
    location = request.args.get('location', '').strip()
    if not location:
        return jsonify([]), 400
    try:
        artisans = Artisan.query.join(User).filter(Artisan.location.ilike(f'%{location}%')).all()
        result = [{
            'id': a.id,
            'name': a.user.name,
            'skills': a.skills,
            'location': a.location,
            'profile_pic': a.user.profile_pic or 'https://via.placeholder.com/150'
        } for a in artisans]
        return jsonify(result)
    except Exception as e:
        logger.error(f"Search error for location {location}: {str(e)}")
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

@main.route('/contact_redirect/<int:artisan_id>')
def contact_redirect(artisan_id):
    return render_template('contact_redirect.html', artisan_id=artisan_id)

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
    # Get all messages where the user is sender or recipient
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.recipient_id == current_user.id)
    ).order_by(Message.timestamp.asc()).all()

    # Group messages by the other participant
    chat_histories = defaultdict(list)
    for msg in messages:
        other_id = msg.recipient_id if msg.sender_id == current_user.id else msg.sender_id
        chat_histories[other_id].append(msg)

    participants = {user.id: user for user in User.query.filter(User.id.in_(chat_histories.keys())).all()}

    return render_template(
        'user_dashboard.html',
        messages=messages,
        chat_histories=chat_histories,
        participants=participants
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
    form = ReplyForm()
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
    if recipient_id == 0:
        recipient_id = int(request.form.get('recipient_id', 0))
    content = request.form.get('content')
    if content and recipient_id and recipient_id != current_user.id:
        message = Message(sender_id=current_user.id, recipient_id=recipient_id, content=content)
        db.session.add(message)
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True})
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': False, 'message': 'Invalid message.'})
    return redirect(url_for('main.messages', partner_id=recipient_id))

@main.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')