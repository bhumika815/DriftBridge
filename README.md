# 🌊 DriftBridge

### An AI-Powered Social Discovery Platform

DriftBridge is a privacy-focused social discovery platform that allows users to meet and communicate with new people through a controlled digital bottle system.

The platform combines anonymous social discovery, real-time multilingual communication, temporary stories, user profiles, connections, and a reputation system to create a safer and more meaningful way to interact online.

---

## 📌 Project Overview

DriftBridge is designed around the concept of a **digital bottle**.

Instead of directly searching for and contacting users, people can discover others through the bottle system. Users can choose whether to accept or discard a received bottle and can build connections through conversations.

The platform also supports multilingual communication using **local language detection and translation**, allowing users who speak different languages to communicate more easily.

---

## ✨ Features

### 🔐 Authentication & User Profiles

- User registration and login
- Secure password hashing
- Logout functionality
- User profile management
- Profile information and preferred language
- Session-based authentication

### 🍾 Digital Bottle System

- Send digital bottles to discover new users
- Receive bottles from other users
- Bottle pool for available discoveries
- Accept/keep bottles
- Throw/discard bottles
- Build connections through accepted bottles
- Block unwanted users

### 💬 Real-Time Chat

- One-to-one conversations
- Real-time messaging using Flask-SocketIO
- Message timestamps
- Conversation management
- Message length validation
- User blocking support
- Multilingual message translation

### 🌐 Local Language Detection & Translation

DriftBridge uses local libraries for language processing.

- Automatic message language detection using `langdetect`
- Local translation using Argos Translate
- Direct translation when a language pair is available
- English pivot translation when a direct language pair is unavailable
- No external AI API is required for translation
- Translation works without sending message content to an external AI service

### 📖 24-Hour Stories

- Create temporary stories
- View active stories
- Story feed
- User stories
- Story viewers
- Automatic expiry after 24 hours

### ⭐ Trust & Reputation System

Users can build reputation through their interactions on the platform.

The reputation system can be used to represent user trust and positive participation within DriftBridge.

### 🛡️ Safety & Privacy

- Password hashing
- Login protection
- User blocking
- Controlled social discovery
- Privacy-aware profile information
- Session-based authentication
- Message validation
- External AI content moderation has been removed from the current implementation

---

## 🧠 AI / Language Processing

The current implementation does **not** use any external generative-AI API.

Language-related functionality is handled locally using:

- **langdetect** — language detection
- **Argos Translate** — machine translation

This means the current translation system does not require an external AI API key.

---

## 🛠️ Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- Bootstrap

### Backend

- Python
- Flask
- Flask-SocketIO
- Flask-Login
- Flask-Bcrypt
- Flask-WTF

### Database

- MySQL
- SQLAlchemy
- Flask-Migrate
- Alembic
- PyMySQL

### Language Processing

- Argos Translate
- langdetect

### Development Tools

- Visual Studio Code
- Git
- GitHub
- MySQL Workbench

### Optional Services

- Cloudinary can be used for media storage where configured.

---

## 📋 Requirements

Before running DriftBridge, make sure you have:

- Python 3.x
- MySQL Server
- MySQL Workbench
- Git
- Visual Studio Code

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bhumika815/DriftBridge.git
cd DriftBridge