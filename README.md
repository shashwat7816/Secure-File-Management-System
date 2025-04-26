# Secure File Management System

A secure file management system that allows users to upload, download, encrypt, and decrypt files.

## Deployment

This application is ready for deployment on Vercel.

### Prerequisites

- Python 3.7+
- Flask
- SQLite
- Vercel account

### Local Development

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python api/index.py
   ```

### Vercel Deployment

1. Install the Vercel CLI:
   ```
   npm install -g vercel
   ```
2. Login to Vercel:
   ```
   vercel login
   ```
3. Deploy:
   ```
   vercel
   ```

## Limitations

- The Vercel deployment uses an in-memory SQLite database, which means:
  - Data will be lost between function invocations
  - This is suitable for demonstration purposes only
  - For production, consider using a persistent database service like PostgreSQL or MongoDB

## Test Account for Vercel

- Username: testuser
- Password: testuser123

## API Endpoints

- `/api/register` - Create a new user account
- `/api/login` - Log in to an existing account
- `/api/logout` - Log out of the current session
- `/api/upload` - Upload a file
- `/api/files` - List all files for the current user
- `/api/download` - Download a file
- `/api/delete` - Delete a file
- `/api/encrypt` - Encrypt a file
- `/api/decrypt` - Decrypt a file
- `/api/health` - Check the health of the API
- `/api/status` - Check the status of the API

## Security Features

- Password hashing with bcrypt
- File encryption with Fernet symmetric encryption
- Secure cookies
- CORS protection
- Input validation
