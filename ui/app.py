#!/usr/bin/env python3
"""
MaSIF-neosurf Web Interface
Flask application for running MaSIF-neosurf preprocessing on HPC via SLURM
Connects to HPC via SSH for remote job submission
"""

import os
import uuid
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import paramiko
from io import StringIO

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['UPLOAD_FOLDER'] = Path('uploads')
app.config['OUTPUT_FOLDER'] = Path('outputs')
app.config['USERS_FILE'] = Path('data/users.json')
app.config['RESET_TOKENS_FILE'] = Path('data/reset_tokens.json')
app.config['VERIFICATION_TOKENS_FILE'] = Path('data/verification_tokens.json')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# HPC SSH Configuration - Set via environment variables
HPC_CONFIG = {
    'hostname': os.environ.get('HPC_HOST', 'your-hpc-login-node.edu'),
    'username': os.environ.get('HPC_USER', 'your_username'),
    'key_filename': os.environ.get('HPC_SSH_KEY', str(Path.home() / '.ssh' / 'id_rsa')),
    'remote_work_dir': os.environ.get('HPC_WORK_DIR', '/home/your_username/masif_jobs'),
    'port': int(os.environ.get('HPC_PORT', '22')),
    'module_init': os.environ.get('HPC_MODULE_INIT', '/etc/profile.d/modules.sh'),
    'easybuild_prefix': os.environ.get('HPC_EASYBUILD_PREFIX', ''),
    'masif_repo': os.environ.get('HPC_MASIF_REPO', '')
}

# PyMOL VDI Configuration
PYMOL_CONFIG = {
    'enabled': os.environ.get('PYMOL_VDI_ENABLED', 'false').lower() == 'true',
    'url': os.environ.get('PYMOL_VDI_URL', 'http://localhost:6080'),
    'shared_volume': Path(os.environ.get('PYMOL_SHARED_VOLUME', '/pymol-shared')),
    'session_timeout': int(os.environ.get('PYMOL_SESSION_TIMEOUT', '3600'))  # 1 hour default
}

# Create PyMOL shared directory if enabled
if PYMOL_CONFIG['enabled']:
    PYMOL_CONFIG['shared_volume'].mkdir(parents=True, exist_ok=True)

# Create necessary directories
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)
app.config['OUTPUT_FOLDER'].mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {'pdb', 'sdf'}


# Docker Management Functions
def check_docker_available():
    """Check if Docker is available on the system"""
    import subprocess
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_pymol_container_status():
    """Check if PyMOL VDI container is running
    
    Returns:
        str: 'running', 'stopped', 'not_found', or 'error'
    """
    import subprocess
    try:
        # Check for container by name pattern
        result = subprocess.run(
            ['docker', 'ps', '-a', '--filter', 'name=pymol', '--format', '{{.Names}}\t{{.Status}}'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return 'error'
        
        output = result.stdout.strip()
        if not output:
            return 'not_found'
        
        # Parse output - look for running status
        for line in output.split('\n'):
            if 'pymol' in line.lower():
                if 'up' in line.lower():
                    return 'running'
                else:
                    return 'stopped'
        
        return 'not_found'
        
    except Exception as e:
        print(f"Error checking PyMOL container status: {e}")
        return 'error'


def start_pymol_container():
    """Start the PyMOL VDI container using docker-compose
    
    Returns:
        tuple: (success: bool, message: str)
    """
    import subprocess
    
    try:
        # Get the directory where app.py is located
        app_dir = Path(__file__).parent
        compose_file = app_dir / 'docker-compose.yml'
        
        if not compose_file.exists():
            return False, f"docker-compose.yml not found at {compose_file}"
        
        print("Starting PyMOL VDI container...")
        
        # Start the pymol-vdi service
        result = subprocess.run(
            ['docker-compose', 'up', '-d', 'pymol-vdi'],
            cwd=str(app_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✓ PyMOL VDI container started successfully")
            return True, "PyMOL VDI container started successfully"
        else:
            error_msg = result.stderr or result.stdout
            print(f"✗ Failed to start PyMOL VDI container: {error_msg}")
            return False, f"Failed to start container: {error_msg}"
            
    except subprocess.TimeoutExpired:
        return False, "Timeout while starting container"
    except FileNotFoundError:
        return False, "docker-compose command not found. Please install docker-compose."
    except Exception as e:
        return False, f"Error starting container: {str(e)}"


def ensure_pymol_container_running():
    """Ensure PyMOL VDI container is running, start it if needed
    
    This function is called during Flask app initialization
    """
    if not PYMOL_CONFIG['enabled']:
        print("PyMOL VDI is disabled in configuration")
        return
    
    print("\n" + "="*60)
    print("Checking PyMOL VDI Container Status")
    print("="*60)
    
    # Check if Docker is available
    if not check_docker_available():
        print("⚠️  Docker is not available on this system")
        print("   PyMOL visualization will not work")
        PYMOL_CONFIG['enabled'] = False
        return
    
    # Check container status
    status = check_pymol_container_status()
    print(f"Container status: {status}")
    
    if status == 'running':
        print("✓ PyMOL VDI container is already running")
        
    elif status == 'stopped':
        print("⚠️  PyMOL VDI container exists but is stopped")
        print("   Attempting to start...")
        success, message = start_pymol_container()
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            print("   PyMOL visualization may not work")
            
    elif status == 'not_found':
        print("⚠️  PyMOL VDI container not found")
        print("   Attempting to create and start...")
        success, message = start_pymol_container()
        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")
            print("   Please run: docker-compose up -d pymol-vdi")
            
    else:  # error
        print("✗ Error checking container status")
        print("   PyMOL visualization may not work")
    
    print("="*60 + "\n")


# Initialize PyMOL container on startup
ensure_pymol_container_running()


# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, email, name, is_admin=False):
        self.id = user_id
        self.email = email
        self.name = name
        self.is_admin = is_admin


def load_users():
    """Load users from JSON file"""
    if not app.config['USERS_FILE'].exists():
        return {}
    with open(app.config['USERS_FILE'], 'r') as f:
        return json.load(f)


def save_users(users):
    """Save users to JSON file"""
    with open(app.config['USERS_FILE'], 'w') as f:
        json.dump(users, f, indent=2)


def load_reset_tokens():
    """Load password reset tokens from JSON file"""
    if not app.config['RESET_TOKENS_FILE'].exists():
        return {}
    with open(app.config['RESET_TOKENS_FILE'], 'r') as f:
        return json.load(f)


def save_reset_tokens(tokens):
    """Save password reset tokens to JSON file"""
    with open(app.config['RESET_TOKENS_FILE'], 'w') as f:
        json.dump(tokens, f, indent=2)


def generate_reset_token():
    """Generate a secure random token"""
    return str(uuid.uuid4())


def load_verification_tokens():
    """Load email verification tokens from JSON file"""
    if not app.config['VERIFICATION_TOKENS_FILE'].exists():
        return {}
    with open(app.config['VERIFICATION_TOKENS_FILE'], 'r') as f:
        return json.load(f)


def save_verification_tokens(tokens):
    """Save email verification tokens to JSON file"""
    with open(app.config['VERIFICATION_TOKENS_FILE'], 'w') as f:
        json.dump(tokens, f, indent=2)


def send_email_via_hpc(to_email, subject, body):
    """Send email using HPC's mail system via SSH"""
    try:
        client = get_ssh_client()
        
        # Create email content
        email_content = f"""Subject: {subject}

{body}
"""
        
        # Use mail command on HPC to send email
        # Escape quotes and newlines for shell
        escaped_content = email_content.replace('"', '\\"').replace('$', '\\$')
        
        cmd = f'echo "{escaped_content}" | mail -s "{subject}" {to_email}'
        
        stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
        exit_code = stdout.channel.recv_exit_status()
        
        client.close()
        
        return exit_code == 0
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    users = load_users()
    if user_id in users:
        user_data = users[user_id]
        is_admin = user_data.get('is_admin', False)
        return User(user_id, user_data['email'], user_data['name'], is_admin)
    return None


def init_admin_user():
    """Initialize admin user if it doesn't exist"""
    users = load_users()
    
    # Check if admin exists
    admin_exists = any(u.get('email') == 'admin@crick.ac.uk' for u in users.values())
    
    if not admin_exists:
        admin_id = str(uuid.uuid4())
        # Default password is 'admin123' - should be changed after first login
        users[admin_id] = {
            'email': 'admin@crick.ac.uk',
            'name': 'Administrator',
            'password_hash': generate_password_hash('admin123'),
            'is_admin': True,
            'email_verified': True,  # Admin is pre-verified
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
        print("Admin user created: admin@crick.ac.uk / admin123")
        print("Please change the password after first login!")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_ssh_client():
    """Create and return an SSH client connected to HPC"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(
            hostname=HPC_CONFIG['hostname'],
            username=HPC_CONFIG['username'],
            key_filename=HPC_CONFIG['key_filename'],
            port=HPC_CONFIG['port'],
            timeout=10
        )
        return client
    except Exception as e:
        raise Exception(f"Failed to connect to HPC: {str(e)}")


def execute_remote_command(command, timeout=30):
    """Execute a command on the HPC via SSH"""
    client = None
    try:
        client = get_ssh_client()
        stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        return exit_code, output, error
    finally:
        if client:
            client.close()


def get_job_status(job_id):
    """Check SLURM job status via SSH"""
    try:
        # Try squeue first (for running/pending jobs)
        exit_code, output, error = execute_remote_command(
            f"squeue -j {job_id} -h -o '%T'",
            timeout=10
        )
        if exit_code == 0 and output.strip():
            return output.strip()
        
        # Job not in queue, check sacct (for completed jobs)
        exit_code, output, error = execute_remote_command(
            f"sacct -j {job_id} -n -o State",
            timeout=10
        )
        if exit_code == 0 and output.strip():
            return output.strip().split()[0]
        
        return 'UNKNOWN'
    except Exception as e:
        return f'ERROR: {str(e)}'


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not name or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if not email.endswith('@crick.ac.uk'):
            flash('Please use your @crick.ac.uk email address', 'error')
            return render_template('register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        users = load_users()
        if any(u['email'] == email for u in users.values()):
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user (unverified)
        user_id = str(uuid.uuid4())
        users[user_id] = {
            'email': email,
            'name': name,
            'password_hash': generate_password_hash(password),
            'email_verified': False,
            'created_at': datetime.now().isoformat()
        }
        save_users(users)
        
        # Generate verification token
        token = str(uuid.uuid4())
        tokens = load_verification_tokens()
        tokens[token] = {
            'user_id': user_id,
            'email': email,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now().timestamp() + 86400)  # 24 hours
        }
        save_verification_tokens(tokens)
        
        # Send verification email
        verification_link = url_for('verify_email', token=token, _external=True)
        email_subject = "Verify your MaSIF-neosurf account"
        email_body = f"""Hello {name},

Thank you for registering for the MaSIF-neosurf web application!

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

If you did not create this account, please ignore this email.

---
MaSIF-neosurf Web Interface
"""
        
        email_sent = send_email_via_hpc(email, email_subject, email_body)
        
        if email_sent:
            flash('Registration successful! Please check your email to verify your account.', 'success')
        else:
            flash('Registration successful! Here is your verification link:', 'success')
            flash(f'{verification_link}', 'info')
            flash('This link will expire in 24 hours.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        users = load_users()
        user_data = None
        user_id = None
        
        # Find user by email
        for uid, data in users.items():
            if data['email'] == email:
                user_data = data
                user_id = uid
                break
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            # Check if email is verified (admin accounts bypass this)
            if not user_data.get('email_verified', False) and not user_data.get('is_admin', False):
                flash('Please verify your email address before logging in. Check your inbox for the verification link.', 'error')
                return render_template('login.html')
            
            is_admin = user_data.get('is_admin', False)
            user = User(user_id, user_data['email'], user_data['name'], is_admin)
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('login.html')


@app.route('/verify-email/<token>')
def verify_email(token):
    """Verify email address with token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Verify token
    tokens = load_verification_tokens()
    token_data = tokens.get(token)
    
    if not token_data:
        flash('Invalid or expired verification link', 'error')
        return redirect(url_for('login'))
    
    # Check if token expired
    if datetime.now().timestamp() > token_data['expires_at']:
        # Clean up expired token
        del tokens[token]
        save_verification_tokens(tokens)
        flash('Verification link has expired. Please contact an administrator.', 'error')
        return redirect(url_for('login'))
    
    # Verify user's email
    users = load_users()
    user_id = token_data['user_id']
    
    if user_id in users:
        users[user_id]['email_verified'] = True
        users[user_id]['email_verified_at'] = datetime.now().isoformat()
        save_users(users)
        
        # Delete used token
        del tokens[token]
        save_verification_tokens(tokens)
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    else:
        flash('User not found', 'error')
        return redirect(url_for('login'))


@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Resend verification email"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email.endswith('@crick.ac.uk'):
            flash('Please use your @crick.ac.uk email address', 'error')
            return render_template('resend_verification.html')
        
        # Find user by email
        users = load_users()
        user_id = None
        user_data = None
        for uid, data in users.items():
            if data['email'] == email:
                user_id = uid
                user_data = data
                break
        
        if user_id and not user_data.get('email_verified', False):
            # Generate new verification token
            token = str(uuid.uuid4())
            tokens = load_verification_tokens()
            
            # Clean up old tokens for this user
            tokens = {t: data for t, data in tokens.items() if data.get('user_id') != user_id}
            
            tokens[token] = {
                'user_id': user_id,
                'email': email,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().timestamp() + 86400)  # 24 hours
            }
            save_verification_tokens(tokens)
            
            # Send verification email
            verification_link = url_for('verify_email', token=token, _external=True)
            email_subject = "Verify your MaSIF-neosurf account"
            email_body = f"""Hello {user_data['name']},

Here is your new verification link for the MaSIF-neosurf web application:

{verification_link}

This link will expire in 24 hours.

---
MaSIF-neosurf Web Interface
"""
            
            email_sent = send_email_via_hpc(email, email_subject, email_body)
            
            if email_sent:
                flash('Verification email has been resent. Please check your inbox.', 'success')
            else:
                flash('Email sending failed. Here is your verification link:', 'info')
                flash(f'{verification_link}', 'success')
        else:
            # Don't reveal if email exists or is already verified
            flash('If an unverified account exists with this email, a verification link has been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('resend_verification.html')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email.endswith('@crick.ac.uk'):
            flash('Please use your @crick.ac.uk email address', 'error')
            return render_template('forgot_password.html')
        
        # Find user by email
        users = load_users()
        user_id = None
        for uid, data in users.items():
            if data['email'] == email:
                user_id = uid
                break
        
        if user_id:
            # Generate reset token
            token = generate_reset_token()
            tokens = load_reset_tokens()
            
            # Clean up old tokens for this user
            tokens = {t: data for t, data in tokens.items() if data.get('user_id') != user_id}
            
            # Store new token (expires in 1 hour)
            tokens[token] = {
                'user_id': user_id,
                'email': email,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now().timestamp() + 3600)  # 1 hour
            }
            save_reset_tokens(tokens)
            
            # Generate reset link
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # Send email via HPC
            email_subject = "MaSIF-neosurf Password Reset"
            email_body = f"""Hello,

You have requested to reset your password for the MaSIF-neosurf web application.

Please click the link below to reset your password:

{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

---
MaSIF-neosurf Web Interface
"""
            
            email_sent = send_email_via_hpc(email, email_subject, email_body)
            
            if email_sent:
                flash('Password reset link has been sent to your email address.', 'success')
                flash('Please check your inbox and follow the instructions.', 'info')
            else:
                # Fallback: display link if email fails
                flash('Email sending failed. Here is your reset link:', 'info')
                flash(f'{reset_link}', 'success')
                flash('This link will expire in 1 hour.', 'info')
        else:
            # Don't reveal if email exists or not (security)
            flash('If an account exists with this email, a reset link has been generated.', 'info')
        
        return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Verify token
    tokens = load_reset_tokens()
    token_data = tokens.get(token)
    
    if not token_data:
        flash('Invalid or expired reset link', 'error')
        return redirect(url_for('login'))
    
    # Check if token expired
    if datetime.now().timestamp() > token_data['expires_at']:
        # Clean up expired token
        del tokens[token]
        save_reset_tokens(tokens)
        flash('Reset link has expired. Please request a new one.', 'error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return render_template('reset_password.html', token=token)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update password
        users = load_users()
        user_id = token_data['user_id']
        
        if user_id in users:
            users[user_id]['password_hash'] = generate_password_hash(new_password)
            users[user_id]['password_reset_at'] = datetime.now().isoformat()
            save_users(users)
            
            # Delete used token
            del tokens[token]
            save_reset_tokens(tokens)
            
            flash('Password reset successful! You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found', 'error')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('change_password.html')
        
        if len(new_password) < 8:
            flash('New password must be at least 8 characters', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('change_password.html')
        
        # Verify current password
        users = load_users()
        user_data = users.get(current_user.id)
        
        if not user_data or not check_password_hash(user_data['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
            return render_template('change_password.html')
        
        # Update password
        user_data['password_hash'] = generate_password_hash(new_password)
        user_data['password_changed_at'] = datetime.now().isoformat()
        users[current_user.id] = user_data
        save_users(users)
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/help')
@login_required
def help_page():
    """Help and documentation page"""
    return render_template('help.html')


@app.route('/examples')
@login_required
def examples():
    """Show example jobs page"""
    return render_template('examples.html')


@app.route('/submit', methods=['POST'])
@login_required
def submit_job():
    """Submit a preprocessing job to SLURM"""
    try:
        # Validate inputs
        if 'pdb_file' not in request.files:
            return jsonify({'error': 'No PDB file provided'}), 400
        
        pdb_file = request.files['pdb_file']
        if pdb_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(pdb_file.filename):
            return jsonify({'error': 'Invalid file type. Only PDB and SDF files allowed'}), 400
        
        # Get form data
        chain_id = request.form.get('chain_id', '').strip()
        ligand_id = request.form.get('ligand_id', '').strip()
        job_name = request.form.get('job_name', '').strip() or f'masif_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        
        if not chain_id:
            return jsonify({'error': 'Chain ID is required'}), 400
        
        # Create unique job directory (local)
        job_uuid = str(uuid.uuid4())[:8]
        local_job_dir = app.config['OUTPUT_FOLDER'] / f'{job_name}_{job_uuid}'
        local_job_dir.mkdir(exist_ok=True)
        
        # Save uploaded files locally first
        pdb_filename = secure_filename(pdb_file.filename)
        local_pdb_path = local_job_dir / pdb_filename
        pdb_file.save(local_pdb_path)
        
        local_sdf_path = None
        sdf_filename = None
        if 'sdf_file' in request.files and request.files['sdf_file'].filename:
            sdf_file = request.files['sdf_file']
            if allowed_file(sdf_file.filename):
                sdf_filename = secure_filename(sdf_file.filename)
                local_sdf_path = local_job_dir / sdf_filename
                sdf_file.save(local_sdf_path)
        
        # Copy preprocess_pdb.sh script
        import shutil
        repo_root = Path(__file__).parent.parent
        preprocess_script = repo_root / 'preprocess_pdb.sh'
        local_preprocess = local_job_dir / 'preprocess_pdb.sh'
        if preprocess_script.exists():
            shutil.copy(preprocess_script, local_preprocess)
        
        # Remote paths on HPC
        remote_job_dir = f"{HPC_CONFIG['remote_work_dir']}/{job_name}_{job_uuid}"
        remote_pdb_path = f"{remote_job_dir}/{pdb_filename}"
        remote_sdf_path = f"{remote_job_dir}/{sdf_filename}" if sdf_filename else None
        
        # Connect to HPC and transfer files
        client = None
        try:
            client = get_ssh_client()
            sftp = client.open_sftp()
            
            # Create remote job directory
            try:
                sftp.mkdir(HPC_CONFIG['remote_work_dir'])
            except:
                pass  # Directory might already exist
            sftp.mkdir(remote_job_dir)
            
            # Upload files
            sftp.put(str(local_pdb_path), remote_pdb_path)
            if local_sdf_path:
                sftp.put(str(local_sdf_path), remote_sdf_path)
            
            # Create a wrapper script that calls preprocess_pdb.sh from the HPC repo
            if HPC_CONFIG['masif_repo']:
                # Create a wrapper that changes to repo directory and runs the script
                wrapper_content = f"""#!/bin/bash
# Wrapper script to run preprocess_pdb.sh from the HPC repo
cd {HPC_CONFIG['masif_repo']}
./preprocess_pdb.sh "$@"
"""
                wrapper_path = f"{remote_job_dir}/preprocess_pdb.sh"
                sftp.putfo(StringIO(wrapper_content), wrapper_path)
                sftp.chmod(wrapper_path, 0o755)
            elif local_preprocess.exists():
                # Fallback: upload the script
                remote_preprocess = f"{remote_job_dir}/preprocess_pdb.sh"
                sftp.put(str(local_preprocess), remote_preprocess)
                sftp.chmod(remote_preprocess, 0o755)
            
            # Build command for remote execution
            cmd_parts = [
                'masif-preprocess',
                remote_pdb_path,
                chain_id
            ]
            
            if ligand_id and remote_sdf_path:
                cmd_parts.extend(['-l', ligand_id, '-s', remote_sdf_path])
            
            cmd_parts.extend(['-o', remote_job_dir])
            
            # Create SLURM script content
            easybuild_setup = ""
            if HPC_CONFIG['easybuild_prefix']:
                easybuild_setup = f"""
# EasyBuild configuration
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
"""
            
            slurm_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={remote_job_dir}/slurm_%j.out
#SBATCH --error={remote_job_dir}/slurm_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4

# Function to send email notification
send_notification() {{
    local status=$1
    local job_id=$2
    
    if [ "$status" = "COMPLETED" ]; then
        local subject="MaSIF-neosurf Job Completed - {job_name}"
        local message="Your MaSIF-neosurf preprocessing job has completed successfully!

Job Name: {job_name}
Job ID: $job_id
Status: Completed

You can view and download your results at:
{url_for('job_details', job_uuid=job_uuid, _external=True)}

---
MaSIF-neosurf Web Interface"
    else
        local subject="MaSIF-neosurf Job Failed - {job_name}"
        local message="Your MaSIF-neosurf preprocessing job has failed.

Job Name: {job_name}
Job ID: $job_id
Status: $status

If you need assistance, please contact the administrator at:
yewmun.yip@crick.ac.uk

Include your Job ID in your email for faster support.

---
MaSIF-neosurf Web Interface"
    fi
    
    echo "$message" | /usr/bin/mail -s "$subject" {current_user.email}
}}

# Trap to send notification on exit
trap 'EXIT_CODE=$?; if [ $EXIT_CODE -eq 0 ]; then send_notification "COMPLETED" $SLURM_JOB_ID; else send_notification "FAILED" $SLURM_JOB_ID; fi' EXIT

# Initialize module system
if [ -f {HPC_CONFIG['module_init']} ]; then
    source {HPC_CONFIG['module_init']}
fi

# Source user bashrc to get additional module paths
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
{easybuild_setup}
# Load Singularity module first (try, but don't fail if not found)
module load Singularity/3.11.3 2>/dev/null || true

# Load MaSIF-neosurf module
module --ignore_cache load MaSIF-neosurf/1.0 2>/dev/null || true

# Add Singularity and MaSIF-neosurf bin to PATH manually
export PATH=/flask/apps/eb/software/Singularity/3.11.3/bin:{HPC_CONFIG['easybuild_prefix']}/software/MaSIF-neosurf/1.0/bin:$PATH

# Set MASIF_REPO environment variable for the container
export MASIF_REPO={HPC_CONFIG['masif_repo']}

echo "Starting MaSIF-neosurf preprocessing"
echo "Job directory: {remote_job_dir}"
echo "MaSIF repo: $MASIF_REPO"
echo "Command: {' '.join(cmd_parts)}"
echo "Started at: $(date)"

# Change to job directory (needed for preprocess_pdb.sh)
cd {remote_job_dir}

{' '.join(cmd_parts)}

echo "Completed at: $(date)"
"""
            
            # Upload SLURM script
            remote_script_path = f"{remote_job_dir}/run_job.sh"
            sftp.putfo(StringIO(slurm_content), remote_script_path)
            sftp.chmod(remote_script_path, 0o755)
            
            sftp.close()
            
            # Submit job via SSH
            stdin, stdout, stderr = client.exec_command(f'sbatch {remote_script_path}', timeout=10)
            exit_code = stdout.channel.recv_exit_status()
            sbatch_output = stdout.read().decode('utf-8')
            sbatch_error = stderr.read().decode('utf-8')
            
            if exit_code != 0:
                return jsonify({'error': f'Failed to submit job: {sbatch_error}'}), 500
            
            # Extract job ID from sbatch output
            job_id = sbatch_output.strip().split()[-1]
            
        finally:
            if client:
                client.close()
        
        # Save job metadata locally
        metadata = {
            'job_id': job_id,
            'job_name': job_name,
            'job_uuid': job_uuid,
            'user_id': current_user.id,
            'user_email': current_user.email,
            'local_job_dir': str(local_job_dir),
            'remote_job_dir': remote_job_dir,
            'pdb_file': pdb_filename,
            'chain_id': chain_id,
            'ligand_id': ligand_id,
            'sdf_file': sdf_filename,
            'submitted_at': datetime.now().isoformat(),
            'command': ' '.join(cmd_parts)
        }
        
        (local_job_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'job_name': job_name,
            'job_uuid': job_uuid,
            'message': f'Job submitted successfully with ID: {job_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/job-status/<job_id>')
@login_required
def api_job_status(job_id):
    """Get status of a SLURM job via API"""
    status = get_job_status(job_id)
    return jsonify({'job_id': job_id, 'status': status})


@app.route('/jobs')
@login_required
def list_jobs():
    """List user's jobs (or all jobs for admin)"""
    jobs = []
    for job_dir in sorted(app.config['OUTPUT_FOLDER'].iterdir(), reverse=True):
        if job_dir.is_dir():
            metadata_file = job_dir / 'metadata.json'
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
                # Show all jobs for admin, only own jobs for regular users
                if current_user.is_admin or metadata.get('user_id') == current_user.id:
                    # Don't fetch status here - will be loaded via AJAX
                    metadata['status'] = 'LOADING'
                    jobs.append(metadata)
    
    return render_template('jobs.html', jobs=jobs, is_admin=current_user.is_admin)


@app.route('/job/<job_uuid>')
@login_required
def job_details(job_uuid):
    """View job details and outputs"""
    # Find job directory
    job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
    if not job_dirs:
        return 'Job not found', 404
    
    local_job_dir = job_dirs[0]
    metadata_file = local_job_dir / 'metadata.json'
    
    if not metadata_file.exists():
        return 'Job metadata not found', 404
    
    metadata = json.loads(metadata_file.read_text())
    
    # Check if job belongs to current user (or if user is admin)
    if not current_user.is_admin and metadata.get('user_id') != current_user.id:
        return 'Access denied', 403
    
    status = get_job_status(metadata['job_id'])
    
    # Fetch logs and output files from remote HPC
    logs = {}
    output_files = []
    file_fetch_error = None
    
    try:
        client = get_ssh_client()
        sftp = client.open_sftp()
        remote_job_dir = metadata['remote_job_dir']
        
        # Try to get all remote files (recursively)
        try:
            import stat
            
            def list_files_recursive(sftp, path, base_path):
                """Recursively list all files in a directory"""
                files = []
                try:
                    items = sftp.listdir_attr(path)
                    for item in items:
                        item_path = f"{path}/{item.filename}"
                        relative_path = item_path.replace(f"{base_path}/", "")
                        
                        if stat.S_ISDIR(item.st_mode):
                            # Recursively list subdirectory
                            files.extend(list_files_recursive(sftp, item_path, base_path))
                        elif stat.S_ISREG(item.st_mode):
                            # Add file with relative path
                            files.append((relative_path, item.st_size))
                except Exception as e:
                    print(f"Error listing {path}: {e}")
                return files
            
            # Get all files recursively
            all_files = list_files_recursive(sftp, remote_job_dir, remote_job_dir)
            
            for relative_path, file_size in all_files:
                # Collect log files (admin only)
                if relative_path.startswith('slurm_') and (relative_path.endswith('.out') or relative_path.endswith('.err')):
                    try:
                        remote_path = f"{remote_job_dir}/{relative_path}"
                        with sftp.file(remote_path, 'r') as f:
                            content = f.read().decode('utf-8')
                            logs[relative_path] = content if len(content) < 1024*1024 else 'Log file too large'
                    except Exception as log_err:
                        logs[relative_path] = f'Unable to read log file: {str(log_err)}'
                # Collect output files (exclude only scripts, logs, and metadata)
                elif not relative_path.startswith('slurm_') and relative_path not in ['run_job.sh', 'preprocess_pdb.sh', 'metadata.json']:
                    output_files.append(relative_path)
                    print(f"Added output file: {relative_path} ({file_size} bytes)")  # Debug print
                    
        except Exception as list_err:
            file_fetch_error = f'Could not list remote files: {str(list_err)}'
            print(f"Error listing files in {remote_job_dir}: {list_err}")
        
        sftp.close()
        client.close()
    except Exception as e:
        file_fetch_error = f'Could not connect to HPC: {str(e)}'
        print(f"Error connecting to HPC: {e}")
    
    # Add error to logs if admin
    if file_fetch_error and current_user.is_admin:
        logs['fetch_error'] = file_fetch_error
    
    return render_template('job_details.html', 
                         metadata=metadata, 
                         status=status, 
                         logs=logs,
                         output_files=output_files,
                         job_uuid=job_uuid)


@app.route('/debug-files/<job_uuid>')
@login_required
def debug_files(job_uuid):
    """Debug endpoint to see what files exist on HPC"""
    if not current_user.is_admin:
        return 'Admin only', 403
    
    job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
    if not job_dirs:
        return 'Job not found', 404
    
    local_job_dir = job_dirs[0]
    metadata_file = local_job_dir / 'metadata.json'
    
    if not metadata_file.exists():
        return 'Job metadata not found', 404
    
    metadata = json.loads(metadata_file.read_text())
    remote_job_dir = metadata['remote_job_dir']
    
    debug_info = {
        'remote_job_dir': remote_job_dir,
        'files': [],
        'error': None
    }
    
    try:
        client = get_ssh_client()
        sftp = client.open_sftp()
        
        import stat
        remote_files = sftp.listdir_attr(remote_job_dir)
        
        for file_attr in remote_files:
            file_info = {
                'name': file_attr.filename,
                'size': file_attr.st_size,
                'is_file': stat.S_ISREG(file_attr.st_mode),
                'is_dir': stat.S_ISDIR(file_attr.st_mode),
                'mode': oct(file_attr.st_mode)
            }
            debug_info['files'].append(file_info)
        
        sftp.close()
        client.close()
    except Exception as e:
        debug_info['error'] = str(e)
    
    return jsonify(debug_info)


@app.route('/download-all/<job_uuid>')
@login_required
def download_all_files(job_uuid):
    """Download all job files as a ZIP archive"""
    import zipfile
    import tempfile
    
    job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
    if not job_dirs:
        return 'Job not found', 404
    
    local_job_dir = job_dirs[0]
    metadata_file = local_job_dir / 'metadata.json'
    
    if not metadata_file.exists():
        return 'Job metadata not found', 404
    
    metadata = json.loads(metadata_file.read_text())
    
    # Check if job belongs to current user (or if user is admin)
    if not current_user.is_admin and metadata.get('user_id') != current_user.id:
        return 'Access denied', 403
    
    try:
        # Create a temporary ZIP file
        zip_filename = f"{metadata['job_name']}.zip"
        zip_path = local_job_dir / zip_filename
        
        # Connect to HPC and download all files
        client = get_ssh_client()
        sftp = client.open_sftp()
        remote_job_dir = metadata['remote_job_dir']
        
        import stat
        
        def download_recursive(sftp, remote_path, local_base_path):
            """Recursively download all files from remote directory"""
            try:
                items = sftp.listdir_attr(remote_path)
                for item in items:
                    remote_item_path = f"{remote_path}/{item.filename}"
                    relative_path = remote_item_path.replace(f"{remote_job_dir}/", "")
                    local_item_path = local_base_path / relative_path
                    
                    if stat.S_ISDIR(item.st_mode):
                        # Create local directory and recurse
                        local_item_path.mkdir(parents=True, exist_ok=True)
                        download_recursive(sftp, remote_item_path, local_base_path)
                    elif stat.S_ISREG(item.st_mode):
                        # Download file if not already present
                        if not local_item_path.exists():
                            local_item_path.parent.mkdir(parents=True, exist_ok=True)
                            sftp.get(remote_item_path, str(local_item_path))
            except Exception as e:
                print(f"Error downloading {remote_path}: {e}")
        
        # Download all files
        download_recursive(sftp, remote_job_dir, local_job_dir)
        
        sftp.close()
        client.close()
        
        # Create ZIP archive
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in local_job_dir.rglob('*'):
                if file_path.is_file() and file_path != zip_path:
                    # Add file to zip with relative path
                    arcname = file_path.relative_to(local_job_dir)
                    zipf.write(file_path, arcname)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        return f'Failed to create archive: {str(e)}', 500


@app.route('/download/<job_uuid>/<path:filename>')
@login_required
def download_file(job_uuid, filename):
    """Download output file from HPC"""
    job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
    if not job_dirs:
        return 'Job not found', 404
    
    local_job_dir = job_dirs[0]
    metadata_file = local_job_dir / 'metadata.json'
    
    if not metadata_file.exists():
        return 'Job metadata not found', 404
    
    metadata = json.loads(metadata_file.read_text())
    
    # Check if job belongs to current user (or if user is admin)
    if not current_user.is_admin and metadata.get('user_id') != current_user.id:
        return 'Access denied', 403
    
    # Handle relative paths (e.g., "output/file.txt")
    # Secure each part of the path separately
    path_parts = filename.split('/')
    safe_path_parts = [secure_filename(part) for part in path_parts]
    safe_relative_path = '/'.join(safe_path_parts)
    
    # Create local path preserving directory structure
    local_file_path = local_job_dir / safe_relative_path
    
    # If file doesn't exist locally, try to download from HPC
    if not local_file_path.exists():
        try:
            client = get_ssh_client()
            sftp = client.open_sftp()
            remote_path = f"{metadata['remote_job_dir']}/{safe_relative_path}"
            
            # Check if remote path is a file (not a directory)
            import stat
            file_attr = sftp.stat(remote_path)
            if not stat.S_ISREG(file_attr.st_mode):
                sftp.close()
                client.close()
                return 'Cannot download directories. Please contact admin if you need directory contents.', 400
            
            # Create local subdirectories if needed
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            sftp.get(remote_path, str(local_file_path))
            sftp.close()
            client.close()
        except Exception as e:
            return f'Failed to download file from HPC: {str(e)}', 500
    
    # Verify local file exists and is not empty
    if not local_file_path.exists() or local_file_path.stat().st_size == 0:
        return 'File is empty or does not exist', 404
    
    # Get just the filename for the download
    download_filename = path_parts[-1]
    return send_file(local_file_path, as_attachment=True, download_name=download_filename)


def cleanup_old_sessions(user_id, job_uuid):
    """Clean up old PyMOL sessions for a specific user and job"""
    import shutil
    
    if not PYMOL_CONFIG['enabled']:
        return
    
    try:
        shared_volume = PYMOL_CONFIG['shared_volume']
        pattern = f"{user_id}_{job_uuid}_*"
        
        # Find and remove old sessions
        for session_dir in shared_volume.glob(pattern):
            if session_dir.is_dir():
                try:
                    shutil.rmtree(session_dir)
                    print(f"Cleaned up old session: {session_dir.name}")
                except Exception as e:
                    print(f"Failed to cleanup {session_dir.name}: {e}")
    except Exception as e:
        print(f"Error during session cleanup: {e}")


@app.route('/api/prepare-pymol-session/<job_uuid>')
@login_required
def prepare_pymol_session(job_uuid):
    """Prepare a PyMOL VDI session with job files"""
    import time
    
    if not PYMOL_CONFIG['enabled']:
        return jsonify({'success': False, 'error': 'PyMOL visualization is not enabled'}), 503
    
    try:
        # Get job directory
        job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
        if not job_dirs:
            return jsonify({'success': False, 'error': 'Job not found'}), 404
        
        local_job_dir = job_dirs[0]
        metadata_file = local_job_dir / 'metadata.json'
        
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Job metadata not found'}), 404
        
        metadata = json.loads(metadata_file.read_text())
        
        # Check permissions
        if not current_user.is_admin and metadata.get('user_id') != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Ensure files are downloaded from HPC
        try:
            download_job_files_from_hpc(job_uuid, local_job_dir, metadata)
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to download files: {str(e)}'}), 500
        
        # Clean up old sessions for this user and job
        cleanup_old_sessions(current_user.id, job_uuid)
        
        # Create session directory in shared volume
        session_id = f"{current_user.id}_{job_uuid}_{int(time.time())}"
        session_dir = PYMOL_CONFIG['shared_volume'] / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create symlink to job directory (or copy files)
        import shutil
        data_link = session_dir / 'data'
        if data_link.exists():
            data_link.unlink()
        
        # Copy files instead of symlink for better compatibility
        shutil.copytree(local_job_dir, data_link, dirs_exist_ok=True)
        
        # Generate PyMOL startup script with absolute paths for container
        pymol_script = generate_pymol_script(session_id, data_link, metadata)
        script_file = session_dir / 'load_results.pml'
        script_file.write_text(pymol_script)
        
        # Create session metadata
        session_metadata = {
            'session_id': session_id,
            'user_id': current_user.id,
            'job_uuid': job_uuid,
            'job_name': metadata['job_name'],
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now().timestamp() + PYMOL_CONFIG['session_timeout'])
        }
        
        # Create a README for the user
        readme_file = session_dir / 'README.txt'
        readme_content = f"""MaSIF-neosurf Results - {metadata['job_name']}
{'='*60}

To load the results in PyMOL, run this command in the PyMOL console:

    @/data/{session_id}/load_results.pml

Or drag and drop the load_results.pml file into PyMOL.

Files are located in: /data/{session_id}/data/

Session expires at: {datetime.fromtimestamp(session_metadata['expires_at']).strftime('%Y-%m-%d %H:%M:%S')}
"""
        readme_file.write_text(readme_content)
        
        session_metadata_file = session_dir / 'session.json'
        session_metadata_file.write_text(json.dumps(session_metadata, indent=2))
        
        # Generate PyMOL VDI URL with auto-load script
        # Use vnc.html for the noVNC interface
        # Pass the script path as a parameter that PyMOL can auto-execute
        script_path = f"/data/{session_id}/load_results.pml"
        
        # Create a startup script that PyMOL will auto-execute
        startup_script = session_dir / 'startup.pml'
        startup_script.write_text(f"@{script_path}\n")
        
        # URL with autoconnect
        pymol_url = f"{PYMOL_CONFIG['url']}/vnc.html?autoconnect=true&resize=scale"
        
        return jsonify({
            'success': True,
            'pymol_url': pymol_url,
            'session_id': session_id,
            'script_path': script_path,
            'expires_in': PYMOL_CONFIG['session_timeout']
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_pymol_script(session_id, job_dir, metadata):
    """Generate PyMOL script to load MaSIF results
    
    Args:
        session_id: The session ID (used to construct absolute paths in container)
        job_dir: Local path to the data directory
        metadata: Job metadata dictionary
    """
    # Base path inside the PyMOL container
    container_data_path = f"/data/{session_id}/data"
    
    script = f"""# MaSIF-neosurf Results Visualization
# Job: {metadata['job_name']}
# Chain: {metadata['chain_id']}
# Submitted: {metadata['submitted_at']}

print "="*60
print "Loading MaSIF-neosurf results..."
print "Job: {metadata['job_name']}"
print "="*60

# Set background and rendering
bg_color white
set antialias, 2
set ray_trace_mode, 1
set surface_quality, 2
set transparency, 0.3

"""
    
    # Find PDB file
    pdb_filename = metadata.get('pdb_file', '')
    pdb_file = job_dir / pdb_filename
    
    if pdb_file.exists():
        pdb_path = f"{container_data_path}/{pdb_filename}"
        script += f"# Load PDB structure\n"
        script += f"load {pdb_path}, protein\n"
        script += "color cyan, protein\n"
        script += "show cartoon, protein\n"
        script += "hide lines, protein\n"
        script += "print 'Loaded protein structure: {pdb_filename}'\n\n"
    else:
        script += f"print 'Warning: PDB file not found: {pdb_filename}'\n\n"
    
    script += "# Load surface files (.ply)\n"
    
    # Find and load .ply files
    ply_files = sorted(job_dir.rglob('*.ply'))
    
    if ply_files:
        for i, ply_file in enumerate(ply_files):
            # Get relative path from job_dir
            rel_path = ply_file.relative_to(job_dir)
            # Construct absolute path in container
            ply_path = f"{container_data_path}/{rel_path}"
            obj_name = ply_file.stem.replace('-', '_').replace('.', '_')
            
            script += f"load {ply_path}, {obj_name}\n"
            
            # Color surfaces based on type
            if 'target' in ply_file.name.lower():
                script += f"color red, {obj_name}\n"
            elif 'ligand' in ply_file.name.lower():
                script += f"color yellow, {obj_name}\n"
            else:
                script += f"color green, {obj_name}\n"
        
        script += f"print 'Loaded {len(ply_files)} surface files'\n\n"
    else:
        script += "print 'Warning: No .ply surface files found'\n\n"
    
    script += """# Adjust view
zoom
center

print "="*60
print "MaSIF-neosurf results loaded successfully!"
print "="*60
print ""
print "Mouse controls:"
print "  Rotate: Left-click and drag"
print "  Zoom: Scroll wheel"
print "  Pan: Right-click and drag"
print ""

# Label
set label_size, 20
set label_color, black

print "MaSIF-neosurf results loaded successfully!"
print "Job: """ + metadata['job_name'] + """"
print "Use mouse to rotate, zoom, and explore the structure"
"""
    
    return script


def download_job_files_from_hpc(job_uuid, local_job_dir, metadata):
    """Download all job files from HPC if not already present"""
    try:
        client = get_ssh_client()
        sftp = client.open_sftp()
        remote_job_dir = metadata['remote_job_dir']
        
        import stat
        
        def download_recursive(sftp, remote_path, local_base_path):
            try:
                items = sftp.listdir_attr(remote_path)
                for item in items:
                    remote_item_path = f"{remote_path}/{item.filename}"
                    relative_path = remote_item_path.replace(f"{remote_job_dir}/", "")
                    local_item_path = local_base_path / relative_path
                    
                    if stat.S_ISDIR(item.st_mode):
                        local_item_path.mkdir(parents=True, exist_ok=True)
                        download_recursive(sftp, remote_item_path, local_base_path)
                    elif stat.S_ISREG(item.st_mode):
                        # Download if file doesn't exist or is empty
                        if not local_item_path.exists() or local_item_path.stat().st_size == 0:
                            local_item_path.parent.mkdir(parents=True, exist_ok=True)
                            sftp.get(remote_item_path, str(local_item_path))
            except Exception as e:
                print(f"Error downloading {remote_path}: {e}")
        
        download_recursive(sftp, remote_job_dir, local_job_dir)
        sftp.close()
        client.close()
        
    except Exception as e:
        print(f"Error connecting to HPC: {e}")
        raise


@app.route('/api/cleanup-pymol-session/<session_id>', methods=['POST'])
@login_required
def cleanup_pymol_session(session_id):
    """Clean up a PyMOL session"""
    if not PYMOL_CONFIG['enabled']:
        return jsonify({'success': False, 'error': 'PyMOL visualization is not enabled'}), 503
    
    try:
        session_dir = PYMOL_CONFIG['shared_volume'] / session_id
        
        if not session_dir.exists():
            return jsonify({'success': True, 'message': 'Session already cleaned up'})
        
        # Verify session belongs to current user
        session_metadata_file = session_dir / 'session.json'
        if session_metadata_file.exists():
            session_metadata = json.loads(session_metadata_file.read_text())
            if session_metadata.get('user_id') != current_user.id and not current_user.is_admin:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        # Remove session directory
        import shutil
        shutil.rmtree(session_dir)
        
        return jsonify({'success': True, 'message': 'Session cleaned up successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/pymol-health')
@login_required
def pymol_health():
    """Check PyMOL VDI container health status
    
    Returns container status and provides option to start if stopped
    """
    if not PYMOL_CONFIG['enabled']:
        return jsonify({
            'enabled': False,
            'status': 'disabled',
            'message': 'PyMOL visualization is disabled in configuration'
        })
    
    # Check Docker availability
    if not check_docker_available():
        return jsonify({
            'enabled': True,
            'status': 'error',
            'message': 'Docker is not available on this system',
            'can_start': False
        })
    
    # Check container status
    container_status = check_pymol_container_status()
    
    response = {
        'enabled': True,
        'status': container_status,
        'can_start': container_status in ['stopped', 'not_found']
    }
    
    if container_status == 'running':
        response['message'] = 'PyMOL VDI container is running'
        response['url'] = PYMOL_CONFIG['url']
    elif container_status == 'stopped':
        response['message'] = 'PyMOL VDI container is stopped'
    elif container_status == 'not_found':
        response['message'] = 'PyMOL VDI container not found'
    else:
        response['message'] = 'Error checking container status'
    
    return jsonify(response)


@app.route('/api/pymol-start', methods=['POST'])
@login_required
def pymol_start():
    """Start the PyMOL VDI container (admin only)"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin access required'}), 403
    
    if not PYMOL_CONFIG['enabled']:
        return jsonify({'success': False, 'error': 'PyMOL visualization is disabled'}), 503
    
    success, message = start_pymol_container()
    
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'error': message}), 500


@app.route('/download-multiple', methods=['POST'])
@login_required
def download_multiple_jobs():
    """Download multiple jobs as a single ZIP archive"""
    import zipfile
    import tempfile
    from datetime import datetime
    
    job_uuids = request.form.getlist('job_uuids')
    
    if not job_uuids:
        flash('No jobs selected for download', 'error')
        return redirect(url_for('list_jobs'))
    
    try:
        # Create a temporary ZIP file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"masif_jobs_{timestamp}.zip"
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_zip_path = Path(temp_zip.name)
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for job_uuid in job_uuids:
                # Find job directory
                job_dirs = list(app.config['OUTPUT_FOLDER'].glob(f'*_{job_uuid}'))
                if not job_dirs:
                    continue
                
                local_job_dir = job_dirs[0]
                metadata_file = local_job_dir / 'metadata.json'
                
                if not metadata_file.exists():
                    continue
                
                metadata = json.loads(metadata_file.read_text())
                
                # Check if job belongs to current user (or if user is admin)
                if not current_user.is_admin and metadata.get('user_id') != current_user.id:
                    continue
                
                job_name = metadata.get('job_name', job_uuid)
                
                # Download files from HPC if needed
                try:
                    client = get_ssh_client()
                    sftp = client.open_sftp()
                    remote_job_dir = metadata['remote_job_dir']
                    
                    import stat
                    
                    def download_recursive(sftp, remote_path, local_base_path):
                        """Recursively download all files from remote directory"""
                        try:
                            items = sftp.listdir_attr(remote_path)
                            for item in items:
                                remote_item_path = f"{remote_path}/{item.filename}"
                                relative_path = remote_item_path.replace(f"{remote_job_dir}/", "")
                                local_item_path = local_base_path / relative_path
                                
                                if stat.S_ISDIR(item.st_mode):
                                    # Create local directory and recurse
                                    local_item_path.mkdir(parents=True, exist_ok=True)
                                    download_recursive(sftp, remote_item_path, local_base_path)
                                elif stat.S_ISREG(item.st_mode):
                                    # Download file if not already present or if it's empty
                                    if not local_item_path.exists() or local_item_path.stat().st_size == 0:
                                        local_item_path.parent.mkdir(parents=True, exist_ok=True)
                                        sftp.get(remote_item_path, str(local_item_path))
                        except Exception as e:
                            print(f"Error downloading {remote_path}: {e}")
                    
                    # Download all files
                    download_recursive(sftp, remote_job_dir, local_job_dir)
                    
                    sftp.close()
                    client.close()
                except Exception as e:
                    print(f"Error downloading files for job {job_uuid}: {e}")
                
                # Add all files from this job to the ZIP
                for file_path in local_job_dir.rglob('*'):
                    if file_path.is_file():
                        # Skip metadata and scripts
                        if file_path.name in ['metadata.json', 'run_job.sh', 'preprocess_pdb.sh']:
                            continue
                        
                        # Add file to zip with job name as folder
                        relative_path = file_path.relative_to(local_job_dir)
                        arcname = f"{job_name}/{relative_path}"
                        zipf.write(file_path, arcname)
        
        # Send the ZIP file
        return send_file(
            temp_zip_path,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        flash(f'Failed to create archive: {str(e)}', 'error')
        return redirect(url_for('list_jobs'))


@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get all users
    users = load_users()
    user_list = []
    for user_id, user_data in users.items():
        user_info = {
            'id': user_id,
            'email': user_data['email'],
            'name': user_data['name'],
            'is_admin': user_data.get('is_admin', False),
            'email_verified': user_data.get('email_verified', False),
            'created_at': user_data.get('created_at', 'Unknown')
        }
        
        # Count jobs for this user (fast - no status checks)
        job_count = 0
        for job_dir in app.config['OUTPUT_FOLDER'].iterdir():
            if job_dir.is_dir():
                metadata_file = job_dir / 'metadata.json'
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text())
                    if metadata.get('user_id') == user_id:
                        job_count += 1
        
        user_info['job_count'] = job_count
        user_list.append(user_info)
    
    # Get job statistics (fast - just count files)
    total_jobs = sum(1 for d in app.config['OUTPUT_FOLDER'].iterdir() 
                     if d.is_dir() and (d / 'metadata.json').exists())
    
    stats = {
        'total_users': len(users),
        'total_jobs': total_jobs,
        'running_jobs': '?',  # Will be loaded via AJAX if needed
        'completed_jobs': '?',
        'failed_jobs': '?'
    }
    
    return render_template('admin.html', users=user_list, stats=stats)


@app.route('/admin/send-verification/<user_id>', methods=['POST'])
@login_required
def admin_send_verification(user_id):
    """Admin sends verification email to a user"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    users = load_users()
    user_data = users.get(user_id)
    
    if not user_data:
        flash('User not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if user_data.get('email_verified', False):
        flash('User is already verified', 'info')
        return redirect(url_for('admin_dashboard'))
    
    # Generate verification token
    token = str(uuid.uuid4())
    tokens = load_verification_tokens()
    
    # Clean up old tokens for this user
    tokens = {t: data for t, data in tokens.items() if data.get('user_id') != user_id}
    
    tokens[token] = {
        'user_id': user_id,
        'email': user_data['email'],
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now().timestamp() + 86400)  # 24 hours
    }
    save_verification_tokens(tokens)
    
    # Send verification email
    verification_link = url_for('verify_email', token=token, _external=True)
    email_subject = "Verify your MaSIF-neosurf account"
    email_body = f"""Hello {user_data['name']},

An administrator has sent you a verification link for the MaSIF-neosurf web application.

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

---
MaSIF-neosurf Web Interface
"""
    
    email_sent = send_email_via_hpc(user_data['email'], email_subject, email_body)
    
    if email_sent:
        flash(f'Verification email sent to {user_data["email"]}', 'success')
    else:
        flash(f'Failed to send email. Verification link: {verification_link}', 'error')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/submit-example', methods=['POST'])
@login_required
def submit_example():
    """Submit a pre-configured example job"""
    try:
        print("=== Submit Example Request ===")
        data = request.get_json()
        print(f"Request data: {data}")
        example_type = data.get('example_type')
        print(f"Example type: {example_type}")
        
        # Get the repository root (parent of ui folder)
        repo_root = Path(__file__).parent.parent
        example_dir = repo_root / 'example'
        
        if not example_dir.exists():
            return jsonify({'error': 'Example directory not found'}), 404
        
        # Define example configurations
        examples = {
            'basic': {
                'pdb_file': example_dir / '1a7x.pdb',
                'chain_id': '1A7X_A',
                'ligand_id': None,
                'sdf_file': None,
                'job_name': 'example_basic'
            },
            'ligand': {
                'pdb_file': example_dir / '1a7x.pdb',
                'chain_id': '1A7X_A',
                'ligand_id': 'FKA_B',
                'sdf_file': example_dir / '1a7x_C_FKA.sdf',
                'job_name': 'example_ligand'
            }
        }
        
        if example_type not in examples:
            return jsonify({'error': 'Invalid example type'}), 400
        
        config = examples[example_type]
        
        # Check if example files exist
        if not config['pdb_file'].exists():
            return jsonify({'error': f'Example PDB file not found: {config["pdb_file"]}'}), 404
        
        if config['sdf_file'] and not config['sdf_file'].exists():
            return jsonify({'error': f'Example SDF file not found: {config["sdf_file"]}'}), 404
        
        # Create unique job directory
        job_uuid = str(uuid.uuid4())[:8]
        job_name = f"{config['job_name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        local_job_dir = app.config['OUTPUT_FOLDER'] / f'{job_name}_{job_uuid}'
        local_job_dir.mkdir(exist_ok=True)
        
        # Copy example files to local job directory
        pdb_filename = config['pdb_file'].name
        local_pdb_path = local_job_dir / pdb_filename
        import shutil
        shutil.copy(config['pdb_file'], local_pdb_path)
        
        local_sdf_path = None
        sdf_filename = None
        if config['sdf_file']:
            sdf_filename = config['sdf_file'].name
            local_sdf_path = local_job_dir / sdf_filename
            shutil.copy(config['sdf_file'], local_sdf_path)
        
        # Copy preprocess_pdb.sh script
        preprocess_script = repo_root / 'preprocess_pdb.sh'
        local_preprocess = local_job_dir / 'preprocess_pdb.sh'
        if preprocess_script.exists():
            shutil.copy(preprocess_script, local_preprocess)
        
        # Remote paths on HPC
        remote_job_dir = f"{HPC_CONFIG['remote_work_dir']}/{job_name}_{job_uuid}"
        remote_pdb_path = f"{remote_job_dir}/{pdb_filename}"
        remote_sdf_path = f"{remote_job_dir}/{sdf_filename}" if sdf_filename else None
        
        # Connect to HPC and transfer files
        client = None
        try:
            client = get_ssh_client()
            sftp = client.open_sftp()
            
            # Create remote job directory
            try:
                sftp.mkdir(HPC_CONFIG['remote_work_dir'])
            except:
                pass
            sftp.mkdir(remote_job_dir)
            
            # Upload files
            sftp.put(str(local_pdb_path), remote_pdb_path)
            if local_sdf_path:
                sftp.put(str(local_sdf_path), remote_sdf_path)
            
            # Create a wrapper script that calls preprocess_pdb.sh from the HPC repo
            if HPC_CONFIG['masif_repo']:
                # Create a wrapper that changes to repo directory and runs the script
                wrapper_content = f"""#!/bin/bash
# Wrapper script to run preprocess_pdb.sh from the HPC repo
cd {HPC_CONFIG['masif_repo']}
./preprocess_pdb.sh "$@"
"""
                wrapper_path = f"{remote_job_dir}/preprocess_pdb.sh"
                sftp.putfo(StringIO(wrapper_content), wrapper_path)
                sftp.chmod(wrapper_path, 0o755)
            elif local_preprocess.exists():
                # Fallback: upload the script
                remote_preprocess = f"{remote_job_dir}/preprocess_pdb.sh"
                sftp.put(str(local_preprocess), remote_preprocess)
                sftp.chmod(remote_preprocess, 0o755)
            
            # Build command
            cmd_parts = [
                'masif-preprocess',
                remote_pdb_path,
                config['chain_id']
            ]
            
            if config['ligand_id'] and remote_sdf_path:
                cmd_parts.extend(['-l', config['ligand_id'], '-s', remote_sdf_path])
            
            cmd_parts.extend(['-o', remote_job_dir])
            
            # Create SLURM script
            easybuild_setup = ""
            if HPC_CONFIG['easybuild_prefix']:
                easybuild_setup = f"""
# EasyBuild configuration
export EASYBUILD_PREFIX={HPC_CONFIG['easybuild_prefix']}
export MODULEPATH=$EASYBUILD_PREFIX/modules/all:$MODULEPATH
"""
            
            slurm_content = f"""#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --output={remote_job_dir}/slurm_%j.out
#SBATCH --error={remote_job_dir}/slurm_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=4

# Function to send email notification
send_notification() {{
    local status=$1
    local job_id=$2
    
    if [ "$status" = "COMPLETED" ]; then
        local subject="MaSIF-neosurf Job Completed - {job_name}"
        local message="Your MaSIF-neosurf preprocessing job has completed successfully!

Job Name: {job_name}
Job ID: $job_id
Status: Completed

You can view and download your results at:
{url_for('job_details', job_uuid=job_uuid, _external=True)}

---
MaSIF-neosurf Web Interface"
    else
        local subject="MaSIF-neosurf Job Failed - {job_name}"
        local message="Your MaSIF-neosurf preprocessing job has failed.

Job Name: {job_name}
Job ID: $job_id
Status: $status

If you need assistance, please contact the administrator at:
yewmun.yip@crick.ac.uk

Include your Job ID in your email for faster support.

---
MaSIF-neosurf Web Interface"
    fi
    
    echo "$message" | /usr/bin/mail -s "$subject" {current_user.email}
}}

# Trap to send notification on exit
trap 'EXIT_CODE=$?; if [ $EXIT_CODE -eq 0 ]; then send_notification "COMPLETED" $SLURM_JOB_ID; else send_notification "FAILED" $SLURM_JOB_ID; fi' EXIT

# Initialize module system
if [ -f {HPC_CONFIG['module_init']} ]; then
    source {HPC_CONFIG['module_init']}
fi

# Source user bashrc to get additional module paths
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
{easybuild_setup}
# Load Singularity module first (try, but don't fail if not found)
module load Singularity/3.11.3 2>/dev/null || true

# Load MaSIF-neosurf module
module --ignore_cache load MaSIF-neosurf/1.0 2>/dev/null || true

# Add Singularity and MaSIF-neosurf bin to PATH manually
export PATH=/flask/apps/eb/software/Singularity/3.11.3/bin:{HPC_CONFIG['easybuild_prefix']}/software/MaSIF-neosurf/1.0/bin:$PATH

# Set MASIF_REPO environment variable for the container
export MASIF_REPO={HPC_CONFIG['masif_repo']}

echo "Starting MaSIF-neosurf preprocessing (Example Job)"
echo "Job directory: {remote_job_dir}"
echo "MaSIF repo: $MASIF_REPO"
echo "Command: {' '.join(cmd_parts)}"
echo "Started at: $(date)"

# Change to job directory (needed for preprocess_pdb.sh)
cd {remote_job_dir}

{' '.join(cmd_parts)}

echo "Completed at: $(date)"
"""
            
            # Upload SLURM script
            remote_script_path = f"{remote_job_dir}/run_job.sh"
            sftp.putfo(StringIO(slurm_content), remote_script_path)
            sftp.chmod(remote_script_path, 0o755)
            
            sftp.close()
            
            # Submit job
            stdin, stdout, stderr = client.exec_command(f'sbatch {remote_script_path}', timeout=10)
            exit_code = stdout.channel.recv_exit_status()
            sbatch_output = stdout.read().decode('utf-8')
            sbatch_error = stderr.read().decode('utf-8')
            
            if exit_code != 0:
                return jsonify({'error': f'Failed to submit job: {sbatch_error}'}), 500
            
            job_id = sbatch_output.strip().split()[-1]
            
        finally:
            if client:
                client.close()
        
        # Save metadata
        metadata = {
            'job_id': job_id,
            'job_name': job_name,
            'job_uuid': job_uuid,
            'user_id': current_user.id,
            'user_email': current_user.email,
            'local_job_dir': str(local_job_dir),
            'remote_job_dir': remote_job_dir,
            'pdb_file': pdb_filename,
            'chain_id': config['chain_id'],
            'ligand_id': config['ligand_id'],
            'sdf_file': sdf_filename,
            'submitted_at': datetime.now().isoformat(),
            'command': ' '.join(cmd_parts),
            'example_type': example_type
        }
        
        (local_job_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2))
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'job_name': job_name,
            'job_uuid': job_uuid,
            'message': f'Example job submitted successfully with ID: {job_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def migrate_existing_users():
    """Migrate existing users to add email_verified field"""
    users = load_users()
    updated = False
    
    for user_id, user_data in users.items():
        # Add email_verified field if missing
        if 'email_verified' not in user_data:
            # Admin accounts are automatically verified
            if user_data.get('is_admin', False):
                user_data['email_verified'] = True
                print(f"Verified admin account: {user_data['email']}")
            else:
                # Regular users default to unverified
                user_data['email_verified'] = False
                print(f"Marked as unverified: {user_data['email']}")
            updated = True
    
    if updated:
        save_users(users)
        print("User migration completed!")


if __name__ == '__main__':
    # Migrate existing users
    migrate_existing_users()
    # Initialize admin user on startup
    init_admin_user()
    app.run(host='0.0.0.0', port=5000, debug=True)
