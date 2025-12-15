# MaSIF-neosurf Web Interface

A professional Flask web application for running MaSIF-neosurf preprocessing on HPC clusters via SLURM.

## 🚀 Quick Start

```bash
cd ui
pixi install
cp .env.example .env
# Edit .env with your HPC credentials
pixi run python app.py
```

Visit `http://localhost:5000` and register with your @crick.ac.uk email.

## 📁 Directory Structure

```
ui/
├── app.py                          # Main Flask application
├── email_notification_service.py  # Email notification daemon
├── templates/                      # HTML templates (Jinja2)
├── static/                         # Static assets (CSS, JS, images)
├── data/                          # User data and tokens (gitignored)
├── logs/                          # Application logs (gitignored)
├── scripts/                       # Utility and test scripts
├── docs/                          # Documentation
├── uploads/                       # Uploaded PDB/SDF files (gitignored)
├── outputs/                       # Job outputs (gitignored)
└── .env                           # Environment configuration (gitignored)
```

## ✨ Features

### User Management
- 🔐 Secure authentication with @crick.ac.uk emails only
- ✉️ Email verification required for new accounts
- 🔑 Password reset via email
- 👤 User profile and password management
- 👑 Admin dashboard for system monitoring

### Job Management
- 📤 Web-based file upload (PDB, SDF)
- 🚀 Automatic SLURM job submission via SSH
- 📊 Real-time job status monitoring
- 📥 Individual file downloads
- 📦 Bulk download (ZIP) for single or multiple jobs
- 📧 Email notifications on job completion/failure
- 🗂️ Organized file browser with directory tree

### User Experience
- 🎨 Modern, professional UI with animations
- 📱 Responsive design for mobile devices
- ⚡ Loading modals during file preparation
- 🔄 Auto-refresh for running jobs
- 💡 Contextual help and documentation
- ⚠️ Clear error messages and warnings

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Flask
SECRET_KEY=your-secret-key-here

# HPC Connection
HPC_HOST=your-hpc-login-node.edu
HPC_USER=your_username
HPC_SSH_KEY=/path/to/.ssh/id_rsa
HPC_WORK_DIR=/home/your_username/masif_jobs
HPC_PORT=22

# HPC Environment
HPC_MODULE_INIT=/etc/profile.d/modules.sh
HPC_EASYBUILD_PREFIX=/path/to/easybuild
HPC_MASIF_REPO=/path/to/masif-neosurf
```

### Admin Account

Default credentials (⚠️ **change immediately**):
- Email: `admin@crick.ac.uk`
- Password: `admin123`

## 📚 Documentation

- [Full Documentation](docs/README.md) - Complete setup and usage guide
- [Email Service Setup](docs/EMAIL_SERVICE_README.md) - Email notification configuration
- [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md) - Production deployment guide

## 🛠️ Development

### Running Tests

```bash
# Test SSH connection
pixi run python scripts/test_ssh_connection.py

# Test email notifications
bash scripts/test_email_notification.sh

# Test module loading
pixi run python scripts/test_module_load.py
```

### Starting Email Service

```bash
bash scripts/start_email_service.sh
bash scripts/check_email_service.sh
```

## 🔒 Security

- All passwords are hashed using Werkzeug
- User data stored in `data/` (excluded from git)
- SSH key-based authentication to HPC
- Session-based authentication with Flask-Login
- CSRF protection on all forms
- File upload validation and sanitization
- User isolation (can only access own jobs)

## 📦 Dependencies

- Flask - Web framework
- Flask-Login - User session management
- Paramiko - SSH connection to HPC
- python-dotenv - Environment configuration
- Werkzeug - Security utilities

## 🤝 Support

Created and maintained by **Yew Mun Yip**  
Chemical Biology STP, The Francis Crick Institute

For issues or questions, contact: yewmun.yip@crick.ac.uk

## 📄 License

See LICENSE file in the root directory.
