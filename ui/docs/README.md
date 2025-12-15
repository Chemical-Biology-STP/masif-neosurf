# MaSIF-neosurf Web Interface

A user-friendly Flask web application for running MaSIF-neosurf preprocessing on HPC via SLURM.

## Features

- 👥 User authentication with @crick.ac.uk email accounts
- 🌐 Web-based interface for non-command-line users
- 🔐 Secure SSH connection to HPC cluster
- 📤 File upload for PDB and SDF files
- 🚀 Automatic SLURM job submission via SSH
- 📊 Real-time job status monitoring
- 📥 Download output files directly from the browser
- 📝 View job logs and details
- 🔄 Automatic file transfer between web server and HPC
- 🔒 Each user can only see their own jobs
- 📧 Email notifications when jobs complete or fail

## Installation

1. Install dependencies with pixi:
```bash
cd ui
pixi install
```

2. Set up SSH key authentication to your HPC:
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096

# Copy public key to HPC
ssh-copy-id your_username@your-hpc-login-node.edu
```

3. Configure HPC connection:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your HPC details
nano .env
```

Set these variables in `.env`:
- `HPC_HOST`: Your HPC login node hostname
- `HPC_USER`: Your HPC username
- `HPC_SSH_KEY`: Path to your SSH private key
- `HPC_WORK_DIR`: Remote directory for job files on HPC
- `HPC_PORT`: SSH port (usually 22)

4. Ensure MaSIF-neosurf module is available on your HPC:
```bash
ssh your_username@your-hpc-login-node.edu
module load MaSIF-neosurf/1.0
```

## Usage

### Start the Web Server (Development)

```bash
# Load environment variables and start server
source .env  # or use python-dotenv
pixi run dev
```

The application will start on `http://0.0.0.0:5000`

**Note:** Make sure your `.env` file is configured with correct HPC credentials before starting.

### For Production Deployment

Use a production WSGI server like Gunicorn:

```bash
pixi add gunicorn
pixi run prod
```

Or run directly:
```bash
pixi run gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Access the Interface

1. Open your browser to `http://your-server:5000`
2. Register with your @crick.ac.uk email address
3. Log in with your credentials
4. Upload your PDB file and configure parameters
5. Submit the job
6. Monitor job status in the "My Jobs" page
7. Download results when complete

### User Management

- Users must register with a valid @crick.ac.uk email address
- **Email Verification Required**: New users must verify their email before logging in
  - Verification link sent via HPC mail system
  - Link valid for 24 hours
  - Can resend verification email if needed
- Passwords are securely hashed using Werkzeug
- Each user can only see and access their own jobs
- User data is stored in `users.json` (excluded from git)
- Users receive email notifications when their jobs complete or fail (via SLURM)

### Admin Account

- An admin account is automatically created on first startup
- **Email:** `admin@crick.ac.uk`
- **Default Password:** `admin123` (⚠️ **Change this immediately after first login!**)
- Admin can:
  - View all users' jobs
  - Access admin dashboard with system statistics
  - Monitor all job submissions across all users
  - Send verification emails to unverified users
  - View user verification status

### Password Management

- **Change Password**: All users can change their password via "Change Password" in the navigation menu
  - Requires current password verification
  - New password must be at least 8 characters
  
- **Forgot Password**: Users can reset their password if forgotten
  - Click "Forgot your password?" on the login page
  - Enter your @crick.ac.uk email
  - Receive a secure reset link via email (sent through HPC mail system)
  - Link is valid for 1 hour
  - Set a new password using the link
  
- All passwords are securely hashed using Werkzeug

## Configuration

- `UPLOAD_FOLDER`: Directory for uploaded files (default: `uploads/`)
- `OUTPUT_FOLDER`: Directory for job outputs (default: `outputs/`)
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 100MB)

## Security Notes

- Change the `SECRET_KEY` in production
- Consider adding authentication for multi-user environments
- Restrict network access appropriately
- Set proper file permissions on upload/output directories
