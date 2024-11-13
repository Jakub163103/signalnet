# SignalNet

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Flask Version](https://img.shields.io/badge/Flask-3.0.3-green.svg)
![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)

## Table of Content

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Database Setup](#database-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Introduction

**SignalNet** is a robust Flask-based web application designed to provide real-time financial market signals. It empowers traders and investors with timely and accurate data to make informed decisions. With user authentication, subscription plans, and comprehensive notification systems, SignalNet ensures a seamless and secure experience for its users.

## Features

- **User Authentication**: Secure sign-up and login functionalities with password hashing.
- **Subscription Plans**: Multiple tiers (Basic, Pro, Professional) integrated with Stripe for payments.
- **Real-Time Financial Signals**: Fetches and displays real-time data from Binance.
- **Profile Management**: Users can update their profiles, including profile pictures.
- **Notifications**: Real-time in-app notifications with read/unread functionality.
- **Responsive Design**: Accessible on various devices and screen sizes.
- **Privacy Settings**: Detailed privacy and notification preferences.
- **Admin Dashboard**: Administrators can send notifications to all users.
- **Secure File Uploads**: Validates and securely handles profile picture uploads.
- **CSRF Protection**: Protects against Cross-Site Request Forgery attacks.

## Technologies Used

- **Backend**:
  - Python 3.10+
  - Flask 3.0.3
  - Flask-Login
  - Flask-Mail
  - Flask-Migrate
  - Flask-SocketIO
  - Flask-SQLAlchemy
  - Flask-WTF
  - SQLAlchemy
  - Alembic
  - Stripe API
- **Frontend**:
  - HTML5
  - CSS3
  - JavaScript
  - Bootstrap
  - Font Awesome
- **Database**:
  - SQLite (for development; can be switched to PostgreSQL/MySQL)
- **Others**:
  - dotenv
  - Pillow
  - Binance API

## Getting Started

### Prerequisites

- **Python 3.10+**: Ensure you have Python installed. You can download it [here](https://www.python.org/downloads/).
- **Git**: Version control system. Install it from [here](https://git-scm.com/downloads).
- **Virtual Environment Tool**: `venv` is recommended, which comes with Python.

### Installation

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/yourusername/SignalNet.git
    cd SignalNet
    ```

2. **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1. **Set Up Environment Variables**:

    Create a `.env` file in the root directory and populate it with the following variables:

    ```env
    SECRET_KEY=gfewregDewgwr432423423
    SQLALCHEMY_DATABASE_URI=sqlite:///site.db
    STRIPE_SECRET_KEY=sk_test_51QJFxwIAaVTtgQY4MB3DqYbBGQmC4IwwjLEPxVXzkgjUwCcIsXaF2ix78BXaeyR68PWhqTucsXqtiIMP3Hn6lk2B00j3l6nPyK
    STRIPE_PUBLIC_KEY=pk_test_51QJFxwIAaVTtgQY4nip1EPXyljQqx7kMajWfFZfBRTvEmpufRv7LWf8C0FgrhfoCVSBbV3j5okoZbOuxOZtKm34c003KlIYDtW
    MAIL_USERNAME=your_email@example.com
    MAIL_PASSWORD=your_email_password
    MAIL_SERVER=smtp.yourmailserver.com
    MAIL_PORT=587
    MAIL_USE_TLS=True
    BASIC_PRICE_ID=price_1QJyJbIAaVTtgQY4k8MYqnb1
    PRO_PRICE_ID=price_1QJyTpIAaVTtgQY4ro473TT3
    PROFESSIONAL_PRICE_ID=price_1QJyXAIAaVTtgQY4ptwnOTZ6
    ```

    **Note**: Replace the placeholder values with your actual credentials and keys.

2. **Initialize the Database**:

    ```bash
    flask db init
    flask db migrate -m "Initial migration."
    flask db upgrade
    ```

3. **Populate Subscription Plans**:

    Run the `add_subscription.py` script to add subscription plans to the database.

    ```bash
    python add_subscription.py
    ```

### Database Setup

SignalNet uses SQLAlchemy for ORM. The default configuration uses SQLite for development. For production, it's recommended to switch to PostgreSQL or MySQL.

Ensure the `SQLALCHEMY_DATABASE_URI` in your `.env` file points to your desired database.

## Usage

1. **Run the Application**:
    ```bash
    flask run
    ```

    The app will be accessible at `http://127.0.0.1:5000/`.

2. **Accessing the Application**:
    - **Home Page**: Explore the main features and subscribe to plans.
    - **Sign Up**: Create a new account.
    - **Login**: Access your dashboard and manage subscriptions.
    - **Profile**: Update your profile information and picture.
    - **Notifications**: View real-time notifications.
    - **Admin Dashboard**: Available to admin users for sending notifications.

3. **Testing Notifications**:
    - Visit `http://127.0.0.1:5000/test_flash` to test flash messages.

## Project Structure 