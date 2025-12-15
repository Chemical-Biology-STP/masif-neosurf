# Data Directory

This directory contains application data files that are generated at runtime.

## Files

- `users.json` - User account information (passwords are hashed)
- `reset_tokens.json` - Password reset tokens (temporary)
- `verification_tokens.json` - Email verification tokens (temporary)

## Security

⚠️ **Important**: These files contain sensitive user data and should never be committed to version control. They are excluded via `.gitignore`.

## Backup

Consider backing up `users.json` regularly to prevent data loss.
