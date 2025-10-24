# Flask Gmail System

A comprehensive email system built with Flask, featuring user authentication, JWT, MongoDB, password hashing, encryption, and full email functionality.

## Features

### 🔐 Authentication & Security
- **JWT-based authentication** with access and refresh tokens
- **Password hashing** using bcrypt
- **Data encryption** for sensitive user information
- **Rate limiting** to prevent abuse
- **CORS support** for cross-origin requests

### 📧 Email Functionality
- **Send emails** with support for multiple recipients
- **Email attachments** with file validation
- **Reply and forward** functionality
- **Email threading** for conversations
- **Search emails** by subject, body, or recipients
- **Email flags** (read, starred, important, deleted)
- **Folder management** (inbox, sent, archive, trash)

### 👤 User Management
- **User registration** with validation
- **Profile management** with avatar upload
- **Settings management** (notifications, privacy, theme)
- **User search** functionality
- **Account deactivation**

### 📊 Statistics & Monitoring
- **Email statistics** (counts by folder, unread, starred)
- **Storage usage** tracking
- **User activity** logging
- **Comprehensive error logging**

## Tech Stack

- **Backend**: Flask 3.1+
- **Database**: MongoDB with PyMongo
- **Authentication**: Flask-JWT-Extended
- **Security**: bcrypt, cryptography
- **Rate Limiting**: Flask-Limiter
- **Email**: Flask-Mail
- **CORS**: Flask-CORS
- **Python**: 3.12+

## Installation

### Prerequisites

1. **Python 3.12+**
2. **MongoDB** (local or cloud instance)
3. **Git**

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd flask-gmail-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```env
   # Flask Configuration
   SECRET_KEY=your-secret-key-here-change-in-production
   JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
   
   # MongoDB Configuration
   MONGODB_URI=mongodb://localhost:27017/
   DATABASE_NAME=flask_gmail_system
   
   # Email Configuration
   SECURITY_PASSWORD_SALT=your-password-salt-here-change-in-production
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_USE_TLS=True
   MAIL_USE_SSL=False
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   
   # Encryption Key (for encrypting sensitive user data)
   ENCRYPTION_KEY=your-encryption-key-here-change-in-production
   ```

5. **Start MongoDB**
   ```bash
   # If using local MongoDB
   mongod
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login user |
| POST | `/auth/logout` | Logout user |
| POST | `/auth/refresh` | Refresh JWT token |
| GET | `/auth/me` | Get current user info |
| GET | `/auth/check-username/<username>` | Check username availability |
| GET | `/auth/check-email/<email>` | Check email availability |

### Email Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mail/inbox` | Get user's inbox |
| GET | `/mail/sent` | Get sent emails |
| GET | `/mail/email/<email_id>` | Get specific email |
| POST | `/mail/send` | Send new email |
| POST | `/mail/send-with-attachments` | Send email with attachments |
| POST | `/mail/reply/<email_id>` | Reply to email |
| POST | `/mail/forward/<email_id>` | Forward email |
| POST | `/mail/email/<email_id>/read` | Mark email as read |
| POST | `/mail/email/<email_id>/star` | Toggle star status |
| POST | `/mail/email/<email_id>/important` | Toggle important status |
| POST | `/mail/email/<email_id>/move` | Move email to folder |
| DELETE | `/mail/email/<email_id>/delete` | Delete email |
| GET | `/mail/search` | Search emails |
| GET | `/mail/stats` | Get email statistics |
| GET | `/mail/thread/<thread_id>` | Get email thread |

### User Profile

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/profile` | Get user profile |
| PUT | `/user/profile` | Update user profile |
| POST | `/user/profile/avatar` | Upload avatar |
| GET | `/user/stats` | Get user statistics |
| GET | `/user/search` | Search users |
| POST | `/user/profile/change-password` | Change password |
| POST | `/user/profile/deactivate` | Deactivate account |

### Settings

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/settings` | Get user settings |
| PUT | `/user/settings` | Update user settings |
| PUT | `/user/settings/notifications` | Update notification settings |
| PUT | `/user/settings/privacy` | Update privacy settings |
| PUT | `/user/settings/theme` | Update theme |
| POST | `/user/settings/reset` | Reset settings to default |
| GET | `/user/settings/export` | Export settings |
| POST | `/user/settings/import` | Import settings |

## Usage Examples

### Register a new user
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword123"
  }'
```

### Send an email
```bash
curl -X POST http://localhost:5000/mail/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "recipients": ["recipient@example.com"],
    "subject": "Hello from Flask Gmail System",
    "body": "This is a test email sent from the Flask Gmail System."
  }'
```

### Get inbox
```bash
curl -X GET http://localhost:5000/mail/inbox \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Project Structure

```
flask-gmail-system/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── extensions.py            # Flask extensions
│   ├── auth/                    # Authentication module
│   │   ├── __init__.py
│   │   ├── login.py
│   │   ├── register.py
│   │   ├── logout.py
│   │   ├── password_reset.py
│   │   └── email_verification.py
│   ├── mail/                    # Email module
│   │   ├── __init__.py
│   │   ├── inbox.py
│   │   └── send.py
│   ├── user/                    # User management module
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   └── settings.py
│   ├── models/                  # Database models
│   │   ├── __init__.py
│   │   ├── user_model.py
│   │   └── mail_model.py
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── authmanager.py
│       └── logger.py
├── config.py                    # Configuration
├── app.py                       # Application entry point
├── pyproject.toml              # Project dependencies
├── README.md                   # This file
└── logs/                       # Application logs
```

## Security Features

- **Password Hashing**: All passwords are hashed using bcrypt
- **Data Encryption**: Sensitive user data is encrypted using Fernet
- **JWT Tokens**: Secure token-based authentication
- **Rate Limiting**: Prevents abuse and brute force attacks
- **Input Validation**: Comprehensive validation for all inputs
- **Error Handling**: Secure error handling without information leakage

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8 .
```

### Type Checking
```bash
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue on GitHub or contact the development team.

## Changelog

### v0.1.0
- Initial release
- Complete authentication system
- Full email functionality
- User profile management
- Settings management
- Comprehensive API documentation