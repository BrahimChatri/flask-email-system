# 📧 Flask Email System

This is a learning project that simulates a basic email system (inspired by Gmail) using the **Flask** framework. The goal is to understand core backend development concepts such as authentication, encryption, database interaction, and modular architecture.

---

## 🚀 Features

- ✅ User Registration & Login
- 🔒 Secure Password Hashing using **bcrypt**
- 🔑 JWT-based Authentication with **flask-jwt-extended**
- 🗄 MongoDB Integration using **pymongo**
- 🔐 Message & User Data Encryption
- 📬 Send/Receive Emails (basic simulation)
- 🧩 Modular Architecture with Flask Blueprints
- 🛠 Environment Config with `.env` & `python-dotenv`
- 📦 Project managed using **uv** and **pyproject.toml**

---

## 🗂 Project Structure

```

flask-email-system/
├── app.py               # Entry point
├── config.py            # Configuration settings
├── .env                 # Environment variables
├── pyproject.toml       # Project & dependency management (via uv)
├── app/
│   ├── **init**.py      # App factory + blueprint registration
│   ├── auth/            # Auth routes: login, register, logout
│   ├── user/            # User profile management
│   ├── mail/            # Email features: send, inbox
│   ├── models/          # MongoDB schemas and database logic
│   └── utils/           # Reusable logic (JWT handling, logger, etc.)

````

---

## 🔧 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/BrahimChatri/flask-email-system.git
cd flask-email-system
````

### 2. Set up virtual environment using `uv`

```bash
uv venv  # Or `python -m venv venv` if you don't use uv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

### 3. Install Dependencies

```bash
uv sync # Or use `pip install -r requirements.txt` if you don't use uv
```

### 4. Set up your `.env` file

Create a `.env` file with the following content:

```env
SECRET_KEY=your_flask_secret
JWT_SECRET_KEY=your_jwt_secret
MONGO_URI=mongodb://localhost:27017/email_db
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
```

> ⚠ Never commit your `.env` file or secrets to GitHub.

---

## 🏁 Running the App

```bash
uv run app.py # Or `python app.py`
```

Flask will start on `http://127.0.0.1:5000`.

---

## 📬 Endpoints Overview

| Route            | Method | Description                 |
| ---------------- | ------ | --------------------------- |
| `/auth/register` | POST   | Register a new user         |
| `/auth/login`    | POST   | Login and get JWT           |
| `/user/profile`  | GET    | View current user's profile |
| `/mail/inbox`    | GET    | View received messages      |
| `/mail/send`     | POST   | Send a new message          |


---

## 🧠 Learning Goals

* Understand backend authentication and JWT
* Learn how to structure a real-world Flask project
* Practice integrating MongoDB into Python apps
* Work with encryption and security best practices
* Use modern Python tooling (`uv`, `.env`, `pyproject.toml`)

---

## 🪪 License

This project is licensed under the [MIT](LICENSE) License.